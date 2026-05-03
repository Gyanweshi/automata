"""Load and validate brand profiles from YAML files."""
from __future__ import annotations

from pathlib import Path

import yaml

from .models import BrandProfile


def _resolve_brands_dir(brands_dir: str | Path | None) -> Path:
    if brands_dir:
        return Path(brands_dir)
    import os
    env_dir = os.environ.get("AGENCY_BRANDS_DIR")
    if env_dir:
        return Path(env_dir)
    # Walk up from CWD looking for a brands/ directory
    cwd = Path.cwd()
    for candidate in [cwd / "brands", cwd.parent / "brands"]:
        if candidate.is_dir():
            return candidate
    return cwd / "brands"


def load_brand(slug: str, brands_dir: str | Path | None = None) -> BrandProfile:
    """Load a brand profile YAML by slug. Raises FileNotFoundError if not found."""
    dir_path = _resolve_brands_dir(brands_dir)
    yaml_path = dir_path / f"{slug}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(
            f"Brand profile not found: {yaml_path}\n"
            f"Available brands: {list_brands(brands_dir)}"
        )
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    if not data.get("slug"):
        data["slug"] = slug
    return BrandProfile.model_validate(data)


def list_brands(brands_dir: str | Path | None = None) -> list[str]:
    """Return list of brand slugs available in the brands directory."""
    dir_path = _resolve_brands_dir(brands_dir)
    if not dir_path.is_dir():
        return []
    return [
        p.stem for p in sorted(dir_path.glob("*.yaml"))
        if not p.stem.startswith("_")
    ]
