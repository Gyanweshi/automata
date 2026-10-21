"""Inject AGENTS.md skill-routing context into Claude Code and Codex sessions.

Usage (hook command): skill_routing_context.py session|prompt
Both runtimes accept the same JSON shape: hookSpecificOutput.additionalContext.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/agency-common/src"))

FIRST_ACTION = """AGENTS.md "First Action" is mandatory, not advisory:
1. Before the first substantive tool call, match the request against the skills/agents below and the session's own skill catalog.
2. Read the best-matching SKILL.md (and the references it requires) before using tools for the task. Name the chosen skill in one line.
3. Load project context first: brand note in the vault, prior decisions, existing assets and design systems. Do not invent a new direction where one exists.
4. Re-run this routing whenever scope changes (e.g. a quick look becomes research, research becomes a deck). Context compaction does not reset these rules."""

PROMPT_REMINDER = ("AGENTS.md routing check: if this prompt starts new work or changes scope, match it to a skill "
                   "(`make list-workflows`), read that SKILL.md and the brand/project context before acting, and "
                   "name the skill used. Skip only for pure follow-ups inside work already routed.")


def catalog_text() -> str:
    try:
        from agency_common.workflow_discovery import workflow_catalog
        catalog = workflow_catalog(ROOT)
    except Exception:  # missing venv deps: fall back to a plain directory scan
        catalog = {"skills": [{"name": p.parent.name, "description": ""}
                              for p in sorted((ROOT / "skills").glob("*/SKILL.md"))],
                   "agents": [{"name": p.parent.name}
                              for p in sorted((ROOT / "agents/openedswarm_core").glob("*/instructions.md"))]}
    lines = ["Repo skills (skills/<name>/SKILL.md):"]
    for skill in catalog["skills"]:
        desc = " ".join(str(skill.get("description", "")).split())
        lines.append(f"- {skill['name']}: {desc[:180]}" if desc else f"- {skill['name']}")
    if catalog.get("agents"):
        names = ", ".join(agent["name"] for agent in catalog["agents"])
        lines.append(f"Specialist instructions (agents/openedswarm_core/<name>/instructions.md): {names}")
    return "\n".join(lines)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "session"
    if mode == "prompt":
        event, context = "UserPromptSubmit", PROMPT_REMINDER
    else:
        event, context = "SessionStart", f"{FIRST_ACTION}\n\n{catalog_text()}"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}))


if __name__ == "__main__":
    main()
