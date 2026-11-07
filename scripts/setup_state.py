#!/usr/bin/env python3
"""Know whether this machine's setup matches the checkout, and bring it up to date after a pull.

Git never runs repo code on clone or pull, so this works in three layers:
  1. scripts/bootstrap.py records a stamp (a hash of the files that define the setup) when it succeeds,
     and installs git hooks (post-merge, post-rewrite) that call `--after-pull`.
  2. `--after-pull`: if the stamp no longer matches (lockfiles, manifest, MCP config or the bootstrap changed),
     re-run the bootstrap non-interactively. It never fails the pull.
  3. Before the hooks exist (an old clone's first pull), the Claude Code SessionStart hook and run-agent.py
     call `stale_message()` and ask for the bootstrap to be run.

    python scripts/setup_state.py --check        # exit 1 and explain when the setup is out of date
    python scripts/setup_state.py --after-pull   # what the git hooks run
Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess  # nosec B404 - runs the repo's own bootstrap
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ("uv.lock", "package-lock.json", "agents/automata_core/ig-research/package-lock.json",
          "dependencies.toml", ".mcp.json", "scripts/bootstrap.py",
          "scripts/setup_state.py", "scripts/hooks/pre_commit.py")  # hook code: changes reinstall the hooks
BOOTSTRAP = "uv run --no-project --python 3.12 scripts/bootstrap.py --yes"
HOOK_MARKER = "# automata-setup-hook"
HOOK_NAMES = ("post-merge", "post-rewrite")
PRE_COMMIT_BODY = f"""#!/bin/sh
{HOOK_MARKER}: installed by scripts/bootstrap.py. Block commits that break the repo's rules (fast checks).
cd "$(git rev-parse --show-toplevel)" || exit 0
[ -f scripts/hooks/pre_commit.py ] || exit 0
for p in .venv/Scripts/python.exe .venv/bin/python; do
  [ -x "$p" ] && exec "$p" scripts/hooks/pre_commit.py
done
command -v python3 >/dev/null 2>&1 && exec python3 scripts/hooks/pre_commit.py
command -v python >/dev/null 2>&1 && exec python scripts/hooks/pre_commit.py
exit 0
"""
HOOK_BODY = f"""#!/bin/sh
{HOOK_MARKER}: installed by scripts/bootstrap.py. After a pull, bring this machine's setup up to date.
cd "$(git rev-parse --show-toplevel)" || exit 0
[ -f scripts/setup_state.py ] || exit 0
[ "$(basename "$0")" = post-rewrite ] && [ "$1" = amend ] && exit 0  # amending a commit is not a pull
for p in .venv/Scripts/python.exe .venv/bin/python; do
  [ -x "$p" ] && exec "$p" scripts/setup_state.py --after-pull
done
command -v python3 >/dev/null 2>&1 && exec python3 scripts/setup_state.py --after-pull
command -v python >/dev/null 2>&1 && exec python scripts/setup_state.py --after-pull
exit 0
"""


def stamp_path(root: Path = ROOT) -> Path:
    return root / ".venv" / ".automata-setup-stamp"


def current_stamp(root: Path = ROOT) -> str:
    digest = hashlib.sha256()
    for name in INPUTS:
        path = root / name
        digest.update(name.encode())
        # normalise line endings so a Windows checkout and a Linux checkout hash the same
        digest.update(path.read_bytes().replace(b"\r\n", b"\n") if path.exists() else b"<missing>")
    return digest.hexdigest()


def record(root: Path = ROOT) -> None:
    path = stamp_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(current_stamp(root), encoding="utf-8")


def is_stale(root: Path = ROOT) -> bool:
    path = stamp_path(root)
    return not path.exists() or path.read_text(encoding="utf-8").strip() != current_stamp(root)


def stale_message(root: Path = ROOT) -> str | None:
    if not is_stale(root):
        return None
    reason = "has never been set up with the current bootstrap" if not stamp_path(root).exists() \
        else "changed since this machine was last set up (dependencies, MCP config or setup steps)"
    return (f"SETUP OUT OF DATE: this checkout {reason}. Before other work, run `{BOOTSTRAP}` from the repo root "
            "(it installs what changed, removes leftovers, re-registers scheduled jobs and runs the doctor), "
            "then report the doctor summary.")


def install_hooks(root: Path = ROOT) -> list[str]:
    """Install the post-pull hooks; leaves any hook that isn't ours alone. Returns notes for the user."""
    notes = []
    try:
        hooks_dir = Path(subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=root, check=True,  # nosec B603 B607
                                        capture_output=True, text=True).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return ["not a git checkout; no update hooks installed"]
    hooks_dir = hooks_dir if hooks_dir.is_absolute() else root / hooks_dir
    hooks_dir.mkdir(parents=True, exist_ok=True)
    bodies = {**{name: HOOK_BODY for name in HOOK_NAMES}, "pre-commit": PRE_COMMIT_BODY}
    for name, body in bodies.items():
        hook = hooks_dir / name
        if hook.exists() and HOOK_MARKER not in hook.read_text(encoding="utf-8", errors="ignore"):
            notes.append(f"kept your existing {name} hook; add the repo's check to it by hand (see scripts/setup_state.py)")
            continue
        hook.write_text(body, encoding="utf-8", newline="\n")
        hook.chmod(0o755)
    return notes


def after_pull(root: Path = ROOT) -> int:
    if not is_stale(root):
        return 0
    print("automata: the setup changed in this pull; updating this machine (scripts/bootstrap.py --yes) ...", flush=True)
    try:
        result = subprocess.run([sys.executable, str(root / "scripts" / "bootstrap.py"), "--yes", "--auto-schedules"],  # nosec B603
                                cwd=root, stdin=subprocess.DEVNULL)
        if result.returncode:
            print(f"automata: setup update finished with problems; see above, or run `{BOOTSTRAP}`", flush=True)
    except OSError as exc:
        print(f"automata: could not run the setup update ({exc}); run `{BOOTSTRAP}`", flush=True)
    return 0  # never fail the pull


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--after-pull", action="store_true")
    args = parser.parse_args(argv)
    if args.after_pull:
        return after_pull()
    message = stale_message()
    print(message or "automata: setup is up to date with this checkout")
    return 1 if message else 0


if __name__ == "__main__":
    sys.exit(main())
