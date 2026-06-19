"""Instagram scraper using the CDP-based ig-research Node.js tool.

Wraps ~/ig-research/scripts/scrape.js so the scrape runs inside the agency
pipeline and its output feeds directly into PostData / CompetitorAnalysis
objects — the same interface as every other scraper.

The Node tool requires Chrome running with --remote-debugging-port=9222.
Wraps agents/automata_core/ig-research/scripts/scrape.js so the scrape runs
inside the agency pipeline and its output feeds directly into PostData /
CompetitorAnalysis objects — the same interface as every other scraper.

The Node tool requires Chrome running with --remote-debugging-port=9222
(see agents/automata_core/scripts/open-instagram-session.ps1 -Mode cdp).
If Chrome is not reachable, this scraper logs a warning and returns empty
results rather than crashing the whole research run.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

from agency_common.models import CompetitorAnalysis, PostData

logger = logging.getLogger(__name__)

# Location of the ig-research tool
IG_RESEARCH_DIR = Path.home() / "ig-research"
# Location of the ig-research tool. Ships in-repo; override with IG_RESEARCH_DIR
# for a custom install.
_REPO_IG_RESEARCH_DIR = Path(__file__).resolve().parents[5] / "agents" / "automata_core" / "ig-research"
IG_RESEARCH_DIR = Path(os.environ.get("IG_RESEARCH_DIR", str(_REPO_IG_RESEARCH_DIR)))
SCRAPE_SCRIPT = IG_RESEARCH_DIR / "scripts" / "scrape.js"


def _parse_engagement(likes_str: str) -> int:
    """Convert '1,234', '94,180 likes', '6.3M', '10.4K' to int."""
    if not likes_str:
        return 0
    s = (
        str(likes_str)
        .replace(",", "")
        .replace(" likes", "")
        .replace(" like", "")
        .strip()
    )
    try:
        if s.upper().endswith("M"):
            return int(float(s[:-1]) * 1_000_000)
        if s.upper().endswith("K"):
            return int(float(s[:-1]) * 1_000)
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def _parse_comments(comments_str: str) -> int:
    if not comments_str:
        return 0
    s = str(comments_str).replace("View all", "").replace("comments", "").replace(",", "").strip()
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def _raw_post_to_post_data(raw: dict) -> PostData:
    url = raw.get("url") or ("https://www.instagram.com" + raw.get("href", ""))
    return PostData(
        platform="instagram",
        post_id=raw.get("postId", ""),
        url=url,
        caption=raw.get("fullCaption") or raw.get("caption", ""),
        likes=_parse_engagement(raw.get("likes", "")),
        comments=_parse_comments(raw.get("comments", "")),
        shares=_parse_engagement(str(raw.get("shares", 0))),
        timestamp=raw.get("date", ""),
        media_type=raw.get("type", ""),
        hashtags=[
            w.lstrip("#")
            for w in (raw.get("fullCaption") or "").split()
            if w.startswith("#")
        ],
    )


class CDPInstagramScraper:
    """Scrape Instagram via the CDP Node.js tool (requires Chrome on port 9222).

    Implements the same research_brand() interface as the other Instagram
    scrapers so it can be swapped in via --scraper cdp in the CLI.
    """

    def __init__(
        self,
        dry_run: bool = False,
        chrome_port: int = 9222,
        project_dir: Optional[Path] = None,
    ):
        self.dry_run = dry_run
        self.chrome_port = chrome_port
        # Allow override for testing; default to a temp dir per run
        self._project_dir = project_dir

    # ------------------------------------------------------------------
    # Public interface (mirrors PlaywrightInstagramScraper)
    # ------------------------------------------------------------------

    def research_brand(
        self,
        competitor_handles: list[str],
        hashtags: list[str],
        post_count: int = 50,
    ) -> tuple[list[CompetitorAnalysis], list[PostData]]:
        """Run the CDP scraper for the given hashtags and competitor handles.

        Returns (competitor_analyses, hashtag_posts) just like the other scrapers.
        """
        if self.dry_run:
            logger.info("[CDPInstagramScraper] dry_run — returning empty results")
            return [], []

        if not SCRAPE_SCRIPT.exists():
            logger.warning(
                "[CDPInstagramScraper] scrape.js not found at %s — skipping", SCRAPE_SCRIPT
            )
            return [], []

        if not self._chrome_reachable():
            logger.warning(
                "[CDPInstagramScraper] Chrome not reachable on port %d. "
                "Start Chrome with: google-chrome --remote-debugging-port=%d "
                "--user-data-dir=/tmp/chrome-debug — skipping",
                self.chrome_port,
                self.chrome_port,
            )
            return [], []

        with tempfile.TemporaryDirectory(prefix="ig-research-") as tmpdir:
            project_dir = self._project_dir or Path(tmpdir) / "project"
            project_dir.mkdir(parents=True, exist_ok=True)

            config = {
                "name": "agency-research",
                "niche": "brand research",
                "searchTerms": hashtags[:5],
                "competitors": [
                    f"https://www.instagram.com/{h.lstrip('@')}/"
                    for h in competitor_handles
                ],
                "browserPort": self.chrome_port,
                "maxPostsPerSearch": post_count,
                "maxCompetitorPosts": min(post_count, 20),
            }
            (project_dir / "config.json").write_text(json.dumps(config, indent=2))

            # Create subfolders the scraper expects
            (project_dir / "transcripts").mkdir(exist_ok=True)
            (project_dir / "hook-screenshots").mkdir(exist_ok=True)

            logger.info(
                "[CDPInstagramScraper] scraping %d hashtags + %d competitors",
                len(hashtags),
                len(competitor_handles),
            )

            # Symlink projects/<slug> into ig-research so the script can find it
            projects_dir = IG_RESEARCH_DIR / "projects"
            slug = "agency-research-tmp"
            link = projects_dir / slug
            link.unlink(missing_ok=True)
            link.symlink_to(project_dir)

            try:
                result = subprocess.run(
                    ["node", str(SCRAPE_SCRIPT), slug],
                    cwd=str(IG_RESEARCH_DIR),
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
                if result.returncode != 0:
                    logger.warning(
                        "[CDPInstagramScraper] scrape.js exited %d: %s",
                        result.returncode,
                        result.stderr[:500],
                    )
                    return [], []
            finally:
                link.unlink(missing_ok=True)
            result = subprocess.run(
                ["node", str(SCRAPE_SCRIPT), str(project_dir)],
                cwd=str(IG_RESEARCH_DIR),
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.returncode != 0:
                logger.warning(
                    "[CDPInstagramScraper] scrape.js exited %d: %s",
                    result.returncode,
                    result.stderr[:500],
                )
                return [], []

            raw_posts_file = project_dir / "raw-posts.json"
            if not raw_posts_file.exists():
                logger.warning("[CDPInstagramScraper] no raw-posts.json produced")
                return [], []

            data = json.loads(raw_posts_file.read_text())
            raw_posts: list[dict] = data.get("posts", [])

        # Split into competitor posts vs hashtag posts
        competitor_posts: dict[str, list[PostData]] = {}
        hashtag_posts: list[PostData] = []

        for raw in raw_posts:
            post = _raw_post_to_post_data(raw)
            source: str = raw.get("source", "")
            if source.startswith("competitor:"):
                handle = source.split("competitor:")[-1].lstrip("@")
                competitor_posts.setdefault(handle, []).append(post)
            else:
                hashtag_posts.append(post)

        competitors = [
            self._build_competitor_analysis(handle, posts)
            for handle, posts in competitor_posts.items()
        ]

        logger.info(
            "[CDPInstagramScraper] done — %d competitor handles, %d hashtag posts",
            len(competitors),
            len(hashtag_posts),
        )
        return competitors, hashtag_posts

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _chrome_reachable(self) -> bool:
        import urllib.request
        try:
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.chrome_port}/json/version", timeout=3
            )
            return True
        except Exception:
            return False

    def _build_competitor_analysis(
        self, handle: str, posts: list[PostData]
    ) -> CompetitorAnalysis:
        if not posts:
            return CompetitorAnalysis(handle=handle, platform="instagram")

        top_posts = sorted(posts, key=lambda p: p.likes + p.comments * 3, reverse=True)[:20]

        format_counter: Counter = Counter(p.media_type for p in posts if p.media_type)
        content_types = dict(format_counter.most_common())

        return CompetitorAnalysis(
            handle=handle,
            platform="instagram",
            follower_count=0,  # not available without profile scrape
            avg_engagement_rate=0.0,  # no follower count to normalise against
            avg_likes=sum(p.likes for p in posts) / len(posts),
            avg_comments=sum(p.comments for p in posts) / len(posts),
            top_posts=top_posts,
            content_types=content_types,
            scraped_at=datetime.utcnow().isoformat(),
        )
