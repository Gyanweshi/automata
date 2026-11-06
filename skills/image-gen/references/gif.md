# Animated GIF workflow

Use `scripts/make_gif.py` to assemble ordered still frames. This is frame animation,
not a video-generation model or automatic motion interpolation. For complex natural
motion, explain the limits of separately generated frames rather than promising
smooth video. No API calls are made by the assembler.

1. Reuse supplied frames where possible. Otherwise choose a short motion cycle and
   a modest frame count (for example 8 frames). Before paid generation, communicate
   the number of calls and respect the existing API authorization and budget.
2. Generate an anchor frame. For each subsequent frame use it as an image reference
   through `image_gen.py edit`; specify the exact next pose while locking identity,
   camera, background, lighting, palette, scale, and framing. Keep prompts and frames
   in the project. Independent text-to-image batch jobs are not temporally coherent.
3. Inspect every frame for drift. Keep equal canvas dimensions. Order the paths
   explicitly; do not rely on lexicographic sorting of filenames such as 1, 10, 2.
4. Assemble with the CLI below. `--ping-pong` reverses the interior frames so
   endpoints are not doubled. Use it for reversible motions, not walking forward.
5. Inspect the animation in a viewer that plays GIFs, including the last-to-first
   transition. Check timing, flicker, subject drift, size and palette banding.
   Report if only frame inspection was possible. Local assembly can be repeated
   freely; generating replacement frames may require additional paid calls.

Install Pillow in the selected virtual environment: `python -m pip install pillow`.
Run with explicit ordered paths (at least two):

```text
python "PATH_TO_SKILL/scripts/make_gif.py" --frames frame-01.png frame-02.png frame-03.png --out output/imagegen/motion.gif --fps 8 --width 512 --loop 0 --ping-pong
```

- `--fps`: 10 by default; 1–50. GIF timing is rounded to 10 ms increments.
- `--duration-ms`: one duration per source frame, overriding the default FPS;
  do not combine with `--fps`. Each must be 20–655350 ms and divisible by 10.
- `--width`: proportional resize of all frames; otherwise retain source size.
  Mismatched source dimensions fail instead of silently stretching/cropping.
- `--loop 0`: repeat forever (default); `--loop -1`: play once;
  positive values specify additional repeats.
- `--matte '#ffffff'`: explicit opaque background for transparent inputs. Without
  a matte, transparent inputs are rejected so alpha is never silently discarded.
  This assembler currently creates opaque GIFs, not transparent animated stickers.
- `--force`: replace an existing output only when the user authorized replacement.

GIF has a limited color palette. A common palette is used across frames to reduce
color flicker; photographic gradients may still show banding. Identical adjacent
frames may be merged by the encoder while preserving total duration.

[Pillow GIF documentation](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif)
