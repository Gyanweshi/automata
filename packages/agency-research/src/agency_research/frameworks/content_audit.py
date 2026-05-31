"""Content Audit Matrix framework.

Maps each competitor across: format mix, posting frequency, themes.
Surfaces coverage gaps and high-opportunity formats.
Pure data computation — no LLM required.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

from agency_common.models import (
    BrandProfile,
    ContentAuditResult,
    ContentAuditRow,
    ResearchOutput,
)
from .base import FrameworkBase


class ContentAuditFramework(FrameworkBase):
    OUTPUT_FIELD = "content_audit"
    STALENESS_DAYS = 7

    def is_applicable(self, research: ResearchOutput, brand: BrandProfile) -> bool:
        return any(
            platform.competitors
            for platform in research.platforms.values()
        )

    def analyze(self, research: ResearchOutput, brand: BrandProfile) -> ContentAuditResult:
        rows: list[ContentAuditRow] = []
        all_formats: Counter = Counter()
        used_format_combos: list[frozenset] = []

        for platform_key, platform in research.platforms.items():
            # Cross-competitor theme list for this platform
            platform_themes = [t.theme for t in platform.content_themes[:5]]

            # Competitor ranked by ER for engagement_leader flag
            ranked = sorted(
                platform.competitors,
                key=lambda c: c.avg_engagement_rate,
                reverse=True,
            )
            leader_handle = ranked[0].handle if ranked else ""

            for comp in platform.competitors:
                primary_format = (
                    max(comp.content_types, key=comp.content_types.get)
                    if comp.content_types
                    else ""
                )
                for fmt, cnt in comp.content_types.items():
                    all_formats[fmt] += cnt

                if comp.content_types:
                    used_format_combos.append(frozenset(comp.content_types.keys()))

                rows.append(
                    ContentAuditRow(
                        handle=comp.handle,
                        platform=platform_key,
                        primary_format=primary_format,
                        format_mix=dict(comp.content_types),
                        posting_frequency=comp.posting_frequency,
                        primary_themes=platform_themes[:3],
                        engagement_leader=(comp.handle == leader_handle),
                    )
                )

        # Coverage gaps: formats used by only one competitor
        coverage_gaps = [
            fmt for fmt, count in all_formats.items() if count == 1
        ]

        # Opportunity formats: used by leader but not by most others
        leader_rows = [r for r in rows if r.engagement_leader]
        leader_formats: set[str] = set()
        for lr in leader_rows:
            leader_formats.update(lr.format_mix.keys())

        non_leader_formats: Counter = Counter()
        for r in rows:
            if not r.engagement_leader:
                non_leader_formats.update(r.format_mix.keys())

        total_non_leaders = max(1, sum(1 for r in rows if not r.engagement_leader))
        opportunity_formats = [
            fmt for fmt in leader_formats
            if (non_leader_formats.get(fmt, 0) / total_non_leaders) < 0.4
        ]

        summary_parts = [f"{len(rows)} competitors audited across {len(research.platforms)} platform(s)."]
        if coverage_gaps:
            summary_parts.append(f"Underused formats: {', '.join(coverage_gaps[:4])}.")
        if opportunity_formats:
            summary_parts.append(f"Leader-exclusive formats (opportunity): {', '.join(opportunity_formats[:4])}.")

        return ContentAuditResult(
            computed_at=datetime.utcnow().isoformat(),
            rows=rows,
            coverage_gaps=coverage_gaps,
            opportunity_formats=opportunity_formats,
            summary=" ".join(summary_parts),
        )
