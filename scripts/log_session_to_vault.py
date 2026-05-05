#!/usr/bin/env python3
"""
Log a Claude Code or Codex session to the Obsidian vault.

Reads session info from stdin, finds the corresponding JSONL transcript,
extracts the conversation, detects relevant files and brands mentioned, writes
a Markdown note to Agent_Sessions/ in the vault, and
appends a one-line summary to the Session History section of each mentioned
brand note.

Usage (called by Claude Code Stop hook):
    echo '{"session_id": "...", "stop_hook_active": true}' | python3 log_session_to_vault.py

Usage for the current Codex session:
    python3 scripts/log_session_to_vault.py --codex-current
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

VAULT_ENV = "OBSIDIAN_VAULT_PATH"
CLAUDE_SESSIONS_DIR = "Agent_Sessions"
CODEX_SESSIONS_DIR = "Agent_Sessions"
BRANDS_SUBDIR = "Brands"
PROJECTS_DIR = Path.home() / ".claude" / "projects"
CODEX_SESSIONS_DIR_ROOT = Path.home() / ".codex" / "sessions"
SESSION_HISTORY_HEADING = "## Session History"


def get_vault() -> Path | None:
    raw = os.environ.get(VAULT_ENV)
    if not raw:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                key, sep, value = line.partition("=")
                if sep and key.strip() == VAULT_ENV:
                    raw = value.strip()
                    break
    if not raw:
        return None
    p = Path(raw).expanduser().resolve()
    return p if p.is_dir() else None


def find_jsonl(session_id: str) -> Path | None:
    for project_dir in PROJECTS_DIR.iterdir():
        candidate = project_dir / f"{session_id}.jsonl"
        if candidate.exists():
            return candidate
    return None


def find_codex_jsonl(session_id: str) -> Path | None:
    if not CODEX_SESSIONS_DIR_ROOT.is_dir():
        return None
    matches = sorted(CODEX_SESSIONS_DIR_ROOT.rglob(f"*{session_id}*.jsonl"))
    return matches[-1] if matches else None


def _text_from_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") in {"text", "input_text", "output_text"}:
                parts.append(str(block.get("text", "")))
        return "\n".join(parts)
    return ""


def extract_conversation(jsonl_path: Path) -> list[dict]:
    """Return ordered list of {role, text} dicts from the session."""
    messages = []
    for raw in jsonl_path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        role = entry.get("type")
        if role not in ("user", "assistant"):
            continue
        msg = entry.get("message", {})
        content = msg.get("content", "")
        text = _text_from_content(content)
        text = text.strip()
        if text:
            messages.append({"role": role, "text": text})
    return messages


def extract_codex_conversation(jsonl_path: Path) -> list[dict]:
    """Return ordered user/assistant messages from a Codex rollout JSONL."""
    messages = []
    for raw in jsonl_path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "response_item":
            continue
        payload = entry.get("payload", {})
        if payload.get("type") != "message":
            continue
        role = payload.get("role")
        if role not in ("user", "assistant"):
            continue
        text = _text_from_content(payload.get("content", "")).strip()
        if not text:
            continue
        if role == "user" and text.startswith("# AGENTS.md instructions"):
            continue
        messages.append({"role": role, "text": text})
    return messages


def extract_codex_project_path(jsonl_path: Path) -> str:
    for raw in jsonl_path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if entry.get("type") == "session_meta":
            return str(entry.get("payload", {}).get("cwd", ""))
    return str(jsonl_path.parent)


def clean_text(text: str) -> str:
    """Strip XML-style tags (slash commands, system messages)."""
    return re.sub(r"<[^>]+>", "", text).strip()


def make_summary(messages: list[dict]) -> str:
    """One-line summary from the first meaningful user message."""
    for m in messages:
        if m["role"] != "user":
            continue
        cleaned = clean_text(m["text"])
        if cleaned:
            return cleaned[:120].replace("\n", " ")
    return "Session"


def detect_entities(messages: list[dict], vault: Path) -> dict:
    """Find file paths and brand slugs mentioned in the conversation."""
    full_text = " ".join(m["text"] for m in messages)

    file_pattern = re.compile(r"(?<![:/])(?:[\w./~-]+/)+[\w.-]+\.\w{1,6}")
    raw_files = file_pattern.findall(full_text)
    files = sorted({
        f for f in raw_files
        if len(f) > 4
        and not f.startswith("/")       # no absolute paths — Obsidian creates stubs from them
        and not f.startswith("//")
        and not f.startswith("~")
        and "www." not in f
    })

    brands_dir = vault / BRANDS_SUBDIR
    known_brands = (
        {p.stem for p in brands_dir.glob("*.md")} | {p.stem for p in brands_dir.glob("*.yaml")}
        if brands_dir.is_dir() else set()
    )
    mentioned_brands = sorted({b for b in known_brands if b.lower() in full_text.lower()})

    return {"files": files[:20], "brands": mentioned_brands}


def build_session_note(
    session_id: str,
    messages: list[dict],
    entities: dict,
    summary: str,
    timestamp: datetime,
    project_path: str,
    agent_label: str = "Claude",
    tag_prefix: str = "claude-code",
) -> str:
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H:%M")

    tags = [tag_prefix, "agent-session"]
    if entities["brands"]:
        tags += [f"brand/{b}" for b in entities["brands"]]

    fm = "\n".join([
        "---",
        f"date: {date_str}",
        f"time: {time_str}",
        f"session_id: {session_id}",
        f"project: {project_path}",
        f'summary: "{summary}"',
        f"tags: [{', '.join(tags)}]",
        "---",
    ])

    lines = [f"# {agent_label} Session - {date_str} {time_str}", "", "## Summary", summary, ""]

    if entities["brands"]:
        # Only wikilink to brands that have an actual note in the vault
        links = " ".join(f"[[{BRANDS_SUBDIR}/{b}|{b}]]" for b in entities["brands"])
        lines += ["## Brands", links, ""]
        # Note: competitors/handles are external links in brand notes, never wikilinked here

    if entities["files"]:
        lines += ["## Files mentioned", ""]
        for f in entities["files"]:
            lines.append(f"- `{f}`")
        lines.append("")

    return fm + "\n" + "\n".join(lines)


def append_to_brand_note(
    brand_slug: str,
    vault: Path,
    session_note_name: str,
    summary: str,
    date_str: str,
    sessions_subdir: str = CLAUDE_SESSIONS_DIR,
) -> None:
    """Append a one-line session entry to the brand's Session History section."""
    brand_path = vault / BRANDS_SUBDIR / f"{brand_slug}.md"
    if not brand_path.exists():
        return

    content = brand_path.read_text(encoding="utf-8")

    # Don't add a duplicate entry if this session was already logged
    if session_note_name in content:
        return

    entry = f"- {date_str}: {summary} - [[{sessions_subdir}/{session_note_name}|view session]]"

    if SESSION_HISTORY_HEADING in content:
        content = content.replace(
            SESSION_HISTORY_HEADING,
            f"{SESSION_HISTORY_HEADING}\n{entry}",
            1,
        )
    else:
        content = content.rstrip() + f"\n\n{SESSION_HISTORY_HEADING}\n{entry}\n"

    brand_path.write_text(content, encoding="utf-8")


def main() -> int:
    mode = "claude"
    args = sys.argv[1:]
    if "--codex-current" in args:
        mode = "codex"
        payload = {"session_id": os.environ.get("CODEX_THREAD_ID", "")}
    else:
        try:
            payload = json.loads(sys.stdin.read())
        except (json.JSONDecodeError, ValueError):
            payload = {}
        if payload.get("codex") or payload.get("source") == "codex":
            mode = "codex"

    session_id = payload.get("session_id", "")
    if not session_id:
        return 0

    vault = get_vault()
    if not vault:
        return 0

    jsonl_path = find_codex_jsonl(session_id) if mode == "codex" else find_jsonl(session_id)
    if not jsonl_path:
        return 0

    messages = extract_codex_conversation(jsonl_path) if mode == "codex" else extract_conversation(jsonl_path)
    if not messages:
        return 0

    project_path = extract_codex_project_path(jsonl_path) if mode == "codex" else str(jsonl_path.parent.name)
    entities = detect_entities(messages, vault)
    summary = make_summary(messages)
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    short_id = session_id[:8]
    filename = f"Session_{date_str}_{short_id}"
    sessions_subdir = CODEX_SESSIONS_DIR if mode == "codex" else CLAUDE_SESSIONS_DIR

    note = build_session_note(
        session_id=session_id,
        messages=messages,
        entities=entities,
        summary=summary,
        timestamp=timestamp,
        project_path=project_path,
        agent_label="Codex" if mode == "codex" else "Claude",
        tag_prefix="codex" if mode == "codex" else "claude-code",
    )

    sessions_dir = vault / sessions_subdir
    sessions_dir.mkdir(exist_ok=True)
    out_path = sessions_dir / f"{filename}.md"
    out_path.write_text(note, encoding="utf-8")

    # Brand notes use a Dataview query to surface sessions — no manual appending needed

    print(out_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
