"""Community listening node — top weekly posts from Reddit, YouTube RSS, and X/Twitter.

Step 1 of the deep research pipeline: build an automated, algorithm-free feed of
raw consumer questions, debates, and emerging topics from non-social-network sources.
"""
from __future__ import annotations

import logging
from defusedxml import ElementTree as ET
from collections import Counter
from datetime import datetime

import requests

from agency_common.models import CommunityPost, ListeningNodeReport

LOGGER = logging.getLogger(__name__)

YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
REDDIT_ACTOR = "epctex/reddit-scraper"
X_ACTOR = "apidojo/tweet-scraper"


class CommunityListener:
    """Scrape top weekly posts from Reddit, YouTube RSS feeds, and X/Twitter lists."""

    def __init__(self, apify_token: str = "", dry_run: bool = False):
        self.apify_token = apify_token
        self.dry_run = dry_run

    def scrape(
        self,
        subreddits: list[str],
        youtube_channels: list[str],
        x_lists: list[str],
        post_count: int = 25,
    ) -> ListeningNodeReport:
        posts: list[CommunityPost] = []
        sources: list[str] = []

        if subreddits:
            reddit_posts = self._scrape_reddit(subreddits, post_count)
            posts += reddit_posts
            if reddit_posts:
                sources.append("reddit")

        if youtube_channels:
            yt_posts = self._scrape_youtube(youtube_channels, post_count)
            posts += yt_posts
            if yt_posts:
                sources.append("youtube")

        if x_lists:
            x_posts = self._scrape_x(x_lists, post_count)
            posts += x_posts
            if x_posts:
                sources.append("x")

        return self._build_report(posts, sources)

    # ------------------------------------------------------------------
    # Reddit via Apify
    # ------------------------------------------------------------------

    def _scrape_reddit(self, subreddits: list[str], post_count: int) -> list[CommunityPost]:
        if self.dry_run:
            LOGGER.info("[dry-run] Would scrape Reddit subreddits: %s", subreddits)
            return []

        if not self.apify_token:
            LOGGER.warning("No APIFY_API_TOKEN — skipping Reddit scrape")
            return []

        try:
            from apify_client import ApifyClient
            client = ApifyClient(self.apify_token)
            start_urls = [
                {"url": f"https://www.reddit.com/r/{sub.lstrip('r/').lstrip('/').lstrip('r/')}/top/?t=week"}
                for sub in subreddits
            ]
            run_input = {
                "startUrls": start_urls,
                "sort": "top",
                "time": "week",
                "maxPostCount": post_count,
                "includeComments": False,
                "proxy": {"useApifyProxy": True},
            }
            run = client.actor(REDDIT_ACTOR).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            posts = []
            for item in items:
                author = item.get("author", "")
                if isinstance(author, dict):
                    author = author.get("name", "")
                posts.append(CommunityPost(
                    source="reddit",
                    subreddit=item.get("community", {}).get("name", "") or item.get("subreddit", ""),
                    title=item.get("title", ""),
                    body=(item.get("body", "") or item.get("text", ""))[:2000],
                    url=item.get("url", "") or item.get("permalink", ""),
                    upvotes=int(item.get("upVotes", 0) or item.get("score", 0) or 0),
                    comments=int(item.get("numberOfComments", 0) or item.get("num_comments", 0) or 0),
                    author=str(author),
                    timestamp=str(item.get("createdAt", "") or item.get("created_utc", "")),
                    score=float(item.get("upVoteRatio", 0) or 0),
                ))
            LOGGER.info("Reddit: scraped %d posts from %s", len(posts), subreddits)
            return posts
        except Exception as exc:
            LOGGER.error("Reddit scrape failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # YouTube RSS — no API key required
    # ------------------------------------------------------------------

    def _scrape_youtube(self, channel_ids: list[str], video_count: int) -> list[CommunityPost]:
        posts: list[CommunityPost] = []
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "media": "http://search.yahoo.com/mrss/",
        }
        for channel_id in channel_ids:
            channel_id = channel_id.strip()
            if self.dry_run:
                LOGGER.info("[dry-run] Would fetch YouTube RSS for channel: %s", channel_id)
                continue
            try:
                url = YOUTUBE_RSS_URL.format(channel_id=channel_id)
                resp = requests.get(url, timeout=15, headers={"User-Agent": "agency-research/1.0"})
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
                entries = root.findall("atom:entry", ns)[:video_count]
                for entry in entries:
                    title = entry.findtext("atom:title", "", ns)
                    link_elem = entry.find("atom:link", ns)
                    href = link_elem.get("href", "") if link_elem is not None else ""
                    published = entry.findtext("atom:published", "", ns)
                    author_elem = entry.find("atom:author", ns)
                    author = author_elem.findtext("atom:name", "", ns) if author_elem is not None else ""

                    community = entry.find(".//media:community", ns)
                    views = 0
                    likes = 0
                    if community is not None:
                        stats = community.find("media:statistics", ns)
                        if stats is not None:
                            views = int(stats.get("views", 0) or 0)
                        star = community.find("media:starRating", ns)
                        if star is not None:
                            likes = int(star.get("count", 0) or 0)

                    posts.append(CommunityPost(
                        source="youtube",
                        subreddit="",
                        title=title,
                        body="",
                        url=href,
                        upvotes=views,
                        comments=0,
                        author=author,
                        timestamp=published,
                        score=float(likes),
                    ))
                LOGGER.info("YouTube RSS (%s): %d videos", channel_id, len(entries))
            except Exception as exc:
                LOGGER.error("YouTube RSS failed for channel %s: %s", channel_id, exc)
        return posts

    # ------------------------------------------------------------------
    # X / Twitter lists via Apify
    # ------------------------------------------------------------------

    def _scrape_x(self, list_urls: list[str], post_count: int) -> list[CommunityPost]:
        if self.dry_run:
            LOGGER.info("[dry-run] Would scrape X/Twitter lists: %s", list_urls)
            return []

        if not self.apify_token:
            LOGGER.warning("No APIFY_API_TOKEN — skipping X/Twitter scrape")
            return []

        try:
            from apify_client import ApifyClient
            client = ApifyClient(self.apify_token)
            run_input = {
                "startUrls": [{"url": u} for u in list_urls],
                "maxItems": post_count,
            }
            run = client.actor(X_ACTOR).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            posts = []
            for item in items:
                author = item.get("author", {})
                author_name = author.get("userName", "") if isinstance(author, dict) else str(author)
                posts.append(CommunityPost(
                    source="x",
                    subreddit="",
                    title="",
                    body=(item.get("text", "") or item.get("full_text", ""))[:2000],
                    url=item.get("url", "") or item.get("twitterUrl", ""),
                    upvotes=int(item.get("likeCount", 0) or 0),
                    comments=int(item.get("replyCount", 0) or 0),
                    author=author_name,
                    timestamp=str(item.get("createdAt", "")),
                    score=float(item.get("retweetCount", 0) or 0),
                ))
            LOGGER.info("X/Twitter: scraped %d posts", len(posts))
            return posts
        except Exception as exc:
            LOGGER.error("X/Twitter scrape failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Report builder
    # ------------------------------------------------------------------

    def _build_report(
        self,
        posts: list[CommunityPost],
        sources: list[str],
    ) -> ListeningNodeReport:
        # Extract emerging keywords from titles + bodies
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "is", "are", "was", "were", "with", "this", "that", "it", "be",
            "have", "has", "do", "does", "not", "by", "from", "as", "its", "how",
            "what", "why", "when", "who", "will", "can", "my", "your", "we", "they",
        }
        word_counts: Counter = Counter()
        for post in posts:
            text = f"{post.title} {post.body}".lower()
            words = [w.strip(".,!?;:\"'()[]") for w in text.split()]
            for w in words:
                if len(w) >= 4 and w not in stopwords:
                    word_counts[w] += 1

        emerging_keywords = [w for w, _ in word_counts.most_common(20) if word_counts[w] >= 2]

        # Identify questions from titles
        questions = [
            p.title for p in posts
            if p.title and ("?" in p.title or p.title.lower().startswith(("how", "why", "what", "when", "is ", "are ", "should", "can ", "does")))
        ][:15]

        # Top debates: posts with high comment counts relative to upvotes
        debates = sorted(
            [p for p in posts if p.comments > 0],
            key=lambda p: p.comments / max(p.upvotes, 1),
            reverse=True,
        )[:8]
        debate_titles = [d.title for d in debates if d.title]

        return ListeningNodeReport(
            scraped_at=datetime.utcnow().isoformat(),
            sources=sources,
            posts=posts,
            top_questions=questions,
            recurring_debates=debate_titles,
            emerging_keywords=emerging_keywords,
        )
