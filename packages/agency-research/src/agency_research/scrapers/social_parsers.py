"""Turn social page HTML into research data. Pure functions: no browser, no network (unit-tested on saved pages).

Each parser handles both the logged-out and the logged-in markup where the two differ. Sites change their markup;
when a parser starts returning nothing, save the page HTML and update the selectors here.
"""
from __future__ import annotations

import re
from collections import Counter

from bs4 import BeautifulSoup

from agency_common.models import CommunityPost, CompetitorAnalysis, PostData

# A number with an optional unit: K/M/B, or the Indian lakh/crore (pages served in Hindi, e.g. from an Indian IP).
UNITS = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000, "हज़ार": 1_000, "हजार": 1_000, "lakh": 100_000,
         "लाख": 100_000, "crore": 10_000_000, "करोड़": 10_000_000}
UNIT_RE = r"(?:[KkMmBb](?![a-z])|lakh|crore|हज़ार|हजार|लाख|करोड़)?"
COUNT = rf"(\d[\d.,]*\s*{UNIT_RE})"
FOLLOWERS = r"(?:followers|फ़ॉलोअर|फॉलोअर|abonnés|seguidores|Follower)"
REACTIONS = r"(?:All reactions|सभी रिएक्शन|सभी प्रतिक्रियाएँ|सभी प्रतिक्रियाएं)"


def parse_count(raw: str | None) -> int:
    """'1,778,611' -> 1778611, '2.1M' -> 2100000, '14 Comments' -> 14, '' -> 0."""
    match = re.search(rf"(\d[\d.,]*)\s*({UNIT_RE})", raw or "")
    if not match:
        return 0
    number, suffix = match.group(1), match.group(2).lower()
    if suffix:
        value = float(number.replace(",", ""))
    else:  # without a unit, '.' and ',' are digit-group separators (1,778,611 / 17,78,611 / 1.234)
        value = float(re.sub(r"[.,]", "", number))
    return int(value * UNITS.get(suffix, 1))


def _hashtags(text: str) -> list[str]:
    return [t.lstrip("#") for t in re.findall(r"#\w+", text or "")]


def _meta(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return str(tag["content"])
    return ""


def summarize(analysis: CompetitorAnalysis, posts: list[PostData]) -> CompetitorAnalysis:
    """Fill averages, top posts, hashtags and content types from the posts read."""
    if posts:
        analysis.top_posts = sorted(posts, key=lambda p: p.likes + p.comments + p.shares, reverse=True)[:5]
        analysis.avg_likes = sum(p.likes for p in posts) / len(posts)
        analysis.avg_comments = sum(p.comments for p in posts) / len(posts)
        if analysis.follower_count:
            analysis.avg_engagement_rate = round((analysis.avg_likes + analysis.avg_comments) / analysis.follower_count * 100, 4)
        analysis.top_hashtags = [t for t, _ in Counter(t for p in posts for t in p.hashtags).most_common(10)]
        analysis.content_types = dict(Counter(p.media_type or "post" for p in posts))
    return analysis


# ----------------------------------------------------------------------------------------------------------- LinkedIn

LINKEDIN_TOP_CARD = ".org-top-card-summary-info-list, .top-card-layout__first-subline, .org-top-card-summary__info-item"
# sidebars listing other companies, each with its own follower count
LINKEDIN_OTHER_PAGES = re.compile(r"also viewed|similar pages|affiliated pages|showcase pages|छोड़कर", re.I)


def _strip_other_pages(soup: BeautifulSoup) -> None:
    """Drop markup that carries other companies' follower counts: embedded JSON and the 'people also viewed' sidebars."""
    for tag in soup.select("script, code, aside"):
        tag.decompose()
    for heading in soup.find_all(["h2", "h3"], string=LINKEDIN_OTHER_PAGES):
        (heading.find_parent("section") or heading.parent).decompose()


def parse_linkedin_company(html: str, handle: str) -> CompetitorAnalysis:
    soup = BeautifulSoup(html, "html.parser")
    description = _meta(soup, "og:description", "description")
    top_card = " ".join(e.get_text(" ", strip=True) for e in soup.select(LINKEDIN_TOP_CARD))
    _strip_other_pages(soup)
    text = soup.get_text("\n", strip=True)
    followers = (re.search(COUNT + r"\s+" + FOLLOWERS, top_card) or re.search(COUNT + r"\s+" + FOLLOWERS, description)
                 or re.search(COUNT + r"\s+" + FOLLOWERS, text))
    about = soup.select_one('[data-test-id="about-us__description"]') \
        or soup.select_one("section.org-about-module p, p.org-about-us-organization-description__text") \
        or soup.select_one(".org-top-card-summary__tagline")
    bio = about.get_text(" ", strip=True) if about else (description.split(" | ", 2)[-1] if " | " in description else description)
    return CompetitorAnalysis(handle=handle, platform="linkedin", follower_count=parse_count(followers.group(1)) if followers else 0,
                              bio=bio[:500])


LINKEDIN_RELATIVE_TIME = re.compile(r"\d+\s?(?:s|m|h|d|w|mo|yr)")


def _linkedin_sdui_count(card, label: str) -> int:
    """Count inside the action button whose aria-label starts with `label` (new layout: no test ids, hashed classes)."""
    for span in card.find_all("span"):
        text = span.get_text(strip=True)
        if not re.fullmatch(COUNT, text):
            continue
        owner = next((p for p in span.parents if p.get("aria-label")), None)
        if owner is not None and owner.get("aria-label", "").startswith(label):
            return parse_count(text)
    return 0


def parse_linkedin_sdui_posts(html: str, limit: int = 20) -> list[PostData]:
    """Logged-in 2026 layout (profile 'recent activity'): server-driven UI cards, hashed class names, no activity
    URNs. Counts sit in the Reaction / Comment / Repost buttons; reposts of other people's posts are flagged."""
    soup = BeautifulSoup(html, "html.parser")
    posts: list[PostData] = []
    for card in soup.select('div[role="listitem"][componentkey^="update-card-focus"]'):
        key = card["componentkey"].removeprefix("update-card-focus")
        key = key.split("FeedType_")[0]
        body = card.select_one('[data-testid="expandable-text-box"]')
        caption = body.get_text(" ", strip=True) if body else ""
        tokens = card.get_text(" | ", strip=True).split(" | ")
        when = next((t for t in tokens[:20] if LINKEDIN_RELATIVE_TIME.fullmatch(t)), None)
        reposted = any("reposted this" in t for t in tokens[:6])
        media = "video" if card.select_one("video") else "image" if len(card.select("img")) > 1 else "text"
        posts.append(PostData(
            platform="linkedin", post_id=key, caption=caption[:2000], url="",
            likes=_linkedin_sdui_count(card, "Reaction"), comments=_linkedin_sdui_count(card, "Comment"),
            shares=_linkedin_sdui_count(card, "Repost"), timestamp=when, hashtags=_hashtags(caption),
            media_type="repost" if reposted else media,
        ))
        if len(posts) >= limit:
            break
    return posts


def parse_linkedin_posts(html: str, limit: int = 20) -> list[PostData]:
    soup = BeautifulSoup(html, "html.parser")
    # logged-out: <article data-activity-urn>; logged-in: <div data-urn="urn:li:activity:...">
    cards = soup.select("article[data-activity-urn]") or soup.select('[data-urn^="urn:li:activity:"]')
    if not cards:  # logged-in server-driven layout (profile activity pages since 2026)
        return parse_linkedin_sdui_posts(html, limit)
    posts: list[PostData] = []
    seen: set[str] = set()
    for card in cards:
        urn = card.get("data-activity-urn") or card.get("data-urn") or ""
        if urn and urn in seen:  # logged in, the same post is rendered twice (wrapper + inner update)
            continue
        seen.add(urn)
        body = (card.select_one('[data-test-id="main-feed-activity-card__commentary"]')
                or card.select_one(".update-components-text, .feed-shared-update-v2__description, .feed-shared-text"))
        caption = body.get_text(" ", strip=True) if body else ""
        reactions = card.select_one('[data-test-id="social-actions__reaction-count"], '
                                    '.social-details-social-counts__reactions-count')
        comments = card.select_one('[data-test-id="social-actions__comments"]')
        card_text = card.get_text(" | ", strip=True)
        comment_count = int(comments.get("data-num-comments") or parse_count(comments.get_text())) if comments else 0
        if not comments:
            found = re.search(COUNT + r"\s+comments?", card_text, re.I)
            comment_count = parse_count(found.group(1)) if found else 0
        reposts = re.search(COUNT + r"\s+reposts?", card_text, re.I)
        when = card.select_one("time") or card.select_one(".update-components-actor__sub-description")
        media = "video" if card.select_one('[data-test-id="feed-native-video-content"], video, .update-components-linkedin-video') \
            else "image" if card.select_one('[data-test-id="feed-images-content"], .update-components-image') else "text"
        posts.append(PostData(
            platform="linkedin", post_id=urn.rsplit(":", 1)[-1], caption=caption[:2000],
            url=f"https://www.linkedin.com/feed/update/{urn}/" if urn else "",
            likes=parse_count(reactions.get_text()) if reactions else 0, comments=comment_count,
            shares=parse_count(reposts.group(1)) if reposts else 0,
            timestamp=when.get_text(" ", strip=True).split("•")[0].strip() if when else None,
            hashtags=_hashtags(caption), media_type=media,
        ))
        if len(posts) >= limit:
            break
    return posts


# ----------------------------------------------------------------------------------------------------------- Facebook

FB_DATE = re.compile(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),? [^|]{6,40}? at \d{1,2}:\d{2}")


def parse_facebook_page(html: str, handle: str) -> CompetitorAnalysis:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" | ", strip=True)
    link = soup.select_one('a[href$="/followers/"], a[href*="/followers/?"]')
    followers = re.search(COUNT, link.get_text(" ", strip=True)) if link else None
    followers = followers or re.search(COUNT + r"\s*\|?\s*" + FOLLOWERS, text, re.I)
    likes = re.search(COUNT + r"\s*\|?\s*likes", text, re.I)
    # the sidebar intro is the last 'Intro' heading (in Hindi the About tab uses the same word)
    intros = re.findall(r"\|\s*(?:Intro|परिचय)\s*\|\s*([^|]{3,300})", text)
    intro_text = next((i for i in reversed(intros) if len(i.split()) > 2), "")
    return CompetitorAnalysis(handle=handle, platform="facebook",
                              follower_count=parse_count(followers.group(1)) if followers else
                              (parse_count(likes.group(1)) if likes else 0),
                              bio=intro_text.strip() or _meta(soup, "og:description", "description")[:500])


def parse_facebook_posts(html: str, limit: int = 20) -> list[PostData]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("[aria-posinset]") or [a for a in soup.select('[role="article"]')
                                               if not a.find_parent(attrs={"role": "article"})]
    posts: list[PostData] = []
    for card in cards:
        text = card.get_text(" | ", strip=True)
        message = card.select_one('[data-ad-preview="message"], [data-ad-comet-preview="message"]')
        caption = message.get_text(" ", strip=True) if message else ""
        link = next((a["href"].split("?")[0] for a in card.select("a[href]")
                     if re.search(r"/(posts|videos|reel|photos|permalink)/|story_fbid|pfbid", a["href"])), "")
        reactions = re.search(REACTIONS + r":\s*\|\s*" + COUNT, text)
        # after the reaction count, Facebook shows the comment and share counts (with or without the words)
        tail = text[reactions.end():] if reactions else text
        comments = re.search(COUNT + r"\s*comments?", tail, re.I) or re.match(r"\s*\|\s*" + COUNT + r"\s*\|", tail)
        shares = re.search(COUNT + r"\s*shares?", tail, re.I)
        date = FB_DATE.search(text)
        if not caption and not link:
            continue
        posts.append(PostData(
            platform="facebook", post_id=link.rstrip("/").rsplit("/", 1)[-1] if link else "", url=link,
            caption=caption[:2000], likes=parse_count(reactions.group(1)) if reactions else 0,
            comments=parse_count(comments.group(1)) if comments else 0,
            shares=parse_count(shares.group(1)) if shares else 0,
            timestamp=date.group(0) if date else None, hashtags=_hashtags(caption),
            media_type="video" if card.select_one("video") or "/videos/" in link or "/reel/" in link else "post",
        ))
        if len(posts) >= limit:
            break
    return posts


# ----------------------------------------------------------------------------------------------------------- Reddit

def parse_reddit_listing(html: str, limit: int = 25) -> list[CommunityPost]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[CommunityPost] = []
    for post in soup.select("shreddit-post"):  # www.reddit.com
        body = post.select_one('[slot="text-body"]')
        permalink = post.get("permalink", "")
        posts.append(CommunityPost(
            source="reddit", subreddit=post.get("subreddit-prefixed-name", ""), title=post.get("post-title", ""),
            body=body.get_text(" ", strip=True)[:2000] if body else "", url=f"https://www.reddit.com{permalink}" if permalink else "",
            upvotes=parse_count(post.get("score")), comments=parse_count(post.get("comment-count")),
            author=post.get("author", ""), timestamp=post.get("created-timestamp"),
            score=float(parse_count(post.get("score"))),
        ))
    for thing in soup.select('div.thing[data-fullname^="t3_"]'):  # old.reddit.com
        title = thing.select_one("a.title")
        posts.append(CommunityPost(
            source="reddit", subreddit=thing.get("data-subreddit-prefixed", ""), title=title.get_text(strip=True) if title else "",
            url=f"https://www.reddit.com{thing.get('data-permalink', '')}", upvotes=parse_count(thing.get("data-score")),
            comments=parse_count(thing.get("data-comments-count")), author=thing.get("data-author", ""),
            timestamp=thing.get("data-timestamp"), score=float(parse_count(thing.get("data-score"))),
        ))
    return posts[:limit]


# ----------------------------------------------------------------------------------------------------------- X

def parse_x_timeline(html: str, limit: int = 25) -> list[CommunityPost]:
    """X (Twitter) profile, list or search timeline. X shows nothing when logged out, so this needs a login."""
    soup = BeautifulSoup(html, "html.parser")
    posts: list[CommunityPost] = []
    for tweet in soup.select('article[data-testid="tweet"]'):
        text = tweet.select_one('[data-testid="tweetText"]')
        link = next((a["href"] for a in tweet.select('a[href*="/status/"]') if a.select_one("time")), "")
        when = tweet.select_one("time")

        def action(name: str) -> int:
            button = tweet.select_one(f'[data-testid="{name}"]')
            return parse_count(button.get("aria-label") or button.get_text()) if button else 0

        posts.append(CommunityPost(
            source="x", body=text.get_text(" ", strip=True)[:2000] if text else "",
            url=f"https://x.com{link}" if link.startswith("/") else link,
            upvotes=action("like") or action("unlike"), comments=action("reply"),
            author=link.strip("/").split("/")[0] if link else "",
            timestamp=when.get("datetime") if when else None, score=float(action("retweet") or action("unretweet")),
        ))
        if len(posts) >= limit:
            break
    return posts


# ----------------------------------------------------------------------------------------------------------- Meta Ad Library

AD_CTAS = ("Learn more", "Sign up", "Shop now", "Download", "Book now", "Get offer", "Contact us", "Apply now",
           "Subscribe", "Watch more", "Send message", "Get quote", "Order now", "Install now", "Register now",
           "Send WhatsApp message", "Call now", "See menu", "Play game", "Listen now", "Get started")


def parse_ad_library(html: str, limit: int = 20) -> list[dict]:
    """Public Meta Ad Library search results (facebook.com/ads/library), no login needed. Returns dicts with
    ad_id, page_name, started_running (e.g. '24 Sep 2026'), ad_copy, cta."""
    from datetime import datetime

    text = BeautifulSoup(html, "html.parser").get_text(" | ", strip=True)
    ads: list[dict] = []
    for chunk in text.split("Library ID:")[1:]:
        ad_id = re.match(r"\s*(\d+)", chunk)
        started = re.search(r"Started running on\s*([0-9]{1,2} \w{3,9} \d{4}|\w{3,9} \d{1,2}, \d{4})", chunk)
        sponsored = re.search(r"\|\s*([^|]{1,80}?)\s*\|\s*Sponsored\s*\|(.*)", chunk, re.S)
        page_name, body = (sponsored.group(1).strip(), sponsored.group(2)) if sponsored else ("", "")
        body = re.split(r"\|\s*(?:Active|Inactive)\s*\|", body)[0]
        parts = [p.strip() for p in body.split("|") if p.strip() and not re.fullmatch(r"[\d:/ \u200b]+", p.strip())]
        cta = next((p for p in parts if p in AD_CTAS), "")
        copy = " ".join(p for p in parts if p != cta)
        days = 0
        if started:
            for fmt in ("%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"):
                try:
                    days = (datetime.now() - datetime.strptime(started.group(1), fmt)).days
                    break
                except ValueError:
                    continue
        ads.append({"ad_id": ad_id.group(1) if ad_id else "", "page_name": page_name,
                    "started_running": started.group(1) if started else "", "days_running": days,
                    "ad_copy": copy[:500], "cta": cta, "hook": copy[:200]})
        if len(ads) >= limit:
            break
    return ads
