"""Install the housekeeping watchdog with this machine's native scheduler.

Kept as the `agency-housekeeper-install` entry point; the work is done by agency_common.scheduled_jobs, which
schedules the same Python job on Linux (systemd user timer or cron) and Windows (Task Scheduler).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from agency_common.scheduled_jobs import JOBS, REPO, ScheduleError, apply_plan, build_plan, normalize_system

WatchdogInstallError = ScheduleError

__all__ = ["WatchdogInstallError", "build_plan", "normalize_system", "main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agency-housekeeper-install",
        description="Install the native housekeeping scheduler for this machine.",
    )
    parser.add_argument("--repo", default=str(REPO))
    parser.add_argument("--daily-at", default="03:00")
    parser.add_argument("--retention-days", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        plan = build_plan("housekeeper", repo=Path(args.repo), daily_at=args.daily_at,
                          retention_days=args.retention_days)
        if args.dry_run:
            print(json.dumps({"adapter": plan.adapter, "files": plan.files, "commands": plan.commands}, indent=2))
            return 0
        print(f"Detected adapter: {plan.adapter}")
        apply_plan(plan, JOBS["housekeeper"])
    except (ScheduleError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Watchdog installer: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
