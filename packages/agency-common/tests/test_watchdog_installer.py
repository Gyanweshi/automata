"""Scheduling plans for the nightly jobs: the same Python job on Windows and Linux, no shell scripts."""
import shutil
import uuid
from pathlib import Path

import pytest

from agency_common.scheduled_jobs import JOBS, build_plan, cron_line, normalize_system
from agency_common.watchdog_installer import WatchdogInstallError


@pytest.fixture
def repo():
    path = Path.cwd() / "workspace" / f"watchdog-installer-test-{uuid.uuid4().hex}" / "repo"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path.parent, ignore_errors=True)


def test_windows_registers_the_python_job_in_task_scheduler(repo, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _name: "powershell.exe")
    plan = build_plan("housekeeper", repo=repo, system_name="Windows", daily_at="03:15", retention_days=7)

    assert plan.adapter == "windows-task-scheduler"
    command = plan.commands[0]
    assert command[0] == "powershell.exe"
    script = command[-1]
    assert "Register-ScheduledTask -TaskName 'Automata Housekeeper'" in script
    assert "schedule.py run housekeeper --retention-days 7" in script
    assert "'03:15'" in script
    assert ".ps1" not in script and ".sh" not in script


def test_linux_systemd_runs_the_python_job_from_the_repo(repo):
    plan = build_plan("vault-index", repo=repo, system_name="Linux", use_systemd=True)

    assert plan.adapter == "linux-systemd-user"
    service = next(v for k, v in plan.files.items() if k.endswith("automata-vault-index.service"))
    timer = next(v for k, v in plan.files.items() if k.endswith("automata-vault-index.timer"))
    assert f"WorkingDirectory={repo.resolve()}\n" in service
    assert "schedule.py\" \"run\" \"vault-index\"" in service
    assert ".sh" not in service
    assert "OnCalendar=*-*-* 02:30:00" in timer


def test_cron_line_quotes_paths_and_marks_the_job(tmp_path):
    repo = tmp_path / "my repo"
    line = cron_line(JOBS["housekeeper"], repo, "04:05", 9)
    assert line.startswith("5 4 * * * cd ")
    assert "'" in line  # the space in the path is quoted
    assert line.endswith("--retention-days 9 # automata-housekeeper")


def test_unsupported_system_fails_instead_of_guessing():
    with pytest.raises(WatchdogInstallError, match="Unsupported operating system"):
        normalize_system("Plan9")


@pytest.mark.parametrize("daily_at", ["3:00", "24:00", "12:60", "bad"])
def test_invalid_daily_time_is_rejected(repo, daily_at):
    with pytest.raises(WatchdogInstallError, match="HH:MM"):
        build_plan("housekeeper", repo=repo, system_name="Linux", daily_at=daily_at, use_systemd=True)
