from pathlib import Path

import pytest

from agency_common.knowledge_reader import (
    VaultPathError,
    get_vault_path,
    iter_markdown_files,
    parse_markdown_file,
    read_obsidian_vault,
)


def test_get_vault_path_requires_env(monkeypatch, tmp_path):
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(VaultPathError, match="OBSIDIAN_VAULT_PATH is not set"):
        get_vault_path()


def test_get_vault_path_requires_existing_directory(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing"
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(missing_path))

    with pytest.raises(VaultPathError, match="does not exist"):
        get_vault_path()


def test_get_vault_path_returns_absolute_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))

    assert get_vault_path() == tmp_path.resolve()


def test_get_vault_path_loads_env_file(monkeypatch, tmp_path):
    vault_path = tmp_path / "Vault"
    vault_path.mkdir()
    (tmp_path / ".env").write_text(f"OBSIDIAN_VAULT_PATH={vault_path}\n", encoding="utf-8")
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    assert get_vault_path() == vault_path.resolve()


def test_iter_markdown_files_ignores_obsidian_git_and_non_markdown(tmp_path):
    (tmp_path / "Concept.md").write_text("# Concept", encoding="utf-8")
    (tmp_path / "image.png").write_text("not an image for this test", encoding="utf-8")
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "config.md").write_text("# Config", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "ignored.md").write_text("# Git", encoding="utf-8")
    nested = tmp_path / "Nested"
    nested.mkdir()
    (nested / "Note.MD").write_text("# Nested", encoding="utf-8")

    files = iter_markdown_files(tmp_path)

    assert [path.relative_to(tmp_path) for path in files] == [
        Path("Concept.md"),
        Path("Nested/Note.MD"),
    ]


def test_parse_markdown_file_separates_frontmatter(tmp_path):
    note = tmp_path / "Concept.md"
    note.write_text(
        "---\ntags:\n  - ai\nstatus: draft\n---\n# Concept\nBody text\n",
        encoding="utf-8",
    )

    parsed = parse_markdown_file(note)

    assert parsed["filename"] == "Concept.md"
    assert parsed["filepath"] == str(note.resolve())
    assert parsed["metadata"] == {"tags": ["ai"], "status": "draft"}
    assert parsed["content"] == "# Concept\nBody text"


def test_read_obsidian_vault_skips_malformed_files_when_not_strict(tmp_path):
    (tmp_path / "Good.md").write_text("# Good", encoding="utf-8")
    (tmp_path / "Bad.md").write_text("---\n:\n---\n# Bad", encoding="utf-8")

    notes = read_obsidian_vault(tmp_path)

    assert [note["filename"] for note in notes] == ["Good.md"]


def test_read_obsidian_vault_raises_on_malformed_files_when_strict(tmp_path):
    (tmp_path / "Bad.md").write_text("---\n:\n---\n# Bad", encoding="utf-8")

    with pytest.raises(Exception, match="Could not parse frontmatter"):
        read_obsidian_vault(tmp_path, strict=True)
