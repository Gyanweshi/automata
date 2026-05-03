from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import instaloader
from fastmcp import FastMCP


REPO_ROOT = Path(__file__).resolve().parents[2]
DOWNLOAD_ROOT = REPO_ROOT / "workspace" / "instagram"

mcp = FastMCP("instaloader-mcp")


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _loader(download: bool = False) -> instaloader.Instaloader:
    loader = instaloader.Instaloader(
        dirname_pattern=str(DOWNLOAD_ROOT / "{profile}"),
        download_pictures=download,
        download_videos=download,
        download_video_thumbnails=download,
        download_geotags=False,
        download_comments=False,
        save_metadata=download,
        compress_json=False,
        quiet=True,
    )

    session_username = os.getenv("INSTALOADER_SESSION_USERNAME") or os.getenv("INSTALOADER_USERNAME")
    session_file = os.getenv("INSTALOADER_SESSION_FILE")
    if session_username:
        try:
            loader.load_session_from_file(session_username, session_file)
        except FileNotFoundError:
            password = os.getenv("INSTALOADER_PASSWORD")
            if password:
                loader.login(session_username, password)
                loader.save_session_to_file(session_file)
            else:
                raise

    return loader


def _profile_summary(profile: instaloader.Profile) -> dict[str, Any]:
    return {
        "username": profile.username,
        "user_id": profile.userid,
        "full_name": profile.full_name,
        "biography": profile.biography,
        "external_url": profile.external_url,
        "is_private": profile.is_private,
        "is_verified": profile.is_verified,
        "followers": profile.followers,
        "followees": profile.followees,
        "media_count": profile.mediacount,
        "profile_pic_url": profile.profile_pic_url,
    }


def _post_summary(post: instaloader.Post) -> dict[str, Any]:
    return {
        "shortcode": post.shortcode,
        "url": f"https://www.instagram.com/p/{post.shortcode}/",
        "owner_username": post.owner_username,
        "date_utc": _iso(post.date_utc),
        "typename": post.typename,
        "caption": post.caption,
        "caption_hashtags": list(post.caption_hashtags),
        "caption_mentions": list(post.caption_mentions),
        "likes": post.likes,
        "comments": post.comments,
        "is_video": post.is_video,
        "video_view_count": post.video_view_count if post.is_video else None,
        "video_duration": post.video_duration if post.is_video else None,
        "accessibility_caption": post.accessibility_caption,
    }


def _clamped_limit(value: int, maximum: int = 24) -> int:
    return max(1, min(value, maximum))


@mcp.tool
def get_profile(username: str) -> dict[str, Any]:
    """Return public Instagram profile metadata for a username."""
    try:
        profile = instaloader.Profile.from_username(_loader().context, username.strip().lstrip("@"))
        return _profile_summary(profile)
    except Exception as exc:
        return {"username": username.strip().lstrip("@"), "error": type(exc).__name__, "message": str(exc)}


@mcp.tool
def get_recent_posts(username: str, limit: int = 12) -> dict[str, Any]:
    """Return recent post metadata for a public profile."""
    try:
        loader = _loader()
        profile = instaloader.Profile.from_username(loader.context, username.strip().lstrip("@"))
        posts = []
        for index, post in enumerate(profile.get_posts()):
            if index >= _clamped_limit(limit):
                break
            posts.append(_post_summary(post))

        return {"profile": _profile_summary(profile), "posts": posts}
    except Exception as exc:
        return {"username": username.strip().lstrip("@"), "error": type(exc).__name__, "message": str(exc)}


@mcp.tool
def get_post(shortcode: str) -> dict[str, Any]:
    """Return metadata for a single Instagram post shortcode."""
    try:
        clean_shortcode = shortcode.rstrip("/").split("/")[-1]
        post = instaloader.Post.from_shortcode(_loader().context, clean_shortcode)
        return _post_summary(post)
    except Exception as exc:
        return {"shortcode": shortcode, "error": type(exc).__name__, "message": str(exc)}


@mcp.tool
def download_recent_posts(username: str, limit: int = 3) -> dict[str, Any]:
    """Download recent posts into workspace/instagram and return saved shortcodes."""
    try:
        loader = _loader(download=True)
        profile = instaloader.Profile.from_username(loader.context, username.strip().lstrip("@"))
        saved_shortcodes = []

        for index, post in enumerate(profile.get_posts()):
            if index >= _clamped_limit(limit, maximum=10):
                break
            loader.download_post(post, target=profile.username)
            saved_shortcodes.append(post.shortcode)

        return {
            "profile": profile.username,
            "download_dir": str(DOWNLOAD_ROOT / profile.username),
            "saved_shortcodes": saved_shortcodes,
        }
    except Exception as exc:
        return {"username": username.strip().lstrip("@"), "error": type(exc).__name__, "message": str(exc)}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
