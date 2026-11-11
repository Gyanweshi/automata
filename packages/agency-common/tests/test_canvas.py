from __future__ import annotations

import json

import pytest

from agency_common.canvas import Canvas, card_height, section_grid, vault_relative
from agency_common.models import (
    AdLibraryReport,
    GenerationPrompt,
    PlatformResearch,
    ResearchOutput,
    Scene,
    StoryboardOutput,
)

NODE_FIELDS = {"text": "text", "file": "file", "link": "url", "group": None}


def assert_valid_canvas(data: dict) -> None:
    """The JSON Canvas 1.0 rules Obsidian relies on."""
    assert set(data) == {"nodes", "edges"}
    ids = [n["id"] for n in data["nodes"]] + [e["id"] for e in data["edges"]]
    assert len(ids) == len(set(ids))
    node_ids = {n["id"] for n in data["nodes"]}
    seen_card = False
    for node in data["nodes"]:
        assert node["type"] in NODE_FIELDS
        for key in ("x", "y", "width", "height"):
            assert isinstance(node[key], int)
        assert node["width"] > 0 and node["height"] > 0
        if NODE_FIELDS[node["type"]]:
            assert isinstance(node[NODE_FIELDS[node["type"]]], str)
        if node["type"] == "group":
            assert not seen_card, "groups must come before cards so they render behind them"
        else:
            seen_card = True
    for edge in data["edges"]:
        assert edge["fromNode"] in node_ids and edge["toNode"] in node_ids


def test_canvas_writes_spec_json_and_refuses_overwrite(tmp_path):
    board = Canvas(seed="t")
    a = board.text("# A", 0, 0)
    g = board.group("Group", -20, -20, 500, 300)
    b = board.file("Brands/x/note.md", 500, 0)
    board.link("https://jsoncanvas.org", 0, 400)
    board.edge(a, b, from_side="right", to_side="left", label="see")
    board.edge(g, b, arrow=False)
    path = board.write(tmp_path / "b.canvas")

    data = json.loads(path.read_text(encoding="utf-8"))
    assert_valid_canvas(data)
    assert data["nodes"][0]["id"] == g
    assert data["edges"][1]["toEnd"] == "none"
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        board.write(path)
    board.write(path, overwrite=True)


def test_canvas_ids_are_deterministic():
    def build():
        board = Canvas(seed="same")
        board.edge(board.text("a", 0, 0), board.text("b", 500, 0))
        return board.to_dict()

    assert build() == build()


def test_canvas_rejects_bad_input(tmp_path):
    board = Canvas()
    with pytest.raises(ValueError):
        board.text("x", 0, 0, width=0)
    a = board.text("a", 0, 0)
    with pytest.raises(ValueError, match="existing nodes"):
        board.edge(a, "missing")
    with pytest.raises(ValueError, match="side"):
        board.edge(a, a, from_side="middle")
    with pytest.raises(ValueError, match=".canvas"):
        board.write(tmp_path / "b.json")


def test_card_height_grows_with_text_and_caps():
    assert card_height("one line") < card_height("\n".join(["line"] * 10))
    assert card_height("x\n" * 500) == 900


def test_section_grid_wraps_rows(tmp_path):
    board = Canvas()
    ids = section_grid(board, [(f"S{i}", ["card"]) for i in range(4)], x=0, y=0, columns=3)
    groups = {n["id"]: n for n in board.to_dict()["nodes"] if n["type"] == "group"}
    assert [groups[i]["y"] for i in ids[:3]] == [0, 0, 0]
    assert groups[ids[3]]["y"] > 0 and groups[ids[3]]["x"] == 0


def test_vault_relative_prefers_obsidian_root_then_brands(tmp_path):
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    note = vault / "Brands" / "maple" / "Drafts" / "Storyboards" / "n.md"
    assert vault_relative(note) == "Brands/maple/Drafts/Storyboards/n.md"

    local = tmp_path / "workspace" / "vault" / "Brands" / "maple" / "n.md"
    assert vault_relative(local) == "Brands/maple/n.md"
    assert vault_relative(tmp_path / "loose.md") == "loose.md"


def test_storyboard_and_research_outputs_write_a_canvas_beside_the_note(tmp_path):
    storyboard_outputs = pytest.importorskip("agency_storyboard.outputs")
    research_outputs = pytest.importorskip("agency_research.outputs")
    from agency_common.workspace import WorkspaceManager

    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    workspace = WorkspaceManager(tmp_path / "workspace")
    drafts = vault / "Brands" / "maple" / "Drafts"

    story = StoryboardOutput(
        brand_slug="maple", run_id="run-1", topic="5 tips", content_type="carousel",
        scenes=[Scene(scene_number=i, description=f"Scene {i}", mood="calm") for i in (1, 2, 3)],
        prompts=[GenerationPrompt(tool="gpt_image", positive_prompt=f"p{i}") for i in (1, 2, 3)],
    )
    _, md = storyboard_outputs.write_storyboard_output(story, workspace, markdown_dir=drafts / "Storyboards")
    data = json.loads(md.with_suffix(".canvas").read_text(encoding="utf-8"))
    assert_valid_canvas(data)
    files = [n["file"] for n in data["nodes"] if n["type"] == "file"]
    assert files == ["Brands/maple/Drafts/Storyboards/run-1-storyboard.md"]
    assert sum(n["type"] == "group" for n in data["nodes"]) == 3
    assert len(data["edges"]) == 2  # scene 1 -> 2 -> 3

    research = ResearchOutput(
        brand_slug="maple", run_id="run-2", summary="s",
        platforms={"instagram": PlatformResearch(platform="instagram")},
        ad_library=AdLibraryReport(winning_angles=["trade-in"], top_ctas=["Shop"]),
    )
    _, md = research_outputs.write_research_output(research, workspace, markdown_dir=drafts / "Research")
    data = json.loads(md.with_suffix(".canvas").read_text(encoding="utf-8"))
    assert_valid_canvas(data)
    assert [n["label"] for n in data["nodes"] if n["type"] == "group"] == ["Ad library"]

    _, md = research_outputs.write_research_output(
        research.model_copy(update={"run_id": "run-3"}), workspace, markdown_dir=drafts / "Research", canvas=False)
    assert not md.with_suffix(".canvas").exists()
