"""Instagram scraper using browser-act stealth extraction.

This backend supports two modes:
- stealth: read-only stateless `browser-act stealth-extract` for public pages
- session: reuses a named browser-act session that can stay logged in

It parses the rendered markdown or HTML for profile hints and visible post
links. Session mode is useful when pages need a manually logged-in browser
state and should not reopen a fresh login flow for every scrape.
"""
from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter, defaultdict
import logging
import re
import subprocess
import time

from bs4 import BeautifulSoup

from agency_common.models import CompetitorAnalysis, PostData

LOGGER = logging.getLogger(__name__)

PROFILE_URL = "https://www.instagram.com/{handle}/"
HASHTAG_URL = "https://www.instagram.com/explore/tags/{tag}/"
POST_URL_RE = re.compile(
    r"https://(?:www\.)?instagram\.com/(?:[A-Za-z0-9_.-]+/)?(?:p|reel)/([A-Za-z0-9_-]+)/?"
)
GATE_PATTERNS = (
    "login or captcha gate",
    "page appears to be a login or captcha gate",
    "captcha",
    "log in to continue",
    "accounts/login",
)
EMPTY_PATTERNS = (
    "no content extracted",
    "empty",
)


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    content_type: str
    status: str
    error: str = ""


class BrowserActInstagramScraper:
    """Scrape Instagram pages through browser-act."""

    def __init__(
        self,
        dry_run: bool = False,
        *,
        timeout_seconds: int = 90,
        max_workers: int = 4,
        proxy_region: str | None = None,
        mode: str = "stealth",
        session_name: str | None = None,
    ):
        self.dry_run = dry_run
        self.timeout_seconds = timeout_seconds
        self.max_workers = max_workers
        self.proxy_region = (proxy_region or "").strip()
        self.mode = (mode or "stealth").strip().lower()
        self.session_name = (session_name or "").strip()

    def research_brand(
        self,
        competitor_handles: list[str],
        hashtags: list[str],
        post_count: int = 20,
        hashtag_post_count: int = 20,
    ) -> tuple[list[CompetitorAnalysis], list[PostData]]:
        """Scrape competitors and hashtags with bounded parallel extraction."""
        if self.dry_run:
            return (
                [CompetitorAnalysis(handle=h.lstrip("@"), platform="instagram") for h in competitor_handles],
                [],
            )

        tasks = []
        for handle in competitor_handles:
            clean_handle = handle.lstrip("@")
            tasks.append(("profile", clean_handle, post_count))
        for tag in hashtags:
            clean_tag = tag.lstrip("#")
            tasks.append(("hashtag", clean_tag, hashtag_post_count))

        competitors: list[CompetitorAnalysis] = []
        hashtag_posts: list[PostData] = []

        worker_count = max(1, min(self.max_workers, len(tasks) or 1))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_task = {
                executor.submit(self._run_task, task_type, value, count): (task_type, value)
                for task_type, value, count in tasks
            }
            for future in as_completed(future_to_task):
                task_type, value = future_to_task[future]
                try:
                    result = future.result()
                except Exception as exc:
                    LOGGER.error("browser-act scrape failed for %s %s: %s", task_type, value, exc)
                    if task_type == "profile":
                        competitors.append(
                            CompetitorAnalysis(handle=value, platform="instagram", bio=f"Error: {exc}")
                        )
                    continue

                if isinstance(result, CompetitorAnalysis):
                    competitors.append(result)
                else:
                    hashtag_posts.extend(result)

        return competitors, hashtag_posts

    def build_competitor_analysis(self, handle: str, post_count: int = 20) -> CompetitorAnalysis:
        if self.dry_run:
            return CompetitorAnalysis(handle=handle.lstrip("@"), platform="instagram", scrape_status="dry_run")
        return self._scrape_profile(handle.lstrip("@"), post_count=post_count)

    def _run_task(self, task_type: str, value: str, count: int) -> CompetitorAnalysis | list[PostData]:
        if task_type == "profile":
            return self._scrape_profile(value, post_count=count)
        return self._scrape_hashtag(value, post_count=count)

    def _scrape_profile(self, handle: str, *, post_count: int) -> CompetitorAnalysis:
        url = PROFILE_URL.format(handle=handle)
        extracted = self._fetch_document(url)

        if extracted.status == "gated":
            return CompetitorAnalysis(
                handle=handle,
                platform="instagram",
                bio=extracted.error or "Instagram gated the page",
                scrape_status="gated",
            )
        if extracted.status == "error":
            return CompetitorAnalysis(
                handle=handle,
                platform="instagram",
                bio=extracted.error or "browser-act extraction failed",
                scrape_status="error",
            )

        analysis = self._document_to_analysis(handle, extracted.text, extracted.content_type)
        posts = self._document_to_posts(extracted.text, extracted.content_type, default_caption="", limit=post_count)

        if posts:
            analysis.top_posts = posts[:5]
            all_tags = [tag for post in posts for tag in post.hashtags]
            analysis.top_hashtags = [tag for tag, _ in Counter(all_tags).most_common(10)]
            type_counts: dict[str, int] = defaultdict(int)
            for post in posts:
                type_counts[post.media_type or "unknown"] += 1
            analysis.content_types = dict(type_counts)
        analysis.scrape_status = "ok"

        return analysis

    def _scrape_hashtag(self, tag: str, *, post_count: int) -> list[PostData]:
        url = HASHTAG_URL.format(tag=tag)
        extracted = self._fetch_document(url)
        if extracted.status == "gated":
            LOGGER.warning("browser-act hashtag gated for #%s: %s", tag, extracted.error or "Instagram blocked the page")
            return []
        if extracted.status == "error":
            LOGGER.error("browser-act hashtag extraction failed for #%s: %s", tag, extracted.error or "browser-act error")
            return []

        posts = self._document_to_posts(extracted.text, extracted.content_type, default_caption=f"#{tag}", limit=post_count)
        for post in posts:
            if tag not in post.hashtags:
                post.hashtags.append(tag)
        return posts

    def _fetch_document(self, url: str) -> ExtractedDocument:
        statuses: list[ExtractedDocument] = []
        for content_type in ("markdown", "html"):
            extracted = self._attempt_extract(url, content_type=content_type)
            statuses.append(extracted)
            if extracted.status == "ok":
                return extracted
        for status in statuses:
            if status.status == "gated":
                return status
        for status in statuses:
            if status.status == "error":
                return status
        return statuses[-1] if statuses else ExtractedDocument("", "markdown", "empty", "No content extracted")

    def _attempt_extract(self, url: str, *, content_type: str) -> ExtractedDocument:
        if self.mode == "session":
            return self._attempt_session_extract(url, content_type=content_type)

        last_error = ""
        for attempt in range(1, 3):
            try:
                completed = subprocess.run(
                    self._build_command(url, content_type=content_type),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
                stdout = (completed.stdout or "").strip()
                if not stdout:
                    return ExtractedDocument("", content_type, "empty", "No content extracted")
                if self._looks_gated(stdout):
                    return ExtractedDocument(stdout, content_type, "gated", "Instagram login/captcha gate detected")
                return ExtractedDocument(stdout, content_type, "ok")
            except subprocess.CalledProcessError as exc:
                last_error = (exc.stderr or exc.stdout or str(exc)).strip()
                if self._looks_gated(last_error):
                    return ExtractedDocument("", content_type, "gated", last_error)
                if self._looks_empty(last_error):
                    return ExtractedDocument("", content_type, "empty", last_error)
            except subprocess.TimeoutExpired as exc:
                last_error = f"timed out after {exc.timeout} seconds"

            if attempt == 1:
                time.sleep(1)

        if self._looks_gated(last_error):
            return ExtractedDocument("", content_type, "gated", last_error)
        if self._looks_empty(last_error):
            return ExtractedDocument("", content_type, "empty", last_error)
        return ExtractedDocument("", content_type, "error", last_error or f"browser-act extraction failed for {url}")

    def _attempt_session_extract(self, url: str, *, content_type: str) -> ExtractedDocument:
        if not self.session_name:
            return ExtractedDocument(
                "",
                content_type,
                "error",
                "browser-act session mode requires a session name",
            )

        last_error = ""
        commands = [
            ["browser-act", "--session", self.session_name, "navigate", url],
            ["browser-act", "--session", self.session_name, "wait", "stable"],
            ["browser-act", "--session", self.session_name, "get", content_type],
        ]
        for attempt in range(1, 3):
            try:
                for command in commands[:-1]:
                    subprocess.run(
                        command,
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout_seconds,
                    )
                completed = subprocess.run(
                    commands[-1],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
                stdout = (completed.stdout or "").strip()
                if not stdout:
                    return ExtractedDocument("", content_type, "empty", "No content extracted")
                if self._looks_gated(stdout):
                    return ExtractedDocument(stdout, content_type, "gated", "Instagram login/captcha gate detected")
                return ExtractedDocument(stdout, content_type, "ok")
            except subprocess.CalledProcessError as exc:
                last_error = (exc.stderr or exc.stdout or str(exc)).strip()
                if self._looks_gated(last_error):
                    return ExtractedDocument("", content_type, "gated", last_error)
                if self._looks_empty(last_error):
                    return ExtractedDocument("", content_type, "empty", last_error)
            except subprocess.TimeoutExpired as exc:
                last_error = f"timed out after {exc.timeout} seconds"

            if attempt == 1:
                time.sleep(1)

        if self._looks_gated(last_error):
            return ExtractedDocument("", content_type, "gated", last_error)
        if self._looks_empty(last_error):
            return ExtractedDocument("", content_type, "empty", last_error)
        return ExtractedDocument("", content_type, "error", last_error or f"browser-act session extraction failed for {url}")

    def _build_command(self, url: str, *, content_type: str) -> list[str]:
        cmd = ["browser-act", "stealth-extract", url, "--content-type", content_type]
        if self.proxy_region:
            cmd += ["--dynamic-proxy", self.proxy_region]
        return cmd

    def _looks_gated(self, text: str) -> bool:
        lowered = text.lower()
        return any(pattern in lowered for pattern in GATE_PATTERNS)

    def _looks_empty(self, text: str) -> bool:
        lowered = text.lower()
        return any(pattern in lowered for pattern in EMPTY_PATTERNS)

    def _document_to_analysis(self, handle: str, document: str, content_type: str) -> CompetitorAnalysis:
        text = self._document_text(document, content_type)
        followers = self._extract_count(text, "followers")
        following = self._extract_count(text, "following")
        post_count = self._extract_count(text, "posts")
        bio = self._extract_bio(text, handle)

        return CompetitorAnalysis(
            handle=handle,
            platform="instagram",
            follower_count=followers,
            following_count=following,
            post_count=post_count,
            bio=bio,
        )

    def _document_to_posts(self, document: str, content_type: str, *, default_caption: str, limit: int) -> list[PostData]:
        posts: list[PostData] = []
        seen: set[str] = set()
        if content_type == "html":
            soup = BeautifulSoup(document, "html.parser")
            for anchor in soup.find_all("a", href=True):
                href = str(anchor.get("href") or "")
                absolute_href = self._absolute_url(href)
                match = POST_URL_RE.search(absolute_href)
                if not match:
                    continue
                shortcode = match.group(1)
                if shortcode in seen:
                    continue
                seen.add(shortcode)
                caption = self._anchor_caption(anchor) or default_caption
                posts.append(
                    PostData(
                        platform="instagram",
                        post_id=shortcode,
                        url=absolute_href,
                        caption=caption,
                        hashtags=self._hashtags(caption),
                        media_type="Reel" if "/reel/" in absolute_href else "GraphImage",
                    )
                )
                if len(posts) >= limit:
                    return posts
            return posts

        lines = document.splitlines()
        for index, line in enumerate(lines):
            for match in POST_URL_RE.finditer(line):
                shortcode = match.group(1)
                if shortcode in seen:
                    continue
                seen.add(shortcode)
                caption = self._nearby_caption(lines, index) or default_caption
                posts.append(
                    PostData(
                        platform="instagram",
                        post_id=shortcode,
                        url=match.group(0),
                        caption=caption,
                        hashtags=self._hashtags(caption),
                        media_type="Reel" if "/reel/" in match.group(0) else "GraphImage",
                    )
                )
                if len(posts) >= limit:
                    return posts
        return posts

    def _document_text(self, document: str, content_type: str) -> str:
        if content_type != "html":
            return document
        soup = BeautifulSoup(document, "html.parser")
        return soup.get_text("\n", strip=True)

    def _anchor_caption(self, anchor) -> str:
        text = anchor.get_text(" ", strip=True)
        if text and not self._looks_gated(text):
            return text[:500]
        parent = anchor.find_parent(["article", "div", "section"])
        if parent is not None:
            parent_text = parent.get_text(" ", strip=True)
            if parent_text:
                return parent_text[:500]
        return ""

    def _absolute_url(self, href: str) -> str:
        if href.startswith("http://") or href.startswith("https://"):
            return href
        if href.startswith("/"):
            return f"https://www.instagram.com{href}"
        return f"https://www.instagram.com/{href.lstrip('/')}"

    def _extract_count(self, markdown: str, label: str) -> int:
        pattern = re.compile(rf"([\d,.]+)\s*([kKmM]?)\s+{re.escape(label)}", re.IGNORECASE)
        match = pattern.search(markdown)
        if not match:
            return 0

        value = float(match.group(1).replace(",", ""))
        suffix = match.group(2).lower()
        if suffix == "k":
            value *= 1_000
        elif suffix == "m":
            value *= 1_000_000
        return int(value)

    def _extract_bio(self, markdown: str, handle: str) -> str:
        stripped_lines = [line.strip() for line in markdown.splitlines() if line.strip()]
        skipped = {
            "verified",
            "options",
            "media",
            "posts",
            "reels",
            "tagged",
            "related accounts",
            "see all",
            "follow",
            "sign up",
            "log in",
            "close",
        }
        for line in stripped_lines:
            clean = re.sub(r"[*_`#\[\]()>-]+", "", line).strip()
            if not clean:
                continue
            lower = clean.lower()
            if lower in skipped:
                continue
            if re.search(r"\b(posts|followers|following)\b", lower):
                continue
            if handle.lower() in lower or "instagram" in lower:
                continue
            if POST_URL_RE.search(clean):
                continue
            return clean[:500]
        return ""

    def _nearby_caption(self, lines: list[str], index: int) -> str:
        start = max(0, index - 2)
        end = min(len(lines), index + 3)
        for line in lines[start:end]:
            clean = re.sub(r"\s+", " ", line).strip()
            if clean and not POST_URL_RE.search(clean):
                return clean[:500]
        return ""

    def _hashtags(self, text: str) -> list[str]:
        return [tag.lstrip("#") for tag in re.findall(r"#\w+", text)]
