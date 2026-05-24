"""ResearchAgent — orchestrates scrapers and analyzers for a brand.

Five-step deep research pipeline:
  1. Listening node   — Reddit, YouTube RSS, X/Twitter community posts
  2. Meta Ad Library  — active ads running 30+ days (what converts)
  3. Visual DNA       — aesthetic trend analysis and pattern interrupt opportunity
  4. Comment analysis — LLM-extracted fears, questions, knowledge gaps, content pillars
  5. Adjacency map    — cross-industry narrative/visual trends bleeding into the category
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime

from agency_common.config import AgencyConfig
from agency_common.models import (
    AdLibraryReport,
    AdjacencyReport,
    BrandProfile,
    CommentAnalysis,
    ListeningNodeReport,
    PlatformResearch,
    PostData,
    ResearchOutput,
    VisualDNA,
)
from agency_common.obsidian_writer import update_brand_memory
from .analyzers import (
    AdjacencyMapper,
    CommentAnalyzer,
    CompetitorAnalyzer,
    SentimentAnalyzer,
    TrendAnalyzer,
    VisualAnalyzer,
)
from .scrapers import (
    ApifyInstagramScraper,
    CommunityListener,
    FacebookScraper,
    LinkedInScraper,
    MetaAdsLibraryScraper,
    PlaywrightInstagramScraper,
)

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
        scraper: str = "apify",
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

        # Step 1 & 2 scrapers
        self.community = CommunityListener(
            apify_token=self.config.apify_token,
            dry_run=dry_run,
        )
        self.meta_ads = MetaAdsLibraryScraper(
            access_token=self.config.meta_ad_library_token,
            apify_token=self.config.apify_token,
            dry_run=dry_run,
        )

        # Core analyzers
        self.competitor_analyzer = CompetitorAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()

        # Steps 3–5 analyzers
        self.visual_analyzer = VisualAnalyzer(
            anthropic_api_key=self.config.anthropic_api_key,
            dry_run=dry_run,
        )
        self.comment_analyzer = CommentAnalyzer(
            anthropic_api_key=self.config.anthropic_api_key,
            dry_run=dry_run,
        )
        self.adjacency_mapper = AdjacencyMapper(
            anthropic_api_key=self.config.anthropic_api_key,
            dry_run=dry_run,
        )

    def run(
        self,
        brand: BrandProfile,
        platforms: list[str] | None = None,
        post_count: int = 20,
        enable_listening: bool | None = None,
        enable_ads: bool | None = None,
        enable_visual_dna: bool | None = None,
        enable_comments: bool | None = None,
        enable_adjacencies: bool | None = None,
    ) -> ResearchOutput:
        """Run full research for a brand.

        The five new steps auto-enable when the brand has the relevant config fields
        populated. Pass explicit True/False to override.

        Args:
            brand: loaded BrandProfile
            platforms: list of platform keys to scrape (default: all configured)
            post_count: posts per competitor
            enable_listening: Step 1 — community listening node
            enable_ads: Step 2 — Meta Ad Library audit
            enable_visual_dna: Step 3 — visual DNA extraction
            enable_comments: Step 4 — LLM comment analysis
            enable_adjacencies: Step 5 — cross-industry adjacency map
        """
        if brand.memory:
            LOGGER.info("Brand memory loaded for %s (%d entries)", brand.slug, len(brand.memory))

        # Auto-detect which extended steps to run based on brand config
        do_listening = enable_listening if enable_listening is not None else bool(
            brand.community.subreddits or brand.community.youtube_channels or brand.community.x_lists
        )
        do_ads = enable_ads if enable_ads is not None else bool(brand.meta_ads.keywords)
        do_visual_dna = enable_visual_dna if enable_visual_dna is not None else True
        do_comments = enable_comments if enable_comments is not None else True
        do_adjacencies = enable_adjacencies if enable_adjacencies is not None else bool(brand.adjacent_industries)

        if platforms is None:
            platforms = []
            if brand.platforms.instagram:
                platforms.append("instagram")
            if brand.platforms.linkedin:
                platforms.append("linkedin")

        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        platform_results: dict[str, PlatformResearch] = {}
        all_posts: list[PostData] = []

        # ---- Platform scraping (existing pipeline) ----
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

        # ---- Step 1: Listening node ----
        listening_node: ListeningNodeReport | None = None
        if do_listening:
            LOGGER.info("Step 1: Running community listening node for %s", brand.slug)
            listening_node = self.community.scrape(
                subreddits=brand.community.subreddits,
                youtube_channels=brand.community.youtube_channels,
                x_lists=brand.community.x_lists,
                post_count=post_count,
            )

        # ---- Step 2: Meta Ad Library ----
        ad_library: AdLibraryReport | None = None
        if do_ads:
            LOGGER.info("Step 2: Auditing Meta Ad Library for %s", brand.slug)
            ad_library = self.meta_ads.audit(
                keywords=brand.meta_ads.keywords,
                countries=brand.meta_ads.countries or None,
            )

        # ---- Step 3: Visual DNA ----
        visual_dna: VisualDNA | None = None
        if do_visual_dna and all_posts:
            LOGGER.info("Step 3: Extracting visual DNA from %d posts", len(all_posts))
            visual_dna = self.visual_analyzer.analyze(all_posts)

        # ---- Step 4: Comment / audience analysis ----
        comment_analysis: CommentAnalysis | None = None
        if do_comments and all_posts:
            LOGGER.info("Step 4: Running LLM comment analysis on %d posts", len(all_posts))
            comment_analysis = self.comment_analyzer.analyze(
                posts=all_posts,
                subject=f"{brand.name} — {brand.audience.primary}",
            )

        # ---- Step 5: Adjacency mapping ----
        adjacency_report: AdjacencyReport | None = None
        if do_adjacencies:
            LOGGER.info("Step 5: Mapping cross-industry adjacencies for %s", brand.slug)
            adjacency_report = self.adjacency_mapper.map(
                primary_category=brand.name,
                adjacent_industries=brand.adjacent_industries,
            )

        output = ResearchOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            platforms=platform_results,
            cross_platform_trends=cross_trends,
            cross_platform_themes=cross_themes,
            listening_node=listening_node,
            ad_library=ad_library,
            visual_dna=visual_dna,
            comment_analysis=comment_analysis,
            adjacency_report=adjacency_report,
            summary=self._generate_summary(
                brand,
                platform_results,
                listening_node=listening_node,
                ad_library=ad_library,
                visual_dna=visual_dna,
                comment_analysis=comment_analysis,
                adjacency_report=adjacency_report,
            ),
        )

        # Distil one line from this run into brand memory
        top_insights = []
        for platform, research in platform_results.items():
            active = [c for c in research.competitors if c.avg_engagement_rate > 0]
            if active:
                top = max(active, key=lambda c: c.avg_engagement_rate)
                top_insights.append(
                    f"{platform}: {top.handle} leads at {top.avg_engagement_rate:.1%} engagement"
                )
        if visual_dna and visual_dna.pattern_interrupt_opportunity:
            top_insights.append(
                f"visual pattern interrupt: {visual_dna.pattern_interrupt_opportunity[:80]}"
            )
        if comment_analysis and comment_analysis.content_pillars:
            top_insights.append(
                f"audience pillar: {comment_analysis.content_pillars[0][:80]}"
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

    # ------------------------------------------------------------------
    # Platform research methods (unchanged)
    # ------------------------------------------------------------------

    def _research_instagram(self, brand: BrandProfile, post_count: int) -> PlatformResearch:
        ig_config = brand.platforms.instagram
        hashtags = ig_config.hashtag_groups.niche[:3] if ig_config else []

        competitors, hashtag_posts = self.ig.research_brand(
            competitor_handles=brand.competitors.instagram,
            hashtags=hashtags,
            post_count=post_count,
        )
        all_posts: list[PostData] = []
        for a in competitors:
            all_posts += a.top_posts
        all_posts += hashtag_posts

        return PlatformResearch(
            platform="instagram",
            scraped_at=datetime.utcnow().isoformat(),
            competitors=competitors,
            trending_hashtags=self.trend_analyzer.trending_hashtags(all_posts),
            content_themes=self.trend_analyzer.content_themes(all_posts),
            sentiment=self.sentiment_analyzer.analyze_posts(all_posts),
            raw_posts=all_posts[:100],
        )

    def _research_linkedin(self, brand: BrandProfile, post_count: int) -> PlatformResearch:
        competitors = []
        all_posts: list[PostData] = []
        for company_url in brand.competitors.linkedin:
            analysis = self.li.build_competitor_analysis(company_url, post_count=post_count)
            competitors.append(analysis)
            all_posts += analysis.top_posts

        return PlatformResearch(
            platform="linkedin",
            scraped_at=datetime.utcnow().isoformat(),
            competitors=competitors,
            trending_hashtags=self.trend_analyzer.trending_hashtags(all_posts),
            content_themes=self.trend_analyzer.content_themes(all_posts),
            sentiment=self.sentiment_analyzer.analyze_posts(all_posts),
            raw_posts=all_posts[:100],
        )

    def _research_facebook(self, brand: BrandProfile, post_count: int) -> PlatformResearch:
        competitors = []
        all_posts: list[PostData] = []
        for page in brand.competitors.facebook:
            analysis = self.fb.build_competitor_analysis(page, post_count=post_count)
            competitors.append(analysis)
            all_posts += analysis.top_posts

        return PlatformResearch(
            platform="facebook",
            scraped_at=datetime.utcnow().isoformat(),
            competitors=competitors,
            content_themes=self.trend_analyzer.content_themes(all_posts),
            raw_posts=all_posts[:100],
        )

    # ------------------------------------------------------------------
    # Summary generation
    # ------------------------------------------------------------------

    def _generate_summary(
        self,
        brand: BrandProfile,
        results: dict[str, PlatformResearch],
        listening_node: ListeningNodeReport | None = None,
        ad_library: AdLibraryReport | None = None,
        visual_dna: VisualDNA | None = None,
        comment_analysis: CommentAnalysis | None = None,
        adjacency_report: AdjacencyReport | None = None,
    ) -> str:
        parts = [f"# Research Summary: {brand.name}\n"]

        # ---- Platform sections ----
        for platform, research in results.items():
            comp_count = len(research.competitors)
            post_count = len(research.raw_posts)
            parts.append(f"## {platform.capitalize()} ({comp_count} competitors, {post_count} posts)\n")

            active = [c for c in research.competitors if c.avg_engagement_rate > 0]
            if active:
                top = max(active, key=lambda c: c.avg_engagement_rate)
                parts.append(
                    f"**Highest engagement**: {top.handle} "
                    f"({top.avg_engagement_rate:.2%} avg) — "
                    f"{top.follower_count:,} followers, "
                    f"posting {top.posting_frequency or 'unknown frequency'}."
                )

            format_counter: Counter = Counter()
            for c in research.competitors:
                for fmt, cnt in c.content_types.items():
                    format_counter[fmt] += cnt
            if format_counter:
                ranked = format_counter.most_common(3)
                fmt_str = ", ".join(f"{fmt} ({cnt})" for fmt, cnt in ranked)
                parts.append(f"**Format distribution**: {fmt_str}.")

            if research.content_themes:
                themes = [t.theme for t in research.content_themes[:6]]
                parts.append(f"**Competitor content themes**: {', '.join(themes)}.")

            if research.trending_hashtags:
                rising = [h for h in research.trending_hashtags if h.trend_direction == "rising"]
                stable = [h for h in research.trending_hashtags if h.trend_direction == "stable"]
                if rising:
                    parts.append(f"**Rising tags**: {', '.join(h.tag for h in rising[:5])}.")
                if stable:
                    parts.append(f"**Established tags**: {', '.join(h.tag for h in stable[:5])}.")

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

        # ---- Content gap ----
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
                f"angles they're not covering.\n"
            )

        # ---- Step 1: Listening node ----
        if listening_node and listening_node.posts:
            sources_str = ", ".join(listening_node.sources) or "community"
            parts.append(f"## Community Listening ({sources_str} — {len(listening_node.posts)} posts)\n")
            if listening_node.top_questions:
                parts.append("**Top consumer questions:**")
                for q in listening_node.top_questions[:6]:
                    parts.append(f"- {q}")
                parts.append("")
            if listening_node.recurring_debates:
                parts.append("**Recurring debates:**")
                for d in listening_node.recurring_debates[:4]:
                    parts.append(f"- {d}")
                parts.append("")
            if listening_node.emerging_keywords:
                kws = ", ".join(listening_node.emerging_keywords[:12])
                parts.append(f"**Emerging keywords**: {kws}\n")

        # ---- Step 2: Meta Ad Library ----
        if ad_library and ad_library.ads:
            parts.append(f"## Meta Ad Library ({len(ad_library.ads)} long-running ads)\n")
            if ad_library.winning_angles:
                parts.append("**Winning angles (ads running 30+ days):**")
                for angle in ad_library.winning_angles[:5]:
                    parts.append(f"- {angle}")
                parts.append("")
            if ad_library.top_ctas:
                parts.append(f"**Dominant CTAs**: {', '.join(ad_library.top_ctas[:4])}\n")

        # ---- Step 3: Visual DNA ----
        if visual_dna and visual_dna.dominant_aesthetic:
            parts.append("## Visual DNA\n")
            parts.append(f"**Dominant aesthetic**: {visual_dna.dominant_aesthetic}")
            if visual_dna.color_palette_trend:
                parts.append(f"**Color direction**: {visual_dna.color_palette_trend}")
            if visual_dna.pacing_trend:
                parts.append(f"**Content pacing**: {visual_dna.pacing_trend}")
            if visual_dna.industry_standard_aesthetic:
                parts.append(f"**Industry standard**: {visual_dna.industry_standard_aesthetic}")
            if visual_dna.pattern_interrupt_opportunity:
                parts.append(f"\n**Pattern interrupt opportunity**: {visual_dna.pattern_interrupt_opportunity}")
            parts.append("")

        # ---- Step 4: Comment / audience analysis ----
        if comment_analysis and comment_analysis.clusters:
            parts.append("## Audience Intelligence (LLM Comment Analysis)\n")
            for cluster in comment_analysis.clusters:
                if cluster.items:
                    label = cluster.category.replace("_", " ").title()
                    parts.append(f"**{label}:**")
                    for item in cluster.items[:5]:
                        parts.append(f"- {item}")
                    parts.append("")
            if comment_analysis.content_pillars:
                parts.append("**Suggested content pillars:**")
                for pillar in comment_analysis.content_pillars:
                    parts.append(f"- {pillar}")
                parts.append("")

        # ---- Step 5: Adjacency report ----
        if adjacency_report and adjacency_report.insights:
            parts.append("## Cross-Industry Adjacency Map\n")
            for insight in adjacency_report.insights[:5]:
                readiness = insight.readiness_to_cross or "unknown"
                parts.append(
                    f"**{insight.source_industry}** ({readiness}): "
                    f"{insight.trend_or_narrative}"
                )
                parts.append(f"  → *Adapt as*: {insight.how_to_adapt}")
                parts.append("")
            if adjacency_report.top_opportunities:
                parts.append("**Top cross-industry opportunities:**")
                for opp in adjacency_report.top_opportunities[:4]:
                    parts.append(f"- {opp}")
                parts.append("")

        return "\n".join(parts)
