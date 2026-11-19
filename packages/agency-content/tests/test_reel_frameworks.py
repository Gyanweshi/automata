import pytest
from agency_common.models import BrandProfile

from agency_content.agent import ContentAgent
from agency_content.cli import build_parser
from agency_content.writers.instagram import InstagramWriter


@pytest.fixture
def brand():
    return BrandProfile(slug="brand-a", name="Brand A")


def test_default_reel_uses_timeline(brand):
    piece = InstagramWriter(brand).reel_script_brief("sleep")
    assert "| Time | Visual |" in piece.body
    assert "retention" not in piece.body


def test_retention_framework_has_all_sections(brand):
    body = InstagramWriter(brand).reel_script_brief("sleep", framework="retention").body
    for section in ("Hook", "Lock-in zone", "Body block 1", "Rehook 1", "Body block 2", "CTA"):
        assert section in body
    assert "Four S's" in body


def test_unknown_framework_rejected(brand):
    with pytest.raises(ValueError):
        InstagramWriter(brand).reel_script_brief("sleep", framework="nope")


def test_agent_passes_framework_only_to_reels(brand):
    agent = ContentAgent.__new__(ContentAgent)
    reel = agent.generate(brand, "instagram", "reel", "sleep", variations=1, script_framework="retention")
    assert "Lock-in zone" in reel.pieces[0].body
    caption = agent.generate(brand, "instagram", "caption", "sleep", variations=1, script_framework="retention")
    assert "Caption Brief" in caption.pieces[0].body


def test_cli_flag():
    args = build_parser().parse_args(["--brand", "x", "--type", "reel", "--script-framework", "retention"])
    assert args.script_framework == "retention"
