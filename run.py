#!/usr/bin/env python3
"""Interactive launcher — asks what you want, then runs it."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
BRANDS_DIR = ROOT / "brands"


def pick(prompt: str, options: list[str]) -> str:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        raw = input("  > ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        # also accept typing the name directly
        if raw in options:
            return raw
        print(f"  Pick 1–{len(options)}")


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"\n{prompt}{suffix}: ").strip()
    return val or default


def brands() -> list[str]:
    try:
        from agency_common.brand_loader import list_brands
        return list_brands()
    except Exception:
        return sorted(
            p.stem for p in BRANDS_DIR.glob("*.yaml") if not p.stem.startswith("_")
        )


def main() -> None:
    available = brands()
    if not available:
        sys.exit("No brands found in brands/. Add a YAML file first.")

    brand = pick("Which brand?", available)

    action = pick(
        "What do you want to run?",
        ["research", "storyboard", "content", "pipeline", "week", "dry-run"],
    )

    cmd = ["make", action, f"BRAND={brand}"]

    if action in ("storyboard", "content", "pipeline"):
        topic = ask("Topic")
        if not topic:
            sys.exit("Topic is required for this action.")
        content_type = pick(
            "Content type?",
            ["carousel", "caption", "reel", "post", "article", "document_carousel"],
        )
        cmd += [f"TOPIC={topic}", f"TYPE={content_type}"]

    print(f"\n$ {' '.join(cmd)}\n{'─' * 50}")
    result = subprocess.run(cmd, cwd=ROOT)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
