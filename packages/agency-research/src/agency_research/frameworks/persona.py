"""Persona + Psychographic Profiling framework.

Builds 2–3 audience segments from comment analysis, sentiment, and community signals.
Uses claude-haiku.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from agency_common.models import BrandProfile, PersonaResult, PersonaSegment, ResearchOutput
from .base import FrameworkBase

LOGGER = logging.getLogger(__name__)

_PROMPT = """You are an audience research specialist building psychographic personas.

Brand: {brand_name}
Primary audience description: {audience_desc}
Audience pain points: {pain_points}
Audience desires: {desires}

Sentiment breakdown: {sentiment}
Comment-derived fears: {fears}
Comment-derived desires: {comment_desires}
Community discussion topics: {community}

Build 2–3 distinct audience personas. Each should be specific enough to brief a content creator.

Return a JSON object — no markdown, no explanation, JSON only:
{{
  "personas": [
    {{
      "name": "Short archetype label (e.g. 'The Cautious Researcher')",
      "age_range": "e.g. '25–34'",
      "psychographic": "1 sentence — their worldview, values, and what drives their decisions",
      "pain_points": ["up to 4 specific pain points"],
      "content_preferences": ["up to 4 content formats or styles they respond to"],
      "where_they_hang_out": ["up to 3 platforms or communities"]
    }}
  ],
  "summary": "1–2 sentences on how to speak to all three personas with one content strategy"
}}"""


class PersonaFramework(FrameworkBase):
    OUTPUT_FIELD = "persona"
    STALENESS_DAYS = 30

    def __init__(self, anthropic_api_key: str = "", dry_run: bool = False):
        self.anthropic_api_key = anthropic_api_key
        self.dry_run = dry_run

    def is_applicable(self, research: ResearchOutput, brand: BrandProfile) -> bool:
        has_comment_data = (
            research.comment_analysis is not None
            and bool(research.comment_analysis.clusters)
        )
        has_sentiment = any(
            platform.sentiment is not None
            for platform in research.platforms.values()
        )
        return has_comment_data or has_sentiment or bool(brand.audience.pain_points)

    def analyze(self, research: ResearchOutput, brand: BrandProfile) -> PersonaResult:
        if self.dry_run:
            return PersonaResult(computed_at=datetime.utcnow().isoformat())

        if not self.anthropic_api_key:
            LOGGER.warning("No ANTHROPIC_API_KEY — skipping Persona analysis")
            return PersonaResult(computed_at=datetime.utcnow().isoformat())

        fears, comment_desires = [], []
        if research.comment_analysis:
            for cluster in research.comment_analysis.clusters:
                if cluster.category == "fears":
                    fears = cluster.items[:5]
                elif cluster.category == "desires":
                    comment_desires = cluster.items[:5]

        sentiment_parts: list[str] = []
        for platform_key, platform in research.platforms.items():
            if platform.sentiment:
                s = platform.sentiment
                sentiment_parts.append(
                    f"{platform_key}: {s.positive_pct:.0f}% positive, "
                    f"{s.negative_pct:.0f}% negative"
                )
        sentiment_str = "; ".join(sentiment_parts) or "not available"

        community_lines: list[str] = []
        if research.listening_node:
            community_lines += research.listening_node.top_questions[:4]
            community_lines += research.listening_node.recurring_debates[:2]

        prompt = _PROMPT.format(
            brand_name=brand.name,
            audience_desc=brand.audience.primary or "not specified",
            pain_points="\n".join(f"- {p}" for p in brand.audience.pain_points[:5]) or "- (none specified)",
            desires="\n".join(f"- {d}" for d in brand.audience.desires[:5]) or "- (none specified)",
            sentiment=sentiment_str,
            fears="\n".join(f"- {f}" for f in fears) or "- (none captured)",
            comment_desires="\n".join(f"- {d}" for d in comment_desires) or "- (none captured)",
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
            personas = [
                PersonaSegment(
                    name=p.get("name", ""),
                    age_range=p.get("age_range", ""),
                    psychographic=p.get("psychographic", ""),
                    pain_points=p.get("pain_points", []),
                    content_preferences=p.get("content_preferences", []),
                    where_they_hang_out=p.get("where_they_hang_out", []),
                )
                for p in data.get("personas", [])
            ]
            return PersonaResult(
                computed_at=datetime.utcnow().isoformat(),
                personas=personas,
                summary=data.get("summary", ""),
            )
        except json.JSONDecodeError as exc:
            LOGGER.error("Persona: JSON parse failed: %s", exc)
        except Exception as exc:
            LOGGER.error("Persona LLM call failed: %s", exc)

        return PersonaResult(computed_at=datetime.utcnow().isoformat())
