from __future__ import annotations

import json
from datetime import date

import frontmatter
import pytest

from agency_common.note_cli import NoteError, canvas_for, main, save_note
from agency_common.output_writer import OutputWriter, existing_brand_folder

BODY = """---
tags: [instagram]
status: final
brand: wrong
---
# BBD stress test

Intro line.

## Findings
- one
- two

## Next step
Ship it.
"""


@pytest.fixture
def vault(tmp_path):
    root = tmp_path / "vault"
    (root / ".obsidian").mkdir(parents=True)
    (root / "Brands" / "Maple").mkdir(parents=True)
    (root / "Brands" / "Rasoi Raga").mkdir(parents=True)
    (root / "Brands" / "Rasoi-Raga" / "Drafts").mkdir(parents=True)
    return root


def test_existing_brand_folder_matches_display_names(vault):
    assert existing_brand_folder(vault, "maple") == vault / "Brands" / "Maple"
    assert existing_brand_folder(vault, "rasoi-raga") == vault / "Brands" / "Rasoi-Raga"
    assert existing_brand_folder(vault, "new-brand") is None
    assert OutputWriter.vault_markdown_directory("maple", "Research", vault_path=vault) == \
        vault / "Brands" / "Maple" / "Drafts" / "Research"


def test_save_note_writes_a_tagged_draft_and_a_board(vault):
    note, board = save_note(BODY, title="BBD stress test", artifact_type="Research", brand="maple",
                            tags=["bbd"], vault=vault, today=date(2026, 11, 11))

    assert note == vault / "Brands" / "Maple" / "Drafts" / "Research" / "2026-11-11-bbd-stress-test.md"
    post = frontmatter.load(note)
    assert post["brand"] == "maple" and post["status"] == "draft" and post["type"] == "research"
    assert post["tags"] == ["instagram", "research", "maple", "bbd"]
    assert post.content.startswith("# BBD stress test")

    data = json.loads(board.read_text(encoding="utf-8"))
    assert [n["label"] for n in data["nodes"] if n["type"] == "group"] == ["Findings", "Next step"]
    assert [n["file"] for n in data["nodes"] if n["type"] == "file"] == [
        "Brands/Maple/Drafts/Research/2026-11-11-bbd-stress-test.md"]

    with pytest.raises(NoteError, match="already exists"):
        save_note(BODY, title="BBD stress test", artifact_type="Research", brand="maple", vault=vault,
                  today=date(2026, 11, 11))


def test_topic_notes_go_to_research_and_need_exactly_one_target(vault):
    note, board = save_note("plain body", title="Hooks", artifact_type="Research", topic="Micro_Dramas",
                            canvas=False, vault=vault, today=date(2026, 11, 11))
    assert note == vault / "Research" / "Micro_Dramas" / "2026-11-11-hooks.md"
    assert board is None
    assert "brand" not in frontmatter.load(note).metadata
    with pytest.raises(NoteError, match="exactly one"):
        save_note("x", title="t", artifact_type="Research", vault=vault)
    with pytest.raises(NoteError, match="single folder"):
        save_note("x", title="t", artifact_type="Research", topic="../escape", vault=vault)


def test_canvas_for_an_existing_note_and_cli(vault, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault))
    body = tmp_path / "draft.md"
    body.write_text(BODY, encoding="utf-8")
    assert main(["save", "--brand", "maple", "--title", "CLI note", "--body", str(body), "--no-canvas"]) == 0
    note = next((vault / "Brands" / "Maple" / "Drafts" / "Research").glob("*-cli-note.md"))
    assert not note.with_suffix(".canvas").exists()

    board = canvas_for(note.relative_to(vault))
    assert board == note.with_suffix(".canvas")
    with pytest.raises(FileExistsError):
        canvas_for(note)
    canvas_for(note, overwrite=True)
    with pytest.raises(SystemExit):  # argparse requires --brand or --topic
        main(["save", "--title", "x", "--body", str(body)])


@pytest.mark.parametrize("tags", ["hooks", "hooks, reels", "hooks reels", "[hooks, reels]"])
def test_string_tags_are_kept_whole_not_split_into_letters(vault, tags):
    note, _ = save_note(f"---\ntags: {tags}\n---\nbody", title="Tags", artifact_type="Research", topic="X",
                        vault=vault, canvas=False)
    saved = frontmatter.loads(note.read_text(encoding="utf-8")).metadata["tags"]
    assert saved[0] == "hooks" and "h" not in saved
    assert "research" in saved


@pytest.mark.parametrize("folder, kind", [("Research", "research"), ("Storyboards", "storyboard"),
                                          ("Analysis", "analysis"), ("Ideation", "ideation"),
                                          ("Scripts", "script"), ("Process", "process")])
def test_note_kind_singularises_only_plural_folders(folder, kind):
    from agency_common.note_cli import note_kind
    assert note_kind(folder) == kind
