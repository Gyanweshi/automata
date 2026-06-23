"""Visual DNA extractor — identifies aesthetic trends and pattern interrupt opportunities.

Step 3 of the deep research pipeline. Analyzes the top-performing posts' metadata to
characterize the prevailing aesthetic: color grading direction, typography style, content
pacing, and whether the space is moving toward maximalism or quiet luxury. Returns the
pattern interrupt opportunity — the aesthetic move that would stand out.

Requires: ANTHROPIC_API_KEY
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from agency_common.models import PostData, VisualDNA

LOGGER = logging.getLogger(__name__)

_VISUAL_DNA_PROMPT = """You are a visual trend analyst for premium social media brands.

Analyze the following top-performing social media posts (ranked by engagement, highest first).
Based on the post metadata — media types, caption styles, and engagement signals — identify
the prevailing visual aesthetic and trend direction in this content space.

Posts:
{posts_summary}

Return a JSON object with this EXACT structure — no markdown, no explanation, JSON only:
{{
  "dominant_aesthetic": "one of: maximalist | minimalist | quiet-luxury | bold-graphic | raw-authentic | editorial | cinematic | lo-fi | corporate-polished",
  "color_palette_trend": "Describe the dominant color direction in 1-2 sentences (e.g. warm earth tones, high-contrast black-and-white, pastel softness)",
  "typography_trend": "Describe the text/caption style trend (e.g. all-caps urgency, minimal sans-serif authority, handwritten authenticity)",
  "pacing_trend": "fast-cut | slow-burn | static | mixed — followed by a brief explanation",
  "industry_standard_aesthetic": "What the majority of content in this space is doing right now — the dominant mode",
  "pattern_interrupt_opportunity": "The specific aesthetic move that would visually stand out against the industry standard — be concrete",
  "reasoning": "2-3 sentences explaining your analysis and what signals led to these conclusions"
}}"""


class VisualAnalyzer:
    """Analyze top post metadata to extract aesthetic DNA and identify pattern interrupts."""

    def __init__(self, anthropic_api_key: str = "", openai_api_base: str = "", openai_api_key: str = "", dry_run: bool = False):
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_base = openai_api_base
        self.openai_api_key = openai_api_key
        self.dry_run = dry_run

    def analyze(self, posts: list[PostData], top_n: int = 30) -> VisualDNA:
        """Return VisualDNA from the top N posts by engagement."""
        if self.dry_run:
            return VisualDNA(analyzed_at=datetime.utcnow().isoformat())

        if not posts:
            return VisualDNA(analyzed_at=datetime.utcnow().isoformat())

        if not self.anthropic_api_key and not self.openai_api_base:
            LOGGER.warning("No ANTHROPIC_API_KEY or OPENAI_API_BASE — skipping visual DNA analysis")
            return VisualDNA(analyzed_at=datetime.utcnow().isoformat())

        ranked = sorted(posts, key=lambda p: p.likes + p.comments * 3, reverse=True)[:top_n]

        posts_summary_lines = []
        for i, post in enumerate(ranked, 1):
            caption_snippet = post.caption[:250].replace("\n", " ").strip() if post.caption else "(no caption)"
            line = (
                f"{i}. [{post.platform} | {post.media_type or 'unknown'} | "
                f"{post.likes:,} likes / {post.comments:,} comments]: {caption_snippet}"
            )
            posts_summary_lines.append(line)

        prompt = _VISUAL_DNA_PROMPT.format(
            posts_summary="\n".join(posts_summary_lines)
        )

        try:
            if self.anthropic_api_key:
                import anthropic
                client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1200,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = response.content[0].text.strip()
            else:
                from openai import OpenAI
                client = OpenAI(base_url=self.openai_api_base, api_key=self.openai_api_key or "sk-local")
                response = client.chat.completions.create(
                    model="qwen2.5-7b-instruct",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1200,
                )
                raw = response.choices[0].message.content.strip()

            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            data = json.loads(raw)

            return VisualDNA(
                analyzed_at=datetime.utcnow().isoformat(),
                dominant_aesthetic=data.get("dominant_aesthetic", ""),
                color_palette_trend=data.get("color_palette_trend", ""),
                typography_trend=data.get("typography_trend", ""),
                pacing_trend=data.get("pacing_trend", ""),
                industry_standard_aesthetic=data.get("industry_standard_aesthetic", ""),
                pattern_interrupt_opportunity=data.get("pattern_interrupt_opportunity", ""),
                raw_analysis=data.get("reasoning", ""),
            )

        except json.JSONDecodeError as exc:
            LOGGER.error("Visual DNA: JSON parse failed: %s", exc)
            return VisualDNA(analyzed_at=datetime.utcnow().isoformat())
        except Exception as exc:
            LOGGER.error("Visual DNA LLM call failed: %s", exc)
            return VisualDNA(analyzed_at=datetime.utcnow().isoformat())
