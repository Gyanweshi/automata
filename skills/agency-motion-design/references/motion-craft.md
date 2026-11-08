# Motion that explains the words

## Turn narration into action

Choose a literal demonstration where possible, then a visual metaphor when it makes
an abstract idea easier to understand. A screenshot is evidence; a reconstructed
interface is an illustration and should be identified as such where confusion is
possible. Neither should show a capability or result the product does not have.

| Spoken idea | Possible visual action |
| --- | --- |
| A repeated task | The same object completes several jobs; a counter reflects the actual count |
| A bottleneck | Items queue at a visible obstruction; changing the process releases the queue |
| A comparison | The same example changes between two clearly labeled states |
| A sequence | Each action causes the next; progress follows the spoken steps |
| A quantity or result | A legible counter or chart lands on the exact value, with source when factual |
| A product instruction | The relevant control performs the described action in a real capture or labeled reconstruction |

For arcade styling, a small cast and a few recurring worlds can connect the beats.
Make the character cause the action rather than merely stand beside a label. Use
the brand's chosen character, an authorized reference or a new agreed character;
do not default to another company's mascot. A consistent running example helps
the viewer track changes without relearning the setup each shot.

## Composition and pacing

Start with a meaningful composed frame. Spend motion on the concept, not on building
an empty stage while narration has already moved on. Alternate wider context and
readable details when the story calls for it; avoid changing the camera simply to
create movement. Keep real screenshots and text large enough at the final placement.

Use quick, playful beats for suitable material, and longer holds for reading or
understanding. The original arcade workflow's frequent actions are a style option,
not a requirement for every subject. Key events should land on the spoken word;
inspect sync near those words with a target tolerance around 0.1 seconds when that
precision is appropriate. Treat uncertain word timing as uncertain until checked.

Keep a single source of truth for repeated names, values, colors, type sizes and
character scale. In pixel work, use deliberate pixel-grid scaling and avoid blurry
resampling. Keep high-resolution captions/UI separate if they need smoother text.
Use a cut, reveal, counter or character reaction that communicates the idea; avoid
decorative motion that competes with it.

## Seekable implementation

Store timing constants with the beat data. Calculate positions, opacity and text
state from absolute or beat-local time; do not accumulate movement based on the
previous frame, wall clock or unseeded randomness. Clamp interpolation progress
and define stable states before/after each event. Seeking directly to a key action
must produce the same frame as playing from the beginning.

Keep content within its assigned panel. If a scene camera moves, transform only
the scene layers; captions and persistent labels have an explicit independent
coordinate system. Anticipation, follow-through and arcs can make a physical action
read clearly, but the final object must settle without popping or swapping identity.

## Review actual encoded frames

Inspect a contact sheet across the whole video for composition and repetition,
then denser strips around key actions and cuts. A sparse sheet cannot establish
frame-perfect sync. Check the exact action frame and neighboring decoded frames.

- No empty/black flash, stray neighboring scene, clipped sprite or unreadable label.
- No changing names/numbers, missing glyphs, distorted logo or unexplained cast change.
- No premature reveal, truncated final action or audio drifting after concatenation.
- No captions duplicated between the motion asset and the final editor.
- Transparent assets have no matte fringe or unintended opaque background when
  composited over both light and dark material.
- Reading holds remain long enough; intentional stillness is not automatically a defect.

For interactive HTML previews, preserve the same information under reduced motion.
For a fixed video, avoid unnecessary flashing and offer a calmer variant when the
brief requires one. Do not claim accessibility or platform certification from these
checks alone. Record what was actually viewed and heard.
