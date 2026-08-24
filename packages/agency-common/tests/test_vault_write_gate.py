from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from agency_common.obsidian_writer import log_agent_session, update_brand_memory
from agency_common.vault_write_gate import VaultWriteBlockedError, require_vault_write


@pytest.fixture
def local_test_dir():
    path = Path.cwd() / "workspace" / f"vault-gate-test-{uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_gate_denies_missing_one_shot_commit():
    with pytest.raises(VaultWriteBlockedError, match="explicit commit_vault=True"):
        require_vault_write(
            commit_vault=False,
            commit_reason=None,
            operation="test write",
        )


def test_gate_denies_commit_without_reason():
    with pytest.raises(VaultWriteBlockedError, match="non-empty commit reason"):
        require_vault_write(
            commit_vault=True,
            commit_reason="  ",
            operation="test write",
        )


def test_session_logger_does_not_touch_vault_by_default(local_test_dir, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(local_test_dir))

    with pytest.raises(VaultWriteBlockedError):
        log_agent_session("Agent", "Task", "Transcript")

    assert not (local_test_dir / "Agent_Sessions").exists()


def test_explicit_session_commit_writes_once(local_test_dir, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(local_test_dir))

    output = log_agent_session(
        "Agent",
        "Approved task",
        "Final transcript",
        commit_vault=True,
        commit_reason="User approved final output",
    )

    assert output.is_file()
    assert len(list((local_test_dir / "Agent_Sessions").glob("*.md"))) == 1


def test_brand_memory_requires_explicit_finalization(local_test_dir):
    brands = local_test_dir / "Brands"
    brands.mkdir()
    note = brands / "maple.md"
    note.write_text("# Maple\n\n## Memory\n", encoding="utf-8")

    with pytest.raises(VaultWriteBlockedError):
        update_brand_memory("maple", "draft insight", vault_path=local_test_dir)
    assert "draft insight" not in note.read_text(encoding="utf-8")

    assert update_brand_memory(
        "maple",
        "approved insight",
        vault_path=local_test_dir,
        commit_vault=True,
        commit_reason="User approved final output",
    )
    assert "approved insight" in note.read_text(encoding="utf-8")
