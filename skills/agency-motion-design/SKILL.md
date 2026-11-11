---
name: agency-motion-design
description: Create and render narration-timed motion graphics, animated charts, product walkthroughs and pixel or arcade scenes, as standalone videos or exact-size overlays for an edit. Also use to analyze or recreate an animation from a screen recording, match reference motion or timing, or use Motiscope. For code-driven animation and motion assets; not generic AI video prompts, games, or editable slide decks.
---

# Agency motion design

Make the idea visible as an action: a comparison changes, a step completes, a value
accumulates, or a character causes a consequence. Keep one coherent visual system
and time important changes to the narration. Pixel/arcade is an optional style;
brand-led editorial graphics use the same timing and composition discipline.

## Context and output contract

Read repo `AGENTS.md`, then the selected concept, brand note/Memory, approved assets,
style reference and remaining budget. Resolve brand context through
`agency_common.get_vault_path()`. Do not replace a selected direction with a retro
mascot or a new story. For campaign work retain storyboard's research readiness and
concept gates; standalone execution can use the supplied brief.

Read [timeline.md](references/timeline.md) before production. Determine whether the
output is a complete narrated video, silent panel, transparent overlay or asset set.
Record dimensions, frame rate, duration, timeline origin and reserved text/caption
regions before drawing. For a supplied video edit, the
[video editor](../agency-video-editing/SKILL.md) owns those choices and final audio.

## Plan and build

1. Inspect narration or source footage and obtain checked word/phrase times. Listen
   to key words and numbers; transcription timing can drift. Without recorded audio,
   timing is provisional and cannot be claimed synchronized. A request for a plan
   needs no render; a requested video must continue beyond the beat sheet.
2. Read [motion-craft.md](references/motion-craft.md). Write beats describing the
   words, action, causal actor/object, scene, source asset and exact key moment.
   Keep numbers and names in one shared data object. Plan in phrases and readable
   holds rather than mechanically cutting on every word.
3. Reuse or prepare the cast, backgrounds, real product references and other assets.
   For pixel work keep a consistent pixel scale, palette and silhouette language.
   For new art use the applicable visual-generation skill and the existing budget;
   for local image repair use `image-compositing-repair`. No Charles sprite library,
   mascot, private folders, API keys or paid service is assumed present.
4. Build each scene from an explicit timeline. Use seconds for editorial timing and
   frame indices for rendering; keep a consistent rounding rule. Scene functions
   must render correctly when sought directly to any time, without prior playback.
   Keep layout independent of the camera so overlays and text do not drift.
5. Render stills at beat starts, important actions and transitions before the full
   encode. Inspect them at delivery scale; fix composition, text and asset defects.
   Then render the video and inspect frame strips around every cut/key action,
   followed by playback with the narration. Check the first and last frames and
   alpha against contrasting backgrounds for transparent delivery.
6. Deliver the render, editable source, timeline/asset manifest and optional SFX cue
   file. Report dimensions, frame rate, duration and timing limitations. For asset
   sets, state active intervals and any handles explicitly. Verify a representative
   asset in the editor's final composition, not just in isolation.

## Rendering route

For sound-effect creation or review of a complete video's soundtrack, read the
shared [Earshot workflow](../agency-video-editing/references/earshot.md). The video
editor owns the final mix when delivering overlays for an existing edit.

For recreating motion from a supplied screen recording, use the optional
[Motiscope analysis step](references/motiscope.md) before building the timeline.
It supplies timing evidence and selected frames; the agent still identifies the
elements, writes the animation and verifies the rendered result.

The portable local route is the repo `.venv` with MoviePy 1.x, NumPy/Pillow and
FFmpeg/ffprobe. Write a project-local Python renderer whose frame function depends
only on time and declared assets. Draw new procedural shapes/text with this toolkit;
route edits to existing image assets through the appropriate image-editing skill.
Use installed/version-appropriate APIs, subprocess argument lists and `pathlib`.
Keep authored type as separate layers and use licensed font files available locally.
Avoid an ImageMagick dependency just for text.

For an existing HTML animation project, its configured renderer may be reused.
Read `html-preview` when changing HTML/CSS, and make its animation clock explicitly
seekable before capture. Do not inject the slide editor into a video scene.
HyperFrames and the original Charles templates are not bundled or required here;
do not reference their helper names as available APIs. If the user specifically
requests that engine, verify its availability and follow the repo dependency
registration/install workflow before using it. Do not silently fetch it through npx.

Missing FFmpeg uses `python scripts/deps.py install ffmpeg`; missing repo Python
packages use bootstrap. Test codec/alpha support in the chosen compositor before
rendering a full batch. Use a tested alpha-capable format or PNG sequence when an
overlay needs transparency; an ordinary H.264 MP4 is an opaque asset.

## Working artifacts and boundaries

Keep scripts, frames, assets, machine-readable beats, manifests and previews under
`workspace/<brand-or-project>/motion/<run>/`. Put human-readable beat plans and
creative decisions in vault drafts with frontmatter and concise Memory. Promote
only selected outputs after authorization. This skill is an agent-led workflow,
not a new callable agent or `run-agent.py` command. It does not authorize publishing,
generation spend or a change to an approved campaign concept.

## Provenance

Adapted from Charles Liu's
[charles-arcade-motion](https://github.com/LemonFace0309/charles-skills/tree/main/skills/charles-arcade-motion).
The adaptation carries over literal visual actions, recurring cast/worlds, real
reference material, narration timing, seekable animation and cut-boundary review.
It replaces the author's personal assets and mandatory HyperFrames/fal stack with
repo tooling, optional styles and an explicit editor handoff.
