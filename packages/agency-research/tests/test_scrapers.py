from agency_common.models import CompetitorAnalysis
from agency_research.scrapers.apify_instagram import ApifyInstagramScraper
from agency_research.scrapers.browser_act_instagram import BrowserActInstagramScraper


def test_apify_item_to_post_maps_common_actor_fields():
    scraper = ApifyInstagramScraper(dry_run=True)

    post = scraper._item_to_post(
        {
            "shortCode": "ABC123",
            "url": "https://www.instagram.com/p/ABC123/",
            "caption": "New drop #design #branding",
            "likesCount": 42,
            "commentsCount": 7,
            "timestamp": "2026-05-06T12:00:00.000Z",
            "hashtags": [{"name": "design"}, {"name": "branding"}],
            "type": "Video",
        }
    )

    assert post is not None
    assert post.platform == "instagram"
    assert post.post_id == "ABC123"
    assert post.likes == 42
    assert post.comments == 7
    assert post.hashtags == ["design", "branding"]
    assert post.media_type == "Video"


def test_apify_build_analysis_calculates_engagement_and_post_metadata():
    scraper = ApifyInstagramScraper(dry_run=True)

    analysis = scraper._build_analysis(
        "brandstudio",
        [
            {
                "shortCode": "ONE",
                "caption": "Launch #creative",
                "likesCount": 100,
                "commentsCount": 10,
                "followersCount": 1000,
                "followingCount": 50,
                "postsCount": 20,
                "biography": "A studio",
                "hashtags": ["creative"],
                "type": "Image",
            },
            {
                "shortCode": "TWO",
                "caption": "Behind the scenes #creative #process",
                "likesCount": 50,
                "commentsCount": 5,
                "hashtags": ["creative", "process"],
                "type": "Video",
            },
        ],
    )

    assert analysis.handle == "brandstudio"
    assert analysis.follower_count == 1000
    assert analysis.following_count == 50
    assert analysis.post_count == 20
    assert analysis.bio == "A studio"
    assert analysis.avg_likes == 75
    assert analysis.avg_comments == 7.5
    assert analysis.avg_engagement_rate == 8.25
    assert analysis.top_hashtags == ["creative", "process"]
    assert analysis.content_types == {"Image": 1, "Video": 1}


def test_apify_research_brand_dry_run_returns_competitor_shells():
    scraper = ApifyInstagramScraper(dry_run=True)

    competitors, hashtag_posts = scraper.research_brand(
        competitor_handles=["@first", "second"],
        hashtags=["niche"],
    )

    assert hashtag_posts == []
    assert competitors == [
        CompetitorAnalysis(handle="first", platform="instagram"),
        CompetitorAnalysis(handle="second", platform="instagram"),
    ]




def test_browser_act_stealth_extract_uses_markdown_content_type(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))

        class Completed:
            stdout = (
                "42K followers 12 following 99 posts\n"
                "Verified\n"
                "Bio line\n"
                "https://www.instagram.com/brandstudio/p/ABC123/"
            )

        return Completed()

    monkeypatch.setattr("agency_research.scrapers.browser_act_instagram.subprocess.run", fake_run)
    scraper = BrowserActInstagramScraper()

    analysis = scraper.build_competitor_analysis("@brandstudio", post_count=3)

    assert calls[0][0] == [
        "browser-act",
        "stealth-extract",
        "https://www.instagram.com/brandstudio/",
        "--content-type",
        "markdown",
    ]
    assert calls[0][1]["check"] is True
    assert calls[0][1]["capture_output"] is True
    assert calls[0][1]["text"] is True
    assert analysis.handle == "brandstudio"
    assert analysis.follower_count == 42000
    assert analysis.following_count == 12
    assert analysis.post_count == 99
    assert analysis.bio == "Bio line"
    assert analysis.top_posts[0].post_id == "ABC123"
    assert analysis.scrape_status == "ok"


def test_browser_act_uses_proxy_and_html_fallback(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        content_type = args[args.index("--content-type") + 1]
        if content_type == "markdown":
            from subprocess import CalledProcessError

            raise CalledProcessError(1, args, stderr="No content extracted")

        class Completed:
            stdout = (
                "<html><body>"
                "<div>42K followers 12 following 99 posts</div>"
                "<div>Bio line</div>"
                '<a href="/brandstudio/p/ABC123/">Open post</a>'
                "</body></html>"
            )

        return Completed()

    monkeypatch.setattr("agency_research.scrapers.browser_act_instagram.subprocess.run", fake_run)
    scraper = BrowserActInstagramScraper(proxy_region="US")

    analysis = scraper.build_competitor_analysis("@brandstudio", post_count=3)

    assert calls[0] == [
        "browser-act",
        "stealth-extract",
        "https://www.instagram.com/brandstudio/",
        "--content-type",
        "markdown",
        "--dynamic-proxy",
        "US",
    ]
    assert calls[1] == [
        "browser-act",
        "stealth-extract",
        "https://www.instagram.com/brandstudio/",
        "--content-type",
        "html",
        "--dynamic-proxy",
        "US",
    ]
    assert analysis.scrape_status == "ok"
    assert analysis.bio == "Bio line"
    assert analysis.top_posts[0].post_id == "ABC123"


def test_browser_act_marks_login_gate_as_gated(monkeypatch):
    def fake_run(args, **kwargs):
        from subprocess import CalledProcessError

        raise CalledProcessError(
            1,
            args,
            stderr="Error: Page appears to be a login or captcha gate (detected by URL/title keywords).",
        )

    monkeypatch.setattr("agency_research.scrapers.browser_act_instagram.subprocess.run", fake_run)
    scraper = BrowserActInstagramScraper()

    analysis = scraper.build_competitor_analysis("@brandstudio", post_count=3)

    assert analysis.scrape_status == "gated"
    assert analysis.top_posts == []
    assert "gate" in analysis.bio.lower()


def test_browser_act_session_mode_uses_persistent_session(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        command = args[-2:]
        if command == ["get", "markdown"]:
            class Completed:
                stdout = (
                    "42K followers 12 following 99 posts\n"
                    "Bio line\n"
                    "https://www.instagram.com/brandstudio/p/ABC123/"
                )

            return Completed()

        class Completed:
            stdout = ""

        return Completed()

    monkeypatch.setattr("agency_research.scrapers.browser_act_instagram.subprocess.run", fake_run)
    scraper = BrowserActInstagramScraper(mode="session", session_name="ig-main")

    analysis = scraper.build_competitor_analysis("@brandstudio", post_count=3)

    assert calls[0] == ["browser-act", "--session", "ig-main", "navigate", "https://www.instagram.com/brandstudio/"]
    assert calls[1] == ["browser-act", "--session", "ig-main", "wait", "stable"]
    assert calls[2] == ["browser-act", "--session", "ig-main", "get", "markdown"]
    assert analysis.scrape_status == "ok"
    assert analysis.top_posts[0].post_id == "ABC123"


def test_browser_act_profile_dry_run_marks_status():
    scraper = BrowserActInstagramScraper(dry_run=True)

    analysis = scraper.build_competitor_analysis("@first", post_count=1)

    assert analysis.scrape_status == "dry_run"


def test_browser_act_research_brand_dry_run_returns_competitor_shells():
    scraper = BrowserActInstagramScraper(dry_run=True)

    competitors, hashtag_posts = scraper.research_brand(
        competitor_handles=["@first", "second"],
        hashtags=["niche"],
    )

    assert hashtag_posts == []
    assert competitors == [
        CompetitorAnalysis(handle="first", platform="instagram"),
        CompetitorAnalysis(handle="second", platform="instagram"),
    ]
