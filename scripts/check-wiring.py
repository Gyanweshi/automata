#!/usr/bin/env python3
"""Fail on Python scripts and modules that nothing calls, so tools are not built and then forgotten.

A file is wired when another tracked file refers to it: an import (absolute or relative), a Make target, a
pyproject entry point, a scheduled job, a hook, a CI workflow, a skill or agent instruction, a dependency
manifest, or a doc that tells people to run it. Tests, package __init__ files and vendored third-party
skills (.agents/skills) are not checked. A one-off script belongs in the session scratchpad or workspace,
not in the repo.

Known orphans live in scripts/wiring-baseline.txt; only new ones fail.

    python scripts/check-wiring.py                    # fail on new orphans
    python scripts/check-wiring.py --all              # list every orphan, baseline included
    python scripts/check-wiring.py --update-baseline  # accept the current orphans as known debt
"""
from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 - git ls-files only
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "scripts" / "wiring-baseline.txt"
TEXT_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".js", ".mjs", ".cfg", ".ini", ".txt", ".sh",
                 ".ps1", ".cmd", ".bat", ""}
SKIP_PREFIXES = (".agents/skills/",)
# Files that list paths without calling them.
NOT_CALLERS = {"scripts/wiring-baseline.txt", "scripts/cross-platform-baseline.txt", ".gitignore", ".gitattributes",
               ".dockerignore"}  # vendored third-party skills, updated by their own installer
# Names too common to count a bare filename mention as a reference; these need an import or full path.
GENERIC_NAMES = {"cli", "agent", "outputs", "models", "utils", "base", "main", "config", "run", "types",
                 "helpers", "common", "core", "app", "server", "client"}


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, check=True,  # nosec B603 B607
                         capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line and (ROOT / line).is_file()]


def is_checked(path: str) -> bool:
    p = PurePosixPath(path)
    return (p.suffix == ".py" and not path.startswith(SKIP_PREFIXES) and "tests" not in p.parts
            and not p.name.startswith("test_") and p.name not in {"__init__.py", "conftest.py", "setup.py"})


def module_name(path: str) -> str:
    parts = list(PurePosixPath(path).with_suffix("").parts)
    if "src" in parts:
        parts = parts[parts.index("src") + 1:]
    return ".".join(parts)


def reference_patterns(path: str) -> tuple[re.Pattern, re.Pattern | None]:
    """(pattern for any file, pattern for files in the same package directory: relative imports)."""
    p = PurePosixPath(path)
    alternatives = [re.escape(path), re.escape(path.replace("/", "\\"))]
    if p.stem not in GENERIC_NAMES:
        alternatives.append(rf"(?<![\w.-]){re.escape(p.name)}\b")
    module = module_name(path)
    if "." in module:
        parent, leaf = module.rsplit(".", 1)
        alternatives += [rf"\b{re.escape(module)}\b",
                         rf"from\s+{re.escape(parent)}\s+import\s+[^\n]*\b{re.escape(leaf)}\b"]
    elif p.stem not in GENERIC_NAMES:  # a top-level module run as `python -m name` or imported as `import name`
        alternatives += [rf"\bimport\s+{re.escape(p.stem)}\b", rf"-m\s+{re.escape(p.stem)}\b",
                         rf"module\s*=\s*['\"]{re.escape(p.stem)}['\"]"]
    relative = re.compile(rf"from\s+\.{re.escape(p.stem)}\b|from\s+\.\s+import\s+[^\n]*\b{re.escape(p.stem)}\b")
    return re.compile("|".join(alternatives)), relative


def find_orphans(files: list[str], read=lambda f: (ROOT / f).read_text(encoding="utf-8", errors="ignore")) -> list[str]:
    sources: dict[str, str] = {}
    for f in files:
        name = PurePosixPath(f)
        if f in NOT_CALLERS or (name.suffix not in TEXT_SUFFIXES and name.name != "Makefile"):
            continue
        if "tests" in name.parts or name.name.startswith("test_"):
            continue  # a test importing a module does not make it used
        try:
            sources[f] = read(f)
        except (OSError, UnicodeDecodeError):
            continue
    orphans = []
    for path in sorted(f for f in files if is_checked(f)):
        anywhere, relative = reference_patterns(path)
        folder = str(PurePosixPath(path).parent)
        stem = PurePosixPath(path).stem  # every pattern contains the stem, so a plain substring test skips most files
        wired = False
        for src, body in sources.items():
            if src == path or stem not in body:
                continue
            if anywhere.search(body) or (str(PurePosixPath(src).parent) == folder and relative.search(body)):
                wired = True
                break
        if not wired:
            orphans.append(path)
    return orphans


def read_baseline() -> set[str]:
    if not BASELINE.is_file():
        return set()
    lines = BASELINE.read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true", help="list every orphan, baseline included")
    parser.add_argument("--update-baseline", action="store_true", help="accept current orphans as known debt")
    args = parser.parse_args(argv)
    orphans = find_orphans(tracked_files())
    baseline = read_baseline()

    if args.update_baseline:
        header = ("# Known unwired Python files (scripts/check-wiring.py). Wire them to a Make target, skill,\n"
                  "# import or schedule, or delete them, then remove their line.\n")
        BASELINE.write_text(header + "".join(f"{o}\n" for o in orphans), encoding="utf-8")
        print(f"wiring: baseline now lists {len(orphans)} file(s)")
        return 0

    new = [o for o in orphans if o not in baseline]
    fixed = sorted(baseline - set(orphans))
    for o in orphans if args.all else new:
        print(f"{'unwired' if o in new else 'known  '}  {o}")
    if fixed:
        print(f"wiring: {len(fixed)} baseline line(s) are now wired or gone; remove them: {', '.join(fixed)}")
    print(f"wiring: {len(new)} new, {len(orphans) - len(new)} known debt")
    if new:
        print("Each new script needs a caller: a Make target, a pyproject entry point, a skill or agent "
              "instruction, an import, a scheduled job or a hook. One-off scripts go in the scratchpad or "
              "workspace/, not the repo.", file=sys.stderr)
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())
