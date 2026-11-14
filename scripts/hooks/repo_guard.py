#!/usr/bin/env python3
"""Claude Code and Codex PreToolUse guard for known old-way commands.

Only clear-cut cases are blocked (a removed script, an installer that bypasses the pins, a new one-OS script, a
browser-act command before its required guide). Everything else passes through untouched. Reads the hook event
as JSON on stdin; prints a deny decision as JSON when a rule matches. Standard library only, fast.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Removed in the cross-platform migration -> the one implementation that replaced them.
REMOVED_SCRIPTS = {
    r"bootstrap\.(sh|ps1|cmd)": "uv run --no-project --python 3.12 scripts/bootstrap.py (or python scripts/bootstrap.py)",
    r"run-agent\.ps1|run-pipeline\.sh": "python scripts/run-agent.py <research|storyboard|content|pipeline|...>",
    r"setup-mcp\.(ps1|cmd|sh)": "python scripts/deps.py check (MCP pins) or python scripts/bootstrap.py",
    r"install-(vault-index|housekeeper-watchdog)\.(sh|ps1)": "python scripts/schedule.py install <vault-index|housekeeper|vault-watchdog>",
    r"install-skills\.sh|Install-Skills\.ps1": "python scripts/install-skills.py",
    r"install-gimp-mcp\.(ps1|sh)": "python scripts/install-gimp-mcp.py",
    r"install-raea\.(sh|ps1|py)": "python scripts/deps.py install raea",
    r"open-instagram-session\.ps1": "python scripts/open-instagram-session.py",
    r"(upscale-storyboard-image|crop-motion-broll)\.ps1": "python skills/render-upscale-crop/scripts/<same name>.py",
    r"mcp-npx\.sh": "node scripts/mcp-npx.mjs",
    r"openedswarm_core|start\.ps1": "nothing: OpenSwarm was removed on purpose (one agent system)",
}

# Installers that bypass dependencies.toml (pins, checksums, per-OS builds).
BYPASS_INSTALLS = [
    (r"raea\.io/install", "python scripts/deps.py install raea (pinned, checksum-verified, per-OS build)"),
    (r"uv\s+tool\s+(install|upgrade)\s+[^|;&]*browser-act-cli", "python scripts/deps.py install browser-act (pinned version)"),
    (r"(npm|npx)\s+(i|install)\s+(-g|--global)\b[^|;&]*(mcp|playwright)", "the pinned MCP configs (node scripts/mcp-npx.mjs) and python scripts/deps.py"),
]

ONE_OS_SUFFIXES = {".sh", ".bash", ".ps1", ".cmd", ".bat"}
# Thin legacy launchers kept on purpose so schedules installed before the migration keep working.
ALLOWED_ONE_OS = {"scripts/run-vault-index.sh", "scripts/run-vault-index.ps1",
                  "scripts/run-housekeeper-watchdog.sh", "scripts/run-housekeeper-watchdog.ps1"}


def deny(reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def browser_act_marker(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "", session_id or "unknown")[:64]
    return Path(tempfile.gettempdir()) / "automata-hooks" / f"browser-act-guide-{safe}"


def executable_text(command: str) -> str:
    """The parts of a shell command that could run something: drop heredoc bodies, single-quoted strings
    (data, e.g. JSON piped into a tool) and echo/printf arguments, so mentions of an old name don't trigger."""
    command = re.sub(r"<<-?\s*'?(\w+)'?.*?\n\1\b", " ", command, flags=re.S)
    command = re.sub(r"'[^']*'", " ", command)
    parts = re.split(r"(&&|\|\||;|\|)", command)
    return " ".join(p for p in parts if not re.match(r"\s*(echo|printf)\b", p))


def check_bash(command: str, session_id: str) -> dict | None:
    command = executable_text(command)
    for pattern, replacement in REMOVED_SCRIPTS.items():
        if re.search(rf"(^|[\s/\\\\]){pattern}", command) and not re.search(r"\b(git|rm|grep|ls|cat|sed|find)\b\s", command.split("&&")[0]):
            return deny(f"That script was removed in the cross-platform migration. Use: {replacement}. "
                        "See AGENTS.md (OS Commands, Cross-Platform Rule).")
    for pattern, replacement in BYPASS_INSTALLS:
        if re.search(pattern, command):
            return deny(f"This installer bypasses dependencies.toml (pins, checksums, per-OS builds). Use: {replacement}.")
    if re.search(r"(^|[;&|]\s*)browser-act\b", command):
        marker = browser_act_marker(session_id)
        if "get-skills" in command:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("loaded", encoding="utf-8")
            return None
        if not marker.exists():
            return deny("The browser-act skill requires its usage guide before any other command, and it changes "
                        "between versions. First run: browser-act get-skills core --skill-version 2.0.2 "
                        "(read it fully), then retry.")
    return None


def check_write(file_path: str) -> dict | None:
    path = Path(file_path)
    try:
        rel = path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None  # outside the repo
    if path.suffix.lower() in ONE_OS_SUFFIXES and rel not in ALLOWED_ONE_OS and not path.exists():
        return deny(f"New {path.suffix} script blocked by the Cross-Platform Rule (AGENTS.md): this repo runs on Linux and "
                    "Windows, so write it once in Python (or Node for MCP launch) with OS handling inside, "
                    "e.g. scripts/<name>.py. Then run make check-cross-platform.")
    return None


def evaluate(event: dict) -> dict | None:
    tool = event.get("tool_name", "")
    data = event.get("tool_input", {}) or {}
    if tool in ("Bash", "PowerShell"):
        return check_bash(str(data.get("command", "")), str(event.get("session_id", "")))
    if tool == "Write":
        return check_write(str(data.get("file_path", "")))
    return None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0  # never break a tool call because the hook could not read its input
    try:
        decision = evaluate(event)
        if decision is None:
            from routing_gate import evaluate as check_route
            decision = check_route(event)
    except Exception as exc:
        decision = deny(f"Repository hook failed ({type(exc).__name__}). Repair the hook before retrying this action.")
    if decision:
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.exit(main())
