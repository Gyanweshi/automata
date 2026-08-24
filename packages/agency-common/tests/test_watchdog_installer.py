import shutil
import uuid
from pathlib import Path

import pytest

from agency_common.watchdog_installer import (
    WatchdogInstallError,
    build_install_command,
    normalize_system,
)


@pytest.fixture
def sandbox_path():
    path = Path.cwd() / "workspace" / f"watchdog-installer-test-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_windows_selects_only_powershell_adapter(sandbox_path, monkeypatch):
    repo = sandbox_path / "repo"
    repo.mkdir()
    monkeypatch.setattr("shutil.which", lambda _name: "powershell.exe")

    adapter, command = build_install_command(
        repo,
        system_name="Windows",
        daily_at="03:15",
        retention_days=7,
    )

    assert adapter == "windows-task-scheduler"
    assert command[0] == "powershell.exe"
    assert str(repo / "scripts" / "install-housekeeper-watchdog.ps1") in command
    assert not any(item.endswith(".sh") for item in command)


def test_linux_selects_only_bash_adapter(sandbox_path, monkeypatch):
    repo = sandbox_path / "repo"
    repo.mkdir()
    monkeypatch.setattr("shutil.which", lambda _name: "/bin/bash")

    adapter, command = build_install_command(
        repo,
        system_name="Linux",
        daily_at="04:30",
        retention_days=9,
    )

    assert adapter == "linux-systemd-or-cron"
    assert command[0] == "/bin/bash"
    assert str(repo / "scripts" / "install-housekeeper-watchdog.sh") in command
    assert not any(item.endswith(".ps1") for item in command)


def test_unsupported_system_fails_instead_of_guessing():
    with pytest.raises(WatchdogInstallError, match="Unsupported operating system"):
        normalize_system("Plan9")


@pytest.mark.parametrize("daily_at", ["3:00", "24:00", "12:60", "bad"])
def test_invalid_daily_time_is_rejected(sandbox_path, daily_at):
    repo = sandbox_path / "repo"
    repo.mkdir()

    with pytest.raises(WatchdogInstallError, match="HH:MM"):
        build_install_command(repo, system_name="Linux", daily_at=daily_at)
