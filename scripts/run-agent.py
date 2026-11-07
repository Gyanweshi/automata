#!/usr/bin/env python3
"""Run the agency agents on Linux, macOS or Windows (replaces run-agent.ps1 and run-pipeline.sh).

    python scripts/run-agent.py research   --brand my-client [--scraper playwright] [--platforms ig] [--parallel]
    python scripts/run-agent.py storyboard --brand my-client --type carousel --topic "5 tips"
    python scripts/run-agent.py content    --brand my-client --type carousel --topic "5 tips"
    python scripts/run-agent.py pipeline   --brand my-client --type carousel --topic "5 tips"
    python scripts/run-agent.py week       --brand my-client
    python scripts/run-agent.py dry-run    --brand my-client
    python scripts/run-agent.py status

Uses the repo's .venv entry points when installed, otherwise runs the package sources with the venv Python.
Vault writes stay draft-only unless --commit-vault and a --commit-reason are given.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess  # nosec B404 - runs the repo's own agent CLIs
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"
BIN = ROOT / ".venv" / ("Scripts" if WINDOWS else "bin")
PACKAGES = ("agency-common", "agency-research", "agency-storyboard", "agency-content")


def venv_python() -> Path:
    return BIN / ("python.exe" if WINDOWS else "python")


def agent_command(cli: str, module: str) -> list[str]:
    entry = BIN / (f"{cli}.exe" if WINDOWS else cli)
    return [str(entry)] if entry.exists() else [str(venv_python()), "-m", module]


def run(cli: str, module: str, args: list[str]) -> None:
    env = dict(os.environ)
    sources = [str(ROOT / "packages" / p / "src") for p in PACKAGES]
    env["PYTHONPATH"] = os.pathsep.join([*sources, *(p for p in [env.get("PYTHONPATH")] if p)])
    command = agent_command(cli, module) + args
    result = subprocess.run(command, cwd=ROOT, env=env)  # nosec B603
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def research_args(a: argparse.Namespace) -> list[str]:
    args = ["--brand", a.brand, "--workspace", a.workspace, "--brands-dir", a.brands_dir, "--scraper", a.scraper,
            "--instagram-login-mode", a.instagram_login_mode, "--browser-act-mode", a.browser_act_mode,
            "--browser-act-session-name", a.browser_act_session_name]
    if a.platforms:
        args += ["--platforms", a.platforms]
    if a.parallel:
        args += ["--parallel", "--max-workers", str(a.max_workers)]
    return args + vault_args(a)


def vault_args(a: argparse.Namespace) -> list[str]:
    return ["--commit-vault", "--commit-reason", a.commit_reason] if a.commit_vault else []


def storyboard_args(a: argparse.Namespace) -> list[str]:
    return ["--brand", a.brand, "--type", a.type, "--topic", a.topic, "--workspace", a.workspace,
            "--brands-dir", a.brands_dir] + vault_args(a)


def content_args(a: argparse.Namespace) -> list[str]:
    return ["--brand", a.brand, "--platform", "instagram", "--type", a.type, "--topic", a.topic,
            "--workspace", a.workspace, "--brands-dir", a.brands_dir] + vault_args(a)


def status() -> None:
    for package in PACKAGES:
        pyproject = ROOT / "packages" / package / "pyproject.toml"
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.M)
        cli = BIN / (f"{package}.exe" if WINDOWS else package)
        state = "installed entry point" if cli.exists() else "source fallback"
        print(f"{package}: {match.group(1) if match else 'unknown'} ({state if package != 'agency-common' else 'library'})")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["research", "storyboard", "content", "pipeline", "week", "dry-run", "status"])
    p.add_argument("--brand", default="example-brand")
    p.add_argument("--type", default="carousel")
    p.add_argument("--topic", default="5 tips for entrepreneurs")
    p.add_argument("--workspace", default=os.environ.get("AGENCY_WORKSPACE", "./workspace"))
    p.add_argument("--brands-dir", default=os.environ.get("AGENCY_BRANDS_DIR", "./brands"))
    p.add_argument("--platforms", default="")
    p.add_argument("--scraper", default="apify", choices=["apify", "playwright", "browser-act", "cdp"])
    p.add_argument("--instagram-login-mode", default="auto", choices=["auto", "manual"])
    p.add_argument("--browser-act-mode", default="stealth", choices=["stealth", "session"])
    p.add_argument("--browser-act-session-name", default="")
    p.add_argument("--parallel", action="store_true")
    p.add_argument("--max-workers", type=int, default=4)
    p.add_argument("--commit-vault", action="store_true")
    p.add_argument("--commit-reason", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    if a.commit_vault and not a.commit_reason.strip():
        raise SystemExit("--commit-reason is required with --commit-vault")
    if a.command != "status" and not venv_python().exists():
        raise SystemExit("The .venv is missing. Run the bootstrap first: python scripts/bootstrap.py")
    sys.path.insert(0, str(ROOT / "scripts"))
    from setup_state import stale_message
    stale = stale_message(ROOT)
    if stale:
        print(f"WARNING: {stale}", file=sys.stderr)
    if a.command == "status":
        status()
    elif a.command == "dry-run":
        run("agency-research", "agency_research.cli", ["--brand", a.brand, "--workspace", a.workspace,
                                                      "--brands-dir", a.brands_dir, "--dry-run"])
        run("agency-content", "agency_content.cli", ["--brand", a.brand, "--platform", "instagram", "--type", "caption",
                                                    "--topic", "test", "--workspace", a.workspace, "--brands-dir",
                                                    a.brands_dir, "--format", "summary", "--dry-run"])
    elif a.command == "research":
        run("agency-research", "agency_research.cli", research_args(a))
    elif a.command == "storyboard":
        run("agency-storyboard", "agency_storyboard.cli", storyboard_args(a))
    elif a.command == "content":
        run("agency-content", "agency_content.cli", content_args(a))
    elif a.command == "week":
        run("agency-content", "agency_content.cli", ["--brand", a.brand, "--week", "--workspace", a.workspace,
                                                    "--brands-dir", a.brands_dir, "--format", "markdown"] + vault_args(a))
    elif a.command == "pipeline":
        for title, cli, module, args in (("Research", "agency-research", "agency_research.cli", research_args(a)),
                                         ("Storyboard", "agency-storyboard", "agency_storyboard.cli", storyboard_args(a)),
                                         ("Content", "agency-content", "agency_content.cli", content_args(a))):
            print(f"==> {title}", flush=True)
            run(cli, module, args)
        print(f"Pipeline complete. Outputs: {a.workspace}/{a.brand}/{{research,storyboards,content}}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
