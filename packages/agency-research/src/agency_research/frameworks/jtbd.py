"""Jobs-to-be-Done (JTBD) framework.

Extracts the functional and emotional jobs the audience is hiring content to do.
Needs CommentAnalysis or ListeningNodeReport to have useful signal.
Uses claude-haiku.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from agency_common.models import BrandProfile, JTBDJob, JTBDResult, ResearchOutput
from .base import FrameworkBase

LOGGER = logging.getLogger(__name__)

_PROMPT = """You are a consumer research analyst using the Jobs-to-be-Done framework.

Brand: {brand_name}
Audience: {audience}

Audience signals collected from social media and community listening:

Fears / pain points:
{fears}

Recurring questions:
{questions}

Desires:
{desires}

Community discussions:
{community}

Based on these signals, identify 4–5 distinct "jobs" the audience is hiring content (and the brand)
to do for them. A "job" is a progress the person is trying to make in their life.

Return a JSON object — no markdown, no explanation, JSON only:
{{
  "jobs": [
    {{
      "job": "The core job statement (verb + object, e.g. 'Reassure myself I'm making the right choice')",
      "context": "When / where this job arises (1 sentence)",
      "trigger": "The specific moment or event that triggers this job",
      "desired_outcome": "What success looks like for the person",
      "content_hook": "A specific content angle or format that would serve this job"
    }}
  ],
  "summary": "1–2 sentence strategic insight about what this audience really wants"
}}"""


class JTBDFramework(FrameworkBase):
    OUTPUT_FIELD = "jtbd"
    STALENESS_DAYS = 30

    def __init__(self, anthropic_api_key: str = "", dry_run: bool = False):
        self.anthropic_api_key = anthropic_api_key
        self.dry_run = dry_run

    def is_applicable(self, research: ResearchOutput, brand: BrandProfile) -> bool:
        has_comments = (
            research.comment_analysis is not None
            and bool(research.comment_analysis.clusters)
        )
        has_listening = (
            research.listening_node is not None
            and bool(research.listening_node.top_questions)
        )
        return has_comments or has_listening

    def analyze(self, research: ResearchOutput, brand: BrandProfile) -> JTBDResult:
        if self.dry_run:
            return JTBDResult(computed_at=datetime.utcnow().isoformat())

        if not self.anthropic_api_key:
            LOGGER.warning("No ANTHROPIC_API_KEY — skipping JTBD analysis")
            return JTBDResult(computed_at=datetime.utcnow().isoformat())

        fears, questions, desires = [], [], []
        if research.comment_analysis:
            for cluster in research.comment_analysis.clusters:
                if cluster.category == "fears":
                    fears = cluster.items[:6]
                elif cluster.category == "recurring_questions":
                    questions = cluster.items[:6]
                elif cluster.category == "desires":
                    desires = cluster.items[:6]

        community_lines: list[str] = []
        if research.listening_node:
            community_lines += research.listening_node.top_questions[:4]
            community_lines += research.listening_node.recurring_debates[:3]

        prompt = _PROMPT.format(
            brand_name=brand.name,
            audience=brand.audience.primary or "general audience",
            fears="\n".join(f"- {f}" for f in fears) or "- (none captured)",
            questions="\n".join(f"- {q}" for q in questions) or "- (none captured)",
            desires="\n".join(f"- {d}" for d in desires) or "- (none captured)",
            community="\n".join(f"- {c}" for c in community_lines) or "- (none captured)",
        )

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1400,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            data = json.loads(raw)
            jobs = [
                JTBDJob(
                    job=j.get("job", ""),
                    context=j.get("context", ""),
                    trigger=j.get("trigger", ""),
                    desired_outcome=j.get("desired_outcome", ""),
                    content_hook=j.get("content_hook", ""),
                )
                for j in data.get("jobs", [])
            ]
            return JTBDResult(
                computed_at=datetime.utcnow().isoformat(),
                jobs=jobs,
                summary=data.get("summary", ""),
            )
        except json.JSONDecodeError as exc:
            LOGGER.error("JTBD: JSON parse failed: %s", exc)
        except Exception as exc:
            LOGGER.error("JTBD LLM call failed: %s", exc)

        return JTBDResult(computed_at=datetime.utcnow().isoformat())
