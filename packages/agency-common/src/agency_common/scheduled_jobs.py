"""Nightly jobs (vault index rebuild, housekeeper purge): run them and schedule them on Linux or Windows.

One implementation for both machines. `run` executes a job with logging under .housekeeper/logs; `install`
registers it with the native scheduler (systemd user timer, else cron, on Linux; Task Scheduler on Windows),
always calling `scripts/schedule.py run JOB` with the repo's venv Python, so no shell script is involved.

    python scripts/schedule.py run vault-index
    python scripts/schedule.py install vault-index [--daily-at 02:30]
    python scripts/schedule.py install housekeeper [--daily-at 03:00] [--retention-days 7]
    python scripts/schedule.py install housekeeper --dry-run     # print what would be registered
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import shlex
import shutil
import subprocess  # nosec B404 - runs the repo's own Python and the OS scheduler
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Job:
    name: str
    module: str
    args: tuple[str, ...]
    log_name: str
    default_time: str
    timeout_minutes: int
    description: str
    unit: str  # systemd unit / cron marker name
    task: str  # Windows Task Scheduler name
    log_filter: str | None = None  # keep only matching output lines in the log
    nice: bool = False


JOBS: dict[str, Job] = {
    "vault-index": Job(
        name="vault-index",
        module="agency_common.obsidian_vector_index",
        args=(),
        log_name="vault-index.log",
        default_time="02:30",
        timeout_minutes=30,
        description="Rebuilds the Automata Second Brain vector index from the Obsidian vault.",
        unit="automata-vault-index",
        task="Automata Vault Index",
        log_filter=r"^(INFO|WARNING|ERROR)",
        nice=True,
    ),
    "housekeeper": Job(
        name="housekeeper",
        module="agency_common.housekeeping",
        args=("purge", "--repo", "{repo}", "--older-than-days", "{retention_days}", "--confirm", "delete"),
        log_name="watchdog.log",
        default_time="03:00",
        timeout_minutes=10,
        description="Purges Automata quarantine batches after the retention period.",
        unit="automata-housekeeper",
        task="Automata Housekeeper",
    ),
}


class ScheduleError(RuntimeError):
    """Bad input, or no usable scheduler on this machine."""


def normalize_system(system_name: str | None = None) -> str:
    detected = (system_name or platform.system()).strip().lower()
    if detected in ("windows", "linux"):
        return detected
    raise ScheduleError(f"Unsupported operating system: {system_name or platform.system()}. "
                        "Supported systems are Windows and Linux.")


def validate(daily_at: str, retention_days: int) -> None:
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", daily_at):
        raise ScheduleError("Daily time must use HH:MM")
    if retention_days < 1:
        raise ScheduleError("Retention must be at least one day")


def venv_python(repo: Path, system: str, windowless: bool = False) -> Path:
    if system == "windows":
        scripts = repo / ".venv" / "Scripts"
        return scripts / "pythonw.exe" if windowless and (scripts / "pythonw.exe").exists() else scripts / "python.exe"
    return repo / ".venv" / "bin" / "python"


def job_command(job: Job, repo: Path, system: str, retention_days: int) -> list[str]:
    command = [str(venv_python(repo, system, windowless=True)), str(repo / "scripts" / "schedule.py"), "run", job.name]
    if "{retention_days}" in job.args:
        command += ["--retention-days", str(retention_days)]
    return command


# ---------------------------------------------------------------- run

def run_job(job_name: str, *, repo: Path = REPO, retention_days: int = 7) -> int:
    job = JOBS[job_name]
    log_dir = repo / ".housekeeper" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / job.log_name
    args = [a.format(repo=repo, retention_days=retention_days) for a in job.args]
    env = dict(os.environ)
    source = str(repo / "packages" / "agency-common" / "src")
    env["PYTHONPATH"] = os.pathsep.join(p for p in (source, env.get("PYTHONPATH")) if p)
    started = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    # cwd = repo: the vault path comes from .env, which is looked up from the working directory
    result = subprocess.run([sys.executable, "-m", job.module, *args], cwd=repo, env=env,  # nosec B603
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = (result.stdout + result.stderr).splitlines()
    kept = [line for line in output if re.match(job.log_filter, line)] if job.log_filter else output
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"[{started}] exit={result.returncode}\n")
        log.writelines(line + "\n" for line in kept)
    if result.returncode != 0:
        print("\n".join(output[-20:]), file=sys.stderr)
        print(f"{job.name} failed with exit code {result.returncode}. See {log_path}", file=sys.stderr)
    return result.returncode


# ---------------------------------------------------------------- install plans

@dataclass
class Plan:
    adapter: str
    files: dict[str, str] = field(default_factory=dict)  # path -> content to write first
    commands: list[list[str]] = field(default_factory=list)


def systemd_quote(arg: str) -> str:
    return '"' + arg.replace("\\", "\\\\").replace('"', '\\"') + '"'


def linux_systemd_plan(job: Job, repo: Path, daily_at: str, retention_days: int, unit_dir: Path) -> Plan:
    command = " ".join(systemd_quote(a) for a in job_command(job, repo, "linux", retention_days))
    service = (f"[Unit]\nDescription={job.description}\n\n[Service]\nType=oneshot\n"
               f"WorkingDirectory={repo}\n"  # systemd reads this path literally: no quotes + ("Nice=10\n" if job.nice else "")
               + f"ExecStart={command}\n")
    timer = (f"[Unit]\nDescription=Run {job.unit} daily\n\n[Timer]\nOnCalendar=*-*-* {daily_at}:00\n"
             f"Persistent=true\nUnit={job.unit}.service\n\n[Install]\nWantedBy=timers.target\n")
    return Plan("linux-systemd-user", {str(unit_dir / f"{job.unit}.service"): service,
                                       str(unit_dir / f"{job.unit}.timer"): timer},
                [["systemctl", "--user", "daemon-reload"],
                 ["systemctl", "--user", "enable", "--now", f"{job.unit}.timer"]])


def cron_line(job: Job, repo: Path, daily_at: str, retention_days: int) -> str:
    hour, minute = (int(p) for p in daily_at.split(":"))
    command = " ".join(shlex.quote(a) for a in job_command(job, repo, "linux", retention_days))
    return f"{minute} {hour} * * * cd {shlex.quote(str(repo))} && {command} # {job.unit}"


def ps_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def windows_plan(job: Job, repo: Path, daily_at: str, retention_days: int) -> Plan:
    exe, *args = job_command(job, repo, "windows", retention_days)
    argument = " ".join(f'"{a}"' if " " in a else a for a in args)
    script = "; ".join([
        f"$a = New-ScheduledTaskAction -Execute {ps_quote(exe)} -Argument {ps_quote(argument)} "
        f"-WorkingDirectory {ps_quote(str(repo))}",
        f"$t = New-ScheduledTaskTrigger -Daily -At {ps_quote(daily_at)}",
        f"$s = New-ScheduledTaskSettingsSet -StartWhenAvailable "
        f"-ExecutionTimeLimit (New-TimeSpan -Minutes {job.timeout_minutes})",
        "$p = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) "
        "-LogonType Interactive -RunLevel Limited",
        f"Register-ScheduledTask -TaskName {ps_quote(job.task)} -Action $a -Trigger $t -Settings $s -Principal $p "
        f"-Description {ps_quote(job.description)} -Force | Out-Null",
        f"Get-ScheduledTask -TaskName {ps_quote(job.task)} | Select-Object TaskName, State",
    ])
    powershell = shutil.which("powershell.exe") or "powershell.exe"
    return Plan("windows-task-scheduler", {}, [[powershell, "-NoProfile", "-NonInteractive", "-Command", script]])


def systemd_user_available() -> bool:
    if not shutil.which("systemctl"):
        return False
    probe = subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True)  # nosec B603 B607
    return probe.returncode == 0


def build_plan(job_name: str, *, repo: Path = REPO, system_name: str | None = None, daily_at: str | None = None,
               retention_days: int = 7, use_systemd: bool | None = None) -> Plan:
    if job_name not in JOBS:
        raise ScheduleError(f"Unknown job {job_name}; choose from {', '.join(JOBS)}")
    job = JOBS[job_name]
    daily_at = daily_at or job.default_time
    validate(daily_at, retention_days)
    repo = Path(repo).resolve()
    if not repo.is_dir() or repo.parent == repo:
        raise ScheduleError("Repo must be an existing non-root directory")
    system = normalize_system(system_name)
    if system == "windows":
        return windows_plan(job, repo, daily_at, retention_days)
    if use_systemd is None:
        use_systemd = systemd_user_available()
    if use_systemd:
        unit_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "systemd" / "user"
        return linux_systemd_plan(job, repo, daily_at, retention_days, unit_dir)
    if not shutil.which("crontab"):
        raise ScheduleError("Neither a usable user systemd session nor crontab is available")
    return Plan("linux-cron", {}, [["crontab", "<add>", cron_line(job, repo, daily_at, retention_days)]])


def apply_plan(plan: Plan, job: Job) -> None:
    for path, content in plan.files.items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
    for command in plan.commands:
        if command[:2] == ["crontab", "<add>"]:
            current = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout  # nosec B603 B607
            lines = [line for line in current.splitlines() if not line.rstrip().endswith(f"# {job.unit}")]
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".cron") as fh:
                fh.write("\n".join([*lines, command[2]]) + "\n")
            subprocess.run(["crontab", fh.name], check=True)  # nosec B603 B607
            os.unlink(fh.name)
            continue
        subprocess.run(command, check=True)  # nosec B603


# ---------------------------------------------------------------- cli

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schedule", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run a job now, with logging")
    run.add_argument("job", choices=sorted(JOBS))
    run.add_argument("--retention-days", type=int, default=7)
    install = sub.add_parser("install", help="schedule a job daily with this OS's scheduler")
    install.add_argument("job", choices=sorted(JOBS))
    install.add_argument("--daily-at")
    install.add_argument("--retention-days", type=int, default=7)
    install.add_argument("--repo", default=str(REPO))
    install.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "run":
        return run_job(args.job, retention_days=args.retention_days)
    try:
        plan = build_plan(args.job, repo=Path(args.repo), daily_at=args.daily_at, retention_days=args.retention_days)
        if args.dry_run:
            print(json.dumps({"adapter": plan.adapter, "files": plan.files, "commands": plan.commands}, indent=2))
            return 0
        print(f"Installing {args.job} with adapter: {plan.adapter}")
        apply_plan(plan, JOBS[args.job])
    except (ScheduleError, OSError, subprocess.CalledProcessError) as exc:
        print(f"schedule: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
