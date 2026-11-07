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
