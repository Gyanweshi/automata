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
The commands below assume you're running from inside this skill folder — adjust
the `.\scripts\...` paths (or `cd` here first) if invoking from elsewhere.

## Defaults when the request is generic

If the user just hands over an image and says something like "use this skill on
it" with no further detail — do **not** copy the `-Motion pan-right` value from
the worked example at the bottom of this file. That value is illustrative, not a
default, and pan/zoom/duration/orientation are all things the source request may
not have specified at all.

- **No motion requested → `-Motion static`.** This matches the script's own
  parameter default: a still, centered crop with no video motion. Only pick a
  `pan-*`/`zoom-*` motion when the user's wording actually implies video/motion —
  "b-roll", "reel", "Ken Burns", "pan", "zoom", "clip", "animate".
- **No orientation given →** default to landscape `3840x2160`, unless the source
  image itself is portrait, in which case use `2160x3840`.
- **No crop region given →** centered (`-CenterX 0.5 -CenterY 0.5`).
- If the source is already large enough for the requested output, skip Stage 1
  entirely and go straight to Stage 2 — don't upscale by default just because
  the script exists.
- If motion, duration, crop region, or intended aspect ratio genuinely can't be
  inferred from the request (e.g. it's ambiguous whether the user wants a still
  or a clip), ask rather than guessing.

## Stage 1 — Upscale (`scripts/upscale-storyboard-image.ps1`)

```powershell
.\scripts\upscale-storyboard-image.ps1 `
  -InputPath "<source-image>" `
  -OutputDirectory "<run-dir>" `
  [-Width4K 3840] [-Height4K 2160] `
  [-PadColor black|white|transparent] [-Force]
```

Runs the proven sequence `source -> exact 4K -> exact 8K`, chaining the 8K pass off
the 4K result (not the raw source). Writes PNGs to `<run-dir>/4k-exact/` and
`<run-dir>/8k-exact/`. Refuses to overwrite existing output unless `-Force`.
For vertical sources, swap the canvas: `-Width4K 2160 -Height4K 3840`.

Only run this stage if the source isn't already at the resolution Stage 2 needs —
skip straight to Stage 2 for sources that are already large enough.

## Stage 2 — Crop a region, optionally with motion (`scripts/crop-motion-broll.ps1`)

```powershell
.\scripts\crop-motion-broll.ps1 `
  -InputPath "<image-or-directory>" `
  -OutputDirectory "<run-dir>" `
  -Motion static|pan-left|pan-right|pan-up|pan-down|zoom-in|zoom-out `
  [-Width 3840] [-Height 2160] `
  [-DurationSeconds 5] [-Fps 30] `
  [-ZoomAmount 0.08] [-CenterX 0.5] [-CenterY 0.5] `
  [-Crf 15] [-Preset medium] `
  [-Assemble] [-AllowUpsample] [-Force]
```

- **`-InputPath`** — a single image, or a directory. When it's a directory, every
  supported image inside (`.png .jpg .jpeg .webp .tif .tiff .bmp`) is processed in
  filename order, each producing its own clip.
- **`-Motion static`** — a plain centered (or off-center, via `-CenterX`/`-CenterY`)
  crop to `-Width`x`-Height`, held for `-DurationSeconds`. This is the "take a small
  part from a big picture" case with no motion.
- **`pan-left/right/up/down`** — fixed zoom (`1 + -ZoomAmount`), the crop window
  slides linearly across the extra room that zoom creates.
- **`zoom-in`/`zoom-out`** — the crop zooms smoothly between `1.0` and
  `1 + -ZoomAmount`, centered on `-CenterX`/`-CenterY`.
- **`-Assemble`** — when a directory produced more than one clip, concatenates them
  (in filename order) into `assembled-<motion>.mp4` in the same run.
- **Orientation** — `-Width`/`-Height` just need to be even. Default is landscape
  `3840x2160`; pass `-Width 2160 -Height 3840` for vertical/reels.

### Resolution guardrail

Every motion except `static` needs the source to already be at least
`Width * (1+ZoomAmount)` by `Height * (1+ZoomAmount)` pixels, or the crop would be
inventing detail rather than resampling it. The script checks this per image (via
`ffprobe`) and throws with a clear message telling you to run Stage 1 first —
pass `-AllowUpsample` only if you deliberately want to let ffmpeg upsample.

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

```powershell
# 1. Upscale a rendered panorama to exact 4K -> 8K (run once, shared by all examples below)
.\scripts\upscale-storyboard-image.ps1 `
  -InputPath "D:\Brainiac2\Research\MyProject\renders\panorama.png" `
  -OutputDirectory "workspace/MyProject/upscaled"

# 2a. Generic "crop me a detail from this image" request -> static, no motion (the default)
.\scripts\crop-motion-broll.ps1 `
  -InputPath "workspace/MyProject/upscaled/8k-exact/panorama-8k.png" `
  -OutputDirectory "workspace/MyProject/broll" `
  -Motion static -Width 3840 -Height 2160 -DurationSeconds 5

# 2b. "Make me a b-roll clip / pan across it" -> pan-right
.\scripts\crop-motion-broll.ps1 `
  -InputPath "workspace/MyProject/upscaled/8k-exact/panorama-8k.png" `
  -OutputDirectory "workspace/MyProject/broll" `
  -Motion pan-right -Width 3840 -Height 2160 -DurationSeconds 6

# 2c. "Ken Burns zoom into it" -> zoom-in
.\scripts\crop-motion-broll.ps1 `
  -InputPath "workspace/MyProject/upscaled/8k-exact/panorama-8k.png" `
  -OutputDirectory "workspace/MyProject/broll" `
  -Motion zoom-in -Width 3840 -Height 2160 -DurationSeconds 6
```
