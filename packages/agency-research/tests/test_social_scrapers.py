"""LinkedIn / Facebook / Reddit / X / Ad Library research through Playwright or browser-act (no paid service).

The HTML snippets mirror the markup read from the live sites in November 2026 (logged-out LinkedIn company page,
Facebook page, www.reddit.com listing, Ad Library search); X follows its documented data-testid markup.
"""
import subprocess

from agency_research.scrapers import page_fetch
from agency_research.scrapers.community_listener import CommunityListener
from agency_research.scrapers.facebook import FacebookScraper
from agency_research.scrapers.linkedin import LinkedInScraper, company_url
from agency_research.scrapers.meta_ads import MetaAdsLibraryScraper
from agency_research.scrapers.page_fetch import BrowserActPageFetcher, FetchedPage, is_wall
from agency_research.scrapers.social_parsers import (
    parse_ad_library, parse_count, parse_facebook_page, parse_facebook_posts, parse_linkedin_company,
    parse_linkedin_posts, parse_reddit_listing, parse_x_timeline,
)

LINKEDIN = """<html><head>
<meta property="og:description" content="Acme | 1,778,611 followers on LinkedIn. Tagline | Long description.">
</head><body>
<p data-test-id="about-us__description">Acme makes CRM software.</p>
<article data-activity-urn="urn:li:activity:111"><time>1d</time>
  <p data-test-id="main-feed-activity-card__commentary">Shipping day #launch #crm</p>
  <div data-test-id="feed-native-video-content"></div>
  <span data-test-id="social-actions__reaction-count">234</span>
  <a data-test-id="social-actions__comments" data-num-comments="14">14 Comments</a></article>
<article data-activity-urn="urn:li:activity:222"><time>1w</time>
  <p data-test-id="main-feed-activity-card__commentary">Q4 plans</p>
  <span data-test-id="social-actions__reaction-count">1.4K</span>
  <a data-test-id="social-actions__comments">3 Comments</a> 5 reposts</article>
</body></html>"""

FACEBOOK = """<html><body>
<span>Acme</span><span>2.1M</span><span>followers</span><span>Intro</span><span>We build CRM tools.</span>
<div aria-posinset="1"><span>Friday 6 November 2026 at 21:12</span>
  <div data-ad-comet-preview="message">never give up on your KPIs #growth</div>
  <a href="https://www.facebook.com/acme/posts/pfbid02abc?__cft__=x">20h</a>
  <span>All reactions:</span><span>3</span><span>1</span><span>Like</span><span>Comment</span></div>
<div aria-posinset="2"><div data-ad-preview="message">Second post</div>
  <a href="https://www.facebook.com/acme/videos/987/">video</a>
  <span>All reactions:</span><span>1.2K</span><span>45 comments</span><span>7 shares</span></div>
</body></html>"""


def test_parse_count_handles_separators_and_suffixes():
    assert parse_count("1,778,611") == 1778611
    assert parse_count("2.1M") == 2_100_000
    assert parse_count("1.4K") == 1400
    assert parse_count("14 Comments") == 14
    assert parse_count("12 Replies. Reply") == 12
    assert parse_count("") == 0 and parse_count(None) == 0
    assert parse_count("17,78,611") == 1778611          # Indian digit grouping
    assert parse_count("21 लाख") == 2_100_000 and parse_count("1.2 crore") == 12_000_000


def test_pages_served_in_hindi():
    li = '<html><body><span>HubSpot</span><span>17,78,611 फ़ॉलोअर</span></body></html>'
    assert parse_linkedin_company(li, "h").follower_count == 1778611
    fb = ('<a href="https://www.facebook.com/hubspot/followers/"><strong>21 लाख</strong> फ़ॉलोअर</a>'
          '<div aria-posinset="1"><div data-ad-preview="message">Hi</div><span>सभी रिएक्शन:</span><span>3</span></div>')
    assert parse_facebook_page(fb, "h").follower_count == 2_100_000
    assert parse_facebook_posts(fb)[0].likes == 3


def test_linkedin_company_and_posts():
    analysis = parse_linkedin_company(LINKEDIN, "https://www.linkedin.com/company/acme/")
    assert analysis.follower_count == 1778611
    assert analysis.bio == "Acme makes CRM software."
    posts = parse_linkedin_posts(LINKEDIN)
    assert [(p.post_id, p.likes, p.comments, p.shares, p.media_type) for p in posts] == [
        ("111", 234, 14, 0, "video"), ("222", 1400, 3, 5, "text")]
    assert posts[0].hashtags == ["launch", "crm"] and posts[0].timestamp == "1d"
    assert posts[0].url == "https://www.linkedin.com/feed/update/urn:li:activity:111/"


def test_linkedin_logged_in_markup():
    html = ('<div data-urn="urn:li:activity:9"><div class="update-components-text">Hello</div>'
            '<span class="social-details-social-counts__reactions-count">57</span>'
            '<button aria-label="8 comments">8 comments</button></div>')
    post = parse_linkedin_posts(html)[0]
    assert (post.post_id, post.caption, post.likes, post.comments) == ("9", "Hello", 57, 8)


def test_facebook_page_and_posts():
    analysis = parse_facebook_page(FACEBOOK, "acme")
    assert analysis.follower_count == 2_100_000 and analysis.bio == "We build CRM tools."
    first, second = parse_facebook_posts(FACEBOOK)
    assert (first.likes, first.comments, first.caption) == (3, 1, "never give up on your KPIs #growth")
    assert first.url == "https://www.facebook.com/acme/posts/pfbid02abc" and first.timestamp.startswith("Friday")
    assert (second.likes, second.comments, second.shares, second.media_type) == (1200, 45, 7, "video")


def test_reddit_new_and_old_markup():
    html = ('<shreddit-post post-title="How do you price?" score="94" comment-count="147" author="u1" '
            'subreddit-prefixed-name="r/marketing" permalink="/r/marketing/comments/1/x/" '
            'created-timestamp="2026-10-31T18:33:10+0000"><div slot="text-body">Body text</div></shreddit-post>'
            '<div class="thing" data-fullname="t3_2" data-score="5" data-comments-count="2" data-author="u2" '
            'data-permalink="/r/a/comments/2/y/"><a class="title">Old title</a></div>')
    new, old = parse_reddit_listing(html)
    assert (new.title, new.upvotes, new.comments, new.body) == ("How do you price?", 94, 147, "Body text")
    assert new.url == "https://www.reddit.com/r/marketing/comments/1/x/"
    assert (old.title, old.upvotes, old.comments) == ("Old title", 5, 2)


def test_x_timeline():
    html = ('<article data-testid="tweet"><a href="/acme/status/42"><time datetime="2026-11-01T10:00:00Z">1h</time></a>'
            '<div data-testid="tweetText">Big news</div><button data-testid="reply" aria-label="12 Replies. Reply"></button>'
            '<button data-testid="retweet" aria-label="3 reposts. Repost"></button>'
            '<button data-testid="like" aria-label="1.5K Likes. Like"></button></article>')
    post = parse_x_timeline(html)[0]
    assert (post.body, post.comments, post.upvotes, post.score, post.author) == ("Big news", 12, 1500, 3.0, "acme")
    assert post.url == "https://x.com/acme/status/42"


def test_ad_library():
    html = ("<div>~180 results</div><div>Active</div><div>Library ID: 853993154402442</div>"
            "<div>Started running on 24 Sep 2026</div><div>Platforms</div><div>Acme</div><div>Sponsored</div>"
            "<div>Grow faster with Acme.</div><div>0:00 / 0:31</div><div>Learn more</div>"
            "<div>Active</div><div>Library ID: 2</div><div>Started running on 1 Oct 2026</div><div>Beta</div>"
            "<div>Sponsored</div><div>Second ad</div>")
    first, second = parse_ad_library(html)
    assert (first["ad_id"], first["page_name"], first["started_running"]) == ("853993154402442", "Acme", "24 Sep 2026")
    assert first["ad_copy"] == "Grow faster with Acme." and first["cta"] == "Learn more" and first["days_running"] > 0
    assert (second["page_name"], second["ad_copy"]) == ("Beta", "Second ad")


class FakeFetcher:
    backend = "fake"

    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def fetch(self, url, scrolls=0):
        self.calls.append(url)
        return self.pages.get(url, FetchedPage(url, status="gated", error="login"))


def test_linkedin_scraper_uses_overview_and_tolerates_walled_posts_tab():
    url = "https://www.linkedin.com/company/acme/"
    fetcher = FakeFetcher({url: FetchedPage(url, LINKEDIN)})
    analysis = LinkedInScraper(fetcher=fetcher).build_competitor_analysis("acme", post_count=5)
    assert fetcher.calls == [url, url + "posts/?feedView=all"]
    assert analysis.scrape_status == "ok" and analysis.follower_count == 1778611 and len(analysis.top_posts) == 2
    assert analysis.avg_likes == (234 + 1400) / 2 and analysis.content_types == {"video": 1, "text": 1}
    assert company_url("https://www.linkedin.com/company/acme") == url


def test_scrapers_report_a_gated_page_instead_of_failing():
    analysis = FacebookScraper(fetcher=FakeFetcher({})).build_competitor_analysis("acme")
    assert analysis.scrape_status == "gated" and analysis.top_posts == []
    assert LinkedInScraper(fetcher=FakeFetcher({}), dry_run=True).build_competitor_analysis("x").scrape_status == "dry_run"


def test_listener_and_ads_use_the_browser_without_tokens():
    reddit = "https://www.reddit.com/r/marketing/top/?t=week"
    page = FetchedPage(reddit, '<shreddit-post post-title="Q?" score="1" comment-count="2"></shreddit-post>')
    listener = CommunityListener(fetcher_for=lambda site: FakeFetcher({reddit: page}))
    report = listener.scrape(subreddits=["r/marketing"], youtube_channels=[], x_lists=[])
    assert report.sources == ["reddit"] and report.posts[0].title == "Q?"

    ads_page = FetchedPage("x", "<div>Library ID: 7</div><div>Started running on 1 Jan 2026</div><div>Acme</div>"
                                "<div>Sponsored</div><div>Buy now please</div>")
    fetcher = FakeFetcher({})
    fetcher.fetch = lambda url, scrolls=0: ads_page
    report = MetaAdsLibraryScraper(fetcher=fetcher).audit(["crm"])
    assert report.ads[0].ad_id == "7" and report.ads[0].url.endswith("?id=7")


def test_login_walls_are_detected_per_site():
    assert is_wall("linkedin", "https://www.linkedin.com/authwall?trk=x")
    assert is_wall("facebook", "https://www.facebook.com/login/?next=x")
    assert not is_wall("linkedin", "https://www.linkedin.com/company/acme/")


def test_browser_act_fetcher_reads_the_page_in_the_saved_browser(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        out = {"list": '{"browsers": [{"id": "b1", "name": "instagram-research"}]}', "eval": '"https://www.linkedin.com/company/acme/"',
               "html": "<html>ok</html>"}
        key = "list" if "list" in args else "eval" if "eval" in args else "html" if "html" in args else ""
        return subprocess.CompletedProcess(args, 0, out.get(key, ""), "")

    monkeypatch.setattr(page_fetch.subprocess, "run", fake_run)
    page = BrowserActPageFetcher("linkedin").fetch("https://www.linkedin.com/company/acme/", scrolls=1)
    assert page.ok and page.html == "<html>ok</html>"
    assert ["browser-act", "--session", "automata-social-linkedin-1", "browser", "open", "b1",
            "https://www.linkedin.com/company/acme/"] in calls
    assert ["browser-act", "--session", "automata-social-linkedin-1", "scroll", "down", "--amount", "2500"] in calls
    assert calls[-1][:3] == ["browser-act", "session", "close"]


def test_browser_act_fetcher_flags_a_login_wall(monkeypatch):
    def fake_run(args, **kwargs):
        out = '{"browsers": [{"id": "b1", "name": "instagram-research"}]}' if "list" in args else \
            '"https://www.facebook.com/login/?next=x"' if "eval" in args else "<html></html>"
        return subprocess.CompletedProcess(args, 0, out, "")

    monkeypatch.setattr(page_fetch.subprocess, "run", fake_run)
    page = BrowserActPageFetcher("facebook").fetch("https://www.facebook.com/acme")
    assert page.status == "gated" and "--site facebook" in page.error
