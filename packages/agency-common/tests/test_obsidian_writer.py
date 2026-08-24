from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import frontmatter
import pytest

from agency_common import obsidian_writer
from agency_common.obsidian_writer import (
    append_related_concepts,
    build_session_markdown,
    format_related_concepts_section,
    get_sessions_dir,
    log_agent_session,
    log_agent_session_with_related_notes,
    update_brand_memory,
)
from agency_common.vault_write_gate import VaultWriteBlockedError


def test_get_sessions_dir_creates_agent_sessions_directory(tmp_path):
    sessions_dir = get_sessions_dir(vault_path=tmp_path, create=True)

    assert sessions_dir == tmp_path / "Agent_Sessions"
    assert sessions_dir.is_dir()


def test_build_session_markdown_writes_valid_frontmatter():
    timestamp = datetime(2026, 5, 3, 14, 30, 0)

    markdown = build_session_markdown(
        agent_name="Research Agent",
        task_summary="Summarize market notes",
        transcript="User: Start\nAgent: Done",
        tags=["research", "market"],
        timestamp=timestamp,
    )
    parsed = frontmatter.loads(markdown)

    assert parsed.metadata == {
        "date": "2026-05-03T14:30:00",
        "agent": "Research Agent",
        "task_summary": "Summarize market notes",
        "tags": ["research", "market"],
    }
    assert parsed.content.startswith("# Agent Session: Research Agent")
    assert "## Transcript\nUser: Start\nAgent: Done" in parsed.content


def test_build_session_markdown_defaults_to_agent_log_tag():
    markdown = build_session_markdown(
        agent_name="Agent",
        task_summary="Task",
        transcript="Transcript",
        tags=None,
        timestamp=datetime(2026, 5, 3, 14, 30, 0),
    )

    parsed = frontmatter.loads(markdown)

    assert parsed.metadata["tags"] == ["agent-log"]


def test_build_session_markdown_preserves_explicit_empty_tags():
    markdown = build_session_markdown(
        agent_name="Agent",
        task_summary="Task",
        transcript="Transcript",
        tags=[],
        timestamp=datetime(2026, 5, 3, 14, 30, 0),
    )

    parsed = frontmatter.loads(markdown)

    assert parsed.metadata["tags"] == []


def test_log_agent_session_writes_utf8_markdown(monkeypatch, tmp_path):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 5, 3, 14, 30, 0)

    monkeypatch.setattr(obsidian_writer, "datetime", FixedDateTime)
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))

    output_path = log_agent_session(
        "Content Agent",
        "Draft a caption",
        "Agent: Café launch caption ready.",
        tags=["content"],
        commit_vault=True,
        commit_reason="approved test output",
    )

    assert output_path == tmp_path / "Agent_Sessions" / "Session_2026-05-03_14-30-00.md"
    parsed = frontmatter.loads(output_path.read_text(encoding="utf-8"))
    assert parsed.metadata["agent"] == "Content Agent"
    assert "Café launch caption ready." in parsed.content


def test_log_agent_session_uses_suffix_when_filename_exists(monkeypatch, tmp_path):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 5, 3, 14, 30, 0)

    sessions_dir = tmp_path / "Agent_Sessions"
    sessions_dir.mkdir()
    (sessions_dir / "Session_2026-05-03_14-30-00.md").write_text("existing", encoding="utf-8")
    monkeypatch.setattr(obsidian_writer, "datetime", FixedDateTime)
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))

    output_path = log_agent_session(
        "Agent", "Task", "Transcript", commit_vault=True, commit_reason="approved test output"
    )

    assert output_path == sessions_dir / "Session_2026-05-03_14-30-00_02.md"


def test_format_related_concepts_section_renders_wikilinks():
    assert format_related_concepts_section(["[[Agent Repo]]", "[[Second Brain]]"]) == (
        "### Related Concepts\n- [[Agent Repo]]\n- [[Second Brain]]"
    )


def test_append_related_concepts_leaves_transcript_unchanged_without_links():
    assert append_related_concepts("Transcript", []) == "Transcript"


def test_append_related_concepts_adds_section():
    assert append_related_concepts("Transcript\n", ["[[Architecture]]"]) == (
        "Transcript\n\n### Related Concepts\n- [[Architecture]]"
    )


def test_update_brand_memory_creates_section_when_absent(tmp_path):
    brands_dir = tmp_path / "Brands"
    brands_dir.mkdir()
    brand_md = brands_dir / "maple.md"
    brand_md.write_text("# Maple\n\nSome body text.", encoding="utf-8")

    result = update_brand_memory(
        "maple", "carousel brief for topic A.", vault_path=tmp_path,
        commit_vault=True, commit_reason="approved test output",
    )

    assert result is True
    content = brand_md.read_text(encoding="utf-8")
    assert "## Memory" in content
    assert "carousel brief for topic A." in content


def test_update_brand_memory_appends_to_existing_section(tmp_path):
    brands_dir = tmp_path / "Brands"
    brands_dir.mkdir()
    brand_md = brands_dir / "maple.md"
    brand_md.write_text(
        "# Maple\n\n## Memory\n\n- 2026-05-01: first insight.\n",
        encoding="utf-8",
    )

    update_brand_memory(
        "maple", "second insight.", vault_path=tmp_path,
        commit_vault=True, commit_reason="approved test output",
    )

    content = brand_md.read_text(encoding="utf-8")
    assert "first insight." in content
    assert "second insight." in content


def test_update_brand_memory_trims_to_ten_bullets(tmp_path):
    brands_dir = tmp_path / "Brands"
    brands_dir.mkdir()
    brand_md = brands_dir / "maple.md"
    existing_bullets = "\n".join(f"- 2026-05-01: insight {i}." for i in range(10))
    brand_md.write_text(f"# Maple\n\n## Memory\n\n{existing_bullets}\n", encoding="utf-8")

    update_brand_memory(
        "maple", "newest insight.", vault_path=tmp_path,
        commit_vault=True, commit_reason="approved test output",
    )

    content = brand_md.read_text(encoding="utf-8")
    bullets = [line for line in content.splitlines() if line.strip().startswith("-")]
    assert len(bullets) == 10
    assert "newest insight." in content
    assert "insight 0." not in content  # oldest was dropped


def test_update_brand_memory_returns_false_when_brand_note_missing(tmp_path):
    result = update_brand_memory(
        "nonexistent-brand", "some insight.", vault_path=tmp_path,
        commit_vault=True, commit_reason="approved test output",
    )
    assert result is False


def test_update_brand_memory_ignores_html_comments_in_memory_section(tmp_path):
    brands_dir = tmp_path / "Brands"
    brands_dir.mkdir()
    brand_md = brands_dir / "maple.md"
    brand_md.write_text(
        "# Maple\n\n## Memory\n\n<!-- a comment -->\n\n",
        encoding="utf-8",
    )

    update_brand_memory(
        "maple", "real insight.", vault_path=tmp_path,
        commit_vault=True, commit_reason="approved test output",
    )

    content = brand_md.read_text(encoding="utf-8")
    bullets = [line for line in content.splitlines() if line.strip().startswith("-")]
    assert len(bullets) == 1
    assert "real insight." in bullets[0]


def test_update_brand_memory_handles_concurrent_writes(tmp_path):
    brands_dir = tmp_path / "Brands"
    brands_dir.mkdir()
    brand_md = brands_dir / "maple.md"
    brand_md.write_text("# Maple\n\n## Memory\n\n", encoding="utf-8")

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(
            executor.map(
                lambda i: update_brand_memory(
                    "maple", f"parallel insight {i}.", vault_path=tmp_path,
                    commit_vault=True, commit_reason="approved test output",
                ),
                range(20),
            )
        )

    content = brand_md.read_text(encoding="utf-8")
    bullets = [line for line in content.splitlines() if line.strip().startswith("-")]
    assert all(results)
    assert len(bullets) == 10
    assert all("parallel insight" in bullet for bullet in bullets)
    assert not brand_md.with_suffix(".md.lock").exists()


def test_log_agent_session_with_related_notes_appends_and_logs(monkeypatch, tmp_path):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 5, 3, 14, 30, 0)

    monkeypatch.setattr(obsidian_writer, "datetime", FixedDateTime)
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    monkeypatch.setattr(
        "agency_common.obsidian_vector_index.get_related_notes",
        lambda query_text, n_results: ["[[Architecture]]", "[[Agent Harness]]"],
    )

    output_path = log_agent_session_with_related_notes(
        agent_name="Core_Architect",
        task_summary="Analyze system architecture",
        transcript="**User:** Build me a retrieval engine.",
        tags=["agent-log", "architecture"],
        n_related=2,
        commit_vault=True,
        commit_reason="approved test output",
    )

    content = output_path.read_text(encoding="utf-8")

    assert "### Related Concepts\n- [[Architecture]]\n- [[Agent Harness]]" in content


def test_vault_writes_are_blocked_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))

    with pytest.raises(VaultWriteBlockedError, match="explicit commit_vault=True"):
        log_agent_session("Agent", "Task", "Transcript")

    assert not (tmp_path / "Agent_Sessions").exists()


def test_vault_commit_requires_a_reason(tmp_path):
    brands_dir = tmp_path / "Brands"
    brands_dir.mkdir()
    (brands_dir / "maple.md").write_text("# Maple\n", encoding="utf-8")

    with pytest.raises(VaultWriteBlockedError, match="non-empty commit reason"):
        update_brand_memory("maple", "insight", vault_path=tmp_path, commit_vault=True)
