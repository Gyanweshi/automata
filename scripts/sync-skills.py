#!/usr/bin/env python3
"""Create missing portable project shims; check drift without overwriting installations."""
from __future__ import annotations

import argparse
from pathlib import Path

import frontmatter


def sync(root: Path, write: bool = False) -> list[str]:
    issues = []
    for source in sorted((root / "skills").glob("*/SKILL.md")):
        text = source.read_text(encoding="utf-8")
        metadata = frontmatter.loads(text).metadata
        if not metadata.get("name") or not metadata.get("description"):
            issues.append(f"Invalid skill metadata: {source}")
            continue
        header = text.split("---", 2)[1]
        link = f"../../../skills/{source.parent.name}/SKILL.md"
        content = (f"---{header}---\n\nRead and follow the canonical instructions at\n"
                   f"[`skills/{source.parent.name}/SKILL.md`]({link}).\n"
                   "Resolve its scripts and references relative to that canonical skill directory.\n")
        for directory in (".agents/skills", ".claude/skills"):
            target = root / directory / source.parent.name / "SKILL.md"
            if not target.exists() and write and not target.parent.exists() and not target.parent.is_symlink():
                target.parent.mkdir(parents=True)
                target.write_text(content, encoding="utf-8")
            if not target.is_file():
                issues.append(f"Missing registration: {target}")
                continue
            existing = target.read_text(encoding="utf-8")
            registered = frontmatter.loads(existing).metadata
            if any(registered.get(key) != metadata.get(key) for key in ("name", "description")):
                issues.append(f"Metadata differs (preserved): {target}")
            if target.resolve() != source.resolve() and link not in existing:
                issues.append(f"Not a canonical shim (preserved): {target}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync", action="store_true", help="Create missing registrations only")
    parser.add_argument("--check", action="store_true", help="Check registrations without writing")
    args = parser.parse_args()
    if args.sync and args.check:
        parser.error("Choose --sync or --check")
    root = Path(__file__).resolve().parents[1]
    issues = sync(root, write=args.sync)
    for issue in issues:
        print(issue)
    print(f"{len(list((root / 'skills').glob('*/SKILL.md')))} canonical skills checked for Codex and Claude; {len(issues)} issue(s).")
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
