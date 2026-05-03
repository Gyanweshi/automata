"""Instagram scraper using Playwright browser automation.

Falls back gracefully on any per-handle error. Saves session cookies to
~/.agency/ig_session.json so login only happens once.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional

from agency_common.models import CompetitorAnalysis, PostData

logger = logging.getLogger(__name__)

SESSION_PATH = Path.home() / ".agency" / "ig_session.json"


class PlaywrightInstagramScraper:
    """Scrape Instagram via a real browser session (Playwright Chromium).

    On first use, opens a visible browser for login if no saved session exists.
    Subsequent runs reuse the saved session cookies — no re-login needed.
    """

    def __init__(
        self,
        username: str = "",
        password: str = "",
        dry_run: bool = False,
        headless: bool = True,
    ):
        self.username = username
        self.password = password
        self.dry_run = dry_run
        self.headless = headless
        self._browser = None
        self._context = None
        self._page = None

    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------

    def _start(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        storage_state = str(SESSION_PATH) if SESSION_PATH.exists() else None
        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            storage_state=storage_state,
            locale="en-US",
            viewport={"width": 1280, "height": 800},
        )
        self._page = self._context.new_page()

    def _stop(self):
        if self._context:
            try:
                SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
                self._context.storage_state(path=str(SESSION_PATH))
            except Exception:
                pass
        if self._browser:
            self._browser.close()
        if hasattr(self, "_pw"):
            self._pw.stop()
        self._browser = self._context = self._page = None

    def _ensure_logged_in(self) -> bool:
        """Return True if we are logged in (or don't need to be)."""
        page = self._page
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # Check for login wall
        if "accounts/login" not in page.url and not page.query_selector('input[name="username"]'):
            return True  # already logged in via saved session

        if not self.username or not self.password:
            logger.warning("Instagram login required but no credentials provided.")
            return False

        logger.info("Logging in to Instagram…")
        try:
            # Navigate directly to login page for a clean form state
            if "accounts/login" not in page.url:
                page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)

            # Use JS to set values — bypasses headless interactability detection
            page.evaluate("""([u, p]) => {
                function setNativeValue(el, value) {
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(el, value);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                }
                const uField = document.querySelector('input[name="username"]');
                const pField = document.querySelector('input[name="password"]');
                if (uField) setNativeValue(uField, u);
                if (pField) setNativeValue(pField, p);
            }""", [self.username, self.password])
            time.sleep(1)

            # Submit
            submit = page.query_selector('button[type="submit"]')
            if submit:
                submit.click()
            else:
                page.keyboard.press("Enter")

            # Wait for redirect away from login page
            page.wait_for_function(
                "() => !window.location.href.includes('accounts/login')",
                timeout=20000,
            )
            time.sleep(3)
            logger.info("Instagram login successful.")
        except Exception as exc:
            logger.error(f"Instagram login failed: {exc}")
            return False

        return True

    # ------------------------------------------------------------------
    # Public scraping methods
    # ------------------------------------------------------------------

    def scrape_profile(self, handle: str) -> CompetitorAnalysis:
        """Fetch profile metadata for a public Instagram account."""
        handle = handle.lstrip("@")
        if self.dry_run:
            return CompetitorAnalysis(handle=handle, platform="instagram")

        try:
            self._start()
            if not self._ensure_logged_in():
                return CompetitorAnalysis(handle=handle, platform="instagram", bio="Error: login required")

            url = f"https://www.instagram.com/{handle}/"
            self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)

            # Extract from meta tags / page JSON
            data = self._extract_profile_json(handle)
            return data
        except Exception as exc:
            logger.error(f"Playwright profile scrape failed for @{handle}: {exc}")
            return CompetitorAnalysis(handle=handle, platform="instagram", bio=f"Error: {exc}")
        finally:
            self._stop()

    def scrape_recent_posts(self, handle: str, count: int = 20) -> list[PostData]:
        """Fetch recent posts from a public Instagram profile."""
        handle = handle.lstrip("@")
        if self.dry_run:
            return []

        try:
            self._start()
            if not self._ensure_logged_in():
                return []

            url = f"https://www.instagram.com/{handle}/"
            self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            return self._extract_posts_from_page(handle, count)
        except Exception as exc:
            logger.error(f"Playwright posts scrape failed for @{handle}: {exc}")
            return []
        finally:
            self._stop()

    def scrape_hashtag_posts(self, tag: str, count: int = 30) -> list[PostData]:
        """Fetch top posts for a hashtag."""
        tag = tag.lstrip("#")
        if self.dry_run:
            return []

        try:
            self._start()
            if not self._ensure_logged_in():
                return []

            url = f"https://www.instagram.com/explore/tags/{tag}/"
            self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            return self._extract_hashtag_posts(tag, count)
        except Exception as exc:
            logger.error(f"Playwright hashtag scrape failed for #{tag}: {exc}")
            return []
        finally:
            self._stop()

    def research_brand(
        self,
        competitor_handles: list[str],
        hashtags: list[str],
        post_count: int = 20,
        hashtag_post_count: int = 20,
    ) -> tuple[list[CompetitorAnalysis], list[PostData]]:
        """Scrape all competitors and hashtags in ONE browser session.

        Returns (competitor_analyses, hashtag_posts).
        This is the preferred entry point — opening one browser is faster
        and avoids repeated login prompts.
        """
        if self.dry_run:
            return (
                [CompetitorAnalysis(handle=h.lstrip("@"), platform="instagram") for h in competitor_handles],
                [],
            )

        competitors: list[CompetitorAnalysis] = []
        hashtag_posts: list[PostData] = []

        try:
            self._start()
            if not self._ensure_logged_in():
                for h in competitor_handles:
                    competitors.append(CompetitorAnalysis(
                        handle=h.lstrip("@"), platform="instagram", bio="Error: login required"
                    ))
                return competitors, hashtag_posts

            # Scrape each competitor profile + posts
            for handle in competitor_handles:
                handle = handle.lstrip("@")
                try:
                    url = f"https://www.instagram.com/{handle}/"
                    self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2)
                    analysis = self._extract_profile_json(handle)
                    posts = self._extract_posts_from_page(handle, post_count)
                    if posts:
                        analysis.top_posts = posts[:5]
                        analysis.avg_likes = sum(p.likes for p in posts) / len(posts)
                        analysis.avg_comments = sum(p.comments for p in posts) / len(posts)
                        if analysis.follower_count and analysis.follower_count > 0:
                            analysis.avg_engagement_rate = (
                                (analysis.avg_likes + analysis.avg_comments)
                                / analysis.follower_count * 100
                            )
                        all_tags = [t for p in posts for t in p.hashtags]
                        analysis.top_hashtags = [t for t, _ in Counter(all_tags).most_common(10)]
                        type_counts: dict = defaultdict(int)
                        for p in posts:
                            type_counts[p.media_type or "unknown"] += 1
                        analysis.content_types = dict(type_counts)
                    competitors.append(analysis)
                except Exception as exc:
                    logger.error(f"Failed scraping @{handle}: {exc}")
                    competitors.append(CompetitorAnalysis(handle=handle, platform="instagram", bio=f"Error: {exc}"))

            # Scrape hashtag pages in the same session
            for tag in hashtags:
                tag = tag.lstrip("#")
                try:
                    url = f"https://www.instagram.com/explore/tags/{tag}/"
                    self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2)
                    posts = self._extract_hashtag_posts(tag, hashtag_post_count)
                    hashtag_posts.extend(posts)
                except Exception as exc:
                    logger.error(f"Failed scraping #{tag}: {exc}")

        except Exception as exc:
            logger.error(f"Playwright research_brand session failed: {exc}")
        finally:
            self._stop()

        return competitors, hashtag_posts

    def build_competitor_analysis(self, handle: str, post_count: int = 20) -> CompetitorAnalysis:
        """Full competitor analysis: profile + posts + computed metrics.

        Opens one browser session for all operations on this handle.
        """
        handle = handle.lstrip("@")
        if self.dry_run:
            return CompetitorAnalysis(handle=handle, platform="instagram")

        try:
            self._start()
            if not self._ensure_logged_in():
                return CompetitorAnalysis(handle=handle, platform="instagram", bio="Error: login required")

            # Profile
            url = f"https://www.instagram.com/{handle}/"
            self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            analysis = self._extract_profile_json(handle)

            # Posts
            posts = self._extract_posts_from_page(handle, post_count)
            if posts:
                analysis.top_posts = posts[:5]
                analysis.avg_likes = sum(p.likes for p in posts) / len(posts)
                analysis.avg_comments = sum(p.comments for p in posts) / len(posts)
                if analysis.follower_count and analysis.follower_count > 0:
                    analysis.avg_engagement_rate = (
                        (analysis.avg_likes + analysis.avg_comments)
                        / analysis.follower_count * 100
                    )
                all_tags = [t for p in posts for t in p.hashtags]
                analysis.top_hashtags = [t for t, _ in Counter(all_tags).most_common(10)]
                type_counts: dict = defaultdict(int)
                for p in posts:
                    type_counts[p.media_type or "unknown"] += 1
                analysis.content_types = dict(type_counts)

            return analysis
        except Exception as exc:
            logger.error(f"Playwright competitor analysis failed for @{handle}: {exc}")
            return CompetitorAnalysis(handle=handle, platform="instagram", bio=f"Error: {exc}")
        finally:
            self._stop()

    # ------------------------------------------------------------------
    # Internal extraction helpers
    # ------------------------------------------------------------------

    def _extract_profile_json(self, handle: str) -> CompetitorAnalysis:
        """Try to pull profile stats from the page's inline JSON or meta tags."""
        page = self._page
        bio = ""
        followers = 0
        following = 0
        post_count = 0

        try:
            # Instagram embeds data in a <script type="application/json"> tag
            content = page.evaluate("""() => {
                const scripts = document.querySelectorAll('script[type="application/json"]');
                for (const s of scripts) {
                    const text = s.textContent;
                    if (text.includes('edge_followed_by') || text.includes('follower_count')) {
                        return text;
                    }
                }
                return null;
            }""")
            if content:
                data = json.loads(content)
                user = self._dig(data, "edge_followed_by") or {}
                # Try multiple known JSON shapes
                for path in [
                    ["data", "user"],
                    ["user"],
                    ["graphql", "user"],
                ]:
                    node = data
                    for key in path:
                        node = node.get(key, {}) if isinstance(node, dict) else {}
                    if node.get("edge_followed_by"):
                        followers = node["edge_followed_by"].get("count", 0)
                        following = node.get("edge_follow", {}).get("count", 0)
                        post_count = node.get("edge_owner_to_timeline_media", {}).get("count", 0)
                        bio = node.get("biography", "")
                        break
        except Exception:
            pass

        # Fallback: meta description often has "X Followers, Y Following, Z Posts"
        if followers == 0:
            try:
                desc = page.evaluate(
                    "() => document.querySelector('meta[name=\"description\"]')?.content || ''"
                )
                import re
                m = re.search(r"([\d,]+)\s+Followers", desc or "")
                if m:
                    followers = int(m.group(1).replace(",", ""))
                m2 = re.search(r"([\d,]+)\s+Following", desc or "")
                if m2:
                    following = int(m2.group(1).replace(",", ""))
                m3 = re.search(r"([\d,]+)\s+Posts", desc or "")
                if m3:
                    post_count = int(m3.group(1).replace(",", ""))
            except Exception:
                pass

        return CompetitorAnalysis(
            handle=handle,
            platform="instagram",
            follower_count=followers,
            following_count=following,
            post_count=post_count,
            bio=bio,
        )

    def _dig(self, obj, key: str):
        """Recursively search dict/list for first occurrence of key."""
        if isinstance(obj, dict):
            if key in obj:
                return obj[key]
            for v in obj.values():
                result = self._dig(v, key)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self._dig(item, key)
                if result is not None:
                    return result
        return None

    def _extract_posts_from_page(self, handle: str, count: int) -> list[PostData]:
        """Extract visible post links from a profile page."""
        page = self._page
        posts: list[PostData] = []
        try:
            # Collect post links
            page.wait_for_selector("a[href*='/p/']", timeout=10000)
            links = page.eval_on_selector_all(
                "a[href*='/p/']",
                "els => els.map(e => e.href)"
            )
            seen = set()
            unique_links = []
            for link in links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)

            for link in unique_links[:count]:
                shortcode = link.rstrip("/").split("/")[-1]
                posts.append(PostData(
                    platform="instagram",
                    post_id=shortcode,
                    url=link,
                    caption="",
                    likes=0,
                    comments=0,
                    media_type="GraphImage",
                ))
        except Exception as exc:
            logger.debug(f"Post extraction from profile page failed: {exc}")
        return posts

    def _extract_hashtag_posts(self, tag: str, count: int) -> list[PostData]:
        """Extract visible post links from a hashtag explore page."""
        return self._extract_posts_from_page(tag, count)
