#!/usr/bin/env python3
"""Flag code that will work on one of our machines (Linux / Windows) but not the other.

Checks tracked files for:
  one-os-script   a .sh/.bash or .ps1/.cmd/.bat script with no counterpart for the other OS
                  (write the logic once in Python instead; a launcher may wrap it)
  machine-path    a hardcoded user/machine path (/home/<user>, /mnt/<disk>, C:\\Users\\<name>, /Users/<name>)
  crlf-shell      a shell script with Windows line endings (bash fails on them)

Known debt lives in scripts/cross-platform-baseline.txt; only findings not in it fail the check, so new
work must be cross-platform while old work is migrated over time.

    python scripts/check-cross-platform.py                    # fail on new findings
    python scripts/check-cross-platform.py --all              # list every finding, baseline included
    python scripts/check-cross-platform.py --update-baseline  # accept the current findings as known debt
"""
from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 - git ls-files only
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "scripts" / "cross-platform-baseline.txt"
UNIX_SCRIPTS = {".sh", ".bash"}
WINDOWS_SCRIPTS = {".ps1", ".cmd", ".bat"}
CODE_SUFFIXES = {".py", ".sh", ".bash", ".ps1", ".cmd", ".bat", ".js", ".mjs", ".ts", ".tsx", ".json", ".toml",
                 ".yaml", ".yml", ".cfg", ".ini"}
SKIP_PATHS = {".claude/settings.local.json", "scripts/cross-platform-baseline.txt", "scripts/check-cross-platform.py"}
MACHINE_PATH = re.compile(r"(/home/[a-z][\w.-]*/|/mnt/sd[a-z]|[A-Za-z]:\\\\?Users\\\\?[\w.-]+|/Users/[\w.-]+/)")


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, check=True,  # nosec B603 B607
                         capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line and (ROOT / line).is_file()]


def stem_key(path: str) -> str:
    """install-skills.sh and Install-Skills.ps1 are the same script for two OSes."""
    p = Path(path)
    return str(p.parent / re.sub(r"[_\s]+", "-", p.stem).lower())


def findings(files: list[str]) -> list[str]:
    results: list[str] = []
    unix = {stem_key(f): f for f in files if Path(f).suffix in UNIX_SCRIPTS}
    windows = {stem_key(f): f for f in files if Path(f).suffix in WINDOWS_SCRIPTS}
    for key, f in sorted(unix.items()):
        if key not in windows:
            results.append(f"one-os-script\t{f}\tLinux/macOS only")
    for key, f in sorted(windows.items()):
        if key not in unix:
            results.append(f"one-os-script\t{f}\tWindows only")

    for f in files:
        path = ROOT / f
        suffix = path.suffix
        if f in SKIP_PATHS or suffix not in CODE_SUFFIXES or "node_modules/" in f:
            continue
        data = path.read_bytes()
        if suffix in UNIX_SCRIPTS and b"\r\n" in data:
            results.append(f"crlf-shell\t{f}\tCRLF line endings")
        text = data.decode("utf-8", errors="ignore")
        for match in sorted(set(MACHINE_PATH.findall(text))):
            results.append(f"machine-path\t{f}\t{match}")
    return sorted(set(results))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="list every finding, baseline included")
    parser.add_argument("--update-baseline", action="store_true", help="write current findings as known debt")
    args = parser.parse_args(argv)

    current = findings(tracked_files())
    if args.update_baseline:
        BASELINE.write_text("# Known cross-platform debt (scripts/check-cross-platform.py). Remove lines as you fix them.\n"
                            + "".join(line + "\n" for line in current), encoding="utf-8")
        print(f"baseline: {len(current)} known finding(s) written to {BASELINE.relative_to(ROOT)}")
        return 0

    known = set()
    if BASELINE.exists():
        known = {line for line in BASELINE.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")}
    new = [line for line in current if line not in known]
    fixed = sorted(known - set(current))
    for line in (current if args.all else new):
        kind, path, detail = line.split("\t")
        print(f"{'NEW ' if line in new else 'known'} {kind:14} {path}  ({detail})")
    if fixed:
        print(f"{len(fixed)} baseline line(s) are fixed now; run --update-baseline to drop them")
    print(f"cross-platform: {len(new)} new, {len(current) - len(new)} known debt")
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())
