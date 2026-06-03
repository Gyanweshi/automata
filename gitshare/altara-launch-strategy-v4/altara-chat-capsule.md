# Altara Pitch Deck Chat Capsule

## Current Goal

Create a premium, minimal, self-explanatory HTML presentation for Altara's launch/social strategy using the actual Altara design system, not improvised visual devices. The deck should feel like a strategic narrative, not a social-media idea list.

## Source Files

- Strategy markdown: `C:\Users\Devan\Downloads\Altara_Brand_Strategy_Full.md`
- Design system zip: `C:\Users\Devan\Downloads\Altara Design System.zip`
- Extracted design system: `C:\automata\.tmp\altara-design-system\`
- Active HTML deck: `C:\automata\workspace\content\altara\altara-launch-strategy-v4.html`
- Deck assets: `C:\automata\workspace\content\altara\altara-pitch-assets\`

## User Direction

- Do not make text-heavy slides.
- Use title/chapter slides like film chapters.
- Make information visual through diagrams, restrained systems, grids, and editorial layouts.
- Premium minimal, but the presentation must be understandable without spoken narration.
- Verve logo should appear top-right on all slides.
- First slide should include what the presentation is.
- Intro should use StoryBrand logic: the guest has a deeper emotional need, and Altara is the answer.
- Strategy section should use Andy Raskin logic: old world vs new world, strategic shift, why Altara's approach wins.
- Emotional core: people need choices that make them feel, "I chose right. I am going to be okay."

## Major Correction

The user strongly objected to using screenshots from the PDF as deck assets. Those screenshots were only references. The deck must use the real assets already inside the design system:

- `assets/motifs/arch-motif.png`
- `assets/motifs/continuity-device.png`
- `assets/icons/*.png`
- `logo-primary*.png`
- `wordmark*.png`
- `monogram*.png`
- embedded Ivy Presto fonts
- design-system slide templates in `slides/*.html`

Do not copy brand-guide screenshots into the deck.

## Visual Rules From Design System

- Calm paper is dominant.
- Warm vermilion is punctuation, not a full-deck default.
- Root/shadow tones support the system.
- Golden Hour accents should be hairline, restrained, and occasional.
- Use gateway arch, continuity device, four-point star, hairline rules, monogram/wordmark only in brand-appropriate ways.
- Do not use the monogram as a large random wallpaper.
- Do not repeat shower/glass/bar icons across all slides. Use service icons only where the content is about service/experience/sustenance.
- Background motion should be subtle and useful, not flashy. Avoid diagonal shooting-star lines.
- White slides should have varied treatments, not one repeated motif.

## Current HTML State

Current deck has 22 slides in `altara-launch-strategy-v4.html`.

Recent fixes made:

- Removed copied screenshot-derived `brand-guide` asset folder.
- Removed screenshot-derived image references.
- Added ornament classes using real design-system assets:
  - `ornament-arch`
  - `ornament-continuity`
  - `ornament-mono`
  - `ornament-gold`
  - `ornament-star`
  - `service-device`
- Service icons are intended only for sustenance/service slides.
- Paid-media slide was rewritten into a cleaner split system.
- KPI slide contrast was fixed.

## Still Needs A Proper Design Pass

The current file is patched but not yet visually approved. Next pass should:

1. Re-read the design-system templates:
   - `slides/cover.html`
   - `slides/brand-story.html`
   - `slides/moodboard.html`
   - `slides/experience-pillar.html`
   - `slides/quote.html`
   - `slides/data.html`
   - `slides/closing.html`
2. Make the deck feel based on these templates, not just decorated with their assets.
3. Randomize/alternate white-slide treatments intentionally:
   - quote-style centered slide
   - data-style big-number/info slide
   - moodboard grid slide
   - brand-story split slide
   - experience-pillar icon columns
   - sparse chapter slide
4. Avoid using the same background device on consecutive slides.
5. Use design-system gold accents and rules properly.
6. Re-check text alignment and hierarchy, especially on tactical slides.

## BrowserAct

User explicitly said to leave BrowserAct and not use it for this. Continue by source edits unless the user later asks to inspect screenshots again.

## Tone/Writing Preference

User dislikes generic polished writing. Keep language human, direct, strategic, and emotionally clear. Avoid corporate slop. The pitch should make the client understand the strategic reasoning, not just admire the design.

## Important User Feedback To Preserve

- "People need power/decision that make them feel they are alright."
- "I want to feel I chose right."
- "This feels like social media ideas, not brand strategy" was a rejected direction.
- The chosen route is a human emotional story.
- The deck should show why this strategy is the right conclusion for a brand like Altara.
- Pre-launch examples should include things like:
  - painter painting the artwork
  - architect discussing the arch/design problem
  - creative process withheld until later reveal
  - interviews/process before final reveal
- Launch/post-launch/sustenance should include concrete examples, but not in a boring text-heavy way.

