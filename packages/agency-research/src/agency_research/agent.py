"""ResearchAgent — orchestrates scrapers and analyzers for a brand."""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime

from agency_common.config import AgencyConfig
from agency_common.models import BrandProfile, PlatformResearch, ResearchOutput
from agency_common.obsidian_writer import update_brand_memory
from .analyzers import CompetitorAnalyzer, SentimentAnalyzer, TrendAnalyzer
from .scrapers import ApifyInstagramScraper, FacebookScraper, LinkedInScraper, PlaywrightInstagramScraper

LOGGER = logging.getLogger(__name__)

INSTAGRAM_SCRAPERS = {
    "apify": ApifyInstagramScraper,
    "playwright": PlaywrightInstagramScraper,
}


class ResearchAgent:
    """Run a full research sweep for a brand across all configured platforms."""

    def __init__(
        self,
        config: AgencyConfig | None = None,
        dry_run: bool = False,
        scraper: str = "playwright",
    ):
        self.config = config or AgencyConfig.from_env()
        self.dry_run = dry_run

        ig_cls = INSTAGRAM_SCRAPERS.get(scraper, ApifyInstagramScraper)
        if ig_cls is ApifyInstagramScraper:
            self.ig = ig_cls(dry_run=dry_run, api_token=self.config.apify_token)
        else:
            self.ig = ig_cls(dry_run=dry_run)
        self.li = LinkedInScraper(api_token=self.config.apify_token, dry_run=dry_run)
        self.fb = FacebookScraper(
            page_access_token=self.config.fb_page_access_token,
            apify_token=self.config.apify_token,
            dry_run=dry_run,
        )
        self.competitor_analyzer = CompetitorAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()

    def run(
        self,
        brand: BrandProfile,
        platforms: list[str] | None = None,
        post_count: int = 20,
    ) -> ResearchOutput:
        """Run research for a brand. platforms defaults to all configured platforms."""
        # Brand memory (past research findings) is already in brand.memory,
        # loaded from the ## Memory section of the brand .md note. No retrieval needed.
        if brand.memory:
            LOGGER.info("Brand memory loaded for %s (%d entries)", brand.slug, len(brand.memory))

        if platforms is None:
            platforms = []
            if brand.platforms.instagram:
                platforms.append("instagram")
            if brand.platforms.linkedin:
                platforms.append("linkedin")

        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        platform_results: dict[str, PlatformResearch] = {}
        all_posts = []

        if "instagram" in platforms:
            platform_results["instagram"] = self._research_instagram(brand, post_count)
            all_posts += platform_results["instagram"].raw_posts

        if "linkedin" in platforms:
            platform_results["linkedin"] = self._research_linkedin(brand, post_count)
            all_posts += platform_results["linkedin"].raw_posts

        if "facebook" in platforms:
            platform_results["facebook"] = self._research_facebook(brand, post_count)
            all_posts += platform_results["facebook"].raw_posts

        cross_trends = self.trend_analyzer.trending_hashtags(all_posts, top_n=20)
        cross_themes = self.trend_analyzer.content_themes(all_posts, top_n=10)

        output = ResearchOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            platforms=platform_results,
            cross_platform_trends=cross_trends,
            cross_platform_themes=cross_themes,
            summary=self._generate_summary(brand, platform_results),
        )

        # Distil one line from this research run into the brand memory.
        top_insights = []
        for platform, research in platform_results.items():
            active = [c for c in research.competitors if c.avg_engagement_rate > 0]
            if active:
                top = max(active, key=lambda c: c.avg_engagement_rate)
                top_insights.append(
                    f"{platform}: {top.handle} leads at {top.avg_engagement_rate:.1%} engagement"
                )
        insight = (
            "Research — " + "; ".join(top_insights)
            if top_insights
            else f"Research run on {', '.join(platform_results.keys()) or 'no platforms'}."
        )
        updated = update_brand_memory(brand_slug=brand.slug, insight=insight)
        if updated:
            LOGGER.info("Brand memory updated for %s", brand.slug)

        return output

    def _research_instagram(self, brand: BrandProfile, post_count: int) -> PlatformResearch:
        competitors = []
        all_posts = []

        ig_config = brand.platforms.instagram
        hashtags = ig_config.hashtag_groups.niche[:3] if ig_config else []

        competitors, hashtag_posts = self.ig.research_brand(
            competitor_handles=brand.competitors.instagram,
            hashtags=hashtags,
            post_count=post_count,
        )
        for a in competitors:
            all_posts += a.top_posts
        all_posts += hashtag_posts

        trending = self.trend_analyzer.trending_hashtags(all_posts)
        themes = self.trend_analyzer.content_themes(all_posts)
        sentiment = self.sentiment_analyzer.analyze_posts(all_posts)

        return PlatformResearch(
            platform="instagram",
            scraped_at=datetime.utcnow().isoformat(),
            competitors=competitors,
            trending_hashtags=trending,
            content_themes=themes,
            sentiment=sentiment,
            raw_posts=all_posts[:100],
        )

    def _research_linkedin(self, brand: BrandProfile, post_count: int) -> PlatformResearch:
        competitors = []
        all_posts = []
        for company_url in brand.competitors.linkedin:
            analysis = self.li.build_competitor_analysis(company_url, post_count=post_count)
            competitors.append(analysis)
            all_posts += analysis.top_posts

        trending = self.trend_analyzer.trending_hashtags(all_posts)
        themes = self.trend_analyzer.content_themes(all_posts)
        sentiment = self.sentiment_analyzer.analyze_posts(all_posts)

        return PlatformResearch(
            platform="linkedin",
            scraped_at=datetime.utcnow().isoformat(),
            competitors=competitors,
            trending_hashtags=trending,
            content_themes=themes,
            sentiment=sentiment,
            raw_posts=all_posts[:100],
        )

    def _research_facebook(self, brand: BrandProfile, post_count: int) -> PlatformResearch:
        competitors = []
        all_posts = []
        for page in brand.competitors.facebook:
            analysis = self.fb.build_competitor_analysis(page, post_count=post_count)
            competitors.append(analysis)
            all_posts += analysis.top_posts

        themes = self.trend_analyzer.content_themes(all_posts)

        return PlatformResearch(
            platform="facebook",
            scraped_at=datetime.utcnow().isoformat(),
            competitors=competitors,
            content_themes=themes,
            raw_posts=all_posts[:100],
        )

    def _generate_summary(
        self,
        brand: BrandProfile,
        results: dict[str, PlatformResearch],
    ) -> str:
        parts = [f"# Research Summary: {brand.name}\n"]

        for platform, research in results.items():
            comp_count = len(research.competitors)
            post_count = len(research.raw_posts)
            parts.append(f"## {platform.capitalize()} ({comp_count} competitors, {post_count} posts)\n")

            # Highest-engagement competitor
            active = [c for c in research.competitors if c.avg_engagement_rate > 0]
            if active:
                top = max(active, key=lambda c: c.avg_engagement_rate)
                parts.append(
                    f"**Highest engagement**: {top.handle} "
                    f"({top.avg_engagement_rate:.2%} avg) — "
                    f"{top.follower_count:,} followers, "
                    f"posting {top.posting_frequency or 'unknown frequency'}."
                )

            # Dominant content formats across all competitors
            format_counter: Counter = Counter()
            for c in research.competitors:
                for fmt, cnt in c.content_types.items():
                    format_counter[fmt] += cnt
            if format_counter:
                ranked = format_counter.most_common(3)
                fmt_str = ", ".join(f"{fmt} ({cnt})" for fmt, cnt in ranked)
                parts.append(f"**Format distribution**: {fmt_str}.")

            # Top themes from competitor captions
            if research.content_themes:
                themes = [t.theme for t in research.content_themes[:6]]
                parts.append(f"**Competitor content themes**: {', '.join(themes)}.")

            # Top trending hashtags by trend score
            if research.trending_hashtags:
                rising = [h for h in research.trending_hashtags if h.trend_direction == "rising"]
                stable = [h for h in research.trending_hashtags if h.trend_direction == "stable"]
                if rising:
                    parts.append(f"**Rising tags**: {', '.join(h.tag for h in rising[:5])}.")
                if stable:
                    parts.append(f"**Established tags**: {', '.join(h.tag for h in stable[:5])}.")

            # Top posts worth noting
            top_posts = sorted(research.raw_posts, key=lambda p: p.likes + p.comments * 3, reverse=True)[:3]
            if top_posts:
                parts.append("\n**Top performing posts:**")
                for post in top_posts:
                    snippet = post.caption[:120].replace("\n", " ").strip()
                    if len(post.caption) > 120:
                        snippet += "..."
                    parts.append(
                        f"- {post.likes:,} likes / {post.comments:,} comments "
                        f"[{post.media_type or 'post'}]: \"{snippet}\""
                    )

            parts.append("")

        # Content gap: themes competitors cluster on vs. brand's declared pillars
        all_competitor_themes: set[str] = set()
        for r in results.values():
            for t in r.content_themes[:10]:
                all_competitor_themes.add(t.theme.lower())

        if all_competitor_themes:
            theme_list = ", ".join(sorted(all_competitor_themes)[:8])
            parts.append(
                f"## Content Gap Opportunity\n"
                f"Competitors cluster around: {theme_list}.\n"
                f"Cross-reference with {brand.name}'s content pillars to identify "
                f"angles they're not covering — that's where differentiated content lives.\n"
            )

        return "\n".join(parts)
