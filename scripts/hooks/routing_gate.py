"""Per-prompt skill routing receipt and PreToolUse guard. Standard library only.

This is a workflow guardrail, not a security boundary or proof of comprehension.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
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
        return bool(data.get("skills") or data.get("builtin_skills") or data.get("no_skill"))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def shell_segments(command: str) -> tuple[list[list[str]], str | None]:
    """Parse a conservative shell subset, preserving quoted operator characters as data."""
    segments, parts, word = [], [], []
    quote = None
    started = False
    i = 0
    def finish_word():
        nonlocal word, started
        if started:
            parts.append("".join(word))
            word, started = [], False
    while i < len(command):
        char = command[i]
        if char == "\\" and quote != "'":
            if i + 1 == len(command):
                return [], "trailing escape character \\\\"
            # Within double quotes, shell backslashes only escape these characters.
            if quote == '"' and command[i + 1] not in '$`"\\\n':
                word.append(char)
                started = True
                i += 1
                continue
            word.append(command[i + 1])
            started = True
            i += 2
            continue
        if char in "\"'":
            if quote is None:
                quote, started = char, True
            elif quote == char:
                quote = None
            else:
                word.append(char)
            i += 1
            continue
        if quote != "'" and (char == "`" or command.startswith("$(", i)):
            return [], f"command substitution {char!r} requires routing"
        if quote != "'" and command.startswith("${", i):
            match = re.match(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}", command[i:])
            if not match:
                return [], "complex parameter expansion '${' requires routing"
            word.append(match.group())
            started = True
            i += len(match.group())
            continue
        if quote:
            word.append(char)
            i += 1
            continue
        if char in "<>":
            return [], f"redirection character {char!r} requires routing"
        if char in "()":
            return [], f"shell grouping character {char!r} requires routing"
        if char in ";|&\n":
            finish_word()
            operator = char
            if char in "|&" and i + 1 < len(command) and command[i + 1] == char:
                operator += char
                i += 1
            if operator == "&":
                return [], "background operator '&' requires routing"
            if not parts:
                if char == "\n":
                    i += 1
                    continue
                return [], f"unexpected shell operator {operator!r}"
            segments.append(parts)
            parts = []
            i += 1
            continue
        if char.isspace():
            finish_word()
        else:
            word.append(char)
            started = True
        i += 1
    if quote:
        return [], f"unclosed quote {quote!r}"
    finish_word()
    if parts:
        segments.append(parts)
    elif command.rstrip().endswith(("|", "&")):
        return [], "incomplete command chain"
    return segments, None


def read_segment(parts: list[str], cwd: str) -> bool:
    if not parts:
        return True
    executable = parts[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    if executable in {"cat", "ls", "pwd", "head", "tail", "wc", "grep", "egrep", "fgrep"}:
        return True
    if executable == "find":
        return not any(p in {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0",
                             "-fprintf", "-fls"} for p in parts[1:])
    if executable == "sed":
        # Only explicit print selections. sed's e/w commands and -i mutate or execute.
        args = parts[1:]
        if not args or args.pop(0) != "-n":
            return False
        if args and args[0] == "-e":
            args.pop(0)
        if not args:
            return False
        address = r"(?:[0-9]+|\$|/[^/]+/)"
        return bool(re.fullmatch(rf"(?:{address}(?:,{address})?)?p", args[0])) and not any(
            p.startswith("-") for p in args[1:])
    if executable == "rg":
        return not any(p.startswith(("--pre", "--hostname-bin")) for p in parts[1:])
    if executable == "git":
        args = parts[1:]
        while args and args[0] in {"-C", "--no-pager", "--literal-pathspecs"}:
            option = args.pop(0)
            if option == "-C":
                if not args:
                    return False
                args.pop(0)
        return bool(args) and args[0] in {"status", "diff", "log", "show", "ls-files", "rev-parse"} and not any(
            p.startswith(("--output", "--ext-diff", "--textconv")) for p in args[1:])
    if executable == "make":
        return len(parts) > 1 and parts[1] in {"list-workflows", "brand-context"} and all(
            re.fullmatch(r"BRAND=[\w-]+", p) for p in parts[2:])
    if executable in {"python", "python3", "python.exe", "python3.exe", "py", "py.exe"} and len(parts) > 1:
        script = (Path(cwd) / parts[1]).resolve()
        return script in {ROOT / "scripts/hooks/routing_gate.py", ROOT / "scripts/brand_context.py"}
    return False


def command_block_reason(command: str, cwd: str) -> str | None:
    segments, error = shell_segments(command)
    if error:
        return error
    for index, parts in enumerate(segments, 1):
        if not read_segment(parts, cwd):
            return f"command segment {index} ({parts[0]!r}) is outside the discovery allowlist"
    return None


def discovery_command(command: str, cwd: str) -> bool:
    return command_block_reason(command, cwd) is None


LOCAL_DISCOVERY_TOOLS = {
    "Read", "Glob", "Grep", "LS", "WebSearch", "WebFetch", "read_file", "list_dir", "view_image", "update_plan",
    "request_user_input", "request_user_input_async", "Skill", "skill",
    "list_mcp_resources", "list_mcp_resource_templates", "read_mcp_resource",
}
# Match the operation at the START of the tool name, never a word anywhere in it.
READ_OPERATIONS = {"get", "list", "show", "search", "describe", "read", "fetch", "inspect", "balance", "status"}


def tool_operation(tool: str) -> str:
    name = tool.rsplit("__", 1)[-1].lower()
    # Codex app tools flatten the provider into the final name, e.g. higgsfield_list_models.
    if tool.startswith("mcp__codex_apps__") and "_" in name:
        providers = ("codex_document_control", "plugin_management", "safety_settings", "search_service", "google_drive")
        provider = next((p for p in providers if name.startswith(p + "_")), name.split("_", 1)[0])
        name = name[len(provider) + 1:]
    return name.split("_", 1)[0]


def route_block_reason(event: dict) -> str | None:
    tool = event.get("tool_name", "")
    data = event.get("tool_input", {}) or {}
    if tool in {"Bash", "PowerShell", "exec_command", "shell_command"}:
        return command_block_reason(str(data.get("command", data.get("cmd", ""))), event.get("cwd", str(ROOT)))
    if tool in LOCAL_DISCOVERY_TOOLS:
        return None
    if tool.startswith("mcp__") and tool_operation(tool) in READ_OPERATIONS:
        # A read prefix must not hide a mixed operation such as get_or_create.
        operation = tool.rsplit("__", 1)[-1].lower().split("_")
        mutations = {"create", "generate", "delete", "write", "share", "trash", "rent", "start",
                     "execute", "publish", "upload", "update", "send"}
        if not mutations.intersection(operation):
            return None
    return f"tool {tool!r} is not on the read-only discovery allowlist"


def needs_route(event: dict) -> bool:
    return route_block_reason(event) is not None


def evaluate(event: dict) -> dict | None:
    blocked = route_block_reason(event)
    if blocked is None or routed(str(event.get("session_id", ""))):
        return None
    session = str(event.get("session_id", ""))
    reason = (f"Routing gate: {blocked}. Skill routing is required before this action. Run the repo Python with "
              f"scripts/hooks/routing_gate.py --session {json.dumps(session)} "
              "--skill <path/to/SKILL.md> --reason <why-this-skill>. Read the returned instructions and required references. "
              "For fileless built-in skills, invoke the skill, then use --builtin-skill <name> --reason <task-match>. "
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
    group.add_argument("--builtin-skill", action="append")
    group.add_argument("--no-skill", action="store_true")
    args = parser.parse_args()
    if not args.reason.strip():
        parser.error("--reason must explain the route")
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_:/.-]*", name) for name in args.builtin_skill or []):
        parser.error("--builtin-skill must name an invoked built-in skill")
    items, texts = [], []
    try:
        for value in args.skill or []:
            path = Path(value).resolve()
            if path.name != "SKILL.md":
                raise ValueError("Choose a SKILL.md path from the available catalog")
            content = path.read_bytes()
            texts.append(f"Skill: {path}\n{content.decode('utf-8')}")
            items.append({"path": str(path), "sha256": hashlib.sha256(content).hexdigest()})
        for name in args.builtin_skill or []:
            texts.append(f"Built-in skill: {name} (agent reports prior invocation; no local file hash available).")
        # Deliver instructions before recording the receipt. A broken output pipe must not unlock work.
        print("\n\n".join(texts) if texts else f"No matching skill: {args.reason}", flush=True)
        save(args.session, {"routed": True, "reason": args.reason, "skills": items, "builtin_skills": args.builtin_skill or [], "no_skill": args.no_skill})
    except (OSError, ValueError) as exc:
        print(f"Routing failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
