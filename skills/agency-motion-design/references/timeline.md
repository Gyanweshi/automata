# Shared editor / motion timeline contract

Use this contract whether one agent performs both roles or hands work to another.
It is a project interchange convention, not a schema already consumed by a repo CLI.
Persist it as JSON with the run artifacts; keep the human-readable brief in the vault.

## Request

Record these fields before rendering:

- **Identity:** project/brand, selected concept, asset ID, revision, source media.
- **Canvas:** width, height, frame rate (rational where needed), pixel aspect ratio,
  background/alpha requirement and intended placement in the final frame.
- **Clock:** output edit start/end, local asset origin, requested frame count, and
  any pre/post handles. State whether supplied word times use source, edit or asset
  time. Provide the EDL/time mapping after trims or speed changes.
- **Content:** checked narration excerpt, timed key words, exact names/numbers,
  approved style/cast/assets and their provenance.
- **Exclusions:** caption rectangle, platform UI areas, speaker/face area, and
  readable text region in this asset's own coordinates.
- **Delivery:** filename/format, whether silent, active intervals for an asset set,
  and any music/SFX ownership. Default to silent motion assets within an edit.

Example: a panel spans edit seconds 12.4–15.4 at 30 fps, so it has 90 frames and
local time zero corresponds to edit time 12.4. A hit at edit time 13.1 has local
time 0.7, frame 21. Render frames 0 through 89. The end time is exclusive; do not
render an extra frame at 3.0 seconds. Specify the chosen rounding rule when a
timestamp is not frame-aligned. Source time requires an EDL lookup before this
conversion; an offset alone is wrong after intervening cuts or speed changes.

Quantize events to the chosen frame grid before composition. Floating-point
subtraction such as `edit_time - asset_start` can put an intended boundary just
below its target time and delay an event by one frame. In a frame-based renderer,
compare integer local frame indices to event frames; normalize the renderer's
sample time with a small numerical tolerance rather than relying on raw float
equality. Test the decoded frame before, at and after the event.

## Response

Return the rendered path plus measured width/height, frame rate, frame count,
duration, alpha and audio stream information; editable source; asset provenance;
and checked key-action timestamps. Note any encoder/container duration rounding.

Optional sound cues use **local asset seconds**, for example:

```json
{"asset_id":"panel-01","time_basis":"asset_seconds","cues":[{"t":0.7,"kind":"hit"}]}
```

The editor maps cues back to output time and selects/mixes them. Cue suggestions
are not embedded audio, and a cue does not require a sound if the mix is better
without it. Final captions and music remain in the editor to avoid duplication.

## Boundaries and revisions

Use half-open intervals `[start,end)` throughout. If handles are requested, render
the additional frames and state their lengths; do not silently extend the active
segment. In a noncontiguous asset set, specify every active range and what the gaps
contain. The editor must mask gaps or trim them out; a hold is not automatically
intended for the viewer. Separate short files are simpler when no shared span is needed.

After a cut, speed or layout revision, update the mapping and affected assets/cues.
Do not regenerate approved artwork for a timing-only change. Check decoded frames
immediately before, at and after each join, plus the full final composition, for
empty frames, leaked neighboring scenes, truncated words and unexpected offsets.
