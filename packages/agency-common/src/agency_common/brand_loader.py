"""Load and validate brand profiles from YAML files."""
from __future__ import annotations

import os
import re
from pathlib import Path

import frontmatter
import yaml
from dotenv import find_dotenv, load_dotenv

from .models import BrandProfile


def _parse_memory_section(body: str) -> list[str]:
    """Extract bullet points from the ## Memory section of a brand note body."""
    match = re.search(r'^## Memory\s*\n(.*?)(?=\n## |\Z)', body, re.DOTALL | re.MULTILINE)
    if not match:
        return []
    return [
        line.lstrip("- ").strip()
        for line in match.group(1).splitlines()
        if line.strip().startswith("-")
    ]

_VAULT_BRANDS_SUBDIR = "Brands"


def _vault_brands_dir() -> Path | None:
    """Return the Brands/ folder inside the Obsidian vault, if configured and present."""
    load_dotenv(find_dotenv(usecwd=True))
    vault_raw = os.environ.get("OBSIDIAN_VAULT_PATH")
    if not vault_raw:
        return None
    vault_brands = Path(vault_raw).expanduser().resolve() / _VAULT_BRANDS_SUBDIR
    return vault_brands if vault_brands.is_dir() else None


def _candidate_dirs(brands_dir: str | Path | None) -> list[Path]:
    """Return ordered list of directories to search for brand YAMLs.

    Priority:
      1. Explicit brands_dir argument or AGENCY_BRANDS_DIR env var
      2. Obsidian vault Brands/ folder
      3. Local brands/ directory (repo fallback)
    """
    candidates: list[Path] = []

    if brands_dir:
        candidates.append(Path(brands_dir))
    else:
        env_dir = os.environ.get("AGENCY_BRANDS_DIR")
        if env_dir:
            candidates.append(Path(env_dir))

    vault_dir = _vault_brands_dir()
    if vault_dir:
        candidates.append(vault_dir)

    cwd = Path.cwd()
    for local in [cwd / "brands", cwd.parent / "brands"]:
        if local.is_dir():
            candidates.append(local)
            break

    return candidates


def load_brand(slug: str, brands_dir: str | Path | None = None) -> BrandProfile:
    """Load a brand profile YAML by slug.

    Searches (in order): explicit brands_dir → AGENCY_BRANDS_DIR env var →
    Obsidian vault Brands/ → local brands/ directory.

    Raises FileNotFoundError if not found in any location.
    """
    for dir_path in _candidate_dirs(brands_dir):
        for ext in (".md", ".yaml"):
            brand_path = dir_path / f"{slug}{ext}"
            if not brand_path.exists():
                continue
            with open(brand_path, "r") as f:
                raw = f.read()
            if ext == ".md":
                post = frontmatter.loads(raw)
                data = dict(post.metadata)
                memory = _parse_memory_section(post.content)
                if memory:
                    data["memory"] = memory
            else:
                data = yaml.safe_load(raw)
            if not isinstance(data, dict):
                raise ValueError(f"Brand profile at {brand_path} is empty or malformed.")
            if not data.get("slug"):
                data["slug"] = slug
            return BrandProfile.model_validate(data)

    raise FileNotFoundError(
        f"Brand profile '{slug}.yaml' not found.\n"
        f"Available brands: {list_brands(brands_dir)}"
    )


def list_brands(brands_dir: str | Path | None = None) -> list[str]:
    """Return deduplicated list of brand slugs found across all search locations."""
    seen: set[str] = set()
    slugs: list[str] = []
    for dir_path in _candidate_dirs(brands_dir):
        if not dir_path.is_dir():
            continue
        for p in sorted(dir_path.glob("*.md")) + sorted(dir_path.glob("*.yaml")):
            if not p.stem.startswith("_") and p.stem not in seen:
                seen.add(p.stem)
                slugs.append(p.stem)
    return slugs
