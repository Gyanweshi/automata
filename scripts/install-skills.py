#!/usr/bin/env python3
"""Register the repo's skills (Linux, macOS, Windows; replaces install-skills.sh and Install-Skills.ps1).

    python scripts/install-skills.py              # project shims for Codex and Claude (.agents/, .claude/)
    python scripts/install-skills.py --global     # also link each skills/<name> into ~/.claude/skills
    python scripts/install-skills.py --global --dest "%APPDATA%\\Claude\\skills"   # Claude Desktop on Windows

Global links are symlinks; on Windows without Developer Mode they fall back to directory junctions, which need
no special rights. An existing folder that is not a link is left alone and reported.
"""
from __future__ import annotations

import argparse
import os
import subprocess  # nosec B404 - runs the repo's own sync-skills.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def is_link(path: Path) -> bool:
    return path.is_symlink() or (os.name == "nt" and path.is_dir() and path.is_junction())


def link_dir(target: Path, link: Path) -> str:
    try:
        os.symlink(target, link, target_is_directory=True)
        return "symlink"
    except OSError:
        if os.name != "nt":
            raise
        import _winapi  # CPython on Windows

        _winapi.CreateJunction(str(target), str(link))
        return "junction"


def install_global(dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    skipped = 0
    for skill in sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()):
        link = dest / skill.name
        if is_link(link):
            link.unlink() if link.is_symlink() else os.rmdir(link)
            action = "updated"
        elif link.exists():
            print(f"  skip {skill.name}: {link} exists and is not a link (remove it to relink)")
            skipped += 1
            continue
        else:
            action = "installed"
        kind = link_dir(skill.resolve(), link)
        print(f"  {action} {skill.name} ({kind})")
    print(f"global skills linked into {dest}" + (f"; {skipped} skipped" if skipped else ""))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--global", dest="global_", action="store_true", help="also link skills into a user folder")
    parser.add_argument("--dest", default=str(Path.home() / ".claude" / "skills"))
    args = parser.parse_args(argv)
    venv_python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    python = str(venv_python) if venv_python.exists() else sys.executable  # sync-skills needs python-frontmatter
    result = subprocess.run([python, str(ROOT / "scripts" / "sync-skills.py"), "--sync"], cwd=ROOT)  # nosec B603
    if args.global_:
        install_global(Path(os.path.expandvars(args.dest)).expanduser())
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
