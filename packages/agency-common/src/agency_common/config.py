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
        OBSIDIAN_VAULT_PATH   — path to Obsidian vault root
        ANTHROPIC_API_KEY     — Anthropic / Claude API key
        PERPLEXITY_API_KEY    — Perplexity MCP server key
        FIRECRAWL_API_KEY     — Firecrawl MCP server key
        APIFY_API_TOKEN       — Apify token for scraping
        FB_PAGE_ACCESS_TOKEN  — Facebook Graph API token (owned pages)
        FREEPIK_API_KEY       — Freepik API key (image/video generation)
        CAPSULEHUB_API_KEY    — CapsuleHub / Tilantra API key
        META_AD_LIBRARY_TOKEN — Facebook/Meta access token for Ad Library API
    """

    workspace: Path = field(default_factory=lambda: Path(
        os.environ.get("AGENCY_WORKSPACE", "./workspace")
    ))
    brands_dir: Path = field(default_factory=lambda: Path(
        os.environ.get("AGENCY_BRANDS_DIR", "./brands")
    ))
    obsidian_vault_path: Path | None = field(default_factory=lambda: (
        Path(v).expanduser().resolve() if (v := os.environ.get("OBSIDIAN_VAULT_PATH")) else None
    ))
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    perplexity_api_key: str = field(default_factory=lambda: os.environ.get("PERPLEXITY_API_KEY", ""))
    firecrawl_api_key: str = field(default_factory=lambda: os.environ.get("FIRECRAWL_API_KEY", ""))
    apify_token: str = field(default_factory=lambda: os.environ.get("APIFY_API_TOKEN", ""))
    fb_page_access_token: str = field(default_factory=lambda: os.environ.get("FB_PAGE_ACCESS_TOKEN", ""))
    freepik_api_key: str = field(default_factory=lambda: os.environ.get("FREEPIK_API_KEY", ""))
    capsulehub_api_key: str = field(default_factory=lambda: os.environ.get("CAPSULEHUB_API_KEY", ""))
    meta_ad_library_token: str = field(default_factory=lambda: os.environ.get("META_AD_LIBRARY_TOKEN", ""))

    def validate(self, required: list[str] | None = None) -> list[str]:
        """Return a list of missing required config keys. Empty list = all good."""
        checks = {
            "anthropic_api_key": self.anthropic_api_key,
            "apify_token": self.apify_token,
            "fb_page_access_token": self.fb_page_access_token,
            "freepik_api_key": self.freepik_api_key,
            "perplexity_api_key": self.perplexity_api_key,
            "firecrawl_api_key": self.firecrawl_api_key,
            "capsulehub_api_key": self.capsulehub_api_key,
        }
        if required is None:
            return []
        return [k for k in required if not checks.get(k)]

    @classmethod
    def from_env(cls) -> "AgencyConfig":
        """Load config from environment, auto-loading .env if present."""
        _load_dotenv()
        return cls()


def _load_dotenv():
    """Load .env from cwd or repo root if present. Skips if already loaded."""
    try:
        from dotenv import load_dotenv
        # Try cwd first, then walk up to find .env
        for candidate in [Path.cwd() / ".env", Path(__file__).parents[4] / ".env"]:
            if candidate.exists():
                load_dotenv(candidate, override=False)
                return
    except ImportError:
        pass  # python-dotenv not installed; rely on shell env
