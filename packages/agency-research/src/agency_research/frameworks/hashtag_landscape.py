"""Hashtag Landscape framework.

Tiers all observed hashtags by trend_score, surfaces opportunity tags (high score,
rising direction) and oversaturated ones (high post_count, low engagement).
Pure data computation — no LLM required.
"""
from __future__ import annotations

from datetime import datetime

from agency_common.models import (
    BrandProfile,
    HashtagLandscapeResult,
    HashtagTierGroup,
    HashtagTrend,
    ResearchOutput,
)
from .base import FrameworkBase

# trend_score thresholds for tiering (0–1 normalised score from TrendAnalyzer)
_BROAD_THRESHOLD = 0.65
_MID_THRESHOLD = 0.30


class HashtagLandscapeFramework(FrameworkBase):
    OUTPUT_FIELD = "hashtag_landscape"
    STALENESS_DAYS = 7

    def is_applicable(self, research: ResearchOutput, brand: BrandProfile) -> bool:
        has_platform_tags = any(
            platform.trending_hashtags
            for platform in research.platforms.values()
        )
        return has_platform_tags or bool(research.cross_platform_trends)

    def analyze(self, research: ResearchOutput, brand: BrandProfile) -> HashtagLandscapeResult:
        # Merge all hashtag trends, deduplicate by tag name
        seen: dict[str, HashtagTrend] = {}
        for platform in research.platforms.values():
            for ht in platform.trending_hashtags:
                existing = seen.get(ht.tag)
                if existing is None or ht.trend_score > existing.trend_score:
                    seen[ht.tag] = ht
        for ht in research.cross_platform_trends:
            existing = seen.get(ht.tag)
            if existing is None or ht.trend_score > existing.trend_score:
                seen[ht.tag] = ht

        all_trends = sorted(seen.values(), key=lambda h: h.trend_score, reverse=True)

        broad: list[HashtagTrend] = []
        mid: list[HashtagTrend] = []
        niche: list[HashtagTrend] = []

        for ht in all_trends:
            if ht.trend_score >= _BROAD_THRESHOLD:
                broad.append(ht)
            elif ht.trend_score >= _MID_THRESHOLD:
                mid.append(ht)
            else:
                niche.append(ht)

        def _avg_score(items: list[HashtagTrend]) -> float:
            if not items:
                return 0.0
            return round(sum(h.trend_score for h in items) / len(items), 4)

        tiers = [
            HashtagTierGroup(
                tier="broad",
                tags=[h.tag for h in broad[:20]],
                avg_trend_score=_avg_score(broad),
            ),
            HashtagTierGroup(
                tier="mid",
                tags=[h.tag for h in mid[:20]],
                avg_trend_score=_avg_score(mid),
            ),
            HashtagTierGroup(
                tier="niche",
                tags=[h.tag for h in niche[:20]],
                avg_trend_score=_avg_score(niche),
            ),
        ]

        # Existing brand hashtags (flatten all groups)
        ig_cfg = brand.platforms.instagram
        brand_tags: set[str] = set()
        if ig_cfg:
            brand_tags.update(ig_cfg.hashtag_groups.niche)
            brand_tags.update(ig_cfg.hashtag_groups.broad)
            brand_tags.update(ig_cfg.hashtag_groups.branded)

        # Opportunity: rising or stable + not already in brand set
        opportunity_tags = [
            h.tag for h in all_trends
            if h.trend_direction in ("rising", "stable")
            and h.tag not in brand_tags
            and h.trend_score >= _MID_THRESHOLD
        ][:15]

        # Oversaturated: high post_count, low avg_likes relative to peers
        if all_trends:
            avg_likes = sum(h.avg_likes for h in all_trends) / len(all_trends)
            avg_posts = sum(h.post_count for h in all_trends) / len(all_trends)
            oversaturated_tags = [
                h.tag for h in all_trends
                if h.post_count > avg_posts * 1.5
                and h.avg_likes < avg_likes * 0.6
            ][:10]
        else:
            oversaturated_tags = []

        # Recommended mix: ~20% broad, ~50% mid, ~30% niche
        recommended_mix = {
            "broad": [h.tag for h in broad[:3]],
            "mid": [h.tag for h in mid[:6]],
            "niche": [h.tag for h in niche[:4]],
        }

        summary_parts = [
            f"{len(all_trends)} hashtags mapped: "
            f"{len(broad)} broad / {len(mid)} mid / {len(niche)} niche."
        ]
        if opportunity_tags:
            summary_parts.append(f"Top opportunity tags: {', '.join(opportunity_tags[:5])}.")
        if oversaturated_tags:
            summary_parts.append(f"Avoid (oversaturated): {', '.join(oversaturated_tags[:3])}.")

        return HashtagLandscapeResult(
            computed_at=datetime.utcnow().isoformat(),
            tiers=tiers,
            opportunity_tags=opportunity_tags,
            oversaturated_tags=oversaturated_tags,
            recommended_mix=recommended_mix,
            summary=" ".join(summary_parts),
        )
