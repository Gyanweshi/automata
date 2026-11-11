#!/usr/bin/env python3
"""Git pre-commit check (installed by scripts/bootstrap.py): blocks commits that break the repo's rules.

Runs for every committer, Claude Code, Codex or a person, because it is a git hook, not an agent hook. Fast checks
only (a few seconds); the full suite runs in CI. Bypass in an emergency with `git commit --no-verify`.
"""
from __future__ import annotations

import os
import subprocess  # nosec B404 - runs the repo's own check scripts
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

CHECKS = [
    ("cross-platform rules", ["scripts/check-cross-platform.py"]),
    ("dependency pins agree", ["scripts/deps.py", "check", "--pins-only"]),
    ("dependency register up to date", ["scripts/deps.py", "docs", "--check"]),
    ("skill registrations", ["scripts/sync-skills.py", "--check"]),
    ("every script has a caller", ["scripts/check-wiring.py"]),
    ("hooks start on a fresh clone", ["scripts/check-hooks.py"]),
]


def main() -> int:
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    failed = []
    for name, args in CHECKS:
        result = subprocess.run([python, *args], cwd=ROOT, capture_output=True, text=True,  # nosec B603
                                encoding="utf-8", errors="replace")
        if result.returncode:
            failed.append(name)
            print(f"pre-commit: FAILED {name}", file=sys.stderr)
            print("\n".join((result.stdout + result.stderr).strip().splitlines()[-12:]), file=sys.stderr)
    if failed:
        print(f"\npre-commit: commit blocked ({', '.join(failed)}). Fix the above, or see AGENTS.md. "
              "Emergency bypass: git commit --no-verify", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
