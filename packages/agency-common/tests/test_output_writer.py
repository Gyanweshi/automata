from __future__ import annotations

from datetime import datetime

import frontmatter
import pytest

from agency_common.output_writer import OutputWriter


def test_vault_markdown_directory_separates_drafts_and_final_notes(tmp_path):
    draft = OutputWriter.vault_markdown_directory(
        "maple", "Research", status="draft", vault_path=tmp_path
    )
    final = OutputWriter.vault_markdown_directory(
        "maple", "Research", status="final", vault_path=tmp_path
    )

    assert draft == tmp_path / "Brands" / "maple" / "Drafts" / "Research"
    assert final == tmp_path / "Brands" / "maple" / "Research"


@pytest.mark.parametrize("component", ["../escape", "nested/path", "nested\\path", ""])
def test_vault_markdown_directory_rejects_unsafe_components(tmp_path, component):
    with pytest.raises(ValueError, match="Unsafe"):
        OutputWriter.vault_markdown_directory(
            component, "Research", status="draft", vault_path=tmp_path
        )


def test_standard_frontmatter_marks_status_and_creation_date(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def utcnow(cls):
            return cls(2026, 9, 4)

    monkeypatch.setattr("agency_common.output_writer.datetime", FixedDateTime)

    metadata = OutputWriter.standard_frontmatter(
        "research", "maple", "run-1", status="final"
    )

    assert metadata["status"] == "final"
    assert metadata["created"] == "2026-09-04"


def test_write_markdown_refuses_to_overwrite_by_default(tmp_path):
    note = tmp_path / "note.md"
    OutputWriter.write_markdown("first", note, {"status": "draft"})

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        OutputWriter.write_markdown("second", note, {"status": "draft"})

    assert frontmatter.load(note).content == "first"


def test_write_markdown_can_overwrite_explicitly(tmp_path):
    note = tmp_path / "note.md"
    OutputWriter.write_markdown("first", note)
    OutputWriter.write_markdown("second", note, overwrite=True)

    assert note.read_text(encoding="utf-8") == "second"
