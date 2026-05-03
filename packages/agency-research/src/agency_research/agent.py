"""ResearchAgent — orchestrates scrapers and analyzers for a brand."""
from __future__ import annotations

from datetime import datetime

from agency_common.config import AgencyConfig
from agency_common.models import BrandProfile, PlatformResearch, ResearchOutput
from agency_common.workspace import WorkspaceManager

from .analyzers import CompetitorAnalyzer, SentimentAnalyzer, TrendAnalyzer
from .scrapers import ApifyInstagramScraper, FacebookScraper, InstagramScraper, LinkedInScraper, PlaywrightInstagramScraper

# Scraper backends available for Instagram
INSTAGRAM_SCRAPERS = {
    "apify": ApifyInstagramScraper,
    "playwright": PlaywrightInstagramScraper,
    "instaloader": InstagramScraper,
}


class ResearchAgent:
    """Run a full research sweep for a brand across all configured platforms.

    Args:
        scraper: Instagram scraper backend — "playwright" (default) or "instaloader".
                 Playwright uses a real browser session; instaloader uses the API.
    """

    def __init__(
        self,
        config: AgencyConfig | None = None,
        dry_run: bool = False,
        scraper: str = "playwright",
    ):
        self.config = config or AgencyConfig.from_env()
        self.dry_run = dry_run

        ig_cls = INSTAGRAM_SCRAPERS.get(scraper, ApifyInstagramScraper)
        self.ig = ig_cls(
            username=self.config.instaloader_username,
            password=self.config.instaloader_password,
            api_token=self.config.apify_token,
            dry_run=dry_run,
        )
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

        return ResearchOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            platforms=platform_results,
            cross_platform_trends=cross_trends,
            cross_platform_themes=cross_themes,
            summary=self._generate_summary(brand, platform_results),
        )

    def _research_instagram(self, brand: BrandProfile, post_count: int) -> PlatformResearch:
        competitors = []
        all_posts = []

        ig_config = brand.platforms.instagram
        hashtags = ig_config.hashtag_groups.niche[:3] if ig_config else []

        # Playwright and Apify: batch scrape in one call
        if isinstance(self.ig, (PlaywrightInstagramScraper, ApifyInstagramScraper)):
            competitors, hashtag_posts = self.ig.research_brand(
                competitor_handles=brand.competitors.instagram,
                hashtags=hashtags,
                post_count=post_count,
            )
            for a in competitors:
                all_posts += a.top_posts
            all_posts += hashtag_posts
        else:
            # instaloader: legacy per-handle calls
            for handle in brand.competitors.instagram:
                analysis = self.ig.build_competitor_analysis(handle, post_count=post_count)
                competitors.append(analysis)
                all_posts += analysis.top_posts
            for tag in hashtags:
                posts = self.ig.scrape_hashtag_posts(tag, count=20)
                all_posts += posts

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

    def _generate_summary(self, brand: BrandProfile, results: dict[str, PlatformResearch]) -> str:
        parts = [f"Research completed for {brand.name}."]
        for platform, research in results.items():
            comp_count = len(research.competitors)
            post_count = len(research.raw_posts)
            parts.append(f"{platform.capitalize()}: {comp_count} competitors, {post_count} posts analyzed.")
        return " ".join(parts)
