import json
import os
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agency_common.housekeeping import (
    DECISION_KEEP_VAULT,
    DECISION_REVIEW,
    DECISION_SAFE_DELETE,
    HousekeepingError,
    apply_plan,
    audit_housekeeping,
    clear_workspace,
    purge_quarantine,
    write_plan,
)
from agency_common import housekeeping


NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def sandbox_path():
    """Use a workspace temp because the managed Windows temp ACL rejects pytest's 0700 dirs."""
    path = Path.cwd() / "workspace" / f"housekeeper-test-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _finding(report, scope: str, path: str):
    return next(item for item in report.findings if item.scope == scope and item.path == path)


def test_exact_workspace_copy_is_safe_delete(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    (repo / "workspace" / "maple" / "content").mkdir(parents=True)
    (vault / "Deliverables").mkdir(parents=True)
    body = "---\ntype: caption\nstatus: final\ncreated: 2026-08-21\ntags: [maple]\n---\nDone\n"
    source = repo / "workspace" / "maple" / "content" / "caption.md"
    source.write_text(body, encoding="utf-8")
    (vault / "Deliverables" / "caption.md").write_text(body, encoding="utf-8")

    report = audit_housekeeping(repo, vault, now=NOW)

    finding = _finding(report, "repo", "workspace/maple/content/caption.md")
    assert finding.decision == DECISION_SAFE_DELETE
    assert finding.duplicate_of == "Deliverables/caption.md"
    assert finding.fingerprint


def test_unverified_workspace_output_requires_review(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    (repo / "workspace").mkdir(parents=True)
    vault.mkdir()
    (repo / "workspace" / "only-local.md").write_text("draft", encoding="utf-8")

    report = audit_housekeeping(repo, vault, now=NOW)

    finding = _finding(report, "repo", "workspace/only-local.md")
    assert finding.decision == DECISION_REVIEW
    assert "no exact vault copy" in finding.reason


def test_vault_notes_are_never_safe_delete(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    repo.mkdir()
    (vault / "Brands").mkdir(parents=True)
    (vault / "Notes").mkdir()
    (vault / "Brands" / "maple.md").write_text("# Maple", encoding="utf-8")
    (vault / "Notes" / "loose.md").write_text("# No frontmatter", encoding="utf-8")

    report = audit_housekeeping(repo, vault, now=NOW)

    assert _finding(report, "vault", "Brands/maple.md").decision == DECISION_KEEP_VAULT
    assert _finding(report, "vault", "Notes/loose.md").decision == DECISION_REVIEW
    assert all(
        item.decision != DECISION_SAFE_DELETE
        for item in report.findings
        if item.scope == "vault"
    )


def test_old_cache_is_safe_delete_but_recent_cache_is_review(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    old_cache = repo / "packages" / "one" / "__pycache__"
    recent_cache = repo / "packages" / "two" / ".pytest_cache"
    old_cache.mkdir(parents=True)
    recent_cache.mkdir(parents=True)
    old_file = old_cache / "a.pyc"
    recent_file = recent_cache / "state"
    old_file.write_bytes(b"old")
    recent_file.write_bytes(b"new")
    vault.mkdir()
    old_timestamp = (NOW - timedelta(days=20)).timestamp()
    recent_timestamp = (NOW - timedelta(days=1)).timestamp()
    for path in (old_file, old_cache):
        os.utime(path, (old_timestamp, old_timestamp))
    os.utime(recent_file, (recent_timestamp, recent_timestamp))
    os.utime(recent_cache, (recent_timestamp, recent_timestamp))

    report = audit_housekeeping(repo, vault, min_age_days=7, now=NOW)

    assert _finding(report, "repo", "packages/one/__pycache__").decision == DECISION_SAFE_DELETE
    assert _finding(report, "repo", "packages/two/.pytest_cache").decision == DECISION_REVIEW


def test_safe_file_is_classified_once(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    repo.mkdir()
    vault.mkdir()
    stackdump = repo / "bash.exe.stackdump"
    stackdump.write_bytes(b"crash")
    old_timestamp = (NOW - timedelta(days=20)).timestamp()
    os.utime(stackdump, (old_timestamp, old_timestamp))

    report = audit_housekeeping(repo, vault, min_age_days=7, now=NOW)

    matches = [item for item in report.findings if item.path == "bash.exe.stackdump"]
    assert len(matches) == 1
    assert matches[0].decision == DECISION_SAFE_DELETE


def test_tracked_disposable_file_is_never_safe_delete(monkeypatch, sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    repo.mkdir()
    vault.mkdir()
    stackdump = repo / "bash.exe.stackdump"
    stackdump.write_bytes(b"tracked crash")
    old_timestamp = (NOW - timedelta(days=20)).timestamp()
    os.utime(stackdump, (old_timestamp, old_timestamp))
    monkeypatch.setattr(
        housekeeping,
        "_git_tracked_files",
        lambda _repo: {"bash.exe.stackdump"},
    )

    report = audit_housekeeping(repo, vault, min_age_days=7, now=NOW)

    matches = [item for item in report.findings if item.path == "bash.exe.stackdump"]
    assert matches == []
    assert report.counts()["keep-repo"] == 1


def test_apply_moves_unchanged_candidate_to_quarantine(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    (repo / "workspace").mkdir(parents=True)
    vault.mkdir()
    source = repo / "workspace" / "copy.md"
    vault_copy = vault / "copy.md"
    source.write_text("same", encoding="utf-8")
    vault_copy.write_text("same", encoding="utf-8")
    report = audit_housekeeping(repo, vault, now=NOW)
    plan = write_plan(report, repo / ".housekeeper" / "plans" / "test.json")

    result = apply_plan(plan, confirm="quarantine")

    assert result["moved"] == ["workspace/copy.md"]
    assert not source.exists()
    assert (Path(result["batch"]) / "workspace" / "copy.md").exists()
    assert vault_copy.exists()


def test_apply_can_permanently_delete_verified_safe_candidate(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    (repo / "workspace").mkdir(parents=True)
    vault.mkdir()
    source = repo / "workspace" / "copy.md"
    source.write_text("same", encoding="utf-8")
    (vault / "copy.md").write_text("same", encoding="utf-8")
    report = audit_housekeeping(repo, vault, now=NOW)
    plan = write_plan(report, repo / ".housekeeper" / "plans" / "test.json")

    result = apply_plan(plan, confirm="delete-safe")

    assert result["deleted"] == ["workspace/copy.md"]
    assert not source.exists()
    assert (vault / "copy.md").exists()
    assert Path(result["log"]).exists()


def test_apply_skips_candidate_changed_after_audit(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    (repo / "workspace").mkdir(parents=True)
    vault.mkdir()
    source = repo / "workspace" / "copy.md"
    source.write_text("same", encoding="utf-8")
    (vault / "copy.md").write_text("same", encoding="utf-8")
    report = audit_housekeeping(repo, vault, now=NOW)
    plan = write_plan(report, repo / ".housekeeper" / "plans" / "test.json")
    source.write_text("changed", encoding="utf-8")

    result = apply_plan(plan, confirm="quarantine")

    assert result["moved"] == []
    assert "changed since audit" in result["skipped"][0]
    assert source.exists()


def test_apply_rejects_plan_outside_repo_plan_directory(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    repo.mkdir()
    vault.mkdir()
    report = audit_housekeeping(repo, vault, now=NOW)
    plan = write_plan(report, sandbox_path / "outside-plan.json")

    with pytest.raises(HousekeepingError, match=".housekeeper/plans"):
        apply_plan(plan, confirm="quarantine")


def test_clear_workspace_preserves_tracked_scaffolding_and_quarantines_rest(
    monkeypatch, sandbox_path
):
    repo = sandbox_path / "repo"
    workspace = repo / "workspace"
    (workspace / "content" / "example-brand").mkdir(parents=True)
    (workspace / "research").mkdir()
    (workspace / "shriram").mkdir()
    (workspace / "content" / ".gitkeep").write_text("", encoding="utf-8")
    (workspace / "research" / ".gitkeep").write_text("", encoding="utf-8")
    (workspace / "content" / "example-brand" / "draft.md").write_text(
        "draft", encoding="utf-8"
    )
    (workspace / "shriram" / "qa.png").write_bytes(b"qa")
    monkeypatch.setattr(
        housekeeping,
        "_git_tracked_files",
        lambda _repo: {
            "workspace/content/.gitkeep",
            "workspace/research/.gitkeep",
        },
    )

    result = clear_workspace(repo, confirm="quarantine-workspace")

    assert (workspace / "content" / ".gitkeep").exists()
    assert (workspace / "research" / ".gitkeep").exists()
    assert not (workspace / "content" / "example-brand").exists()
    assert not (workspace / "shriram").exists()
    batch = Path(result["batch"])
    assert (batch / "workspace" / "content" / "example-brand" / "draft.md").exists()
    assert (batch / "workspace" / "shriram" / "qa.png").exists()
    assert sorted(result["preserved"]) == [
        "workspace/content/.gitkeep",
        "workspace/research/.gitkeep",
    ]
    manifest = json.loads((batch / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["retention_days"] == 7
    assert manifest["purge_after"].startswith("20")


def test_purge_uses_manifest_expiry_when_present(sandbox_path):
    repo = sandbox_path / "repo"
    batch = repo / ".housekeeper" / "quarantine" / "old-batch"
    batch.mkdir(parents=True)
    (batch / "artifact.txt").write_text("old", encoding="utf-8")
    (batch / "manifest.json").write_text(
        json.dumps({"purge_after": "2026-08-20T12:00:00+00:00"}),
        encoding="utf-8",
    )

    purged = purge_quarantine(
        repo,
        older_than_days=7,
        confirm="delete",
        now=NOW,
    )

    assert purged == ["old-batch"]
    assert not batch.exists()


def test_report_has_required_vault_metadata_and_short_memory(sandbox_path):
    repo = sandbox_path / "repo"
    vault = sandbox_path / "vault"
    repo.mkdir()
    vault.mkdir()

    markdown = audit_housekeeping(repo, vault, now=NOW).to_markdown()

    assert "type: housekeeping-report" in markdown
    assert "status: complete" in markdown
    assert "created: 2026-08-21" in markdown
    assert "tags: [automata, housekeeping, watchdog]" in markdown
    memory = markdown.split("## Memory", 1)[1]
    memory = memory.split("\n## ", 1)[0]
    assert len([line for line in memory.splitlines() if line.startswith("-")]) <= 10
