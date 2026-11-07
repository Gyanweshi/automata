"""Facebook research: Graph API for pages you own, a real browser (Playwright or browser-act) for competitor pages.

Logged out, Facebook shows a page's follower count and one or two posts; log in once (see page_fetch.py) and
scrolling loads the recent posts with reaction, comment and share counts.
"""
from __future__ import annotations

import logging

from tenacity import retry, stop_after_attempt, wait_exponential

from agency_common.models import CompetitorAnalysis, PostData
from agency_common.rate_limiter import facebook_limiter

from .page_fetch import PageFetcher, make_fetcher
from .social_parsers import parse_facebook_page, parse_facebook_posts, summarize

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def _return_empty_list(retry_state):
    logger.error(f"Facebook Graph API failed after {retry_state.attempt_number} attempts: {retry_state.outcome.exception()}")
    return []


def page_url(identifier: str) -> str:
    value = identifier.strip()
    return value if value.startswith("http") else f"https://www.facebook.com/{value.strip('/')}"


class FacebookScraper:
    def __init__(self, page_access_token: str = "", fetcher: PageFetcher | None = None, dry_run: bool = False):
        self.page_access_token = page_access_token
        self.fetcher = fetcher or make_fetcher("facebook")
        self.dry_run = dry_run

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry_error_callback=_return_empty_list)
    def scrape_owned_page(self, page_id: str, count: int = 20) -> list[PostData]:
        """Fetch posts from a page you own via Graph API (FB_PAGE_ACCESS_TOKEN)."""
        if self.dry_run or not self.page_access_token:
            return []

        import requests
        facebook_limiter.wait()
        resp = requests.get(f"{GRAPH_API_BASE}/{page_id}/posts", params={
            "access_token": self.page_access_token,
            "fields": "id,message,created_time,likes.summary(true),comments.summary(true),shares",
            "limit": count,
        }, timeout=30)
        resp.raise_for_status()
        return [PostData(
            platform="facebook", post_id=item.get("id", ""), caption=item.get("message", ""),
            likes=item.get("likes", {}).get("summary", {}).get("total_count", 0),
            comments=item.get("comments", {}).get("summary", {}).get("total_count", 0),
            shares=item.get("shares", {}).get("count", 0), timestamp=item.get("created_time", ""),
        ) for item in resp.json().get("data", [])]

    def build_competitor_analysis(self, page_identifier: str, post_count: int = 20, is_owned: bool = False) -> CompetitorAnalysis:
        if is_owned:
            return summarize(CompetitorAnalysis(handle=page_identifier, platform="facebook"),
                             self.scrape_owned_page(page_identifier, count=post_count))
        url = page_url(page_identifier)
        if self.dry_run:
            return CompetitorAnalysis(handle=url, platform="facebook", scrape_status="dry_run")
        page = self.fetcher.fetch(url, scrolls=max(2, post_count // 3))
        if not page.ok:
            logger.warning("Facebook %s: %s", url, page.error or page.status)
            return CompetitorAnalysis(handle=url, platform="facebook", bio=page.error, scrape_status=page.status)
        posts = parse_facebook_posts(page.html, limit=post_count)
        analysis = summarize(parse_facebook_page(page.html, url), posts)
        analysis.scrape_status = "ok" if len(posts) > 2 else ("partial" if posts or analysis.follower_count else "empty")
        if analysis.scrape_status == "partial":
            logger.warning("Facebook %s: only the logged-out preview was readable; log in once for full posts "
                           "(python scripts/open-instagram-session.py --site facebook)", url)
        return analysis
