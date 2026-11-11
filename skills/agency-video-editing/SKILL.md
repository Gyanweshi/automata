---
name: agency-video-editing
description: Edit supplied footage into reels, talking-head videos or other finished cuts with take selection, accurate captions, B-roll, overlays, motion graphics and sound. Use for cutting, captioning, mixing or revising existing video; not AI video generation prompts or storyboard-only requests.
---

# Agency video editing

Turn the user's footage into an intelligible, well-paced edit that keeps their voice
and meaning. Apply the requested changes at their actual scope: a caption correction
does not reopen the whole cut, and a finished-video request continues through rendering.

## Load context and inspect sources

1. Read repo `AGENTS.md`. For brand work resolve the vault with
   `agency_common.get_vault_path()` and read `Brands/<slug>.md`, Memory, selected
   concept, existing edit decisions, approved assets and remaining budgets.
2. Locate supplied media and existing project files before asking for them. Inspect
   duration, dimensions, rotation, frame rate/time base, audio streams and any variable
   frame rate using `ffprobe`. Watch representative footage and listen to the speech;
   metadata and a transcript alone cannot establish a good take.
3. Read [editing.md](references/editing.md) before selecting cuts, captions or overlays.
   Determine output dimensions, frame rate, content priorities, treatment and requested
   duration from the brief. State assumptions only where they affect the result.
4. Keep original media untouched. Work in a new
   `workspace/<brand-or-project>/video/<run>/` directory. Human-readable scripts,
   edit briefs and decisions go to vault drafts with frontmatter and a concise Memory;
   transcripts, edit JSON, previews, render scripts and logs stay in the run directory.

## Build and finish the edit

1. Create a time-aligned transcript from supplied captions or an available transcription
   tool. Check speech, names and numbers by listening. If no transcription tool is
   available, manually time the needed material or identify the specific dependency;
   do not present estimated word times as measured. Uploading footage to a service
   must stay within the user's authorization.
2. Select takes and build the base cut. Keep an edit decision list with source path,
   source in/out and output in/out for each retained segment. Preserve qualifiers,
   negations and causal sequence; cut stumbles without manufacturing a different claim.
   Test pacing and audio joins before adding decoration.
3. Time captions and overlays against the **edited output**, not the original footage.
   Use the existing brand treatment. Keep names, numbers and evidence consistent with
   the selected concept and sources. Add a hook title when requested or specified by
   the brief, not automatically to every clip.
4. For animated panels or overlays, read
   [agency-motion-design](../agency-motion-design/SKILL.md) and the shared
   [timeline contract](../agency-motion-design/references/timeline.md). The editor
   chooses layout, exact destination size, timing and caption exclusion zones. Motion
   returns silent assets and sound cues; final captions, music and audio belong here.
5. Add authorized music/SFX when requested or part of the brief. Use the available
   licensed library or provided tracks; do not assume Charles's music folders exist.
   Keep speech intelligible, inspect clipping and listen to the actual mix. Choose
   levels from the recording and delivery needs, not a universal gain offset.
6. Render a preview, inspect it, fix defects, then render the requested deliverable.
   Verify captions at viewing size, every cut and overlay boundary, audio sync after
   retiming, full-clip playback, stream metadata and duration. Include first/last frames
   and the most complex transitions in review strips. A successful encoder exit is
   not proof of visual or audio quality.
7. Deliver the rendered file plus editable project/render source and relevant
   captions/asset provenance. State any remaining limitation. Keep outputs in
   `workspace/` until selected-asset promotion is authorized under the vault policy.

## Execution tools

For local audio analysis, soundtrack review, SFX selection or procedural sound
design, read [Earshot](references/earshot.md) and use its shared MCP/CLI route.

Use installed FFmpeg/ffprobe and the repo's `.venv` Python toolkit (MoviePy 1.x,
Pillow, NumPy) for deterministic local assembly. Check capabilities needed by the
chosen export, including subtitle filters and codecs. Missing FFmpeg uses
`python scripts/deps.py install ffmpeg`; missing repo Python packages use bootstrap.
Do not install system Python packages or fetch an unregistered rendering engine.

Write reusable render code in Python with `pathlib` and subprocess argument lists,
without shell interpolation. Resolve fonts from provided/licensed assets; use raster
text layers or FFmpeg subtitles when appropriate instead of assuming ImageMagick or
macOS fonts. Read live API/help for the installed version before using unfamiliar
calls. Use a real available editor integration if it better fits the user's project.

For a quick automatic highlight cut, a connected Adobe Quick Cut workflow can fit
when exact cuts are not required; follow its skill if chosen. Use `visual-video` plus
the appropriate generation workflow only for authorized new generated footage.
This skill adds no new `run-agent.py` command or MCP server.

## Provenance

Methods adapted from Charles Liu's
[charles-claude-editing](https://github.com/LemonFace0309/charles-skills/tree/main/skills/charles-claude-editing).
The adaptation retains purposeful cuts, accurate short captions, evidence overlays
and layout-aware motion handoffs. Personal fonts, face framing, music paths, fixed
platform safe areas and mandatory rapid pacing are replaced with project choices.
