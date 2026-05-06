"""Tests for brand_loader — including memory section parsing."""
from pathlib import Path

import pytest

from agency_common.brand_loader import _parse_memory_section, load_brand


# ---------------------------------------------------------------------------
# _parse_memory_section
# ---------------------------------------------------------------------------

def test_parse_memory_section_returns_empty_when_no_section():
    body = "# Brand\n\nSome body text with no memory section."
    assert _parse_memory_section(body) == []


def test_parse_memory_section_extracts_bullets():
    body = (
        "# Brand\n\n"
        "## Memory\n\n"
        "- 2026-05-06: carousel brief for topic A.\n"
        "- 2026-05-06: research — @cashify leads.\n"
    )
    result = _parse_memory_section(body)
    assert result == [
        "2026-05-06: carousel brief for topic A.",
        "2026-05-06: research — @cashify leads.",
    ]


def test_parse_memory_section_ignores_html_comments():
    body = (
        "## Memory\n\n"
        "<!-- this is a comment -->\n\n"
        "- 2026-05-06: real insight.\n"
    )
    result = _parse_memory_section(body)
    assert result == ["2026-05-06: real insight."]


def test_parse_memory_section_stops_at_next_heading():
    body = (
        "## Memory\n\n"
        "- 2026-05-06: memory bullet.\n\n"
        "## Competitors\n\n"
        "- @someone\n"
    )
    result = _parse_memory_section(body)
    assert result == ["2026-05-06: memory bullet."]
    assert "@someone" not in result


def test_parse_memory_section_empty_section_returns_empty():
    body = "## Memory\n\n<!-- placeholder -->\n\n## Competitors\n"
    assert _parse_memory_section(body) == []


# ---------------------------------------------------------------------------
# load_brand — memory integration
# ---------------------------------------------------------------------------

def test_load_brand_from_md_includes_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    brands_dir = tmp_path / "Brands"
    brands_dir.mkdir()
    (brands_dir / "maple.md").write_text(
        "---\n"
        "slug: maple\n"
        "name: Maple\n"
        "---\n\n"
        "# Maple\n\n"
        "## Memory\n\n"
        "- 2026-05-06: instagram/carousel brief for '5 tips'.\n"
        "- 2026-05-06: research — @cashify leads at 3.2% engagement.\n",
        encoding="utf-8",
    )

    brand = load_brand("maple")

    assert brand.slug == "maple"
    assert len(brand.memory) == 2
    assert "carousel" in brand.memory[0]
    assert "cashify" in brand.memory[1]


def test_load_brand_from_md_with_no_memory_section(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    brands_dir = tmp_path / "Brands"
    brands_dir.mkdir()
    (brands_dir / "maple.md").write_text(
        "---\nslug: maple\nname: Maple\n---\n\n# Maple\n\nJust the body.\n",
        encoding="utf-8",
    )

    brand = load_brand("maple")

    assert brand.memory == []


def test_load_brand_raises_when_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    (tmp_path / "Brands").mkdir()

    with pytest.raises(FileNotFoundError, match="nonexistent"):
        load_brand("nonexistent")
