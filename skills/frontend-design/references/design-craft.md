# Design craft for editable HTML decks

Use these methods within the parent skill's presentation format. This is a selective
adaptation, not an invocation of all six Charles skills. Video editing, arcade motion
production, and disk cleanup are outside this workflow.

## Direction and subtraction

For an existing deck, inspect rendered slides before deciding how much to change.
Identify specific problems by slide: competing emphasis, repetitive layouts, weak
contrast, redundant copy, arbitrary decoration, or unclear evidence. A coherent deck
with one spacing defect needs that defect fixed, not a new identity. Review-only
requests produce findings and suggested fixes without edits.

For new work, state the audience, the decision or idea the deck must communicate,
the character of its visual language, and one recurring detail that belongs to its
subject. Summarize the direction in one sentence. Use the approved direction when
one exists; derive missing choices from the actual subject rather than a trend.
Proceed within the requested scope; clarify only a consequential missing input.

Choose one focal treatment that serves the argument: a meaningful number, a clear
comparison, a real product detail, a diagram, or a change demonstrated through
interaction. Check it on a title, a dense evidence slide and a concluding slide.
An attractive cover alone is not a functioning deck system.

Remove redundant labels, subtitles, icons, borders and nested containers before adding
effects. Preserve factual content, citations, necessary labels, narrative order and
editor hooks. Do not invent testimonials, performance figures or product capabilities.
Keep legitimate brand colors and marks even when a generic-style checklist dislikes them.

Refine in this order, so later work rests on a stable composition:

1. **Spacing and hierarchy:** group related content, establish consistent alignment,
   and express repeated distances through the deck's spacing tokens.
2. **Color and icons:** use deliberate text roles and accents; keep one icon language.
   Decorations need a purpose beyond filling empty space.
3. **Copy and type:** make headings specific, remove repetition, and keep text legible
   at the actual viewing size. Use fluid type tokens and bounded line lengths.
4. **Composition and details:** give the main evidence the space it needs. Vary layouts
   with the narrative rather than forcing every slide into equal cards. Keep radii,
   borders and depth consistent with the existing system.
5. **Focal treatment:** strengthen the subject-specific detail without obscuring the
   argument or turning dense slides into decorative posters.
6. **Motion:** retain only motion that explains sequence, change or interaction.

## Polish and verification

Use the repo's `html-preview` workflow to capture and inspect before/after screenshots
for edits, or the first render and corrected render for new work. Use the repo Python
environment and configured Playwright browser; follow the repo dependency policy for
missing tooling. Keep review captures under `workspace/`.

Inspect at the intended presentation size and the smallest supported viewing size.
Check all slides in a new deck; for localized changes, inspect affected slides and
representative layouts that share the changed tokens. Look for clipping, unreadable
citations, poor line breaks, stretched images, weak contrast and accidental overlap.
Fix hierarchy before optical details. Measure contrast against the actual background:
4.5:1 for ordinary text and 3:1 for large text and meaningful graphical controls.

Verify the deck's real interactions, not imaginary app states:

- Navigate by keyboard and scroll, including the first and last slides.
- Enter edit mode with E; edit text, resize a block and adjust a gap. Text editing
  must not trigger slide navigation.
- Save with Ctrl/Cmd+S and reopen the downloaded file to check that text and layout
  edits survived. Verify supported layout persistence separately from text saving.
- Keep visible focus and usable control targets. Check for console errors and missing
  assets. Treat editor defects as explicit findings; do not silently rewrite the
  verbatim editor while styling a deck.

When motion is present, inspect intermediate frames as well as endpoints. Check
clipping, flashes, interruption by rapid navigation and the final resting state.
Keep animation timings in named tokens, favor transform/opacity where appropriate,
and avoid blocking input. Respect `prefers-reduced-motion` in both CSS and scripted
scrolling: the same slides and information must be reachable without animated travel.
Do not describe motion as verified if only still screenshots were inspected.

For a polish pass, name the most consequential remaining defect, fix it, and inspect
the affected result. Stop when the requested scope is met and no material defect
remains in the checked states; avoid indefinite subjective score chasing. Report
what was inspected and any unresolved limitation rather than claiming award readiness.

## Ambitious design

Use this section when the user asks for a premium or exploratory result. With no
selected direction, render a few materially different representative-slide concepts
before refining the whole deck. Compare how each communicates the same content,
then choose within the user's authorization or present the options when they requested
a choice. A selected concept stays selected; explore improvements within it.

Invest effort in a recognizable composition, excellent evidence presentation and
careful typography. Custom imagery is useful only when it serves the content. Reuse
approved assets and route new generation through the relevant visual skill with the
existing budget and approval constraints. Do not require an unavailable external
skill, new framework, paid asset, or extra agent merely to perform this review.

Make one deliberate critique pass, address its substantive findings, and verify the
fixes. Additional rounds follow the user's request or a concrete unresolved defect.

## Sources and adaptation

Adapted for this repo's editable slide workflow from Charles Liu's
[charles-unslop](https://github.com/LemonFace0309/charles-skills/tree/main/skills/charles-unslop),
[charles-polish](https://github.com/LemonFace0309/charles-skills/tree/main/skills/charles-polish),
and [charles-unreasonable-craft](https://github.com/LemonFace0309/charles-skills/tree/main/skills/charles-unreasonable-craft).

The unslop material derives from [unslop by Damir Sokolovsky](https://github.com/heydamir/unslop)
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), with contributions credited
upstream to Emil Kowalski and Charles Liu. The polish source credits Emil Kowalski
and Josh Puckett's Interface Craft. This adaptation condenses the methods, translates
app states into deck/editor checks, preserves repo tokens and approval rules, and
replaces external skill dependencies and open-ended scoring with scoped verification.
