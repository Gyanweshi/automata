"""Write agent session logs into a local Obsidian vault."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter

from .knowledge_reader import DEFAULT_VAULT_ENV_VAR, VaultPathError, get_vault_path

DEFAULT_SESSIONS_DIR = "Agent_Sessions"


class ObsidianWriterError(RuntimeError):
    """Raised when an agent session cannot be written to the vault."""


def get_sessions_dir(
    *,
    vault_path: Path | None = None,
    subdirectory: str = DEFAULT_SESSIONS_DIR,
    env_var: str = DEFAULT_VAULT_ENV_VAR,
) -> Path:
    """Return the session log directory, creating it when needed."""
    resolved_vault_path = vault_path.expanduser().resolve() if vault_path else get_vault_path(env_var)
    if not resolved_vault_path.exists():
        raise VaultPathError(f"Vault path does not exist: {resolved_vault_path}")
    if not resolved_vault_path.is_dir():
        raise VaultPathError(f"Vault path must be a directory: {resolved_vault_path}")

    sessions_dir = resolved_vault_path / subdirectory
    try:
        sessions_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ObsidianWriterError(f"Could not create session log directory: {sessions_dir}") from exc

    return sessions_dir


def build_session_markdown(
    *,
    agent_name: str,
    task_summary: str,
    transcript: str,
    tags: list[str] | None = None,
    timestamp: datetime | None = None,
) -> str:
    """Build a Markdown session note with YAML frontmatter."""
    session_time = timestamp or datetime.now()
    safe_tags = tags if tags is not None else ["agent-log"]
    metadata: dict[str, Any] = {
        "date": session_time.isoformat(timespec="seconds"),
        "agent": agent_name,
        "task_summary": task_summary,
        "tags": safe_tags,
    }
    body = "\n".join(
        [
            f"# Agent Session: {agent_name}",
            "",
            "## Task Summary",
            task_summary,
            "",
            "## Transcript",
            transcript,
        ]
    )
    return frontmatter.dumps(frontmatter.Post(body, **metadata))


def _session_filename(timestamp: datetime) -> str:
    return f"Session_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.md"


def _next_available_path(directory: Path, filename: str) -> Path:
    """Return a unique path, preserving the requested timestamp-based filename when possible."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        candidate = directory / f"{stem}_{counter:02d}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def log_agent_session(
    agent_name: str,
    task_summary: str,
    transcript: str,
    tags: list[str] | None = None,
) -> Path:
    """Write an agent session transcript into Agent_Sessions inside the Obsidian vault."""
    safe_tags = tags if tags is not None else ["agent-log"]
    timestamp = datetime.now()
    sessions_dir = get_sessions_dir()
    output_path = _next_available_path(sessions_dir, _session_filename(timestamp))
    markdown = build_session_markdown(
        agent_name=agent_name,
        task_summary=task_summary,
        transcript=transcript,
        tags=safe_tags,
        timestamp=timestamp,
    )

    try:
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        raise ObsidianWriterError(f"Could not write agent session log: {output_path}") from exc

    return output_path


def format_related_concepts_section(related_links: list[str]) -> str:
    """Render related Obsidian wikilinks as a Markdown section."""
    if not related_links:
        return ""

    links_formatted = "\n".join(f"- {link}" for link in related_links)
    return f"### Related Concepts\n{links_formatted}"


def append_related_concepts(transcript: str, related_links: list[str]) -> str:
    """Append related concept backlinks to a transcript when links are available."""
    section = format_related_concepts_section(related_links)
    if not section:
        return transcript

    return f"{transcript.rstrip()}\n\n{section}"


def log_agent_session_with_related_notes(
    agent_name: str,
    task_summary: str,
    transcript: str,
    tags: list[str] | None = None,
    n_related: int = 3,
) -> Path:
    """Find related notes for the task summary, append them, and log the session."""
    from .obsidian_vector_index import get_related_notes

    related_links = get_related_notes(query_text=task_summary, n_results=n_related)
    transcript_with_links = append_related_concepts(transcript, related_links)
    return log_agent_session(
        agent_name=agent_name,
        task_summary=task_summary,
        transcript=transcript_with_links,
        tags=tags,
    )
