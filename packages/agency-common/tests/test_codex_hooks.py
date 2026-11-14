"""Codex silently skips hooks whose approval is stale: the check must say so, and only a person may approve."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("codex_hooks", ROOT / "scripts/codex_hooks.py")
codex_hooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codex_hooks)

REPO_HOOKS = str(codex_hooks.HOOKS_FILE)


def hook(event, status, source="project", path=REPO_HOOKS):
    return {"key": f"{path}:{event}:0:0", "eventName": event, "trustStatus": status, "source": source,
            "sourcePath": path, "currentHash": f"sha256:{event}", "command": "node -e ..."}


class FakeServer:
    def __init__(self, hooks):
        self.hooks, self.writes = hooks, []

    def request(self, method, params):
        if method == "hooks/list":
            return {"data": [{"cwd": str(ROOT), "hooks": self.hooks}]}
        if method == "config/value/write":
            self.writes.append(params)
            for h in self.hooks:
                if h["key"] in params["value"]:
                    h["trustStatus"] = "trusted"
            return {}
        raise AssertionError(method)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass


@pytest.fixture
def server(monkeypatch):
    fake = FakeServer([hook("preToolUse", "modified"), hook("sessionStart", "trusted"),
                       hook("userPromptSubmit", "trusted", source="user", path="/elsewhere/hooks.json")])
    monkeypatch.setattr(codex_hooks.shutil, "which", lambda name: "codex")
    monkeypatch.setattr(codex_hooks, "AppServer", lambda codex: fake)
    monkeypatch.setattr(codex_hooks, "hooks_file_committed", lambda: True)
    return fake


def test_only_this_repos_project_hooks_count(server):
    assert [h["eventName"] for h in codex_hooks.repo_hooks(server)] == ["preToolUse", "sessionStart"]


def test_check_names_the_skipped_hook(server, capsys):
    assert codex_hooks.main(["--check"]) == 1
    assert "preToolUse (modified)" in capsys.readouterr().err
    assert server.writes == []


def test_trust_refuses_without_a_person_at_a_terminal(server, monkeypatch):
    monkeypatch.setattr(codex_hooks.sys.stdin, "isatty", lambda: False, raising=False)
    assert codex_hooks.main(["--trust"]) == 1
    assert server.writes == []


def test_trust_refuses_uncommitted_hooks(server, monkeypatch):
    monkeypatch.setattr(codex_hooks, "hooks_file_committed", lambda: False)
    monkeypatch.setattr(codex_hooks.sys.stdin, "isatty", lambda: True, raising=False)
    assert codex_hooks.main(["--trust"]) == 1
    assert server.writes == []


def test_trust_writes_only_stale_hooks_after_yes(server, monkeypatch):
    monkeypatch.setattr(codex_hooks.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    assert codex_hooks.main(["--trust"]) == 0
    assert server.writes == [{"keyPath": "hooks.state", "mergeStrategy": "upsert",
                              "value": {f"{REPO_HOOKS}:preToolUse:0:0": {"trusted_hash": "sha256:preToolUse"}}}]


def test_trust_respects_no(server, monkeypatch):
    monkeypatch.setattr(codex_hooks.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert codex_hooks.main(["--trust"]) == 1
    assert server.writes == []


def test_no_codex_installed_is_not_an_error(monkeypatch):
    monkeypatch.setattr(codex_hooks.shutil, "which", lambda name: None)
    assert codex_hooks.main(["--check"]) == 0
