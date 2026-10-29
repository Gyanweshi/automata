"""Conservative housekeeping audit for the Automata repo and Obsidian vault."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .vault_write_gate import require_vault_write


DECISION_KEEP_REPO = "keep-repo"
DECISION_KEEP_VAULT = "keep-vault"
DECISION_REVIEW = "review"
DECISION_SAFE_DELETE = "safe-delete"

SAFE_CACHE_DIRS = {"__pycache__", ".pytest_cache", ".playwright-mcp", ".tmp"}
SAFE_FILE_SUFFIXES = {".pyc", ".pyo", ".stackdump", ".tmp"}
REPO_ARTIFACT_SUFFIXES = {
    ".csv", ".docx", ".html", ".jpeg", ".jpg", ".json", ".md", ".pdf",
    ".png", ".pptx", ".txt", ".webp", ".xlsx",
}
PROTECTED_REPO_DIRS = {
    ".agents", ".codex", ".git", ".housekeeper", ".venv", "node_modules",
}
PROTECTED_REPO_FILES = {".env", "env.example"}
PROTECTED_VAULT_DIRS = {".git", ".obsidian", ".trash"}
PROTECTED_VAULT_PREFIXES = {"Agent_Sessions", "Brands", "memory"}
REQUIRED_FINAL_NOTE_KEYS = {"type", "status", "tags"}
MAX_HASH_BYTES = 100 * 1024 * 1024


class HousekeepingError(RuntimeError):
    """Raised when an audit or cleanup would violate a safety boundary."""


@dataclass
class Finding:
    scope: str
    path: str
    decision: str
    reason: str
    size: int = 0
    modified: str = ""
    duplicate_of: str = ""
    fingerprint: str = ""


@dataclass
class AuditReport:
    repo: str
    vault: str
    generated_at: str
    min_age_days: int
    findings: list[Finding] = field(default_factory=list)
    tracked_repo_files: int = 0

    def counts(self) -> dict[str, int]:
        result = {
            DECISION_KEEP_REPO: self.tracked_repo_files,
            DECISION_KEEP_VAULT: 0,
            DECISION_REVIEW: 0,
            DECISION_SAFE_DELETE: 0,
        }
        for finding in self.findings:
            result[finding.decision] = result.get(finding.decision, 0) + 1
        return result

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "repo": self.repo,
            "vault": self.vault,
            "generated_at": self.generated_at,
            "min_age_days": self.min_age_days,
            "tracked_repo_files": self.tracked_repo_files,
            "findings": [asdict(item) for item in self.findings],
        }

    def to_markdown(self) -> str:
        counts = self.counts()
        created = self.generated_at[:10]
        status = "review" if counts[DECISION_REVIEW] else "complete"
        lines = [
            "---",
            "type: housekeeping-report",
            f"status: {status}",
            f"created: {created}",
            "tags: [automata, housekeeping, watchdog]",
            "---",
            "",
            "# Automata housekeeping report",
            "",
            f"Generated: `{self.generated_at}`  ",
            f"Repo: `{self.repo}`  ",
            f"Vault: `{self.vault}`",
            "",
            "## Summary",
            "",
            "| Decision | Count | Meaning |",
            "| --- | ---: | --- |",
            f"| Keep in repo | {counts[DECISION_KEEP_REPO]} | Tracked or protected repo material |",
            f"| Keep in vault | {counts[DECISION_KEEP_VAULT]} | Durable or protected vault material |",
            f"| Review | {counts[DECISION_REVIEW]} | Human judgment or metadata repair required |",
            f"| Safe-delete | {counts[DECISION_SAFE_DELETE]} | Eligible for verified immediate deletion |",
            "",
            "## Memory",
            "",
            "- Vault files were audited read-only; none are eligible for automatic deletion.",
            "- Repo artifacts are removable only when an exact vault copy exists.",
            f"- Disposable caches must be at least {self.min_age_days} days old.",
            "- Safe-delete items may be deleted after fingerprint verification and explicit approval.",
            "- Ambiguous workspace material uses a seven-day quarantine before automatic purge.",
            "- Scheduler setup auto-selects Windows Task Scheduler or Linux systemd/cron.",
        ]

        headings = (
            (DECISION_SAFE_DELETE, "Safe-delete candidates"),
            (DECISION_REVIEW, "Needs review"),
            (DECISION_KEEP_REPO, "Protected local files"),
        )
        for decision, heading in headings:
            matches = sorted(
                (item for item in self.findings if item.decision == decision),
                key=lambda item: (item.scope, item.path.lower()),
            )
            if not matches:
                continue
            lines.extend(["", f"## {heading}", ""])
            for item in matches:
                detail = f"; exact copy: `{item.duplicate_of}`" if item.duplicate_of else ""
                lines.append(f"- `{item.scope}:{item.path}` — {item.reason}{detail}")

        return "\n".join(lines).rstrip() + "\n"


@dataclass
class _RepoArtifact:
    path: Path
    relative: str
    reason_if_unverified: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        return ""


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fingerprint(path: Path) -> str:
    """Hash content and relative names so apply can reject a changed plan."""
    if path.is_symlink():
        raise HousekeepingError(f"Refusing to fingerprint symlink: {path}")
    if path.is_file():
        stat = path.stat()
        return f"file:{stat.st_size}:{_file_hash(path)}"
    if not path.is_dir():
        raise HousekeepingError(f"Unsupported cleanup target: {path}")

    digest = hashlib.sha256()
    file_count = 0
    for root, dirnames, filenames in os.walk(path, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if not (Path(root) / name).is_symlink())
        for filename in sorted(filenames):
            candidate = Path(root) / filename
            if candidate.is_symlink():
                raise HousekeepingError(f"Refusing directory containing symlink: {candidate}")
            relative = candidate.relative_to(path).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(_file_hash(candidate).encode("ascii"))
            file_count += 1
    return f"dir:{file_count}:{digest.hexdigest()}"


def _path_size(path: Path) -> int:
    try:
        if path.is_file():
            return path.stat().st_size
        return sum(
            candidate.stat().st_size
            for candidate in path.rglob("*")
            if candidate.is_file() and not candidate.is_symlink()
        )
    except OSError:
        return 0


def _latest_mtime(path: Path) -> float | None:
    try:
        latest = path.stat().st_mtime
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_symlink():
                    return None
                latest = max(latest, candidate.stat().st_mtime)
        return latest
    except OSError:
        return None


def _is_old_enough(path: Path, min_age_days: int, now: datetime) -> bool:
    latest = _latest_mtime(path)
    if latest is None:
        return False
    cutoff = now - timedelta(days=min_age_days)
    return datetime.fromtimestamp(latest, timezone.utc) <= cutoff


def _within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _git_tracked_files(repo: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return set()
    return {
        item.decode("utf-8", errors="replace").replace("\\", "/")
        for item in result.stdout.split(b"\0")
        if item
    }


def _walk_files(root: Path, excluded_dirs: set[str]) -> Iterable[Path]:
    if not root.is_dir():
        return
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in excluded_dirs and not (Path(current) / name).is_symlink()
        )
        for filename in sorted(filenames):
            candidate = Path(current) / filename
            try:
                if candidate.is_symlink():
                    continue
            except OSError:
                continue
            yield candidate


def _frontmatter_keys(text: str) -> set[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return set()
    keys: set[str] = set()
    for line in lines[1:]:
        if line.strip() == "---":
            return keys
        if ":" in line and not line.startswith((" ", "\t")):
            keys.add(line.split(":", 1)[0].strip())
    return set()


def _protected_vault_note(relative: Path) -> bool:
    return bool(relative.parts and relative.parts[0] in PROTECTED_VAULT_PREFIXES)


def resolve_vault_path(explicit: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env_value = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env_value:
        candidates.append(Path(env_value))
    if os.name == "nt":
        candidates.append(Path(r"D:\Brainiac2"))
    for candidate in candidates:
        expanded = candidate.expanduser().resolve()
        if expanded.is_dir():
            return expanded
    raise HousekeepingError(
        "Vault not found. Pass --vault or set OBSIDIAN_VAULT_PATH; "
        "Windows also checks D:\\Brainiac2."
    )


def _collect_repo_artifacts(repo: Path, tracked: set[str]) -> tuple[list[_RepoArtifact], list[Finding]]:
    artifacts: list[_RepoArtifact] = []
    findings: list[Finding] = []
    workspace = repo / "workspace"
    for candidate in _walk_files(workspace, SAFE_CACHE_DIRS):
        if candidate.name == ".gitkeep" or candidate.suffix.lower() in SAFE_FILE_SUFFIXES:
            continue
        relative = candidate.relative_to(repo).as_posix()
        artifacts.append(_RepoArtifact(
            path=candidate,
            relative=relative,
            reason_if_unverified="temporary workspace output has no exact vault copy",
        ))

    for candidate in sorted(repo.iterdir(), key=lambda path: path.name.lower()):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        relative = candidate.relative_to(repo).as_posix()
        if relative in tracked:
            continue
        if candidate.suffix.lower() in SAFE_FILE_SUFFIXES:
            continue
        if candidate.name in PROTECTED_REPO_FILES:
            findings.append(Finding(
                scope="repo",
                path=relative,
                decision=DECISION_KEEP_REPO,
                reason="protected local configuration or secret material",
                size=_path_size(candidate),
                modified=_iso_mtime(candidate),
            ))
        elif candidate.suffix.lower() in REPO_ARTIFACT_SUFFIXES:
            artifacts.append(_RepoArtifact(
                path=candidate,
                relative=relative,
                reason_if_unverified="loose root artifact has no exact vault copy",
            ))
        else:
            findings.append(Finding(
                scope="repo",
                path=relative,
                decision=DECISION_REVIEW,
                reason="untracked root file is not a recognized disposable artifact",
                size=_path_size(candidate),
                modified=_iso_mtime(candidate),
            ))
    return artifacts, findings


def _collect_cache_findings(
    repo: Path,
    tracked: set[str],
    min_age_days: int,
    now: datetime,
) -> list[Finding]:
    findings: list[Finding] = []
    for current, dirnames, filenames in os.walk(repo, followlinks=False):
        current_path = Path(current)
        if current_path != repo and current_path.name in PROTECTED_REPO_DIRS:
            dirnames[:] = []
            continue

        dirnames[:] = sorted(dirnames)
        filenames = sorted(filenames)

        for dirname in list(dirnames):
            candidate = current_path / dirname
            if dirname in PROTECTED_REPO_DIRS:
                dirnames.remove(dirname)
                continue
            if dirname not in SAFE_CACHE_DIRS:
                continue
            dirnames.remove(dirname)
            relative = candidate.relative_to(repo).as_posix()
            tracked_prefix = relative.rstrip("/") + "/"
            if relative in tracked or any(
                tracked_path.startswith(tracked_prefix) for tracked_path in tracked
            ):
                continue
            old_enough = _is_old_enough(candidate, min_age_days, now)
            fingerprint = ""
            if old_enough:
                try:
                    fingerprint = _fingerprint(candidate)
                except (OSError, HousekeepingError):
                    old_enough = False
            findings.append(Finding(
                scope="repo",
                path=relative,
                decision=DECISION_SAFE_DELETE if old_enough else DECISION_REVIEW,
                reason=(
                    "disposable cache is older than the retention threshold"
                    if old_enough else
                    "disposable cache is recent or could not be inspected"
                ),
                size=_path_size(candidate),
                modified=_iso_mtime(candidate),
                fingerprint=fingerprint,
            ))

        for filename in filenames:
            candidate = current_path / filename
            if candidate.suffix.lower() not in SAFE_FILE_SUFFIXES:
                continue
            relative = candidate.relative_to(repo).as_posix()
            if relative in tracked:
                continue
            old_enough = _is_old_enough(candidate, min_age_days, now)
            fingerprint = ""
            if old_enough:
                try:
                    fingerprint = _fingerprint(candidate)
                except (OSError, HousekeepingError):
                    old_enough = False
            findings.append(Finding(
                scope="repo",
                path=relative,
                decision=DECISION_SAFE_DELETE if old_enough else DECISION_REVIEW,
                reason=(
                    "disposable file is older than the retention threshold"
                    if old_enough else
                    "disposable file is recent or could not be inspected"
                ),
                size=_path_size(candidate),
                modified=_iso_mtime(candidate),
                fingerprint=fingerprint,
            ))
    return findings


def audit_housekeeping(
    repo_path: str | Path,
    vault_path: str | Path,
    *,
    min_age_days: int = 7,
    now: datetime | None = None,
) -> AuditReport:
    if min_age_days < 0:
        raise ValueError("min_age_days must be zero or greater")
    repo = Path(repo_path).resolve()
    vault = Path(vault_path).resolve()
    if not repo.is_dir() or not vault.is_dir():
        raise HousekeepingError("Repo and vault must both be existing directories")
    if repo.parent == repo or vault.parent == vault:
        raise HousekeepingError("Repo and vault cannot be filesystem roots")
    if repo == vault or _within(repo, vault) or _within(vault, repo):
        raise HousekeepingError("Repo and vault must be separate directory trees")

    generated = now or _utc_now()
    tracked = _git_tracked_files(repo)
    artifacts, findings = _collect_repo_artifacts(repo, tracked)
    requested_sizes: set[int] = set()
    for artifact in artifacts:
        try:
            size = artifact.path.stat().st_size
        except OSError:
            continue
        if artifact.path.is_file() and size <= MAX_HASH_BYTES:
            requested_sizes.add(size)

    vault_exact: dict[tuple[int, str], str] = {}
    vault_note_hashes: dict[str, list[str]] = {}
    vault_note_findings: dict[str, Finding] = {}
    for candidate in _walk_files(vault, PROTECTED_VAULT_DIRS):
        relative_path = candidate.relative_to(vault)
        relative = relative_path.as_posix()
        try:
            size = candidate.stat().st_size
        except OSError:
            continue

        digest = ""
        if size <= MAX_HASH_BYTES and (size in requested_sizes or candidate.suffix.lower() == ".md"):
            try:
                digest = _file_hash(candidate)
                vault_exact.setdefault((size, digest), relative)
            except OSError:
                digest = ""

        if candidate.suffix.lower() != ".md":
            continue
        if digest:
            vault_note_hashes.setdefault(digest, []).append(relative)
        try:
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            vault_note_findings[relative] = Finding(
                scope="vault", path=relative, decision=DECISION_REVIEW,
                reason="Markdown note could not be read as UTF-8", size=size,
                modified=_iso_mtime(candidate),
            )
            continue

        if not text.strip():
            decision, reason = DECISION_REVIEW, "empty vault note"
        elif _protected_vault_note(relative_path):
            decision, reason = DECISION_KEEP_VAULT, "protected brand, memory, or session provenance"
        else:
            keys = _frontmatter_keys(text)
            has_date = "created" in keys or "updated" in keys
            missing = sorted(REQUIRED_FINAL_NOTE_KEYS - keys)
            if not has_date:
                missing.append("created-or-updated")
            if missing:
                decision = DECISION_REVIEW
                reason = "final-note metadata missing: " + ", ".join(missing)
            else:
                decision, reason = DECISION_KEEP_VAULT, "durable note has required metadata"
        vault_note_findings[relative] = Finding(
            scope="vault", path=relative, decision=decision, reason=reason,
            size=size, modified=_iso_mtime(candidate),
        )

    for duplicates in vault_note_hashes.values():
        if len(duplicates) < 2:
            continue
        ordered = sorted(
            duplicates,
            key=lambda value: (
                0 if Path(value).parts[0] in PROTECTED_VAULT_PREFIXES else 1,
                len(Path(value).parts),
                value.lower(),
            ),
        )
        canonical = ordered[0]
        for duplicate in ordered[1:]:
            current = vault_note_findings[duplicate]
            current.decision = DECISION_REVIEW
            current.reason = "exact duplicate vault note; choose a canonical note"
            current.duplicate_of = canonical

    for artifact in artifacts:
        try:
            size = artifact.path.stat().st_size
            digest = _file_hash(artifact.path) if size <= MAX_HASH_BYTES else ""
        except OSError:
            findings.append(Finding(
                scope="repo", path=artifact.relative, decision=DECISION_REVIEW,
                reason="artifact could not be read", modified=_iso_mtime(artifact.path),
            ))
            continue
        duplicate = vault_exact.get((size, digest), "") if digest else ""
        if duplicate:
            findings.append(Finding(
                scope="repo", path=artifact.relative, decision=DECISION_SAFE_DELETE,
                reason="temporary repo artifact has an exact byte-for-byte vault copy",
                size=size, modified=_iso_mtime(artifact.path), duplicate_of=duplicate,
                fingerprint=_fingerprint(artifact.path),
            ))
        else:
            findings.append(Finding(
                scope="repo", path=artifact.relative, decision=DECISION_REVIEW,
                reason=artifact.reason_if_unverified, size=size,
                modified=_iso_mtime(artifact.path),
            ))

    findings.extend(_collect_cache_findings(repo, tracked, min_age_days, generated))
    findings.extend(vault_note_findings.values())
    return AuditReport(
        repo=str(repo),
        vault=str(vault),
        generated_at=generated.isoformat(),
        min_age_days=min_age_days,
        findings=findings,
        tracked_repo_files=len(tracked),
    )


def write_plan(report: AuditReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return output.resolve()


def apply_plan(plan_path: str | Path, *, confirm: str) -> dict[str, object]:
    if confirm not in {"quarantine", "delete-safe"}:
        raise HousekeepingError(
            "Apply requires --confirm quarantine or --confirm delete-safe"
        )
    delete_safe = confirm == "delete-safe"
    resolved_plan = Path(plan_path).resolve()
    plan = json.loads(resolved_plan.read_text(encoding="utf-8"))
    if plan.get("schema_version") != 1:
        raise HousekeepingError("Unsupported or missing housekeeping plan schema")
    repo = Path(plan["repo"]).resolve()
    if repo.parent == repo:
        raise HousekeepingError("Plan repo cannot be a filesystem root")
    plans_root = (repo / ".housekeeper" / "plans").resolve()
    if not _within(resolved_plan, plans_root):
        raise HousekeepingError("Plan must be stored under .housekeeper/plans in its repo")
    quarantine_root = (repo / ".housekeeper" / "quarantine").resolve()
    if not _within(quarantine_root, repo) or quarantine_root == repo:
        raise HousekeepingError("Invalid quarantine path")
    batch_name = _utc_now().strftime("%Y%m%dT%H%M%S%fZ")
    batch = quarantine_root / batch_name
    moved: list[str] = []
    deleted: list[str] = []
    skipped: list[str] = []

    for item in plan.get("findings", []):
        if item.get("scope") != "repo" or item.get("decision") != DECISION_SAFE_DELETE:
            continue
        relative = Path(item["path"])
        source = (repo / relative).resolve()
        if not _within(source, repo) or source == repo or _within(source, quarantine_root):
            skipped.append(f"{item['path']}: unsafe path")
            continue
        if not source.exists():
            skipped.append(f"{item['path']}: no longer exists")
            continue
        try:
            current_fingerprint = _fingerprint(source)
        except (OSError, HousekeepingError) as exc:
            skipped.append(f"{item['path']}: {exc}")
            continue
        if not item.get("fingerprint") or current_fingerprint != item["fingerprint"]:
            skipped.append(f"{item['path']}: changed since audit")
            continue
        try:
            if delete_safe:
                if source.is_dir():
                    shutil.rmtree(source)
                else:
                    source.unlink()
                deleted.append(item["path"])
            else:
                destination = batch / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    skipped.append(f"{item['path']}: quarantine collision")
                    continue
                shutil.move(str(source), str(destination))
                moved.append(item["path"])
        except OSError as exc:
            skipped.append(f"{item['path']}: {exc}")

    result: dict[str, object] = {
        "mode": "delete-safe" if delete_safe else "quarantine",
        "batch": "" if delete_safe else str(batch),
        "moved": moved,
        "deleted": deleted,
        "skipped": skipped,
    }
    if delete_safe and (deleted or skipped):
        log_dir = repo / ".housekeeper" / "deletion-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{batch_name}.json"
        result["log"] = str(log_path.resolve())
        log_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elif moved or skipped:
        batch.mkdir(parents=True, exist_ok=True)
        (batch / "manifest.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    return result


def clear_workspace(
    repo_path: str | Path,
    *,
    confirm: str,
    retention_days: int = 7,
) -> dict[str, object]:
    """Quarantine every untracked workspace entry while preserving tracked scaffolding."""
    if confirm != "quarantine-workspace":
        raise HousekeepingError(
            "Workspace cleanup requires --confirm quarantine-workspace"
        )
    if retention_days < 1:
        raise HousekeepingError("Workspace retention must be at least one day")
    repo = Path(repo_path).resolve()
    if not repo.is_dir() or repo.parent == repo:
        raise HousekeepingError("Repo must be an existing non-root directory")
    workspace = (repo / "workspace").resolve()
    if not workspace.is_dir() or not _within(workspace, repo) or workspace.is_symlink():
        raise HousekeepingError("Repo workspace is missing or unsafe")

    tracked = _git_tracked_files(repo)
    tracked_workspace = {
        path for path in tracked
        if path == "workspace" or path.startswith("workspace/")
    }
    quarantine_root = (repo / ".housekeeper" / "quarantine").resolve()
    if not _within(quarantine_root, repo) or quarantine_root == repo:
        raise HousekeepingError("Invalid quarantine path")
    quarantined_at = _utc_now()
    purge_after = quarantined_at + timedelta(days=retention_days)
    batch_name = quarantined_at.strftime("%Y%m%dT%H%M%S%fZ")
    batch = quarantine_root / batch_name
    moved: list[str] = []
    preserved: list[str] = []
    skipped: list[str] = []

    def contains_tracked(relative: str) -> bool:
        prefix = relative.rstrip("/") + "/"
        return relative in tracked_workspace or any(
            tracked_path.startswith(prefix) for tracked_path in tracked_workspace
        )

    def quarantine_entry(source: Path) -> None:
        relative = source.relative_to(repo).as_posix()
        if source.is_symlink():
            skipped.append(f"{relative}: symlink requires manual review")
            return
        if relative in tracked_workspace:
            preserved.append(relative)
            return
        if source.is_dir() and contains_tracked(relative):
            for child in sorted(source.iterdir(), key=lambda path: path.name.lower()):
                quarantine_entry(child)
            return

        destination = batch / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            skipped.append(f"{relative}: quarantine collision")
            return
        shutil.move(str(source), str(destination))
        moved.append(relative)

    for entry in sorted(workspace.iterdir(), key=lambda path: path.name.lower()):
        quarantine_entry(entry)

    remaining = [
        candidate.relative_to(repo).as_posix()
        for candidate in workspace.rglob("*")
        if candidate.is_file() and candidate.name != ".gitkeep"
    ]
    if remaining:
        skipped.extend(f"{path}: workspace cleanup incomplete" for path in remaining)

    result: dict[str, object] = {
        "batch": str(batch),
        "quarantined_at": quarantined_at.isoformat(),
        "purge_after": purge_after.isoformat(),
        "retention_days": retention_days,
        "moved": moved,
        "preserved": preserved,
        "skipped": skipped,
        "workspace_remaining": sorted(remaining),
        "workspace_empty": not remaining,
    }
    if moved or skipped:
        batch.mkdir(parents=True, exist_ok=True)
        (batch / "manifest.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    return result


def purge_quarantine(
    repo_path: str | Path,
    *,
    older_than_days: int,
    confirm: str,
    now: datetime | None = None,
) -> list[str]:
    if confirm != "delete":
        raise HousekeepingError("Purge requires --confirm delete")
    if older_than_days < 1:
        raise HousekeepingError("Quarantine retention must be at least one day")
    repo = Path(repo_path).resolve()
    if repo.parent == repo:
        raise HousekeepingError("Repo cannot be a filesystem root")
    quarantine_root = (repo / ".housekeeper" / "quarantine").resolve()
    if not _within(quarantine_root, repo) or quarantine_root == repo:
        raise HousekeepingError("Invalid quarantine path")
    if not quarantine_root.is_dir():
        return []
    current_time = now or _utc_now()
    cutoff = current_time - timedelta(days=older_than_days)
    purged: list[str] = []
    for batch in sorted(quarantine_root.iterdir()):
        if not batch.is_dir() or batch.is_symlink():
            continue
        purge_after: datetime | None = None
        manifest = batch / "manifest.json"
        if manifest.is_file():
            try:
                payload = json.loads(manifest.read_text(encoding="utf-8"))
                raw_purge_after = payload.get("purge_after")
                if raw_purge_after:
                    purge_after = datetime.fromisoformat(raw_purge_after)
                    if purge_after.tzinfo is None:
                        purge_after = purge_after.replace(tzinfo=timezone.utc)
            except (OSError, ValueError, json.JSONDecodeError):
                purge_after = None
        modified = datetime.fromtimestamp(batch.stat().st_mtime, timezone.utc)
        expired = purge_after <= current_time if purge_after else modified <= cutoff
        if not expired:
            continue
        shutil.rmtree(batch)
        purged.append(batch.name)
    return purged


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agency-housekeeper",
        description="Audit Automata and its vault using conservative cleanup rules.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="Read-only classification and cleanup plan")
    audit.add_argument("--repo", default=".")
    audit.add_argument("--vault")
    audit.add_argument("--min-age-days", type=int, default=7)
    audit.add_argument("--plan", help="Optional JSON plan path")
    audit.add_argument("--report", help="Optional Markdown report path")
    audit.add_argument("--commit-vault", action="store_true", help="Allow --report inside the vault.")
    audit.add_argument("--commit-reason", help="Required reason when committing a report to the vault.")

    apply = subparsers.add_parser(
        "apply", help="Apply fingerprint-verified safe-delete decisions"
    )
    apply.add_argument("--plan", required=True)
    apply.add_argument("--confirm", required=True)

    clear = subparsers.add_parser(
        "clear-workspace",
        help="Quarantine all untracked workspace content and keep tracked scaffolding",
    )
    clear.add_argument("--repo", default=".")
    clear.add_argument("--confirm", required=True)
    clear.add_argument("--retention-days", type=int, default=7)

    triage = subparsers.add_parser(
        "triage", help="Read-only rules-based grouping of an audit plan's review findings"
    )
    triage.add_argument("--plan", required=True)
    triage.add_argument("--report", required=True, help="Markdown output path")
    triage.add_argument("--json", dest="json_out", help="Optional per-file JSON output path")
    triage.add_argument(
        "--advise", action="store_true",
        help="Ask an LLM for advisory suggestions on `review` rows (needs ANTHROPIC_API_KEY; rules still decide)",
    )
    triage.add_argument("--advise-limit", type=int, default=200, help="Max rows sent for advice")

    purge = subparsers.add_parser("purge", help="Permanently remove expired quarantine batches")
    purge.add_argument("--repo", default=".")
    purge.add_argument("--older-than-days", type=int, default=30)
    purge.add_argument("--confirm", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "audit":
            vault = resolve_vault_path(args.vault)
            report = audit_housekeeping(
                args.repo, vault, min_age_days=args.min_age_days
            )
            markdown = report.to_markdown()
            if args.plan:
                print(f"Plan: {write_plan(report, args.plan)}")
            if args.report:
                report_path = Path(args.report).expanduser().resolve()
                if report_path == vault or vault in report_path.parents:
                    require_vault_write(
                        commit_vault=args.commit_vault,
                        commit_reason=args.commit_reason,
                        operation="housekeeping report finalization",
                        target=report_path,
                    )
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(markdown, encoding="utf-8")
                print(f"Report: {report_path.resolve()}")
            else:
                print(markdown, end="")
        elif args.command == "apply":
            print(json.dumps(apply_plan(args.plan, confirm=args.confirm), indent=2))
        elif args.command == "triage":
            from .housekeeping_triage import triage_plan

            backend = log = None
            if args.advise:
                from .config import AgencyConfig
                from .decide import DecisionLog, LLMBackend

                config = AgencyConfig.from_env()
                backend, log = LLMBackend.from_config(config), DecisionLog(config.workspace)
            rows, markdown = triage_plan(args.plan, backend=backend, log=log, advise_limit=args.advise_limit)
            report_path = Path(args.report).expanduser().resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(markdown, encoding="utf-8")
            print(f"Report: {report_path}")
            if args.json_out:
                json_path = Path(args.json_out).expanduser().resolve()
                json_path.parent.mkdir(parents=True, exist_ok=True)
                json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
                print(f"JSON: {json_path}")
        elif args.command == "clear-workspace":
            print(json.dumps(
                clear_workspace(
                    args.repo,
                    confirm=args.confirm,
                    retention_days=args.retention_days,
                ),
                indent=2,
            ))
        else:
            purged = purge_quarantine(
                args.repo,
                older_than_days=args.older_than_days,
                confirm=args.confirm,
            )
            print(json.dumps({"purged": purged}, indent=2))
    except (HousekeepingError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Housekeeper: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
