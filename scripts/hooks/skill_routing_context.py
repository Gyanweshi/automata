"""Inject AGENTS.md skill-routing context into Claude Code and Codex sessions.

Usage (hook command): skill_routing_context.py session|prompt
Both runtimes accept the same JSON shape: hookSpecificOutput.additionalContext.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/agency-common/src"))

FIRST_ACTION = """AGENTS.md "First Action" is mandatory, not advisory:
1. Before the first substantive tool call, match the request against the skills below and the session's own skill catalog.
2. Read the best-matching SKILL.md (and the references it requires) before using tools for the task. Name the chosen skill in one line.
3. Load project context before execution. For brand work, run `make brand-context BRAND=<brand>` or `python scripts/brand_context.py <brand>`. Read the brand note AND existing drafts, decisions, assets, and design systems. For repository maintenance, read the relevant project documentation and configuration. Do not invent a brand name for maintenance tasks.
4. Re-run this routing whenever scope changes (e.g. a quick look becomes research, research becomes a deck). Context compaction does not reset these rules."""

PROMPT_REMINDER = ("AGENTS.md routing check: if this prompt starts new work or changes scope, match it to a skill "
                   "(`make list-workflows`), read that SKILL.md and relevant project context before acting. "
                   "For brand work, also run `make brand-context BRAND=<brand>`. "
                   "Name the skill used. Skip only for pure follow-ups inside work already routed.")


def catalog_text() -> str:
    try:
        from agency_common.workflow_discovery import workflow_catalog
        catalog = workflow_catalog(ROOT)
    except Exception:  # missing venv deps: fall back to a plain directory scan
        paths = {}
        for directory in ("skills", ".agents/skills", ".claude/skills"):
            for p in sorted((ROOT / directory).glob("*/SKILL.md")):
                paths.setdefault(p.parent.name, p)
        catalog = {"skills": [{"name": name, "description": "", "path": str(p)}
                              for name, p in paths.items()]}
    lines = ["Repo skill summaries (read the listed path; full descriptions: make list-workflows).",
             "Also check the session skill catalog."]
    for skill in catalog["skills"]:
        desc = " ".join(str(skill.get("description", "")).split())
        desc = re.split(r"(?<=[.!?])\s", desc, maxsplit=1)[0]
        path = Path(skill["path"])
        try:
            path = path.relative_to(ROOT)
        except ValueError:
            pass
        lines.append(f"- {skill['name']} ({path.as_posix()}): {desc}")
    return "\n".join(lines)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "session"
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    session = str(payload.get("session_id", ""))
    if mode == "prompt":
        event, context = "UserPromptSubmit", PROMPT_REMINDER
        if session:
            from routing_gate import reset
            reset(session)
    else:
        event, context = "SessionStart", f"{FIRST_ACTION}\n\n{catalog_text()}"
        try:
            sys.path.insert(0, str(ROOT / "scripts"))
            from setup_state import stale_message
            stale = stale_message(ROOT)
            if stale:
                context = f"{stale}\n\n{context}"
        except Exception:  # never block a session over the freshness check
            pass
    if session:
        context = ("Routing gate: before writes, generation, or non-discovery shell commands, run "
                   f"the repo Python with scripts/hooks/routing_gate.py --session {json.dumps(session)} "
                   "--skill <SKILL.md-path> --reason <task-match>. Read the returned skill and its required references. "
                   "Use --no-skill with a reason only when no available skill fits. "
                   "Each user prompt requires a new receipt. Reuse the same skill for an unchanged task.\n\n" + context)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}))


if __name__ == "__main__":
    main()
