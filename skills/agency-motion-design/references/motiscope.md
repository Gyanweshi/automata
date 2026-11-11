# Reference motion analysis with Motiscope

Use for supplied animation recordings when timing, easing, holds or loop structure
would inform a recreation. It is optional for original motion design and does not
replace narration timing or the video editor's timeline.

## Run

From the repo root, use the repo virtualenv Python (`.venv/bin/python` on Linux,
`.venv/Scripts/python.exe` on Windows) for these commands:

```text
python scripts/deps.py install motiscope
python scripts/motiscope.py check
python scripts/motiscope.py analyze <recording> --preset balanced --out workspace/<project>/motion/<run>/analysis
```

The installer uses the full commit pin in `dependencies.toml`, verifies Git object
integrity, and keeps each version in `workspace/tools/motiscope/<commit>/`.
It preserves the upstream MIT license. No global plugin, account, API key or paid
generation is needed. Missing FFmpeg: `python scripts/deps.py install ffmpeg`.
Update through `python scripts/deps.py set-pin motiscope <full-commit-sha>`, then
install and smoke-test the new version; regenerate dependency docs.

Use `--start 0:12 --end 0:15` for a selected interval; timestamps remain relative
to the source recording. `draft` reduces frame count; `detailed` helps with fine
motion; `landing` prioritizes readable page sections. Reuse existing analysis
unless the source or requested interval changes.

## Interpret and hand off

Read the generated `report.md`, `motion.json`, and `manifest.json`, then inspect
the selected frames in timestamp order. The report is intermediate tool output,
not a final creative brief. Sample missing moments or regions directly from the
source when the selected frames omit relevant motion.

Treat fitted easing, stagger and loop values as estimates to verify, not recovered
authoring parameters. A uniform fade can produce a false stagger hint; loop
detection can return a half-cycle. Scroll-recording durations depend on the person
scrolling and must not be copied as fixed animation durations. When deriving
velocities or ratios, read the installed `references/measurement-traps.md`
(`python scripts/motiscope.py home` locates it) and cross-check independently.

Carry source timestamps, observed elements, motion properties, confidence and
chosen timings into the project's existing timeline/asset manifest. Keep visual
estimates distinct from measurements and deliberate creative changes. Save human
interpretation through the normal vault draft workflow. Preserve the selected
brand assets and design system.

Recreate in the project's existing renderer or requested CSS/GSAP/Framer stack.
There is no CLI `recreate` command. Compare rendered key moments and playback with
the source; analysis success alone does not establish recreation accuracy.
Exact authored Lottie vectors and original 3D geometry cannot be recovered.

Upstream: <https://github.com/KumarSashank/motiscope> (MIT).
