#!/usr/bin/env python3
"""Set up this repo on a fresh Linux, macOS or Windows machine (replaces bootstrap.sh / bootstrap.ps1 / bootstrap.cmd).

    python3 scripts/bootstrap.py                         # Linux / macOS
    py scripts\\bootstrap.py                             # Windows
    ... --skip-browsers                                  # skip Playwright Chromium downloads

Steps: check Python/uv/Node, create .venv, `uv sync --locked`, `npm ci`, register skills, validate MCP JSON,
check dependency pins, install the Playwright browsers each playwright version needs, report API keys,
then run `scripts/deps.py check` so you see anything optional that is still missing.
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


def require(tool: str, hint: str) -> None:
    path = shutil.which(tool)
    if not path:
        fail(f"{tool} is missing. {hint}")
    ok(f"{tool}: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-browsers", "--skip-playwright-browser", action="store_true")
    args = parser.parse_args(argv)

    step("Checking required tools")
    if sys.version_info < (3, 12):
        fail(f"Python 3.12+ is required; this is {sys.version.split()[0]}")
    ok(f"Python {sys.version.split()[0]}")
    require("uv", "Install: Linux `curl -LsSf https://astral.sh/uv/install.sh | sh`, Windows `winget install astral-sh.uv`.")
    require("node", "Install Node.js 22 (Linux `fnm install 22`, Windows `winget install OpenJS.NodeJS.LTS`).")
    require("npm", "npm ships with Node.js.")
    which = run(["node", "scripts/mcp-npx.mjs", "--which"], capture_output=True, text=True)
    if which.returncode != 0:
        fail("No Node.js ^20.19, ^22.12 or >= 23 found for the MCP servers. Install Node 22.")
    ok(f"MCP Node: {which.stdout.strip()}")

    step("Python environment")
    if not VENV_PYTHON.exists():
        if run([sys.executable, "-m", "venv", ".venv"]).returncode != 0:
            fail("could not create .venv")
        ok("created .venv")
    else:
        ok(".venv already exists")
    run([str(VENV_PYTHON), "-m", "pip", "install", "--quiet", "--upgrade", "pip>=26.2", "setuptools>=83.0.0"])
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

    step("Everything else (optional tools show as warn)")
    run([sys.executable, "scripts/deps.py", "check"])

    activate = r".\.venv\Scripts\Activate.ps1" if WINDOWS else "source .venv/bin/activate"
    print(f"\nBootstrap complete. Activate the environment with:  {activate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
