"""Facebook scraper: Graph API for owned pages, Apify for competitor pages."""
from __future__ import annotations

from agency_common.models import CompetitorAnalysis, PostData
from agency_common.rate_limiter import apify_limiter, facebook_limiter


GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
APIFY_FB_ACTOR = "apify/facebook-pages-scraper"


class FacebookScraper:
    """
    Scrape Facebook pages.

    - Owned pages: Facebook Graph API (requires FB_PAGE_ACCESS_TOKEN)
    - Competitor pages: Apify (requires APIFY_API_TOKEN)
    """

    def __init__(
        self,
        page_access_token: str = "",
        apify_token: str = "",
        dry_run: bool = False,
    ):
        self.page_access_token = page_access_token
        self.apify_token = apify_token
        self.dry_run = dry_run

    def scrape_owned_page(self, page_id: str, count: int = 20) -> list[PostData]:
        """Fetch posts from a page you own via Graph API."""
        if self.dry_run or not self.page_access_token:
            return []

        import requests
        facebook_limiter.wait()
        try:
            url = f"{GRAPH_API_BASE}/{page_id}/posts"
            params = {
                "access_token": self.page_access_token,
                "fields": "id,message,created_time,likes.summary(true),comments.summary(true),shares",
                "limit": count,
            }
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            posts = []
            for item in data.get("data", []):
                posts.append(PostData(
                    platform="facebook",
                    post_id=item.get("id", ""),
                    caption=item.get("message", ""),
                    likes=item.get("likes", {}).get("summary", {}).get("total_count", 0),
                    comments=item.get("comments", {}).get("summary", {}).get("total_count", 0),
                    shares=item.get("shares", {}).get("count", 0),
                    timestamp=item.get("created_time", ""),
                ))
            return posts
        except Exception:
            return []

    def scrape_competitor_page(self, page_url: str, count: int = 20) -> list[PostData]:
        """Scrape a competitor's public Facebook page via Apify."""
        if self.dry_run or not self.apify_token:
            return []

        apify_limiter.wait()
        try:
            from apify_client import ApifyClient
            client = ApifyClient(self.apify_token)
            run = client.actor(APIFY_FB_ACTOR).call(run_input={
                "startUrls": [{"url": page_url}],
                "maxPosts": count,
            })
            posts = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                for post in item.get("posts", [])[:count]:
                    posts.append(PostData(
                        platform="facebook",
                        post_id=post.get("postId", ""),
                        url=post.get("url", ""),
                        caption=post.get("text", ""),
                        likes=post.get("likes", 0),
                        comments=post.get("comments", 0),
                        shares=post.get("shares", 0),
                        timestamp=post.get("time", ""),
                    ))
            return posts
        except Exception:
            return []

    def build_competitor_analysis(
        self, page_identifier: str, post_count: int = 20, is_owned: bool = False
    ) -> CompetitorAnalysis:
        """Full competitor analysis for a Facebook page."""
        if is_owned:
            posts = self.scrape_owned_page(page_identifier, count=post_count)
        else:
            posts = self.scrape_competitor_page(page_identifier, count=post_count)
        analysis = CompetitorAnalysis(handle=page_identifier, platform="facebook")
        if posts:
            analysis.top_posts = posts[:5]
            analysis.avg_likes = sum(p.likes for p in posts) / len(posts)
            analysis.avg_comments = sum(p.comments for p in posts) / len(posts)
        return analysis
