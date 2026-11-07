"""Setup freshness, post-pull hooks and legacy cleanup (scripts/setup_state.py, scripts/bootstrap.py)."""
import importlib.util
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup_state = load("setup_state")
bootstrap = load("bootstrap")


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "uv.lock").write_text("lock v1\n", encoding="utf-8")
    (tmp_path / "dependencies.toml").write_text("deps\n", encoding="utf-8")
    return tmp_path


def test_stamp_tracks_setup_inputs(repo):
    assert setup_state.is_stale(repo)  # never set up
    setup_state.record(repo)
    assert not setup_state.is_stale(repo) and setup_state.stale_message(repo) is None
    (repo / "uv.lock").write_text("lock v2\n", encoding="utf-8")
    assert setup_state.is_stale(repo)
    assert "changed since this machine was last set up" in setup_state.stale_message(repo)


def test_stamp_ignores_line_endings(repo):
    setup_state.record(repo)
    (repo / "uv.lock").write_bytes(b"lock v1\r\n")  # same file checked out on Windows
    assert not setup_state.is_stale(repo)


def test_after_pull_is_a_no_op_when_fresh(repo, monkeypatch):
    setup_state.record(repo)
    monkeypatch.setattr(setup_state.subprocess, "run", lambda *a, **k: pytest.fail("bootstrap must not run"))
    assert setup_state.after_pull(repo) == 0


def test_after_pull_reruns_bootstrap_and_never_fails_the_pull(repo, monkeypatch):
    calls = []

    class Result:
        returncode = 1

    monkeypatch.setattr(setup_state.subprocess, "run", lambda cmd, **k: calls.append(cmd) or Result())
    assert setup_state.after_pull(repo) == 0
    assert calls and calls[0][-2:] == ["--yes", "--auto-schedules"]


def test_hooks_install_and_keep_foreign_hooks(repo):
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    (hooks / "post-rewrite").write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
    notes = setup_state.install_hooks(repo)
    assert setup_state.HOOK_MARKER in (hooks / "post-merge").read_text(encoding="utf-8")
    assert (hooks / "post-rewrite").read_text(encoding="utf-8") == "#!/bin/sh\necho mine\n"
    assert any("post-rewrite" in n for n in notes)
    assert b"\r\n" not in (hooks / "post-merge").read_bytes()  # sh needs LF even on Windows


def test_legacy_cleanup_removes_junk_and_keeps_env(repo):
    legacy = repo / "agents" / "openedswarm_core"
    (legacy / ".venv" / "lib").mkdir(parents=True)
    (legacy / ".venv" / "lib" / "x.py").write_text("x", encoding="utf-8")
    (legacy / "tools" / "__pycache__").mkdir(parents=True)
    (legacy / "tools" / "__pycache__" / "a.pyc").write_bytes(b"0")
    (legacy / "server_background.log").write_text("log", encoding="utf-8")
    (legacy / ".env").write_text("KEY=1", encoding="utf-8")
    notes = bootstrap.clean_legacy(repo)
    assert (legacy / ".env").exists() and not (legacy / ".venv").exists()
    assert not (legacy / "server_background.log").exists()
    assert any(".env" in n for n in notes)
    (legacy / ".env").unlink()
    bootstrap.clean_legacy(repo)
    assert not legacy.exists()
