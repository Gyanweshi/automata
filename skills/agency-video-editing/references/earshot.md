# Earshot: local audio evidence

Shared by Codex and Claude on Windows and Linux. Read this for audio analysis,
sound-effect selection, soundtrack review or procedural sound design.

Install through `python scripts/deps.py install earshot`. This reads the source
commit from `dependencies.toml`, creates an isolated Python 3.12 environment under
`workspace/tools/earshot/`, installs CPU torch, and fetches/loads the local models.
The `video` bootstrap role installs it on another machine; no copied virtualenv
or machine-specific paths are needed. FFmpeg/ffprobe must be on PATH (use
`python scripts/deps.py install ffmpeg` if missing).

Use the `earshot` MCP tools for repeated calls so models stay loaded. Both project
configs launch the same portable wrapper from the repo root. Restart the clients
after installing. For CLI access on either OS:

```text
python scripts/earshot.py doctor --load
python scripts/earshot.py measure workspace/project/video/mix.wav --json
python scripts/earshot.py describe workspace/project/video/hit.wav
python scripts/earshot.py timeline workspace/project/video/final.mp4
python scripts/earshot.py sheet workspace/project/video/final.mp4 -o workspace/project/video/audio-sheet.png
python scripts/earshot.py sfx list
```

Use `python3` on Linux if `python` is unavailable. The wrapper locates its own
isolated interpreter. Pass absolute media paths to MCP. Run subcommand `--help`
before unfamiliar options. Consult the upstream skill for advanced forge/fit/kit
workflows, adapting its install commands to the registered installer above.

For a mix review, measure the rendered output, inspect timeline sync, open the
audio sheet, fix defects and rerun the affected checks. Report measurements and
model interpretations separately. For candidates, use rank/match/find then analyze
the actual selected trim. For synthesis, prefer the shipped bank or forge; keep
recipes, variants, measurement JSON and review images inside the project workspace.
The editor still owns final music, captions and mix; motion overlays stay silent
unless their output contract requests audio.

Loudness and event timing are evidence, not approval. Semantic tags in busy mixes
are uncertain. Realness cannot prove provenance or licensing; synthesis can score
highly. The launch critique reflects one particular film style, not a universal
quality standard. Earshot does not transcribe speech or establish emotional impact.
Do not claim a human listening review from tool output alone.

The default workflow is local. The optional Gemini upload/LLM path is not configured;
using it requires separate user authorization. First setup downloads roughly 1.1 GB
of model weights. `EARSHOT_OFFLINE=1` disables model downloads; `EARSHOT_HOME` can
override the shared repo cache. Missing models: run `doctor --fetch`, then
`doctor --load`. Keep existing offline settings intact.

Upstream: https://github.com/Leonxlnx/earshot (MIT code; models have separate licenses).
Detailed usage: https://github.com/Leonxlnx/earshot/blob/main/skills/earshot/SKILL.md
