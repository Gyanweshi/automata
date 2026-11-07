"""LinkedIn competitor research through a real browser (Playwright or browser-act); free, no scraping service.

Logged out, a company page already shows the follower count, the description and about 10 recent posts with
reaction and comment counts. Logged in (one-time login, see page_fetch.py), scrolling loads more posts.
"""
from __future__ import annotations

import logging

from agency_common.models import CompetitorAnalysis, PostData

from .page_fetch import PageFetcher, make_fetcher
from .social_parsers import parse_linkedin_company, parse_linkedin_posts, summarize

logger = logging.getLogger(__name__)


def company_url(identifier: str) -> str:
    """'hubspot', '/company/hubspot', or a full URL -> https://www.linkedin.com/company/hubspot/"""
    value = identifier.strip()
    if value.startswith("http"):
        return value if value.endswith("/") else value + "/"
    slug = value.strip("/").removeprefix("company/")
    return f"https://www.linkedin.com/company/{slug}/"


class LinkedInScraper:
    def __init__(self, fetcher: PageFetcher | None = None, dry_run: bool = False):
        self.fetcher = fetcher or make_fetcher("linkedin")
        self.dry_run = dry_run

    def build_competitor_analysis(self, company: str, post_count: int = 20) -> CompetitorAnalysis:
        url = company_url(company)
        if self.dry_run:
            return CompetitorAnalysis(handle=url, platform="linkedin", scrape_status="dry_run")
        page = self.fetcher.fetch(url, scrolls=max(0, post_count // 10 - 1))
        if not page.ok:
            logger.warning("LinkedIn %s: %s", url, page.error or page.status)
            return CompetitorAnalysis(handle=url, platform="linkedin", bio=page.error, scrape_status=page.status)
        analysis = parse_linkedin_company(page.html, url)
        posts: list[PostData] = parse_linkedin_posts(page.html, limit=post_count)
        if len(posts) < post_count:
            # logged in, the posts tab lists more than the overview (logged out it is walled and skipped)
            more = self.fetcher.fetch(url + "posts/?feedView=all", scrolls=max(1, post_count // 5))
            if more.ok:
                extra = parse_linkedin_posts(more.html, limit=post_count)
                seen = {p.post_id for p in posts}
                posts += [p for p in extra if p.post_id not in seen][: post_count - len(posts)]
        analysis = summarize(analysis, posts)
        analysis.scrape_status = "ok" if posts or analysis.follower_count else "empty"
        return analysis
