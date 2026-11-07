#!/usr/bin/env python3
"""Deterministic Lanczos upscale: source -> exact 4K canvas -> exact 8K (Linux, macOS, Windows; needs ffmpeg).

    python upscale-storyboard-image.py IMAGE [--output-dir DIR] [--width-4k 3840 --height-4k 2160]
                                       [--pad-color black|white|transparent] [--force] [--dry-run]

Writes DIR/4k-exact/<name>-4k.png and DIR/8k-exact/<name>-8k.png (DIR defaults to <name>-upscaled beside the
image). The 8K pass scales the 4K result, matching the proven storyboard workflow. No generative model touches
the pixels.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess  # nosec B404 - ffmpeg
import sys
from pathlib import Path

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def plan(source: Path, output_dir: Path | None, width: int, height: int, pad: str) -> dict:
    root = (output_dir or source.parent / f"{source.stem}-upscaled").resolve()
    four_k = root / "4k-exact" / f"{source.stem}-4k.png"
    eight_k = root / "8k-exact" / f"{source.stem}-8k.png"
    return {
        "source": str(source.resolve()), "four_k": str(four_k), "eight_k": str(eight_k),
        "filter_4k": (f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=lanczos,"
                      f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={pad},setsar=1"),
        "filter_8k": f"scale={width * 2}:{height * 2}:flags=lanczos,setsar=1",
        "canvas_4k": f"{width}x{height}", "canvas_8k": f"{width * 2}x{height * 2}",
        "method": "Lanczos: source -> 4K -> 8K",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--width-4k", type=int, default=3840)
    parser.add_argument("--height-4k", type=int, default=2160)
    parser.add_argument("--pad-color", choices=["black", "white", "transparent"], default="black")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    args = parser.parse_args(argv)

    if args.width_4k % 2 or args.height_4k % 2:
        parser.error("--width-4k and --height-4k must be even")
    if not args.image.is_file():
        parser.error(f"{args.image} is not a file")
    if args.image.suffix.lower() not in SUPPORTED:
        parser.error(f"unsupported image type {args.image.suffix}")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg and not args.dry_run:
        parser.error("ffmpeg is required (python scripts/deps.py install ffmpeg)")

    p = plan(args.image, args.output_dir, args.width_4k, args.height_4k, args.pad_color)
    if args.dry_run:
        print(json.dumps(p, indent=2))
        return 0
    four_k, eight_k = Path(p["four_k"]), Path(p["eight_k"])
    if not args.force and (four_k.exists() or eight_k.exists()):
        parser.error(f"output already exists under {four_k.parent.parent}; use --force to replace it")
    four_k.parent.mkdir(parents=True, exist_ok=True)
    eight_k.parent.mkdir(parents=True, exist_ok=True)
    base = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    if subprocess.run(base + ["-i", p["source"], "-vf", p["filter_4k"], "-frames:v", "1", str(four_k)]).returncode:  # nosec B603
        raise SystemExit("ffmpeg failed during the 4K Lanczos pass")
    if subprocess.run(base + ["-i", str(four_k), "-vf", p["filter_8k"], "-frames:v", "1", str(eight_k)]).returncode:  # nosec B603
        raise SystemExit("ffmpeg failed during the 8K Lanczos pass")
    print(json.dumps({k: p[k] for k in ("source", "four_k", "eight_k", "method", "canvas_4k", "canvas_8k")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
