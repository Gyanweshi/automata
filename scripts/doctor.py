#!/usr/bin/env python3
"""Check that this machine can actually run everything, one step at a time (Linux, macOS, Windows).

    python scripts/doctor.py            # run every check, then print a summary
    python scripts/doctor.py --quick    # skip the slow ones (the Playwright MCP download)

Read-only: it changes nothing. The bootstrap runs it at the end; run it alone after a `git pull`, after
installing something, or whenever a machine feels broken. Each failing step says what to run.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import subprocess  # nosec B404 - runs the repo's own scripts and tool probes
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"
VENV_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")
PASS, WARN, FAIL, SKIP = "PASS", "WARN", "FAIL", "SKIP"


def run(command: list[str], timeout: int = 300) -> tuple[int, str]:
    exe = shutil.which(command[0]) or command[0]
    try:
        out = subprocess.run([exe, *command[1:]], cwd=ROOT, capture_output=True, text=True,  # nosec B603
                             encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return out.returncode, (out.stdout + out.stderr).strip()


def pin(dep_id: str) -> str:
    with (ROOT / "dependencies.toml").open("rb") as fh:
        return next(d.get("pin", "") for d in tomllib.load(fh)["dependency"] if d["id"] == dep_id)


# ---------------------------------------------------------------- checks: each returns (status, detail, output)

def check_dependencies():
    code, out = run([sys.executable, "scripts/deps.py", "check"])
    warns = [line for line in out.splitlines() if line.startswith("warn")]  # info lines (untagged extras) don't count
    if code:
        return FAIL, "a required dependency is missing or a pin disagrees", out
    return (WARN, f"{len(warns)} optional tool(s) missing (install with deps.py install ID)", "\n".join(warns)) if warns \
        else (PASS, "all installed", "")


def env_vault_value() -> str | None:
    """OBSIDIAN_VAULT_PATH from the environment or .env; None when the key is absent, '' when set to empty."""
    if "OBSIDIAN_VAULT_PATH" in os.environ:
        return os.environ["OBSIDIAN_VAULT_PATH"].strip()
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("OBSIDIAN_VAULT_PATH="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def check_vault():
    value = env_vault_value()
    if value:
        path = Path(value).expanduser()
        return (PASS, f"Obsidian vault at {path}", "") if path.is_dir() else \
            (FAIL, f"OBSIDIAN_VAULT_PATH={value} does not exist (drive not mounted?); set it to empty to work without a vault", "")
    return PASS, "no Obsidian vault: notes stay in workspace/vault (set OBSIDIAN_VAULT_PATH in .env to use one)", ""


def check_cross_platform():
    code, out = run([sys.executable, "scripts/check-cross-platform.py"])
    if code == 0:
        return PASS, "no one-OS scripts, machine paths or encoding gaps", ""
    return WARN, "new findings (often an uncommitted local file)", out


def check_venv():
    if not VENV_PYTHON.exists():
        return FAIL, "no .venv: run the bootstrap", ""
    code, out = run([str(VENV_PYTHON), "-c", "import agency_common, agency_research, agency_storyboard, agency_content"])
    return (PASS, "agency packages import", "") if code == 0 else (FAIL, "packages missing: uv sync --locked", out)


def check_mcp_node():
    code, out = run(["node", "scripts/mcp-npx.mjs", "--which"])
    return (PASS, out, "") if code == 0 else (FAIL, "no compatible Node: python scripts/deps.py install node", out)


def check_playwright_mcp():
    code, out = run(["node", "scripts/mcp-npx.mjs", "-y", f"@playwright/mcp@{pin('playwright-mcp')}", "--version"], 300)
    profile = Path.home() / ".agency" / "chrome-instagram-cdp"
    note = f"profile {'exists' if profile.is_dir() else 'not created yet'}: {profile}"
    return (PASS, f"starts ({out.splitlines()[-1] if out else 'ok'}); {note}", "") if code == 0 \
        else (FAIL, "Playwright MCP did not start", out)


def check_agents():
    if not VENV_PYTHON.exists():
        return SKIP, "no .venv", ""
    # A throwaway brand built from the committed template, so this works without the vault or .env
    # (real brand notes, including example-brand, live in the Obsidian vault).
    work = ROOT / "workspace" / "doctor"
    (work / "brands").mkdir(parents=True, exist_ok=True)
    template = (ROOT / "brands" / "_template.yaml").read_text(encoding="utf-8")
    template = re.sub(r'(?m)^slug: .*$', 'slug: "doctor-check"', template)
    template = re.sub(r'(?m)^name: .*$', 'name: "Doctor Check"', template)
    (work / "brands" / "doctor-check.yaml").write_text(template, encoding="utf-8")
    code, out = run([str(VENV_PYTHON), "scripts/run-agent.py", "dry-run", "--brand", "doctor-check",
                     "--brands-dir", str(work / "brands"), "--workspace", str(work)])
    return (PASS, "research + content dry-run OK on a template brand, no API calls", "") if code == 0 \
        else (FAIL, "agent dry-run failed", out)


def vault_configured() -> bool:
    """True when OBSIDIAN_VAULT_PATH (environment or .env) points to an existing folder."""
    value = os.environ.get("OBSIDIAN_VAULT_PATH", "")
    env_file = ROOT / ".env"
    if not value and env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("OBSIDIAN_VAULT_PATH="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
    return bool(value) and Path(value).expanduser().is_dir()


def watchdog_running() -> bool:
    if WINDOWS:
        return run(["schtasks", "/Query", "/TN", "Automata Vault Watchdog"])[0] == 0
    if shutil.which("systemctl"):
        if run(["systemctl", "is-active", "vault-watchdog"])[0] == 0:  # system-wide service
            return True
        if run(["systemctl", "--user", "is-active", "automata-vault-watchdog"])[0] == 0:
            return True
    return shutil.which("crontab") is not None and "# automata-vault-watchdog" in run(["crontab", "-l"])[1]


def scheduled(job_unit: str, task: str) -> bool:
    if WINDOWS:
        return run(["schtasks", "/Query", "/TN", task])[0] == 0
    if shutil.which("systemctl") and run(["systemctl", "--user", "is-enabled", f"{job_unit}.timer"])[0] == 0:
        return True
    return shutil.which("crontab") is not None and f"# {job_unit}" in run(["crontab", "-l"])[1]


def check_schedules():
    if not VENV_PYTHON.exists():
        return SKIP, "no .venv", ""
    for job in ("vault-index", "housekeeper"):
        code, out = run([str(VENV_PYTHON), "scripts/schedule.py", "install", job, "--dry-run"])
        if code:
            return FAIL, f"cannot plan the {job} schedule on this OS", out
    registered = {name: scheduled(unit, task) for name, unit, task in (
        ("vault-index", "automata-vault-index", "Automata Vault Index"),
        ("housekeeper", "automata-housekeeper", "Automata Housekeeper"))}
    if vault_configured():
        registered["vault-watchdog"] = watchdog_running()
    missing = [name for name, ok in registered.items() if not ok]
    if missing:
        return WARN, "not registered: " + ", ".join(missing) + " (python scripts/schedule.py install NAME)", ""
    return PASS, ", ".join(registered) + " registered" + ("" if "vault-watchdog" in registered
                                                         else " (no vault configured, so no watchdog)"), ""


def check_gimp():
    code, out = run([sys.executable, "scripts/install-gimp-mcp.py", "--dry-run"])
    if code:
        return SKIP, "GIMP 3.x not found (optional)", ""
    match = re.search(r"into (.+gimp-mcp-plugin\.py)", out)
    if match and Path(match.group(1).strip()).exists():
        return PASS, "GIMP MCP plugin installed at the pinned commit path", ""
    return WARN, "GIMP found but plugin missing: python scripts/install-gimp-mcp.py", ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args(argv)
    # judge the machine by what a newly opened terminal sees (installers only update PATH for new terminals)
    spec = importlib.util.spec_from_file_location("deps_for_doctor", ROOT / "scripts" / "deps.py")
    deps_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(deps_module)
    deps_module.refresh_path()

    checks = [
        ("Dependencies installed (deps.py check)", check_dependencies),
        ("Python environment", check_venv),
        ("Vault", check_vault),
        ("Cross-platform rules", check_cross_platform),
        ("Node for MCP servers", check_mcp_node),
        ("Playwright MCP", (lambda: (SKIP, "slow check skipped (--quick)", "")) if args.quick else check_playwright_mcp),
        ("Agents (dry run)", check_agents),
        ("Scheduled jobs", check_schedules),
        ("GIMP MCP plugin", check_gimp),
    ]
    results = []
    for index, (name, check) in enumerate(checks, 1):
        print(f"[{index}/{len(checks)}] {name} ...", flush=True)
        status, detail, output = check()
        results.append((status, name, detail))
        print(f"      {status}  {detail}", flush=True)
        if status in (FAIL, WARN) and output:
            for line in output.splitlines()[-15:]:
                print(f"        | {line}")

    print("\nSummary")
    for status, name, detail in results:
        print(f"  {status}  {name}: {detail}")
    failed = [r for r in results if r[0] == FAIL]
    print("\nAll required checks passed." if not failed else f"\n{len(failed)} check(s) failed: fix those first, then re-run.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
