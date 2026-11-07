#!/usr/bin/env python3
"""Crop a region out of a large still and render it as a short clip, optionally with Ken Burns motion.

Linux, macOS, Windows; needs ffmpeg and ffprobe.

    python crop-motion-broll.py INPUT OUTPUT_DIR [--width 3840 --height 2160] [--motion static|pan-left|pan-right|
        pan-up|pan-down|zoom-in|zoom-out] [--duration 5] [--fps 30] [--zoom-amount 0.08] [--center-x 0.5]
        [--center-y 0.5] [--crf 15] [--preset medium] [--assemble] [--allow-upsample] [--force] [--dry-run]

INPUT is one image or a folder of images (rendered in name order). Motions other than static hold the crop at
(1 + zoom amount), so the source must already be that big, or ffmpeg would invent detail; upscale first with
upscale-storyboard-image.py, or pass --allow-upsample.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess  # nosec B404 - ffmpeg / ffprobe
import sys
from pathlib import Path

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
MOTIONS = ["static", "pan-left", "pan-right", "pan-up", "pan-down", "zoom-in", "zoom-out"]


def video_filter(motion: str, width: int, height: int, frames: int, fps: int, zoom: float, cx: float, cy: float) -> str:
    """The same ffmpeg filter expressions the original PowerShell script used."""
    if motion == "static":
        return (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height}:(iw-ow)*{cx}:(ih-oh)*{cy},format=yuv420p")
    x_center, y_center = f"iw*{cx}-(iw/zoom/2)", f"ih*{cy}-(ih/zoom/2)"
    last = frames - 1
    if motion == "zoom-in":
        z, x, y = f"1+{zoom}*on/({last})", x_center, y_center
    elif motion == "zoom-out":
        z, x, y = f"(1+{zoom})-{zoom}*on/({last})", x_center, y_center
    else:
        z = f"1+{zoom}"
        x, y = {
            "pan-left": (f"(iw-iw/zoom)*(1-on/({last}))", y_center),
            "pan-right": (f"(iw-iw/zoom)*(on/({last}))", y_center),
            "pan-up": (x_center, f"(ih-ih/zoom)*(1-on/({last}))"),
            "pan-down": (x_center, f"(ih-ih/zoom)*(on/({last}))"),
        }[motion]
    return f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={width}x{height},fps={fps},format=yuv420p"


def ffmpeg_args(source: Path, output: Path, a: argparse.Namespace) -> list[str]:
    frames = a.duration * a.fps
    vf = video_filter(a.motion, a.width, a.height, frames, a.fps, a.zoom_amount, a.center_x, a.center_y)
    timing = ["-t", str(a.duration), "-r", str(a.fps)] if a.motion == "static" else ["-frames:v", str(frames)]
    codec = ["-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    return ["-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-i", str(source), "-vf", vf, *timing, *codec,
            str(output)]


def image_size(ffprobe: str, path: Path) -> tuple[int, int]:
    out = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",  # nosec B603
                          "-of", "csv=p=0:s=x", str(path)], capture_output=True, text=True)
    if out.returncode or "x" not in out.stdout:
        raise SystemExit(f"ffprobe could not read dimensions for {path}")
    w, h = out.stdout.strip().split("x")[:2]
    return int(w), int(h)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", type=Path)
    p.add_argument("output_dir", type=Path)
    p.add_argument("--width", type=int, default=3840)
    p.add_argument("--height", type=int, default=2160)
    p.add_argument("--motion", choices=MOTIONS, default="static")
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--zoom-amount", type=float, default=0.08)
    p.add_argument("--center-x", type=float, default=0.5)
    p.add_argument("--center-y", type=float, default=0.5)
    p.add_argument("--crf", type=int, default=15)
    p.add_argument("--preset", default="medium")
    p.add_argument("--assemble", action="store_true", help="also join the clips into assembled-<motion>.mp4")
    p.add_argument("--allow-upsample", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="print the ffmpeg commands, render nothing")
    a = p.parse_args(argv)

    if a.width % 2 or a.height % 2:
        p.error("--width and --height must be even")
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not (ffmpeg and ffprobe):
        p.error("ffmpeg and ffprobe are required (python scripts/deps.py install ffmpeg)")
    if a.input.is_dir():
        sources = sorted(f for f in a.input.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED)
    elif a.input.is_file() and a.input.suffix.lower() in SUPPORTED:
        sources = [a.input]
    else:
        p.error(f"no supported images at {a.input}")
    if not sources:
        p.error(f"no supported images at {a.input}")

    out_root = a.output_dir.resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    zoom_needed = 1.0 if a.motion == "static" else 1.0 + a.zoom_amount
    need_w, need_h = math.ceil(a.width * zoom_needed), math.ceil(a.height * zoom_needed)
    generated: list[Path] = []
    for source in sources:
        w, h = image_size(ffprobe, source)
        if not a.allow_upsample and (w < need_w or h < need_h):
            raise SystemExit(f"{source.name} is {w}x{h}, below the {need_w}x{need_h} needed for --motion {a.motion} "
                             f"at --zoom-amount {a.zoom_amount} without inventing pixels. Run "
                             "upscale-storyboard-image.py first, or pass --allow-upsample.")
        output = out_root / f"{source.stem}-{a.motion}-{a.duration}s.mp4"
        if output.exists() and not a.force:
            print(f"skipping existing {output} (use --force to overwrite)", file=sys.stderr)
            generated.append(output)
            continue
        command = [ffmpeg, *ffmpeg_args(source, output, a)]
        if a.dry_run:
            print(json.dumps(command))
            continue
        if subprocess.run(command).returncode:  # nosec B603
            raise SystemExit(f"ffmpeg failed rendering {source.name}")
        generated.append(output)

    if a.assemble and len(generated) > 1 and not a.dry_run:
        listing = out_root / "sequence.txt"
        listing.write_text("".join(f"file '{g.name}'\n" for g in generated), encoding="ascii")
        assembled = out_root / f"assembled-{a.motion}.mp4"
        if subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",  # nosec B603
                           "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(assembled)]).returncode:
            raise SystemExit("ffmpeg failed to assemble the sequence")
        generated.append(assembled)
    for g in generated:
        print(g)
    return 0


if __name__ == "__main__":
    sys.exit(main())
