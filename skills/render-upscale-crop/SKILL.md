---
name: render-upscale-crop
description: Deterministically upscale a render or photo to exact 4K/8K via Lanczos, then crop small regions out of it — with optional Ken Burns pan/zoom motion — to produce short b-roll video clips. Use when the user asks to upscale a render/image, extract or crop a detail from a large image, turn a still hero shot into motion b-roll, or make micro clips from a panorama/render.
---

# Render Upscale + Crop-to-Motion

Two-stage, deterministic pipeline for turning one large still render into upscaled
stills and/or short motion clips of small regions within it. Both stages are pure
Lanczos/ffmpeg resampling — no generative model touches the pixels, so geometry,
text, and product/architectural detail never drift. Proven on the
`Real_Estate_AI_Video` architectural-frame-pack project.

This skill is self-contained: both scripts live in `scripts/` right next to this
file, so the whole `render-upscale-crop/` folder can be copied or shared as-is.
Both scripts are Python and run the same on Linux, macOS and Windows (`python3` on
Linux/macOS, `python` or `py` on Windows). The commands below assume you're running
from inside this skill folder; adjust the `scripts/...` paths if invoking from elsewhere.
Add `--dry-run` to either script to see the plan or ffmpeg commands without rendering.

## Defaults when the request is generic

If the user just hands over an image and says something like "use this skill on
it" with no further detail — do **not** copy the `--motion pan-right` value from
the worked example at the bottom of this file. That value is illustrative, not a
default, and pan/zoom/duration/orientation are all things the source request may
not have specified at all.

- **No motion requested → `--motion static`.** This matches the script's own
  default: a still, centered crop with no video motion. Only pick a
  `pan-*`/`zoom-*` motion when the user's wording actually implies video/motion —
  "b-roll", "reel", "Ken Burns", "pan", "zoom", "clip", "animate".
- **No orientation given →** default to landscape `3840x2160`, unless the source
  image itself is portrait, in which case use `2160x3840`.
- **No crop region given →** centered (`--center-x 0.5 --center-y 0.5`).
- If the source is already large enough for the requested output, skip Stage 1
  entirely and go straight to Stage 2 — don't upscale by default just because
  the script exists.
- If motion, duration, crop region, or intended aspect ratio genuinely can't be
  inferred from the request (e.g. it's ambiguous whether the user wants a still
  or a clip), ask rather than guessing.

## Stage 1 — Upscale (`scripts/upscale-storyboard-image.py`)

```bash
python scripts/upscale-storyboard-image.py "<source-image>" --output-dir "<run-dir>" \
  [--width-4k 3840] [--height-4k 2160] [--pad-color black|white|transparent] [--force]
```

Runs the proven sequence `source -> exact 4K -> exact 8K`, chaining the 8K pass off
the 4K result (not the raw source). Writes PNGs to `<run-dir>/4k-exact/` and
`<run-dir>/8k-exact/`. Refuses to overwrite existing output unless `--force`.
For vertical sources, swap the canvas: `--width-4k 2160 --height-4k 3840`.

Only run this stage if the source isn't already at the resolution Stage 2 needs —
skip straight to Stage 2 for sources that are already large enough.

## Stage 2 — Crop a region, optionally with motion (`scripts/crop-motion-broll.py`)

```bash
python scripts/crop-motion-broll.py "<image-or-directory>" "<run-dir>" \
  --motion static|pan-left|pan-right|pan-up|pan-down|zoom-in|zoom-out \
  [--width 3840] [--height 2160] [--duration 5] [--fps 30] \
  [--zoom-amount 0.08] [--center-x 0.5] [--center-y 0.5] [--crf 15] [--preset medium] \
  [--assemble] [--allow-upsample] [--force]
```

- **the input** — a single image, or a directory. When it's a directory, every
  supported image inside (`.png .jpg .jpeg .webp .tif .tiff .bmp`) is processed in
  filename order, each producing its own clip.
- **`--motion static`** — a plain centered (or off-center, via `--center-x`/`--center-y`)
  crop to `--width`x`--height`, held for `--duration`. This is the "take a small
  part from a big picture" case with no motion.
- **`pan-left/right/up/down`** — fixed zoom (`1 + --zoom-amount`), the crop window
  slides linearly across the extra room that zoom creates.
- **`zoom-in`/`zoom-out`** — the crop zooms smoothly between `1.0` and
  `1 + --zoom-amount`, centered on `--center-x`/`--center-y`.
- **`--assemble`** — when a directory produced more than one clip, concatenates them
  (in filename order) into `assembled-<motion>.mp4` in the same run.
- **Orientation** — `--width`/`--height` just need to be even. Default is landscape
  `3840x2160`; pass `--width 2160 --height 3840` for vertical/reels.

### Resolution guardrail

Every motion except `static` needs the source to already be at least
`width * (1 + zoom amount)` by `height * (1 + zoom amount)` pixels, or the crop would be
inventing detail rather than resampling it. The script checks this per image (via
`ffprobe`) and stops with a clear message telling you to run Stage 1 first —
pass `--allow-upsample` only if you deliberately want to let ffmpeg upsample.

### Why the ffmpeg internals matter here (do not remove `-frames:v`)

Motion clips use ffmpeg's `zoompan` filter fed by a looped still image (`-loop 1`).
Because the loop is infinite, `zoompan`'s own `d=<frames>` parameter is **not**
sufficient to stop the render — the ffmpeg process must also be capped with
`-frames:v <frames>` on the command line, or it renders forever. This is already
wired into the script for every zoompan branch; if this script is ever edited,
keep that flag on all three (`pan-*`, `zoom-in`, `zoom-out`) branches.

## Requirements

`ffmpeg` and `ffprobe` on `PATH` (both scripts check and fail fast if missing).

## Output location

Keep upscaled intermediates, crop experiments, and motion variants under a task-specific
`workspace/<project>/` directory while selection or review is active. Human-readable
notes go to the matching vault project with `status: draft`. After approval, copy only
the selected deliverable and necessary provenance into the matching vault project; do
not update brand Memory before finalization.

## Worked examples (illustrative — pick the motion that matches the actual request)

```bash
# 1. Upscale a rendered panorama to exact 4K -> 8K (run once, shared by all examples below)
python scripts/upscale-storyboard-image.py "$OBSIDIAN_VAULT_PATH/Research/MyProject/renders/panorama.png" \
  --output-dir workspace/MyProject/upscaled

# 2a. Generic "crop me a detail from this image" request -> static, no motion (the default)
python scripts/crop-motion-broll.py workspace/MyProject/upscaled/8k-exact/panorama-8k.png workspace/MyProject/broll \
  --motion static --width 3840 --height 2160 --duration 5

# 2b. "Make me a b-roll clip / pan across it" -> pan-right
python scripts/crop-motion-broll.py workspace/MyProject/upscaled/8k-exact/panorama-8k.png workspace/MyProject/broll \
  --motion pan-right --width 3840 --height 2160 --duration 6

# 2c. "Ken Burns zoom into it" -> zoom-in
python scripts/crop-motion-broll.py workspace/MyProject/upscaled/8k-exact/panorama-8k.png workspace/MyProject/broll \
  --motion zoom-in --width 3840 --height 2160 --duration 6
```
