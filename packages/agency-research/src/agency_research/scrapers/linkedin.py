"""LinkedIn scraper via Apify actors (handles anti-bot measures)."""
from __future__ import annotations

import logging

from tenacity import retry, stop_after_attempt, wait_exponential

from agency_common.models import CompetitorAnalysis, PostData
from agency_common.rate_limiter import apify_limiter

logger = logging.getLogger(__name__)

def _return_empty_list(retry_state):
    logger.error(f"LinkedIn scrape_company_posts failed after {retry_state.attempt_number} attempts: {retry_state.outcome.exception()}")
    return []

def _return_error_profile(retry_state):
    exc = retry_state.outcome.exception()
    logger.error(f"LinkedIn scrape_company_profile failed after {retry_state.attempt_number} attempts: {exc}")
    handle = retry_state.args[1] if len(retry_state.args) > 1 else "unknown"
    return CompetitorAnalysis(handle=handle, platform="linkedin", bio=f"Error: {exc}")


class LinkedInScraper:
    """Scrape LinkedIn company profiles and posts via Apify.

    Requires APIFY_API_TOKEN. Uses maintained Apify actors that handle
    LinkedIn's anti-scraping measures.
    """

    POSTS_ACTOR = "curious_coder/linkedin-post-search-scraper"
    PROFILE_ACTOR = "curious_coder/linkedin-company-scraper"

    def __init__(self, api_token: str = "", dry_run: bool = False):
        self.api_token = api_token
        self.dry_run = dry_run

    def _client(self):
        from apify_client import ApifyClient
        return ApifyClient(self.api_token)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry_error_callback=_return_empty_list)
    def scrape_company_posts(self, company_url: str, count: int = 20) -> list[PostData]:
        """Scrape recent posts from a LinkedIn company page."""
        if self.dry_run or not self.api_token:
            return []

        apify_limiter.wait()
        client = self._client()
        run = client.actor(self.POSTS_ACTOR).call(run_input={
            "profileUrls": [company_url],
            "maxResults": count,
        })
        posts = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            posts.append(PostData(
                platform="linkedin",
                post_id=item.get("id", ""),
                url=item.get("url", ""),
                caption=item.get("text", ""),
                likes=item.get("likes", 0),
                comments=item.get("comments", 0),
                shares=item.get("shares", 0),
                timestamp=item.get("postedAt", ""),
                hashtags=item.get("hashtags", []),
                media_type=item.get("type", ""),
            ))
        return posts

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry_error_callback=_return_error_profile)
    def scrape_company_profile(self, company_url: str) -> CompetitorAnalysis:
        """Scrape a LinkedIn company profile."""
        if self.dry_run or not self.api_token:
            return CompetitorAnalysis(handle=company_url, platform="linkedin")

        apify_limiter.wait()
        client = self._client()
        run = client.actor(self.PROFILE_ACTOR).call(run_input={
            "startUrls": [{"url": company_url}],
            "maxResults": 1,
        })
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        if not items:
            return CompetitorAnalysis(handle=company_url, platform="linkedin")
        item = items[0]
        return CompetitorAnalysis(
            handle=company_url,
            platform="linkedin",
            follower_count=item.get("followersCount", 0),
            post_count=item.get("postsCount", 0),
            bio=item.get("description", ""),
        )

    def build_competitor_analysis(
        self, company_url: str, post_count: int = 20
    ) -> CompetitorAnalysis:
        """Full competitor analysis: profile + posts + metrics."""
        analysis = self.scrape_company_profile(company_url)
        posts = self.scrape_company_posts(company_url, count=post_count)
        if posts:
            analysis.top_posts = posts[:5]
            analysis.avg_likes = sum(p.likes for p in posts) / len(posts)
            analysis.avg_comments = sum(p.comments for p in posts) / len(posts)
            from collections import Counter
            all_tags = [tag for p in posts for tag in p.hashtags]
            analysis.top_hashtags = [tag for tag, _ in Counter(all_tags).most_common(10)]
        return analysis
