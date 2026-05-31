"""Category Entry Points (CEP) framework — Byron Sharp.

Maps the mental triggers that bring a buyer into the category.
Needs community listening or content themes to have useful signal.
Uses claude-haiku.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from agency_common.models import BrandProfile, CEPEntry, CEPResult, ResearchOutput
from .base import FrameworkBase

LOGGER = logging.getLogger(__name__)

_PROMPT = """You are a brand strategy expert applying Byron Sharp's Category Entry Points framework.

Brand: {brand_name}
Category: {category}
Audience: {audience}

Content themes observed in the category:
{themes}

Community signals (questions, debates, emerging topics):
{community}

Your task: Identify 5–7 Category Entry Points — the specific mental contexts, moments, or
triggers that bring someone into this category and make them ready to engage or buy.
Think situationally: "When people are in situation X, they think of this category."

Return a JSON object — no markdown, no explanation, JSON only:
{{
  "entries": [
    {{
      "trigger": "The specific situation, moment, or mental state (be concrete, not generic)",
      "description": "Why this moment creates category need (1 sentence)",
      "content_hook": "Content format or angle that intercepts this moment"
    }}
  ],
  "summary": "1–2 sentences on the most important CEP opportunity for this brand"
}}"""


class CEPFramework(FrameworkBase):
    OUTPUT_FIELD = "cep"
    STALENESS_DAYS = 30

    def __init__(self, anthropic_api_key: str = "", dry_run: bool = False):
        self.anthropic_api_key = anthropic_api_key
        self.dry_run = dry_run

    def is_applicable(self, research: ResearchOutput, brand: BrandProfile) -> bool:
        has_themes = bool(research.cross_platform_themes) or any(
            platform.content_themes
            for platform in research.platforms.values()
        )
        has_community = (
            research.listening_node is not None
            and (
                research.listening_node.top_questions
                or research.listening_node.recurring_debates
            )
        )
        return has_themes or has_community

    def analyze(self, research: ResearchOutput, brand: BrandProfile) -> CEPResult:
        if self.dry_run:
            return CEPResult(computed_at=datetime.utcnow().isoformat())

        if not self.anthropic_api_key:
            LOGGER.warning("No ANTHROPIC_API_KEY — skipping CEP analysis")
            return CEPResult(computed_at=datetime.utcnow().isoformat())

        all_themes: list[str] = [t.theme for t in research.cross_platform_themes[:8]]
        for platform in research.platforms.values():
            for theme in platform.content_themes[:4]:
                if theme.theme not in all_themes:
                    all_themes.append(theme.theme)

        community_lines: list[str] = []
        if research.listening_node:
            community_lines += research.listening_node.top_questions[:4]
            community_lines += research.listening_node.recurring_debates[:3]
            community_lines += research.listening_node.emerging_keywords[:6]

        prompt = _PROMPT.format(
            brand_name=brand.name,
            category=brand.name,
            audience=brand.audience.primary or "general audience",
            themes="\n".join(f"- {t}" for t in all_themes[:12]) or "- (none captured)",
            community="\n".join(f"- {c}" for c in community_lines) or "- (none captured)",
        )

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            data = json.loads(raw)
            entries = [
                CEPEntry(
                    trigger=e.get("trigger", ""),
                    description=e.get("description", ""),
                    content_hook=e.get("content_hook", ""),
                )
                for e in data.get("entries", [])
            ]
            return CEPResult(
                computed_at=datetime.utcnow().isoformat(),
                entries=entries,
                summary=data.get("summary", ""),
            )
        except json.JSONDecodeError as exc:
            LOGGER.error("CEP: JSON parse failed: %s", exc)
        except Exception as exc:
            LOGGER.error("CEP LLM call failed: %s", exc)

        return CEPResult(computed_at=datetime.utcnow().isoformat())
