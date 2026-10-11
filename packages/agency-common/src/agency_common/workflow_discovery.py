"""Read-only discovery of repo skills and specialist instructions, shared by runtimes."""
from __future__ import annotations

import json
from pathlib import Path

import frontmatter
import yaml


def repo_root() -> Path:
    for origin in (Path(__file__).resolve(), Path.cwd()):
        for parent in (origin, *origin.parents):
            if (parent / "AGENTS.md").is_file() and (parent / "skills").is_dir():
                return parent
    raise FileNotFoundError("Automata repo not found; run from a checkout with AGENTS.md and skills/.")


def skill_roots(root: Path) -> list[Path]:
    return [root / "skills", root / ".agents/skills", root / ".claude/skills",
            root / "agents/openedswarm_core/mnt/skills"]


def workflow_catalog(root: Path | None = None) -> dict:
    root = root or repo_root()
    skills = {}
    errors = []
    for directory in skill_roots(root):
        for path in sorted(directory.glob("*/SKILL.md")):
            try:
                note = frontmatter.load(path)
                name = note.get("name", path.parent.name)
                skills.setdefault(name, {"name": name, "description": note.get("description", ""),
                                         "path": str(path.resolve())})
            except (OSError, ValueError, yaml.YAMLError) as exc:
                errors.append({"path": str(path), "error": str(exc)})
    agents = [{"name": path.parent.name, "instructions": str(path.resolve())}
              for path in sorted((root / "agents/openedswarm_core").glob("*/instructions.md"))]
    return {"policy": str(root / "AGENTS.md"), "skills": list(skills.values()),
            "agents": agents, "errors": errors,
            "note": "Listed agent files are not proof of callable delegation. Also consult the session's installed skill/tool catalog."}


def discover_workflows() -> str:
    try:
        return json.dumps(workflow_catalog(), ensure_ascii=False, indent=2)
    except (OSError, ValueError) as exc:
        return f"Workflow discovery unavailable: {exc}"


def read_workflow(path: str) -> str:
    """Read instructions/references, never arbitrary project secrets or binaries."""
    try:
        root = repo_root()
        target = (root / path).resolve()
        allowed_dirs = [p.resolve() for p in skill_roots(root)] + [(root / "mcp/agents").resolve()]
        allowed_files = {root / "AGENTS.md", root / "agents/openedswarm_core/shared_instructions.md"}
        allowed_files.update((root / "agents/openedswarm_core").glob("*/instructions.md"))
        if target not in allowed_files and not any(target.is_relative_to(p) for p in allowed_dirs):
            return "Workflow read denied: choose an instruction or reference path from discovery."
        if target.suffix.lower() not in {".md", ".json", ".yaml", ".yml", ".txt"}:
            return "Workflow read denied: only text instructions and reference data are supported."
        return target.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        return f"Workflow read failed: {exc}"
