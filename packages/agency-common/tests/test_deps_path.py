"""deps.py judges the machine by a fresh terminal's PATH, so just-installed tools don't look missing."""
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("deps_path", ROOT / "scripts" / "deps.py")
deps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deps)


def test_refresh_path_adds_user_tool_dirs_and_keeps_existing(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "nolocal"))
    monkeypatch.setenv("PATH", os.pathsep.join(["/already/here", "/already/here"]))
    deps.refresh_path()
    parts = os.environ["PATH"].split(os.pathsep)
    assert str(home / ".local" / "bin") in parts
    assert parts.count("/already/here") == 1


def test_path_dirs_come_from_the_manifest_per_os(monkeypatch, tmp_path):
    monkeypatch.setattr(deps, "os_key", lambda: "windows")
    monkeypatch.setenv("TOOLROOT", str(tmp_path))
    dep = {"id": "x", "path_dirs": {"windows": ["$TOOLROOT/app/bin"]}}
    assert deps.path_dirs(dep) == [tmp_path / "app" / "bin"]
    monkeypatch.setattr(deps, "os_key", lambda: "linux")
    assert deps.path_dirs(dep) == []
    assert deps.persist_user_path(tmp_path / "missing") is False  # never writes PATH for a folder that isn't there
