"""Per-prompt skill routing receipt and PreToolUse guard. Standard library only.

This is a workflow guardrail, not a security boundary or proof of comprehension.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def state_path(session: str) -> Path:
    if not session:
        raise ValueError("Hook event has no session_id")
    key = hashlib.sha256(f"{ROOT.resolve()}:{session}".encode()).hexdigest()
    return Path(tempfile.gettempdir()) / "automata-routing" / f"{key}.json"


def save(session: str, data: dict) -> None:
    path = state_path(session)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replacement prevents readers from accepting a partially written receipt.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as f:
        json.dump(data, f)
    Path(f.name).replace(path)


def reset(session: str) -> None:
    save(session, {"routed": False})


def routed(session: str) -> bool:
    try:
        data = json.loads(state_path(session).read_text(encoding="utf-8"))
        if not data.get("routed") or not data.get("reason"):
            return False
        for item in data.get("skills", []):
            if hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest() != item["sha256"]:
                return False
        return bool(data.get("skills") or data.get("no_skill"))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def discovery_command(command: str, cwd: str) -> bool:
    # Conservative: compound commands, substitutions and redirections require routing.
    if any(c in command for c in (";", "|", "&", ">", "<", "`", "$", "\n")):
        return False
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        return False
    if not parts:
        return True
    executable = parts[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    if executable in {"cat", "ls", "pwd", "head", "tail", "wc"}:
        return True
    if executable == "rg":
        return not any(p.startswith(("--pre", "--hostname-bin")) for p in parts[1:])
    if executable == "git":
        return len(parts) > 1 and parts[1] in {"status", "diff", "log", "show", "ls-files", "rev-parse"} and not any(
            p.startswith(("--output", "--ext-diff", "--textconv")) for p in parts[2:])
    if executable == "make":
        return len(parts) > 1 and parts[1] in {"list-workflows", "brand-context"} and all(
            re.fullmatch(r"BRAND=[\w-]+", p) for p in parts[2:])
    if executable in {"python", "python3", "python.exe", "python3.exe", "py", "py.exe"} and len(parts) > 1:
        script = (Path(cwd) / parts[1]).resolve()
        return script in {ROOT / "scripts/hooks/routing_gate.py", ROOT / "scripts/brand_context.py"}
    return False


def needs_route(event: dict) -> bool:
    tool = event.get("tool_name", "")
    data = event.get("tool_input", {}) or {}
    if tool in {"Bash", "PowerShell", "exec_command", "shell_command"}:
        return not discovery_command(str(data.get("command", data.get("cmd", ""))), event.get("cwd", str(ROOT)))
    if tool in {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}:
        return True
    # MCP names vary by client. Gate mutation/generation verbs at token boundaries.
    return bool(re.search(r"(?:^|_)(?:create|generate|imagegen|edit|update|delete|remove|write|upload|publish|deploy|render|train|submit|send)(?:_|$)", tool, re.I))


def evaluate(event: dict) -> dict | None:
    if not needs_route(event) or routed(str(event.get("session_id", ""))):
        return None
    session = str(event.get("session_id", ""))
    reason = ("Skill routing is required before this action. Run the repo Python with "
              f"scripts/hooks/routing_gate.py --session {json.dumps(session)} "
              "--skill <path/to/SKILL.md> --reason <why-this-skill>. Read the returned instructions and required references. "
              "Use --no-skill --reason <why-no-available-skill-fits> only when no skill applies. "
              "Routing does not authorize spending, publishing, or sending.")
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True)
    parser.add_argument("--reason", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--skill", action="append")
    group.add_argument("--no-skill", action="store_true")
    args = parser.parse_args()
    if not args.reason.strip():
        parser.error("--reason must explain the route")
    items, texts = [], []
    try:
        for value in args.skill or []:
            path = Path(value).resolve()
            if path.name != "SKILL.md":
                raise ValueError("Choose a SKILL.md path from the available catalog")
            content = path.read_bytes()
            texts.append(f"Skill: {path}\n{content.decode('utf-8')}")
            items.append({"path": str(path), "sha256": hashlib.sha256(content).hexdigest()})
        # Deliver instructions before recording the receipt. A broken output pipe must not unlock work.
        print("\n\n".join(texts) if texts else f"No matching skill: {args.reason}", flush=True)
        save(args.session, {"routed": True, "reason": args.reason, "skills": items, "no_skill": args.no_skill})
    except (OSError, ValueError) as exc:
        print(f"Routing failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
