from datetime import datetime

import frontmatter

from agency_common import obsidian_writer
from agency_common.obsidian_writer import (
    append_related_concepts,
    build_session_markdown,
    format_related_concepts_section,
    get_sessions_dir,
    log_agent_session,
    log_agent_session_with_related_notes,
)


def test_get_sessions_dir_creates_agent_sessions_directory(tmp_path):
    sessions_dir = get_sessions_dir(vault_path=tmp_path)

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

    output_path = log_agent_session("Agent", "Task", "Transcript")

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
    )

    content = output_path.read_text(encoding="utf-8")

    assert "### Related Concepts\n- [[Architecture]]\n- [[Agent Harness]]" in content
