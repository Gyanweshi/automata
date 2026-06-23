"""LLM comment analysis — surfaces fears, questions, and knowledge gaps from post text.

Step 4 of the deep research pipeline. Feeds top-performing post captions into Claude
with a structured prompt to extract the emotional drivers behind audience engagement.
The output directly hands you content pillars grounded in real consumer psychology.

Requires: ANTHROPIC_API_KEY
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from agency_common.models import CommentAnalysis, CommentCluster, PostData

LOGGER = logging.getLogger(__name__)

_ANALYSIS_PROMPT = """Analyze the following social media post texts. These are the top-performing
posts (ranked by engagement) in the subject area of: {subject}

Post texts:
{texts}

Your task: Identify the core consumer psychology patterns driving engagement in this content.

Return a JSON object with this EXACT structure — no markdown, no explanation, JSON only:
{{
  "fears": [
    "Core fear or pain point (max 6 items)"
  ],
  "recurring_questions": [
    "Question that keeps appearing or is implicitly answered (max 8 items)"
  ],
  "knowledge_gaps": [
    "Something the audience is clearly confused about or wants clarity on (max 6 items)"
  ],
  "desires": [
    "What the audience wants to achieve, feel, or experience (max 6 items)"
  ],
  "content_pillars": [
    "Pillar name: one-line description of the content angle (3-5 items)"
  ]
}}

Rules:
- Be specific — avoid generic answers like "they want to save money"
- Reference the actual subject matter
- Content pillars should directly address the fears, questions, and gaps above
- Each item is a plain string, not an object"""


class CommentAnalyzer:
    """Feed top post captions into Claude to extract audience intelligence."""

    def __init__(self, anthropic_api_key: str = "", openai_api_base: str = "", openai_api_key: str = "", dry_run: bool = False):
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_base = openai_api_base
        self.openai_api_key = openai_api_key
        self.dry_run = dry_run

    def analyze(
        self,
        posts: list[PostData],
        subject: str = "",
        top_n_posts: int = 25,
    ) -> CommentAnalysis:
        """Analyze top N posts by engagement and return audience psychology clusters."""
        if self.dry_run:
            return CommentAnalysis(analyzed_at=datetime.utcnow().isoformat())

        if not posts:
            return CommentAnalysis(analyzed_at=datetime.utcnow().isoformat())

        if not self.anthropic_api_key and not self.openai_api_base:
            LOGGER.warning("No ANTHROPIC_API_KEY or OPENAI_API_BASE — skipping comment analysis")
            return CommentAnalysis(analyzed_at=datetime.utcnow().isoformat())

        # Rank by engagement weight (comments signal intent more than likes)
        ranked = sorted(posts, key=lambda p: p.likes + p.comments * 3, reverse=True)[:top_n_posts]

        texts = []
        for post in ranked:
            if not post.caption:
                continue
            tag_line = f"[{post.platform} | {post.media_type or 'post'} | {post.likes} likes / {post.comments} comments]"
            texts.append(f"{tag_line}\n{post.caption[:600]}")

        if not texts:
            return CommentAnalysis(analyzed_at=datetime.utcnow().isoformat())

        prompt = _ANALYSIS_PROMPT.format(
            subject=subject or "social media content",
            texts="\n\n---\n\n".join(texts)[:14000],
        )

        try:
            if self.anthropic_api_key:
                import anthropic
                client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1800,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = response.content[0].text.strip()
            else:
                from openai import OpenAI
                client = OpenAI(base_url=self.openai_api_base, api_key=self.openai_api_key or "sk-local")
                response = client.chat.completions.create(
                    model="qwen2.5-7b-instruct",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1800,
                )
                raw = response.choices[0].message.content.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            data = json.loads(raw)

            clusters = [
                CommentCluster(
                    category="fears",
                    items=data.get("fears", []),
                    sentiment="negative",
                ),
                CommentCluster(
                    category="recurring_questions",
                    items=data.get("recurring_questions", []),
                    sentiment="neutral",
                ),
                CommentCluster(
                    category="knowledge_gaps",
                    items=data.get("knowledge_gaps", []),
                    sentiment="neutral",
                ),
                CommentCluster(
                    category="desires",
                    items=data.get("desires", []),
                    sentiment="positive",
                ),
            ]

            return CommentAnalysis(
                analyzed_at=datetime.utcnow().isoformat(),
                source_posts=[p.url for p in ranked if p.url][:15],
                comment_count=len(texts),
                clusters=clusters,
                content_pillars=data.get("content_pillars", []),
                raw_analysis=raw,
            )

        except json.JSONDecodeError as exc:
            LOGGER.error("Comment analysis: JSON parse failed: %s", exc)
            return CommentAnalysis(analyzed_at=datetime.utcnow().isoformat(), comment_count=len(texts))
        except Exception as exc:
            LOGGER.error("Comment analysis LLM call failed: %s", exc)
            return CommentAnalysis(analyzed_at=datetime.utcnow().isoformat(), comment_count=len(texts))
