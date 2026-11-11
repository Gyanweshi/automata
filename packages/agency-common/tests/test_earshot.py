"""Portable launcher and shared client contract checks (no model downloads)."""
import importlib.util
import json
from pathlib import Path
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("earshot_runner", ROOT / "scripts/earshot.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.mark.parametrize("platform,relative", [
    ("win32", "Scripts/python.exe"), ("linux", "bin/python"), ("darwin", "bin/python"),
])
def test_interpreter_layout(tmp_path, platform, relative):
    assert runner.python_path(tmp_path, platform) == tmp_path / relative


@pytest.mark.parametrize("pin", ["main", "../escape", "a" * 39, "A" * 40])
def test_rejects_unpinned_or_escaping_source(tmp_path, pin):
    with pytest.raises(ValueError):
        runner.environment_path(tmp_path, pin)


def test_clients_launch_identical_server():
    claude = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["earshot"]
    codex = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))["mcp_servers"]["earshot"]
    storyboard = json.loads((ROOT / "mcp/agents/storyboard.json").read_text(encoding="utf-8"))["mcpServers"]["earshot"]
    for field in ("command", "args", "env"):
        assert claude[field] == codex[field] == storyboard[field]


def test_missing_install_does_not_download(tmp_path, monkeypatch):
    (tmp_path / "dependencies.toml").write_text(
        '[[dependency]]\nid="earshot"\npin="' + "a" * 40 + '"\n', encoding="utf-8")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="deps.py install earshot"):
        runner.main(["mcp"])
