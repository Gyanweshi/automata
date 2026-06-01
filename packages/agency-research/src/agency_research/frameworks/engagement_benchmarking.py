"""Engagement Rate Benchmarking framework.

Computes per-competitor ER, industry average, and relative position.
Pure data computation — no LLM required.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

from agency_common.models import (
    BrandProfile,
    CompetitorEngagementRow,
    EngagementBenchmark,
    ResearchOutput,
)
from .base import FrameworkBase


class EngagementBenchmarkingFramework(FrameworkBase):
    OUTPUT_FIELD = "engagement_benchmark"
    STALENESS_DAYS = 7

    def is_applicable(self, research: ResearchOutput, brand: BrandProfile) -> bool:
        return any(
            c.follower_count > 0 or c.avg_engagement_rate > 0
            for platform in research.platforms.values()
            for c in platform.competitors
        )

    def analyze(self, research: ResearchOutput, brand: BrandProfile) -> EngagementBenchmark:
        rows: list[CompetitorEngagementRow] = []
        for platform_key, platform in research.platforms.items():
            for comp in platform.competitors:
                if comp.avg_engagement_rate <= 0 and comp.follower_count <= 0:
                    continue
                primary_format = (
                    max(comp.content_types, key=comp.content_types.get)
                    if comp.content_types
                    else ""
                )
                rows.append(
                    CompetitorEngagementRow(
                        handle=comp.handle,
                        platform=platform_key,
                        follower_count=comp.follower_count,
                        avg_engagement_rate=comp.avg_engagement_rate,
                        primary_format=primary_format,
                    )
                )

        if not rows:
            return EngagementBenchmark(computed_at=datetime.utcnow().isoformat())

        valid_ers = [r.avg_engagement_rate for r in rows if r.avg_engagement_rate > 0]
        industry_avg = sum(valid_ers) / len(valid_ers) if valid_ers else 0.0

        for row in rows:
            row.er_vs_industry_avg = (
                round(row.avg_engagement_rate / industry_avg, 2) if industry_avg > 0 else 0.0
            )

        # Top format = most common primary_format among top-3 ER competitors
        top3 = sorted(rows, key=lambda r: r.avg_engagement_rate, reverse=True)[:3]
        format_counter: Counter = Counter(r.primary_format for r in top3 if r.primary_format)
        top_format = format_counter.most_common(1)[0][0] if format_counter else ""

        sorted_rows = sorted(rows, key=lambda r: r.avg_engagement_rate, reverse=True)
        summary_lines = [
            f"Industry avg ER: {industry_avg:.2%}. "
            f"Leader: {sorted_rows[0].handle} at {sorted_rows[0].avg_engagement_rate:.2%}."
        ]
        if top_format:
            summary_lines.append(f"Dominant format among top performers: {top_format}.")

        return EngagementBenchmark(
            computed_at=datetime.utcnow().isoformat(),
            industry_avg_er=round(industry_avg, 6),
            rows=sorted_rows,
            top_format_by_er=top_format,
            summary=" ".join(summary_lines),
        )
