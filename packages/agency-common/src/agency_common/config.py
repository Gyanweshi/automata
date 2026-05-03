"""Environment-based configuration for agency agents."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgencyConfig:
    """All configuration sourced from environment variables with sensible defaults.

    Environment variables:
        AGENCY_WORKSPACE      — path to shared workspace directory
        AGENCY_BRANDS_DIR     — path to brands YAML directory
        APIFY_API_TOKEN       — Apify token for LinkedIn/Facebook scraping
        FB_PAGE_ACCESS_TOKEN  — Facebook Graph API token (owned pages)
        INSTALOADER_USERNAME  — optional Instagram login username
        INSTALOADER_PASSWORD  — optional Instagram login password
        FREEPIK_API_KEY       — Freepik API key (image/video generation)
    """

    workspace: Path = field(default_factory=lambda: Path(
        os.environ.get("AGENCY_WORKSPACE", "./workspace")
    ))
    brands_dir: Path = field(default_factory=lambda: Path(
        os.environ.get("AGENCY_BRANDS_DIR", "./brands")
    ))
    apify_token: str = field(default_factory=lambda: os.environ.get("APIFY_API_TOKEN", ""))
    fb_page_access_token: str = field(default_factory=lambda: os.environ.get("FB_PAGE_ACCESS_TOKEN", ""))
    instaloader_username: str = field(default_factory=lambda: os.environ.get("INSTALOADER_USERNAME", ""))
    instaloader_password: str = field(default_factory=lambda: os.environ.get("INSTALOADER_PASSWORD", ""))
    freepik_api_key: str = field(default_factory=lambda: os.environ.get("FREEPIK_API_KEY", ""))

    def validate(self, required: list[str] | None = None) -> list[str]:
        """Return a list of missing required config keys. Empty list = all good."""
        checks = {
            "apify_token": self.apify_token,
            "fb_page_access_token": self.fb_page_access_token,
            "instaloader_username": self.instaloader_username,
            "freepik_api_key": self.freepik_api_key,
        }
        if required is None:
            return []
        return [k for k in required if not checks.get(k)]

    @classmethod
    def from_env(cls) -> "AgencyConfig":
        return cls()
