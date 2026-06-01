import threading
import time
from types import SimpleNamespace

import pytest

from agency_common.models import (
    BrandPlatformConfig,
    BrandPlatforms,
    BrandProfile,
    CompetitorAnalysis,
    PlatformResearch,
    PostData,
)
import agency_research.agent as research_agent_module
from agency_research.agent import ResearchAgent


class EmptyAnalyzer:
    def trending_hashtags(self, posts, top_n=20):
        return []

    def content_themes(self, posts, top_n=10):
        return []

    def analyze_posts(self, posts):
        return None


def _brand() -> BrandProfile:
    return BrandProfile(
        slug="parallel-brand",
        name="Parallel Brand",
        platforms=BrandPlatforms(
            instagram=BrandPlatformConfig(handle="@parallel"),
            linkedin=BrandPlatformConfig(handle="parallel"),
        ),
    )


def _platform_result(platform: str) -> PlatformResearch:
    return PlatformResearch(
        platform=platform,
        competitors=[CompetitorAnalysis(handle=f"{platform}-competitor", platform=platform)],
        raw_posts=[
            PostData(
                platform=platform,
                post_id=f"{platform}-1",
                caption="parallel test",
            )
        ],
    )


def test_research_run_parallelizes_platform_tasks(monkeypatch):
    agent = ResearchAgent(dry_run=True)
    agent.trend_analyzer = EmptyAnalyzer()
    agent.sentiment_analyzer = EmptyAnalyzer()

    lock = threading.Lock()
    started: set[str] = set()
    both_started = threading.Event()

    def task(platform: str):
        with lock:
            started.add(platform)
            if started == {"instagram", "linkedin"}:
                both_started.set()
        assert both_started.wait(2), "platform tasks did not overlap"
        time.sleep(0.01)
        return _platform_result(platform)

    monkeypatch.setattr(agent, "_research_instagram", lambda brand, post_count: task("instagram"))
    monkeypatch.setattr(
        agent,
        "_research_linkedin",
        lambda brand, post_count, **kwargs: task("linkedin"),
    )

    output = agent.run(
        _brand(),
        platforms=["instagram", "linkedin"],
        enable_listening=False,
        enable_ads=False,
        enable_visual_dna=False,
        enable_comments=False,
        enable_adjacencies=False,
        parallel=True,
        max_workers=2,
    )

    assert set(output.platforms) == {"instagram", "linkedin"}


def test_linkedin_competitors_parallelize_when_requested():
    agent = ResearchAgent(dry_run=True)
    agent.trend_analyzer = EmptyAnalyzer()
    agent.sentiment_analyzer = EmptyAnalyzer()

    brand = _brand()
    brand.competitors.linkedin = ["https://linkedin.com/company/a", "https://linkedin.com/company/b"]

    lock = threading.Lock()
    started: set[str] = set()
    both_started = threading.Event()

    def build(company_url: str, post_count: int):
        with lock:
            started.add(company_url)
            if len(started) == 2:
                both_started.set()
        assert both_started.wait(2), "competitor tasks did not overlap"
        return CompetitorAnalysis(
            handle=company_url,
            platform="linkedin",
            top_posts=[PostData(platform="linkedin", post_id=company_url)],
        )

    agent.li = SimpleNamespace(build_competitor_analysis=build)

    output = agent._research_linkedin(brand, post_count=5, parallel=True, max_workers=2)

    assert len(output.competitors) == 2
    assert len(output.raw_posts) == 2


def test_research_run_rejects_invalid_worker_count():
    agent = ResearchAgent(dry_run=True)

    with pytest.raises(ValueError, match="max_workers"):
        agent.run(_brand(), max_workers=0)


def test_research_agent_passes_manual_login_to_playwright(monkeypatch):
    captured = {}

    class StubPlaywrightScraper:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setitem(research_agent_module.INSTAGRAM_SCRAPERS, "playwright", StubPlaywrightScraper)

    ResearchAgent(dry_run=True, scraper="playwright", instagram_login_mode="manual")

    assert captured["dry_run"] is True
    assert captured["manual_login"] is True
