"""Write agent session logs into a local Obsidian vault."""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import time
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


_MEMORY_HEADING = "## Memory"
_MEMORY_MAX_BULLETS = 10
_MEMORY_LOCK_TIMEOUT_SECONDS = 10.0
_MEMORY_LOCK_STALE_SECONDS = 60.0


class _FileLock:
    """Tiny cross-platform lock for short metadata writes."""

    def __init__(self, lock_path: Path, *, timeout_seconds: float, stale_seconds: float):
        self.lock_path = lock_path
        self.timeout_seconds = timeout_seconds
        self.stale_seconds = stale_seconds
        self._fd: int | None = None

    def __enter__(self) -> "_FileLock":
        deadline = time.monotonic() + self.timeout_seconds
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            try:
                self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self._fd, str(os.getpid()).encode("ascii", errors="ignore"))
                return self
            except FileExistsError:
                self._clear_stale_lock()
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out waiting for lock: {self.lock_path}")
                time.sleep(0.05)

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass

    def _clear_stale_lock(self) -> None:
        try:
            age = time.time() - self.lock_path.stat().st_mtime
        except FileNotFoundError:
            return
        if age > self.stale_seconds:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass


def update_brand_memory(
    brand_slug: str,
    insight: str,
    *,
    vault_path: Path | None = None,
) -> bool:
    """
    Append a distilled one-line insight to the brand's ## Memory section.

    Trims to _MEMORY_MAX_BULLETS, keeping the most recent. Writes in-place to
    Brands/<slug>.md. Returns True on success, False (silently) if vault is not
    configured or the brand note does not exist.

    This replaces log_brand_run_summary — instead of writing separate log files
    that accumulate noise, we maintain a single compact memory in the brand note
    itself. The memory is always in context via BrandVoiceEngine.full_brief(),
    with zero retrieval cost.
    """
    try:
        resolved = vault_path.expanduser().resolve() if vault_path else get_vault_path()
    except Exception:
        return False

    brand_md = resolved / "Brands" / f"{brand_slug}.md"
    if not brand_md.exists():
        return False

    try:
        with _FileLock(
            brand_md.with_suffix(f"{brand_md.suffix}.lock"),
            timeout_seconds=_MEMORY_LOCK_TIMEOUT_SECONDS,
            stale_seconds=_MEMORY_LOCK_STALE_SECONDS,
        ):
            content = brand_md.read_text(encoding="utf-8")
            date_str = datetime.now().strftime("%Y-%m-%d")
            new_bullet = f"- {date_str}: {insight.strip()}"

            if _MEMORY_HEADING in content:
                lines = content.splitlines()
                mem_start = next(
                    (i for i, line in enumerate(lines) if line.strip() == _MEMORY_HEADING), None
                )
                if mem_start is not None:
                    mem_end = len(lines)
                    for i in range(mem_start + 1, len(lines)):
                        if lines[i].startswith("## "):
                            mem_end = i
                            break
                    bullets = [line for line in lines[mem_start + 1:mem_end] if line.strip().startswith("-")]
                    bullets.append(new_bullet)
                    if len(bullets) > _MEMORY_MAX_BULLETS:
                        bullets = bullets[-_MEMORY_MAX_BULLETS:]
                    new_block = [_MEMORY_HEADING, ""] + bullets + [""]
                    lines = lines[:mem_start] + new_block + lines[mem_end:]
                    content = "\n".join(lines)
            else:
                content = content.rstrip() + f"\n\n{_MEMORY_HEADING}\n\n{new_bullet}\n"

            brand_md.write_text(content, encoding="utf-8")
        return True
    except (OSError, TimeoutError):
        return False


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
