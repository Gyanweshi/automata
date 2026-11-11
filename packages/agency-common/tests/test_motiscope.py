"""Portable checks for the optional motion analyzer's pin boundary."""
import importlib.util
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("motiscope_runner", ROOT / "scripts/motiscope.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.mark.parametrize("pin", ["main", "../escape", "a" * 39, "z" * 40])
def test_install_path_rejects_unpinned_or_unsafe_revisions(tmp_path, pin):
    with pytest.raises(ValueError):
        runner.install_path(tmp_path, pin)


def test_checkout_verification_rejects_wrong_revision_and_modified_code(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()

    git("init")
    (tmp_path / "bin").mkdir()
    launcher = tmp_path / "bin/motiscope"
    launcher.write_text("# original\n", encoding="utf-8")
    git("add", "bin/motiscope")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-m", "fixture")
    pin = git("rev-parse", "HEAD")
    runner.verify(tmp_path, pin)
    with pytest.raises(ValueError, match="registered pin"):
        runner.verify(tmp_path, "0" * 40)
    launcher.write_text("# changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="modified tracked"):
        runner.verify(tmp_path, pin)
