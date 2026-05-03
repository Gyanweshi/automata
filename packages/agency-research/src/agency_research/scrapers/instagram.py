"""Instagram scraper using instaloader for public profile data."""
from __future__ import annotations

import time
from typing import Optional

from agency_common.models import CompetitorAnalysis, PostData
from agency_common.rate_limiter import instagram_limiter


class InstagramScraper:
    """Scrape public Instagram profiles using instaloader.

    Authentication is optional — public profiles work without it.
    For higher rate limits and richer data, set username/password in AgencyConfig.
    """

    def __init__(self, username: str = "", password: str = "", dry_run: bool = False):
        self.username = username
        self.password = password
        self.dry_run = dry_run
        self._loader = None

    def _get_loader(self):
        if self._loader is None:
            import instaloader
            L = instaloader.Instaloader(
                quiet=True,
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
            )
            if self.username and self.password:
                try:
                    L.login(self.username, self.password)
                except Exception:
                    pass
            self._loader = L
        return self._loader

    def scrape_profile(self, handle: str) -> CompetitorAnalysis:
        """Fetch profile metadata for a public Instagram account."""
        handle = handle.lstrip("@")
        if self.dry_run:
            return CompetitorAnalysis(handle=handle, platform="instagram")

        import instaloader
        instagram_limiter.wait()
        try:
            L = self._get_loader()
            profile = instaloader.Profile.from_username(L.context, handle)
            return CompetitorAnalysis(
                handle=handle,
                platform="instagram",
                follower_count=profile.followers,
                following_count=profile.followees,
                post_count=profile.mediacount,
                bio=profile.biography or "",
            )
        except Exception as e:
            return CompetitorAnalysis(handle=handle, platform="instagram", bio=f"Error: {e}")

    def scrape_recent_posts(self, handle: str, count: int = 20) -> list[PostData]:
        """Fetch recent posts from a public Instagram profile."""
        handle = handle.lstrip("@")
        if self.dry_run:
            return []

        import instaloader
        instagram_limiter.wait()
        posts: list[PostData] = []
        try:
            L = self._get_loader()
            profile = instaloader.Profile.from_username(L.context, handle)
            for i, post in enumerate(profile.get_posts()):
                if i >= count:
                    break
                hashtags = list(post.caption_hashtags) if post.caption else []
                engagement = 0.0
                if profile.followers > 0:
                    engagement = (post.likes + post.comments) / profile.followers * 100
                posts.append(PostData(
                    platform="instagram",
                    post_id=post.shortcode,
                    url=f"https://www.instagram.com/p/{post.shortcode}/",
                    caption=post.caption or "",
                    likes=post.likes,
                    comments=post.comments,
                    timestamp=post.date_utc.isoformat() if post.date_utc else "",
                    hashtags=hashtags,
                    media_type=post.typename,
                    engagement_rate=round(engagement, 4),
                ))
                time.sleep(0.5)
        except Exception:
            pass
        return posts

    def scrape_hashtag_posts(self, tag: str, count: int = 30) -> list[PostData]:
        """Fetch top posts for a hashtag."""
        tag = tag.lstrip("#")
        if self.dry_run:
            return []

        import instaloader
        instagram_limiter.wait()
        posts: list[PostData] = []
        try:
            L = self._get_loader()
            hashtag = instaloader.Hashtag.from_name(L.context, tag)
            for i, post in enumerate(hashtag.get_top_posts()):
                if i >= count:
                    break
                posts.append(PostData(
                    platform="instagram",
                    post_id=post.shortcode,
                    url=f"https://www.instagram.com/p/{post.shortcode}/",
                    caption=post.caption or "",
                    likes=post.likes,
                    comments=post.comments,
                    timestamp=post.date_utc.isoformat() if post.date_utc else "",
                    hashtags=list(post.caption_hashtags) if post.caption else [],
                    media_type=post.typename,
                ))
                time.sleep(0.5)
        except Exception:
            pass
        return posts

    def build_competitor_analysis(
        self, handle: str, post_count: int = 20
    ) -> CompetitorAnalysis:
        """Full competitor analysis: profile + posts + computed metrics."""
        analysis = self.scrape_profile(handle)
        posts = self.scrape_recent_posts(handle, count=post_count)
        if posts:
            analysis.top_posts = posts[:5]
            analysis.avg_likes = sum(p.likes for p in posts) / len(posts)
            analysis.avg_comments = sum(p.comments for p in posts) / len(posts)
            analysis.avg_engagement_rate = sum(p.engagement_rate for p in posts) / len(posts)
            # Aggregate hashtag frequency
            from collections import Counter
            all_tags = [tag for p in posts for tag in p.hashtags]
            analysis.top_hashtags = [tag for tag, _ in Counter(all_tags).most_common(10)]
            # Count content types
            from collections import defaultdict
            type_counts: dict = defaultdict(int)
            for p in posts:
                type_counts[p.media_type or "unknown"] += 1
            analysis.content_types = dict(type_counts)
        return analysis
