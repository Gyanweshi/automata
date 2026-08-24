"""Platform dispatcher for the Automata housekeeping scheduler."""
from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


class WatchdogInstallError(RuntimeError):
    """Raised when no supported native scheduler can be selected."""


def normalize_system(system_name: str | None = None) -> str:
    detected = (system_name or platform.system()).strip().lower()
    if detected == "windows":
        return "windows"
    if detected == "linux":
        return "linux"
    raise WatchdogInstallError(
        f"Unsupported operating system: {system_name or platform.system()}. "
        "Supported systems are Windows and Linux."
    )


def build_install_command(
    repo_path: str | Path,
    *,
    system_name: str | None = None,
    daily_at: str = "03:00",
    retention_days: int = 7,
) -> tuple[str, list[str]]:
    repo = Path(repo_path).resolve()
    if not repo.is_dir() or repo.parent == repo:
        raise WatchdogInstallError("Repo must be an existing non-root directory")
    if retention_days < 1:
        raise WatchdogInstallError("Retention must be at least one day")
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", daily_at):
        raise WatchdogInstallError("Daily time must use HH:MM")

    system = normalize_system(system_name)
    if system == "windows":
        installer = repo / "scripts" / "install-housekeeper-watchdog.ps1"
        executable = shutil.which("powershell.exe") or "powershell.exe"
        command = [
            executable,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(installer),
            "-DailyAt",
            daily_at,
            "-RetentionDays",
            str(retention_days),
        ]
        return "windows-task-scheduler", command

    installer = repo / "scripts" / "install-housekeeper-watchdog.sh"
    executable = shutil.which("bash") or "/bin/bash"
    command = [
        executable,
        str(installer),
        "--daily-at",
        daily_at,
        "--retention-days",
        str(retention_days),
    ]
    return "linux-systemd-or-cron", command


def _default_repo() -> Path:
    return Path(__file__).resolve().parents[4]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agency-housekeeper-install",
        description="Install the native housekeeping scheduler for this machine.",
    )
    parser.add_argument("--repo", default=str(_default_repo()))
    parser.add_argument("--daily-at", default="03:00")
    parser.add_argument("--retention-days", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        adapter, command = build_install_command(
            args.repo,
            daily_at=args.daily_at,
            retention_days=args.retention_days,
        )
        if args.dry_run:
            print(json.dumps({"adapter": adapter, "command": command}, indent=2))
            return 0
        print(f"Detected adapter: {adapter}")
        subprocess.run(command, check=True)
    except (WatchdogInstallError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Watchdog installer: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
