"""Instagram scraper using Apify's instagram-scraper actor.

Apify handles all login, anti-bot, and rate limiting on their end.
Requires APIFY_API_TOKEN in env.
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict

from agency_common.models import CompetitorAnalysis, PostData

logger = logging.getLogger(__name__)

ACTOR_ID = "apify/instagram-scraper"
# Polling interval and max wait
POLL_INTERVAL = 5
MAX_WAIT = 300  # seconds


class ApifyInstagramScraper:
    """Scrape Instagram via Apify's managed instagram-scraper actor."""

    def __init__(self, api_token: str = "", dry_run: bool = False, **kwargs):
        self.api_token = api_token
        self.dry_run = dry_run

    def _client(self):
        from apify_client import ApifyClient
        return ApifyClient(self.api_token)

    def _run_actor(self, run_input: dict) -> list[dict]:
        """Run the actor and return all result items."""
        client = self._client()
        run = client.actor(ACTOR_ID).call(run_input=run_input, timeout_secs=MAX_WAIT)
        items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            items.append(item)
        return items

    def research_brand(
        self,
        competitor_handles: list[str],
        hashtags: list[str],
        post_count: int = 20,
        hashtag_post_count: int = 20,
    ) -> tuple[list[CompetitorAnalysis], list[PostData]]:
        """Scrape all competitors and hashtags via Apify in one actor run."""
        if self.dry_run:
            return (
                [CompetitorAnalysis(handle=h.lstrip("@"), platform="instagram") for h in competitor_handles],
                [],
            )

        if not self.api_token:
            logger.error("APIFY_API_TOKEN not set — cannot use Apify Instagram scraper.")
            return (
                [CompetitorAnalysis(handle=h.lstrip("@"), platform="instagram", bio="Error: no Apify token") for h in competitor_handles],
                [],
            )

        competitors: list[CompetitorAnalysis] = []
        hashtag_posts: list[PostData] = []

        # Scrape profiles
        if competitor_handles:
            try:
                usernames = [h.lstrip("@") for h in competitor_handles]
                direct_urls = [f"https://www.instagram.com/{u}/" for u in usernames]
                items = self._run_actor({
                    "directUrls": direct_urls,
                    "resultsType": "posts",
                    "resultsLimit": post_count,
                })
                # Group items by username
                by_user: dict[str, list[dict]] = defaultdict(list)
                for item in items:
                    owner = item.get("ownerUsername") or item.get("username", "")
                    if owner:
                        by_user[owner.lower()].append(item)

                for handle in usernames:
                    user_items = by_user.get(handle.lower(), [])
                    analysis = self._build_analysis(handle, user_items)
                    competitors.append(analysis)
            except Exception as exc:
                logger.error(f"Apify profile scrape failed: {exc}")
                for handle in competitor_handles:
                    competitors.append(CompetitorAnalysis(
                        handle=handle.lstrip("@"), platform="instagram", bio=f"Error: {exc}"
                    ))

        # Scrape hashtags
        for tag in hashtags:
            tag = tag.lstrip("#")
            try:
                items = self._run_actor({
                    "directUrls": [f"https://www.instagram.com/explore/tags/{tag}/"],
                    "resultsType": "posts",
                    "resultsLimit": hashtag_post_count,
                })
                for item in items:
                    post = self._item_to_post(item)
                    if post:
                        hashtag_posts.append(post)
            except Exception as exc:
                logger.error(f"Apify hashtag scrape failed for #{tag}: {exc}")

        return competitors, hashtag_posts

    def build_competitor_analysis(self, handle: str, post_count: int = 20) -> CompetitorAnalysis:
        if self.dry_run:
            return CompetitorAnalysis(handle=handle.lstrip("@"), platform="instagram")
        competitors, _ = self.research_brand([handle], [], post_count=post_count)
        return competitors[0] if competitors else CompetitorAnalysis(handle=handle.lstrip("@"), platform="instagram")

    def _build_analysis(self, handle: str, items: list[dict]) -> CompetitorAnalysis:
        posts = [p for p in (self._item_to_post(i) for i in items) if p]
        # Profile info often comes from the first item
        first = items[0] if items else {}
        followers = first.get("followersCount") or first.get("authorFollowersCount") or 0
        following = first.get("followingCount") or 0
        post_count = first.get("postsCount") or 0
        bio = first.get("biography") or first.get("bio") or ""

        analysis = CompetitorAnalysis(
            handle=handle,
            platform="instagram",
            follower_count=followers,
            following_count=following,
            post_count=post_count,
            bio=bio,
        )

        if posts:
            analysis.top_posts = posts[:5]
            analysis.avg_likes = sum(p.likes for p in posts) / len(posts)
            analysis.avg_comments = sum(p.comments for p in posts) / len(posts)
            if followers > 0:
                analysis.avg_engagement_rate = (
                    (analysis.avg_likes + analysis.avg_comments) / followers * 100
                )
            all_tags = [t for p in posts for t in p.hashtags]
            analysis.top_hashtags = [t for t, _ in Counter(all_tags).most_common(10)]
            type_counts: dict = defaultdict(int)
            for p in posts:
                type_counts[p.media_type or "unknown"] += 1
            analysis.content_types = dict(type_counts)

        return analysis

    def _item_to_post(self, item: dict) -> PostData | None:
        try:
            shortcode = item.get("shortCode") or item.get("id") or ""
            url = item.get("url") or item.get("displayUrl") or f"https://www.instagram.com/p/{shortcode}/"
            caption = item.get("caption") or item.get("text") or ""
            likes = item.get("likesCount") or item.get("likes") or 0
            comments = item.get("commentsCount") or item.get("comments") or 0
            timestamp = item.get("timestamp") or item.get("takenAt") or ""
            hashtags = item.get("hashtags") or []
            if hashtags and isinstance(hashtags[0], dict):
                hashtags = [h.get("name", "") for h in hashtags]
            media_type = item.get("type") or item.get("mediaType") or "GraphImage"
            return PostData(
                platform="instagram",
                post_id=str(shortcode),
                url=str(url),
                caption=str(caption),
                likes=int(likes),
                comments=int(comments),
                timestamp=str(timestamp),
                hashtags=hashtags,
                media_type=str(media_type),
            )
        except Exception:
            return None
