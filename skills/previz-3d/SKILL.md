---
name: previz-3d
description: Block out 3D previz for a shot before AI video generation using raea, a local GPU renderer driven by TSX code. Produces greybox keyframe PNGs, a rough camera-move clip, and a contact sheet that lock framing, lens, camera path and subject motion before spending Seedance/Kling/Veo/Higgsfield credits. Use for previz, shot blocking, camera moves, drone paths, layout or animatic frames, start/end frames for image-to-video, or "check the framing in 3D first". Not for final photoreal frames.
---

# 3D Previz with raea

The go-to route for 3D previz in this repo. The agent writes the shot as a TSX scene, renders
greybox keyframes and a draft clip on the local GPU in seconds, looks at them, and iterates
until the user approves the blocking. Approved keyframes then become start/end frames or
composition references for AI video generation.

raea (Render Anything Engine, github.com/shinyobjectz/raea) is canary software: pinned in
`dependencies.toml` (id `raea`), changes daily. Its own skills, `raea` and `raea-bevy`, are the API
reference; this skill is the agency workflow on top.

## When to use

- Camera blocking: lens, height, dolly/orbit/drone path, where the subject sits at each beat.
- Subject motion: a car driving through a street, a product turning, a person walking a route.
- Start and end frames for image-to-video, so the AI model inherits a locked composition.
- Comparing two or three camera options quickly before choosing one.

Do not use it for the final look. Greybox frames carry layout, not lighting or materials;
the look comes from the image/video model (see `skills/visual-image`, `skills/visual-video`).

## Setup check

```bash
python scripts/deps.py check raea         # installed, and at the pinned version?
python scripts/deps.py install raea       # install or update (Linux, macOS, Windows)
raea help
```

If the install is blocked for the agent (it downloads and runs outside code), ask the user to
run it themselves (`! python scripts/deps.py install raea` in Claude Code).

## Before writing the scene

1. Follow the storyboard execution gate in `skills/agency-storyboard/SKILL.md`: brand note,
   project memory and any selected concept come first. For a brand project, read
   `$OBSIDIAN_VAULT_PATH/Brands/<slug>.md` and the project's storyboard/draft notes; reuse
   decided beats, locations, vehicles and camera language instead of inventing new ones.
2. Write a one-line spec per shot before any code: aspect ratio and fps (from the delivery
   platform), duration, lens (degrees), camera path start to end, subject path start to end,
   and which frames are the keyframes. Ask only for what can't be inferred.
3. Read the raea references for what the shot needs: `raea guide bevy/scene` always, then
   `bevy/lights`, `bevy/assets` (glTF models), `bevy/characters` (people), `bevy/rooms`
   (interiors), `bevy/splats` (a real location trained from footage) as needed. Claude Code
   can load the `raea-bevy` skill instead.

## Files

One folder per shot, in the run workspace (disposable, git-ignored):

```
workspace/<brand-slug>/storyboards/previz/<shot-id>/
  shot.tsx        # the scene (start from templates/greybox-shot.tsx)
  media/          # .glb models, reference images, footage used by staticFile()
  keys/           # keyframe PNGs
  shot.mp4        # draft camera-move clip
  sheet.png       # contact sheet of the clip
```

No brand: `workspace/previz/<shot-id>/`.

## Workflow

```bash
# PowerShell: $S = "$PWD\workspace\<brand-slug>\storyboards\previz\<shot-id>"  (quote "$S\shot.tsx")
S=$PWD/workspace/<brand-slug>/storyboards/previz/<shot-id>    # always absolute
raea scene lint "$S/shot.tsx" --frame 0                        # floating, sunk, clipping parts
raea render "$S/shot.tsx" --at 0,40,80,119 -o "$S/keys"        # keyframes
raea render "$S/shot.tsx" -o "$S/shot.mp4" --quality draft     # the move
raea media sheet "$S/shot.mp4" -o "$S/sheet.png"               # 12-tile contact sheet
```

1. Copy `templates/greybox-shot.tsx` to `shot.tsx` and edit the set, lens, camera and subject
   paths to match the spec. Use simple blocks at real-world scale (metres). Swap in `.glb`
   models from `media/` only when silhouette matters (a specific car or building).
2. Lint, render the keyframes and the sheet, then **look at them** (Read the PNGs) before
   showing the user. Check framing at every keyframe, horizon, subject size, and that the
   subject visibly moves against the scenery.
3. Fix and re-render until the agent's own check passes, then show the user the sheet and
   keyframes with the spec. Iterate on their notes by editing numbers, not by regenerating.
4. On approval, hand off to generation (below).

Measured on the GTX 1650 Ti 4 GB Linux box: a 9:16 1080x1920 greybox shot of 120 frames
renders in about 9 s; four keyframes in about 6 s; most of a single-frame render is startup.

## Hand-off to AI video

- **Keyframes are composition references.** Turn the chosen keyframes into styled stills with
  the image model (reference/edit mode: keep the layout, apply the brand look), get those
  approved, then use them as the first and last frames for image-to-video. Prompt the video
  model with the camera move from the spec (`skills/visual-video` for the prompt).
- Do not send raw greybox frames as a first frame to a video model; it will animate grey blocks.
- The draft clip is a timing and motion reference for the user and the prompt, and a motion
  reference input only where the chosen model accepts one.
- Record in the storyboard note which previz keyframe each generated clip came from.

## Rules that bite

- Pass absolute paths to `-o`. The repo's hook blocks image outputs that resolve to the repo root.
- `--at A,B,...` writes `frame-00000.png`, `frame-00001.png`, ... in list order, not by frame
  number. Note which frame each file is.
- Angles and `fov` are radians: `(50 * Math.PI) / 180`.
- One camera per shot; cut by jumping its transform at a frame, not with a second camera.
- An `<Entity>` with a `transform` takes no `name`; name the meshes inside it.
- Every value comes from the frame (`useCurrentFrame`, `interpolate`); no `useState`/`useEffect`.
- Vehicles and moving subjects: verify motion against the scenery in the sheet, and do not lock
  a subject's on-screen size across keyframes when the camera move should change it.

## Hybrid vault finalization

Previz media stays in `workspace/` while options are open. The human-readable shot spec and
the user's decisions go in the brand's draft storyboard note under
`$OBSIDIAN_VAULT_PATH/Brands/<slug>/Drafts/Storyboards/` (`status: draft`). After approval,
copy only the chosen keyframes, `sheet.png` and `shot.tsx` (as provenance) next to the
approved storyboard note; never overwrite an existing vault note or asset without approval.

## Updating raea

`python scripts/deps.py outdated` shows newer releases. `python scripts/deps.py set-pin raea NEW`,
`python scripts/deps.py install raea`, then re-render `templates/greybox-shot.tsx` and lint it before relying on
the new version.
