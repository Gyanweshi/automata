"""Community listening node — top weekly posts from Reddit, YouTube RSS, and X/Twitter.

Step 1 of the deep research pipeline: build an automated, algorithm-free feed of
raw consumer questions, debates, and emerging topics from non-social-network sources.
"""
from __future__ import annotations

import logging
import re
from defusedxml import ElementTree as ET
from collections import Counter
from datetime import datetime

from typing import Callable

import requests

from agency_common.models import CommunityPost, ListeningNodeReport

from .page_fetch import PageFetcher, make_fetcher
from .social_parsers import parse_reddit_listing, parse_x_timeline

LOGGER = logging.getLogger(__name__)

YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


class CommunityListener:
    """Top weekly posts from Reddit and X/Twitter (read through a real browser: Playwright or browser-act) and
    YouTube RSS feeds. Reddit works logged out; X needs a one-time login (see page_fetch.py)."""

    def __init__(self, fetcher_for: Callable[[str], PageFetcher] | None = None, dry_run: bool = False):
        self.fetcher_for = fetcher_for or make_fetcher
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
    # Reddit: the subreddit's top-of-the-week page
    # ------------------------------------------------------------------

    def _scrape_reddit(self, subreddits: list[str], post_count: int) -> list[CommunityPost]:
        if self.dry_run:
            LOGGER.info("[dry-run] Would scrape Reddit subreddits: %s", subreddits)
            return []
        fetcher = self.fetcher_for("reddit")
        posts: list[CommunityPost] = []
        for sub in subreddits:
            name = re.sub(r"^/?r/", "", sub.strip()).strip("/")
            page = fetcher.fetch(f"https://www.reddit.com/r/{name}/top/?t=week", scrolls=max(0, post_count // 8))
            if not page.ok:
                LOGGER.warning("Reddit r/%s: %s", name, page.error or page.status)
                continue
            found = parse_reddit_listing(page.html, limit=post_count)
            LOGGER.info("Reddit r/%s: %d posts", name, len(found))
            posts += found
        return posts

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
    # X / Twitter lists, profiles or searches (needs a logged-in browser)
    # ------------------------------------------------------------------

    def _scrape_x(self, list_urls: list[str], post_count: int) -> list[CommunityPost]:
        if self.dry_run:
            LOGGER.info("[dry-run] Would scrape X/Twitter lists: %s", list_urls)
            return []
        fetcher = self.fetcher_for("x")
        posts: list[CommunityPost] = []
        for url in list_urls:
            url = url if url.startswith("http") else f"https://x.com/{url.lstrip('@/')}"
            page = fetcher.fetch(url, scrolls=max(1, post_count // 5))
            found = parse_x_timeline(page.html, limit=post_count) if page.ok else []
            if not found:
                LOGGER.warning("X %s: no posts read (%s). X shows nothing logged out; log in once: "
                               "python scripts/open-instagram-session.py --site x", url, page.error or page.status)
            posts += found
        return posts

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
