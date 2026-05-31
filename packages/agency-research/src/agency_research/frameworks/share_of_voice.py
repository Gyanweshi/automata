"""Share of Voice framework.

Estimates each competitor's share of category engagement using:
    weight = follower_count * avg_engagement_rate

Brand's own SOV is omitted — follower counts are not stored in BrandProfile.
Pure data computation — no LLM required.
"""
from __future__ import annotations

from datetime import datetime

from agency_common.models import (
    BrandProfile,
    ResearchOutput,
    SOVRow,
    ShareOfVoiceResult,
)
from .base import FrameworkBase


class ShareOfVoiceFramework(FrameworkBase):
    OUTPUT_FIELD = "share_of_voice"
    STALENESS_DAYS = 7

    def is_applicable(self, research: ResearchOutput, brand: BrandProfile) -> bool:
        return any(
            c.follower_count > 0
            for platform in research.platforms.values()
            for c in platform.competitors
        )

    def analyze(self, research: ResearchOutput, brand: BrandProfile) -> ShareOfVoiceResult:
        raw: list[tuple[str, str, float]] = []  # (handle, platform, weight)

        for platform_key, platform in research.platforms.items():
            for comp in platform.competitors:
                if comp.follower_count <= 0:
                    continue
                weight = comp.follower_count * max(comp.avg_engagement_rate, 0.0)
                raw.append((comp.handle, platform_key, weight))

        if not raw:
            return ShareOfVoiceResult(computed_at=datetime.utcnow().isoformat())

        total_weight = sum(w for _, _, w in raw) or 1.0
        rows = sorted(
            [
                SOVRow(
                    handle=handle,
                    platform=platform_key,
                    estimated_engagement_weight=round(weight, 2),
                    sov_pct=round(weight / total_weight * 100, 2),
                )
                for handle, platform_key, weight in raw
            ],
            key=lambda r: r.sov_pct,
            reverse=True,
        )

        leader = rows[0]
        summary = (
            f"{leader.handle} leads with {leader.sov_pct:.1f}% estimated share of voice. "
            f"{len(rows)} competitors tracked."
        )

        return ShareOfVoiceResult(
            computed_at=datetime.utcnow().isoformat(),
            rows=rows,
            leader_handle=leader.handle,
            leader_sov_pct=leader.sov_pct,
            summary=summary,
        )
