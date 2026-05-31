"""SWOT Analysis framework.

LLM-synthesised SWOT from the full ResearchOutput and BrandProfile.
Uses claude-haiku for speed and cost.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from agency_common.models import BrandProfile, ResearchOutput, SWOTResult
from .base import FrameworkBase

LOGGER = logging.getLogger(__name__)

_PROMPT = """You are a strategic marketing analyst. Given the research data below, produce a SWOT
analysis for the brand: {brand_name}

Brand context:
- Audience: {audience}
- Platforms: {platforms}
- Competitors: {competitors}

Research signals:
{research_signals}

Return a JSON object with EXACTLY this structure — no markdown, no explanation, JSON only:
{{
  "strengths": ["max 5 items — what the brand does or has that competitors don't"],
  "weaknesses": ["max 5 items — gaps vs. competitors or structural disadvantages"],
  "opportunities": ["max 5 items — market gaps, rising trends, underserved angles"],
  "threats": ["max 5 items — competitor momentum, platform risks, category shifts"],
  "summary": "2-sentence strategic takeaway"
}}

Be specific to this brand and the data provided. Avoid generic statements."""


def _build_signals(research: ResearchOutput, brand: BrandProfile) -> str:
    lines: list[str] = []

    for platform_key, platform in research.platforms.items():
        active = [c for c in platform.competitors if c.avg_engagement_rate > 0]
        if active:
            top = max(active, key=lambda c: c.avg_engagement_rate)
            lines.append(
                f"[{platform_key}] Engagement leader: {top.handle} "
                f"({top.avg_engagement_rate:.2%} avg ER, {top.follower_count:,} followers)"
            )
        themes = [t.theme for t in platform.content_themes[:4]]
        if themes:
            lines.append(f"[{platform_key}] Dominant themes: {', '.join(themes)}")
        rising = [h.tag for h in platform.trending_hashtags if h.trend_direction == "rising"][:5]
        if rising:
            lines.append(f"[{platform_key}] Rising hashtags: {', '.join(rising)}")

    if research.visual_dna and research.visual_dna.pattern_interrupt_opportunity:
        lines.append(f"Visual opportunity: {research.visual_dna.pattern_interrupt_opportunity}")

    if research.comment_analysis:
        if research.comment_analysis.content_pillars:
            lines.append(
                f"Audience pillars: {', '.join(research.comment_analysis.content_pillars[:3])}"
            )
        for cluster in research.comment_analysis.clusters:
            if cluster.items:
                lines.append(
                    f"Audience {cluster.category}: {'; '.join(cluster.items[:3])}"
                )

    if research.listening_node:
        if research.listening_node.top_questions:
            lines.append(
                f"Community top questions: {'; '.join(research.listening_node.top_questions[:3])}"
            )
        if research.listening_node.emerging_keywords:
            lines.append(
                f"Emerging keywords: {', '.join(research.listening_node.emerging_keywords[:8])}"
            )

    if research.ad_library and research.ad_library.winning_angles:
        lines.append(
            f"Competitor winning ad angles: {'; '.join(research.ad_library.winning_angles[:3])}"
        )

    if research.adjacency_report and research.adjacency_report.top_opportunities:
        lines.append(
            f"Cross-industry opportunities: {'; '.join(research.adjacency_report.top_opportunities[:3])}"
        )

    return "\n".join(lines) or "No detailed signals available."


class SWOTFramework(FrameworkBase):
    OUTPUT_FIELD = "swot"
    STALENESS_DAYS = 30

    def __init__(self, anthropic_api_key: str = "", dry_run: bool = False):
        self.anthropic_api_key = anthropic_api_key
        self.dry_run = dry_run

    def is_applicable(self, research: ResearchOutput, brand: BrandProfile) -> bool:
        return bool(research.platforms)

    def analyze(self, research: ResearchOutput, brand: BrandProfile) -> SWOTResult:
        if self.dry_run:
            return SWOTResult(computed_at=datetime.utcnow().isoformat())

        if not self.anthropic_api_key:
            LOGGER.warning("No ANTHROPIC_API_KEY — skipping SWOT analysis")
            return SWOTResult(computed_at=datetime.utcnow().isoformat())

        competitors_str = ", ".join(
            c.handle
            for platform in research.platforms.values()
            for c in platform.competitors[:5]
        ) or "none listed"

        prompt = _PROMPT.format(
            brand_name=brand.name,
            audience=brand.audience.primary or "not specified",
            platforms=", ".join(research.platforms.keys()) or "none",
            competitors=competitors_str,
            research_signals=_build_signals(research, brand),
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
            return SWOTResult(
                computed_at=datetime.utcnow().isoformat(),
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                opportunities=data.get("opportunities", []),
                threats=data.get("threats", []),
                summary=data.get("summary", ""),
            )
        except json.JSONDecodeError as exc:
            LOGGER.error("SWOT: JSON parse failed: %s", exc)
        except Exception as exc:
            LOGGER.error("SWOT LLM call failed: %s", exc)

        return SWOTResult(computed_at=datetime.utcnow().isoformat())
