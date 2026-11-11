# Deck patterns from real reference decks

Layout patterns observed in well-made decks on deck.gallery and the Chronicle gallery
(Linear sales deck 2023, McKinsey State of AI 2025, Browserbase AI Native Summit 2025,
Lovable case study), checked 2026-11-11. Use them while choosing slide layouts in
Direction and subtraction. They are options, not a template: pick the ones the argument
needs. Never copy a reference deck's content, imagery or brand into client work.

Full reference list with client-matched picks: vault `Research/Deck_References/`.

## Headlines

- **Headline = the claim, as a full sentence.** "AI use continues to broaden but remains
  primarily in pilot phases", not "AI adoption". Pairs with the house rule that every
  claim needs a proof point on the same slide.
- **Two-tone headline.** First sentence in the text colour states the point; a second
  sentence in a muted token adds context. Use on openers and section starts.
- **Kicker + footer.** Small label above the headline (section or question, e.g.
  "Key takeaways", "What is X?"); date and deck title in a quiet footer on every slide.

## Evidence slides

- **Stat row.** 3–4 large numbers, one-line label each, separated by hairlines. No icons.
- **Number left, chart right.** Claim and headline figure in a narrow column; the chart
  that proves it fills the rest.
- **Real evidence over icons.** Product screenshots, customer logo walls, real photos.
  An icon is a placeholder for evidence the deck does not have yet.
- **Numbered findings summary.** 01–06 in a two-column grid before the close, so a
  reader who skips to the end still gets the argument.

## Rhythm

- **Breath slide.** One sentence on a full-bleed colour or gradient between dense
  sections. Use 1–3 per deck, never back to back.
- **Series slides with a counter.** When the same structure repeats (four roles, five
  pillars), keep the layout identical and add `1/4 … 4/4` so the series reads as one idea.
- **Three-column problem slide, once.** Icon + title + 2–3 bullets per column works for
  the problem statement; do not let it become the default layout for every slide.
- **One motif throughout.** A single recurring visual (a gradient, the product UI, an
  isometric object) carries identity better than varied decoration.

## Covers

- Display type or one full-bleed image, almost nothing else. Title, subtitle, date.

## Implementing within this skill

All of the above fit the skill contract: stat rows and splits are flex/grid inside
`.slide-content`; the breath slide is a slide-type class with a background token;
kicker and footer use `--text-sm` and a muted colour token; counters are text in an
`editable` block. Mark each stat, chart column and logo wall `editable`.
