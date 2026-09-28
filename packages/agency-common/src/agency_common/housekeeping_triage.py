"""Rules-based triage of housekeeping `review` findings. Read-only: reads a plan, writes a report."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Iterable

ACTION_PROMOTE = "promote"
ACTION_KEEP = "keep"
ACTION_REVIEW = "review"
ACTION_QUARANTINE_OK = "quarantine-ok"

TOOL_STATE_SUFFIXES = {
    ".db", ".db-wal", ".db-shm", ".db-journal", ".journal", ".pma", ".dat", ".bf",
    ".baj", ".baf", ".bad", ".dmp", ".old", ".tmp", ".log",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
MEDIA_SUFFIXES = {".mp4", ".mov", ".mp3", ".wav", ".webm"}
CODE_SUFFIXES = {".py", ".js", ".ps1", ".sh"}
DATA_SUFFIXES = {".json", ".txt", ".csv", ".md", ".html", ".zip"}
CANDIDATE_DIRS = {"candidates", "crops", "crops8k", "figpass", "variants"}
INPUT_DIRS = {
    "source", "sources", "references", "reference-video", "reference-review", "prompts", "inputs",
}
PREVIEW_DIRS = {"preview", "previews"}
FRAME_DIRS = {"video", "frames"}
FINAL_DIRS = {"final", "finals", "approved"}
FINAL_NAME_HINTS = ("final", "approved")

BUCKET_ACTIONS = {
    "browser-profile": ACTION_QUARANTINE_OK,
    "tool-state": ACTION_QUARANTINE_OK,
    "frame-dump": ACTION_QUARANTINE_OK,
    "preview": ACTION_QUARANTINE_OK,
    "final": ACTION_PROMOTE,
    "input": ACTION_KEEP,
    "candidate": ACTION_REVIEW,
    "diagnostic": ACTION_REVIEW,
    "code": ACTION_REVIEW,
    "media": ACTION_REVIEW,
    "data": ACTION_REVIEW,
    "image": ACTION_REVIEW,
    "non-workspace": ACTION_REVIEW,
    "unclassified": ACTION_REVIEW,
}


def classify(path: str) -> str:
    """Return the triage bucket for a repo-relative posix path. Order matters."""
    pure = PurePosixPath(path)
    if not path.startswith("workspace/"):
        return "non-workspace"
    dirs = [part.lower() for part in pure.parts[1:-1]]
    name = pure.name.lower()
    suffix = pure.suffix.lower()

    if any("profile" in part or part == "user-data" for part in dirs):
        return "browser-profile"
    if suffix in TOOL_STATE_SUFFIXES:
        return "tool-state"
    if suffix in CODE_SUFFIXES:
        return "code"
    if FINAL_DIRS & set(dirs) or any(hint in name for hint in FINAL_NAME_HINTS):
        return "final"
    if CANDIDATE_DIRS & set(dirs):
        return "candidate"
    if INPUT_DIRS & set(dirs):
        return "input"
    if PREVIEW_DIRS & set(dirs):
        return "preview"
    if any(part.endswith("review") or part.endswith("inspection") for part in dirs):
        return "diagnostic"
    if suffix in IMAGE_SUFFIXES and FRAME_DIRS & set(dirs):
        return "frame-dump"
    if suffix in MEDIA_SUFFIXES:
        return "media"
    if suffix in DATA_SUFFIXES:
        return "data"
    if suffix in IMAGE_SUFFIXES:
        return "image"
    return "unclassified"


def _project(path: str) -> str:
    parts = PurePosixPath(path).parts
    if parts[0] == "workspace" and len(parts) > 2:
        return parts[1]
    return "(outside workspace)"


def triage_findings(findings: Iterable[dict]) -> list[dict]:
    rows = []
    for item in findings:
        if item.get("decision") != "review":
            continue
        path = item["path"]
        bucket = classify(path) if item.get("scope") == "repo" else "non-workspace"
        rows.append({
            "path": path,
            "scope": item.get("scope", ""),
            "project": _project(path) if item.get("scope") == "repo" else "(vault)",
            "bucket": bucket,
            "action": BUCKET_ACTIONS[bucket],
            "size": int(item.get("size", 0)),
            "reason": item.get("reason", ""),
        })
    return rows


ADVICE_OPTIONS = {
    ACTION_PROMOTE: "a finished output that belongs in the vault",
    ACTION_KEEP: "a source, reference, or prompt input that may be irreplaceable",
    ACTION_REVIEW: "unclear: a person should look",
    ACTION_QUARANTINE_OK: "regenerable scratch output",
}


def advise_rows(rows: list[dict], backend, *, log=None, limit: int = 200) -> list[dict]:
    """Attach advisory `suggested`/`confidence`/`route` to rows still marked `review`.

    Advice never changes `action`: the rules decide that. A suggestion is only a hint that
    lets a person clear obvious cases faster, and only `route == "act"` suggestions are
    worth trusting at a glance. Read-only apart from the optional decision log.
    """
    from .decide import Choice, decide

    question = Choice(
        "housekeeping_action", ADVICE_OPTIONS,
        "What should happen to this untracked workspace file?",
        "Prefer `review` when unsure. Never call something regenerable if it could be a source or final deliverable.",
    )
    siblings: dict[str, int] = defaultdict(int)
    for row in rows:
        siblings[str(PurePosixPath(row["path"]).parent)] += 1
    for row in [r for r in rows if r["action"] == ACTION_REVIEW][:limit]:
        state = {
            "path": row["path"], "bucket": row["bucket"], "project": row["project"], "size_bytes": row["size"],
            "files_in_same_folder": siblings[str(PurePosixPath(row["path"]).parent)],
        }
        decision = decide(state, [question], backend, log=log, name="housekeeping.triage")["housekeeping_action"]
        row.update(
            suggested=decision.answer, confidence=decision.confidence, route=decision.route,
            decision_id=decision.decision_id,
        )
    return rows


def _gb(size: int) -> str:
    return f"{size / 1e9:.2f}"


def render_markdown(rows: list[dict], plan_name: str) -> str:
    by_action: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_project: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for row in rows:
        for cell in (by_action[row["action"]], by_project[row["project"]][row["action"]]):
            cell[0] += 1
            cell[1] += row["size"]

    actions = [ACTION_PROMOTE, ACTION_KEEP, ACTION_REVIEW, ACTION_QUARANTINE_OK]
    lines = [
        "---",
        "type: housekeeping-triage",
        "status: review",
        "---",
        "",
        "# Housekeeping triage",
        "",
        f"Source plan: `{plan_name}`. Rules-based and advisory only; nothing here deletes or moves files.",
        "",
        "## By action",
        "",
        "| Action | Files | GB | Meaning |",
        "| --- | ---: | ---: | --- |",
    ]
    meaning = {
        ACTION_PROMOTE: "Looks like a finished output. Save to the vault before any workspace clearing.",
        ACTION_KEEP: "Source, reference or prompt input. Plausibly irreplaceable.",
        ACTION_REVIEW: "Needs a human call (candidates, code, renders, diagnostics, data, unclassified).",
        ACTION_QUARANTINE_OK: "Regenerable (browser profiles, tool state, frame dumps, previews).",
    }
    for action in actions:
        count, size = by_action.get(action, [0, 0])
        lines.append(f"| {action} | {count} | {_gb(size)} | {meaning[action]} |")

    lines += ["", "## By project", "", "| Project | " + " | ".join(actions) + " |", "| --- | " + " | ".join(["---:"] * len(actions)) + " |"]
    for project in sorted(by_project):
        cells = [f"{by_project[project][a][0]} ({_gb(by_project[project][a][1])} GB)" if by_project[project][a][0] else "-" for a in actions]
        lines.append(f"| {project} | " + " | ".join(cells) + " |")

    lines += ["", "## Promote to the vault first", ""]
    promote = sorted((r for r in rows if r["action"] == ACTION_PROMOTE), key=lambda r: r["path"])
    lines += [f"- `{r['path']}` ({r['size'] / 1e6:.1f} MB)" for r in promote] or ["- none"]

    lines += ["", "## Renders and media to confirm as delivered or disposable", ""]
    media = sorted((r for r in rows if r["bucket"] == "media"), key=lambda r: r["path"])
    lines += [f"- `{r['path']}` ({r['size'] / 1e6:.1f} MB)" for r in media] or ["- none"]

    advised = sorted((r for r in rows if r.get("suggested")), key=lambda r: (r["route"], r["path"]))
    if advised:
        lines += ["", "## Model suggestions (advisory, rules still decide)", "", "| Path | Suggested | Confidence | Route |", "| --- | --- | ---: | --- |"]
        lines += [f"| `{r['path']}` | {r['suggested']} | {r['confidence']:.2f} | {r['route']} |" for r in advised]

    lines += ["", "## Scripts", ""]
    code = sorted((r for r in rows if r["bucket"] == "code"), key=lambda r: r["path"])
    lines += [f"- `{r['path']}`" for r in code] or ["- none"]
    return "\n".join(lines) + "\n"


def triage_plan(plan_path: str, *, backend=None, log=None, advise_limit: int = 200) -> tuple[list[dict], str]:
    plan = json.loads(open(plan_path, encoding="utf-8").read())
    rows = triage_findings(plan["findings"])
    if backend is not None:
        advise_rows(rows, backend, log=log, limit=advise_limit)
    return rows, render_markdown(rows, PurePosixPath(plan_path.replace("\\", "/")).name)


def quarantine_paths(repo_path, rows: list[dict], *, retention_days: int = 7) -> dict:
    """Move chosen untracked workspace files into a recoverable, auto-purging quarantine batch."""
    import shutil
    from datetime import timedelta
    from pathlib import Path

    from .housekeeping import HousekeepingError, _git_tracked_files, _utc_now, _within

    if retention_days < 1:
        raise HousekeepingError("Workspace retention must be at least one day")
    repo = Path(repo_path).resolve()
    workspace = (repo / "workspace").resolve()
    tracked = _git_tracked_files(repo)
    quarantined_at = _utc_now()
    batch = repo / ".housekeeper" / "quarantine" / quarantined_at.strftime("%Y%m%dT%H%M%S%fZ")
    moved: list[str] = []
    skipped: list[str] = []
    for row in rows:
        relative = row["path"]
        source = (repo / relative).resolve()
        if not relative.startswith("workspace/") or not _within(source, workspace) or source == workspace:
            skipped.append(f"{relative}: outside workspace")
        elif relative in tracked:
            skipped.append(f"{relative}: tracked by git")
        elif not source.is_file() or source.is_symlink():
            skipped.append(f"{relative}: missing or not a regular file")
        elif source.stat().st_size != row["size"]:
            skipped.append(f"{relative}: changed since audit")
        else:
            destination = batch / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            moved.append(relative)
    result = {
        "batch": str(batch),
        "quarantined_at": quarantined_at.isoformat(),
        "purge_after": (quarantined_at + timedelta(days=retention_days)).isoformat(),
        "retention_days": retention_days,
        "moved": moved,
        "skipped": skipped,
    }
    if moved or skipped:
        batch.mkdir(parents=True, exist_ok=True)
        (batch / "manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def prune_empty_workspace_dirs(repo_path, exclude_projects: tuple[str, ...] = ()) -> list[str]:
    """Remove empty directories under workspace/. rmdir never removes a non-empty directory."""
    from pathlib import Path

    workspace = (Path(repo_path).resolve() / "workspace")
    removed: list[str] = []
    candidates = (
        p for p in workspace.rglob("*")
        if p.is_dir() and not p.is_symlink()
        and p.relative_to(workspace).parts[0] not in exclude_projects
    )
    for directory in sorted(candidates, key=lambda p: len(p.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            continue
        removed.append(directory.relative_to(workspace.parent).as_posix())
    return removed
