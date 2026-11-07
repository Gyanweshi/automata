#!/usr/bin/env python3
"""Set up this repo on a fresh Linux, macOS or Windows machine (replaces bootstrap.sh / bootstrap.ps1 / bootstrap.cmd).

    uv run --no-project --python 3.12 scripts/bootstrap.py    # any machine with uv; downloads Python if needed
    python3 scripts/bootstrap.py                              # Linux / macOS with Python 3.12+
    py scripts\\bootstrap.py                                  # Windows with Python 3.12+
    ... --yes              install missing tools without asking
    ... --skip-browsers    skip Playwright Chromium downloads
    ... --schedules / --no-schedules   register the nightly jobs without asking / skip them

Steps: check git/uv/Node and install any that are missing (winget on Windows, the manifest's command on
Linux/macOS; asks first unless --yes), create .venv, `uv sync --locked`, `npm ci`, register skills, validate MCP JSON,
check dependency pins, install the Playwright browsers each playwright version needs, report API keys,
offer to register the nightly jobs, then run scripts/doctor.py, which checks everything one step at a time.
Standard library only: it runs before the venv exists.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404 - runs setup tools named here
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"
VENV_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")
API_KEYS = ("APIFY_API_TOKEN",)


def ok(message: str) -> None:
    print(f"OK   {message}", flush=True)


def warn(message: str) -> None:
    print(f"WARN {message}", flush=True)


def fail(message: str) -> None:
    print(f"FAIL {message}", flush=True)
    raise SystemExit(1)


def step(title: str) -> None:
    print(f"\n==> {title}", flush=True)


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    exe = shutil.which(command[0]) or command[0]
    return subprocess.run([exe, *command[1:]], cwd=ROOT, **kwargs)  # nosec B603


# Untracked leftovers git cannot remove when a tracked folder is deleted (OpenSwarm was removed 2026-11-07).
LEGACY_DIRS = ("agents/openedswarm_core",)
LEGACY_JUNK = (".venv", "node_modules", "server_background.log", "__pycache__", ".pytest_cache")
KEEP_FOR_USER = (".env",)  # may hold API keys: report, never delete


def clean_legacy(root: Path = ROOT) -> list[str]:
    """Remove disposable leftovers of removed components; report anything the user should look at."""
    import shutil as _shutil

    notes = []
    for rel in LEGACY_DIRS:
        folder = root / rel
        if not folder.is_dir():
            continue
        for name in (".venv", "node_modules"):  # the big ones: delete whole, don't walk them
            _shutil.rmtree(folder / name, ignore_errors=True)
        for junk in sorted(folder.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if junk.name in LEGACY_JUNK:
                _shutil.rmtree(junk, ignore_errors=True) if junk.is_dir() else junk.unlink(missing_ok=True)
        leftovers = [p for p in folder.rglob("*") if p.is_file()]
        kept = [p for p in leftovers if p.name in KEEP_FOR_USER]
        if leftovers and len(kept) == len(leftovers):
            notes.append(f"{rel} only holds {', '.join(str(p.relative_to(root)) for p in kept)} from the removed "
                         "component; copy any keys you still need into the repo's .env, then delete the folder")
        elif not leftovers:
            _shutil.rmtree(folder, ignore_errors=True)
            notes.append(f"removed leftover folder {rel}")
        else:
            notes.append(f"{rel} still has {len(leftovers)} untracked file(s) from the removed component; review and delete")
    return notes


def refresh_path() -> None:
    """Pick up PATH changes an installer just made, without opening a new terminal."""
    if WINDOWS:
        import winreg

        parts = []
        for hive, key in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                          (winreg.HKEY_CURRENT_USER, "Environment")):
            try:
                with winreg.OpenKey(hive, key) as handle:
                    parts.append(os.path.expandvars(winreg.QueryValueEx(handle, "Path")[0]))
            except OSError:
                continue
        # where winget links portable tools (uv), Astral's own installer, cargo, and the Node.js MSI put binaries
        local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        known = [local / "Microsoft" / "WinGet" / "Links", Path.home() / ".local" / "bin", Path.home() / ".cargo" / "bin",
                 Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs"]
        parts += [str(d) for d in known if d.is_dir()]
        os.environ["PATH"] = os.pathsep.join([*parts, os.environ.get("PATH", "")])
    else:
        extra = [str(Path.home() / d) for d in (".local/bin", ".cargo/bin") if (Path.home() / d).is_dir()]
        os.environ["PATH"] = os.pathsep.join([*extra, os.environ.get("PATH", "")])


def ensure(tool: str, dep_id: str, assume_yes: bool, why: str) -> None:
    """Use the tool if it is there; otherwise offer to install it with `deps.py install`, then re-check."""
    if shutil.which(tool):
        ok(f"{tool}: {shutil.which(tool)}")
        return
    print(f"MISS {tool} is not installed ({why}).", flush=True)
    answer = "y" if assume_yes else input(f"     Install {dep_id} now? [Y/n] ").strip().lower()
    if answer not in ("", "y", "yes"):
        fail(f"{tool} is required. Install it with: python scripts/deps.py install {dep_id}")
    run([sys.executable, "scripts/deps.py", "install", dep_id])
    refresh_path()
    if not shutil.which(tool):
        fail(f"{tool} still not found after installing. Open a new terminal and run the bootstrap again "
             "(see 'Fresh machine troubleshooting' in README.md).")
    ok(f"{tool}: {shutil.which(tool)} (just installed)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-browsers", "--skip-playwright-browser", action="store_true")
    parser.add_argument("--yes", "-y", action="store_true", help="install missing tools without asking")
    schedules = parser.add_mutually_exclusive_group()
    schedules.add_argument("--schedules", dest="schedules", action="store_true", default=None,
                           help="register the nightly jobs without asking")
    schedules.add_argument("--no-schedules", dest="schedules", action="store_false")
    schedules.add_argument("--auto-schedules", dest="schedules", action="store_const", const="auto",
                           help="register jobs that are missing or already belong to this checkout; never take over "
                                "jobs registered for another checkout (used by the post-pull update)")
    args = parser.parse_args(argv)

    step("Checking required tools")
    if sys.version_info < (3, 12):
        fail(f"Python 3.12+ is required; this is {sys.version.split()[0]}. "
             "Run it through uv instead, which downloads Python 3.12: uv run --no-project --python 3.12 scripts/bootstrap.py")
    ok(f"Python {sys.version.split()[0]}")
    refresh_path()
    ensure("git", "git", args.yes, "repo sync and the cross-platform checks")
    ensure("uv", "uv", args.yes, "installs the locked Python packages")
    ensure("node", "node", args.yes, "runs the MCP servers and HTML-to-PPTX")
    ensure("npm", "node", args.yes, "ships with Node.js")
    which = run(["node", "scripts/mcp-npx.mjs", "--which"], capture_output=True, text=True)
    if which.returncode != 0:
        print("MISS Node.js is too old for the MCP servers (need ^20.19, ^22.12 or >= 23).", flush=True)
        answer = "y" if args.yes else input("     Install Node.js LTS now? [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            run([sys.executable, "scripts/deps.py", "install", "node"])
            refresh_path()
            which = run(["node", "scripts/mcp-npx.mjs", "--which"], capture_output=True, text=True)
    if which.returncode != 0:
        fail("No Node.js ^20.19, ^22.12 or >= 23 found for the MCP servers: python scripts/deps.py install node")
    ok(f"MCP Node: {which.stdout.strip()}")
    default_node = run(["node", "--version"], capture_output=True, text=True).stdout.strip()
    parts = tuple(int(x) for x in default_node.lstrip("v").split(".")[:2] if x.isdigit())
    if parts and parts < (22, 12):
        good = which.stdout.split()[-1] if which.stdout.split() else ""
        if good:  # use the compatible Node for every step of this run (npm ci, browser installs, checks)
            os.environ["PATH"] = os.pathsep.join([str(Path(good).parent), os.environ.get("PATH", "")])
        warn(f"this terminal's default `node` is {default_node}, older than 22.12; this setup run uses {good or 'it anyway'}. "
             "Fix the terminal: Linux with fnm, load fnm in ~/.bashrc and open a new terminal (restart Claude Code); "
             "see the `node` entry in docs/DEPENDENCIES.md.")

    step("Python environment")
    if not VENV_PYTHON.exists():
        # uv makes the venv (no python3-venv package needed on Debian/Ubuntu); --seed adds pip for make targets
        if run(["uv", "venv", "--seed", "--python", "3.12", ".venv"]).returncode != 0:
            fail("could not create .venv with uv")
        ok("created .venv")
    else:
        ok(".venv already exists")
    if run(["uv", "sync", "--locked", "--cache-dir", str(ROOT / ".uv-cache")]).returncode != 0:
        fail("uv sync --locked failed (is uv.lock out of date? run `uv lock --check`)")
    ok("agency packages installed from uv.lock")

    step("Node packages")
    for prefix in (".", "agents/automata_core/ig-research"):
        if (ROOT / prefix / "package-lock.json").exists():
            result = run(["npm", "ci", "--no-audit", "--no-fund", "--prefix", prefix])
            (ok if result.returncode == 0 else warn)(f"npm ci in {prefix}")

    step("Skills and configs")
    if run([str(VENV_PYTHON), "scripts/sync-skills.py", "--sync"]).returncode != 0:
        warn("skill registrations need review (scripts/sync-skills.py --check)")
    else:
        ok("repo skills registered for Codex and Claude")
    for config in (".mcp.json", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "mcp" / "agents").glob("*.json"))):
        try:
            json.loads((ROOT / config).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            fail(f"{config} is not valid JSON: {exc}")
    ok("MCP configs are valid JSON")
    if run([sys.executable, "scripts/deps.py", "check", "--pins-only"]).returncode != 0:
        fail("dependency pins disagree between files (see above)")

    if args.skip_browsers:
        warn("skipped Playwright browser installs")
    else:
        step("Playwright browsers (one per playwright version)")
        node_ok = run(["npx", "--no-install", "playwright", "install", "chromium"]).returncode == 0
        (ok if node_ok else warn)("Chromium for the Node playwright (html_to_pptx.js)")
        py_ok = run([str(VENV_PYTHON), "-m", "playwright", "install", "chromium"]).returncode == 0
        (ok if py_ok else warn)("Chromium for the Python playwright (research scraper)")

    step("API keys")
    env_file = ROOT / ".env"
    dotenv = env_file.read_text(encoding="utf-8", errors="ignore") if env_file.exists() else ""
    for key in API_KEYS:
        found = os.environ.get(key) or any(line.strip().startswith(f"{key}=") and line.split("=", 1)[1].strip()
                                           for line in dotenv.splitlines())
        (ok if found else warn)(f"{key} {'is set' if found else 'is not set (add it to .env; see env.example)'}")

    step("Scheduled jobs (vault index 02:30, housekeeper 03:00, vault watchdog at login if a vault is set)")
    wanted = args.schedules
    if wanted is None:
        wanted = input("     Register them with this machine's scheduler now? [Y/n] ").strip().lower() in ("", "y", "yes")
    if wanted:
        sys.path.insert(0, str(ROOT / "scripts"))
        from doctor import vault_configured  # same check the doctor uses
        jobs = ["vault-index", "housekeeper"] + (["vault-watchdog"] if vault_configured() else [])
        if "vault-watchdog" not in jobs:
            warn("no vault configured (OBSIDIAN_VAULT_PATH), so the vault watchdog is not installed")
        if wanted == "auto":
            probe = ("import sys, json; sys.path.insert(0, 'packages/agency-common/src');"
                     "from agency_common.scheduled_jobs import should_install_here;"
                     "print(json.dumps({j: should_install_here(j) for j in sys.argv[1:]}))")
            out = run([str(VENV_PYTHON), "-c", probe, *jobs], capture_output=True, text=True)
            decisions = json.loads(out.stdout) if out.returncode == 0 else {}
            for job in list(jobs):
                install, why = decisions.get(job, (False, "could not check the current registration"))
                if not install:
                    warn(f"{job}: left as is ({why})")
                    jobs.remove(job)
        for job in jobs:
            done = run([str(VENV_PYTHON), "scripts/schedule.py", "install", job]).returncode == 0
            (ok if done else warn)(f"{job} {'scheduled' if done else 'not scheduled (see message above)'}")
    else:
        warn("nightly jobs not registered (python scripts/schedule.py install vault-index / housekeeper)")

    step("Leftovers from removed components")
    notes = clean_legacy()
    for note in notes:
        warn(note)
    if not notes:
        ok("nothing to clean")

    step("Keeping this machine up to date after each git pull")
    sys.path.insert(0, str(ROOT / "scripts"))
    import setup_state

    setup_state.record()
    hook_notes = setup_state.install_hooks()
    for note in hook_notes:
        warn(note)
    ok("setup stamp recorded; post-pull hooks installed (a pull that changes the setup re-runs this bootstrap)")

    step("Checking everything, one step at a time (scripts/doctor.py)")
    doctor = run([sys.executable, "scripts/doctor.py"]).returncode

    activate = r".\.venv\Scripts\Activate.ps1" if WINDOWS else "source .venv/bin/activate"
    print(f"\nBootstrap {'complete' if doctor == 0 else 'finished with failures (see the summary above)'}. "
          f"Activate the environment with:  {activate}")
    return doctor


if __name__ == "__main__":
    sys.exit(main())
