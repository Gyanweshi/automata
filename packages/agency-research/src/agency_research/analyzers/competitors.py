"""Competitor benchmarking across platforms."""
from __future__ import annotations

from agency_common.models import CompetitorAnalysis


class CompetitorAnalyzer:
    """Analyze and benchmark competitors from scraped data."""

    def benchmark(self, competitors: list[CompetitorAnalysis]) -> dict:
        """Compute benchmark statistics across a set of competitors."""
        if not competitors:
            return {}
        followers = [c.follower_count for c in competitors if c.follower_count > 0]
        engagement_rates = [c.avg_engagement_rate for c in competitors if c.avg_engagement_rate > 0]
        result = {
            "count": len(competitors),
            "avg_followers": round(sum(followers) / len(followers), 0) if followers else 0,
            "max_followers": max(followers) if followers else 0,
            "min_followers": min(followers) if followers else 0,
            "avg_engagement_rate": round(sum(engagement_rates) / len(engagement_rates), 4) if engagement_rates else 0,
            "top_competitor": max(competitors, key=lambda c: c.follower_count, default=None),
        }
        if result["top_competitor"]:
            result["top_competitor"] = result["top_competitor"].handle
        return result

    def top_content_types(self, competitors: list[CompetitorAnalysis]) -> dict[str, int]:
        """Aggregate content type distribution across all competitors."""
        from collections import Counter
        counter: Counter = Counter()
        for c in competitors:
            for ct, cnt in c.content_types.items():
                counter[ct] += cnt
        return dict(counter.most_common())

    def top_hashtags(self, competitors: list[CompetitorAnalysis], top_n: int = 20) -> list[str]:
        """Return the most commonly used hashtags across all competitors."""
        from collections import Counter
        counter: Counter = Counter()
        for c in competitors:
            for tag in c.top_hashtags:
                counter[tag] += 1
        return [tag for tag, _ in counter.most_common(top_n)]
