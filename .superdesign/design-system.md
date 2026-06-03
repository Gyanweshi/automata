# Altara Deck Design System

Source of truth: `gitshare/altara-launch-strategy-v4/altara-launch-strategy-v4.html`

## Purpose
Editorial brand deck for Altara launch direction and social strategy. Visual language is luxury hospitality: warm red, cream, muted gold, serif-led, quiet motion, minimal chrome.

## Fonts
- Display: `Ivy Presto Display`
- Body: `Ivy Presto Text`
- Sans: `Roboto`

## Core Tokens
```css
:root {
  --warm: #6a1611;
  --calm: #e1dacb;
  --paper: #f3efe6;
  --surface: #faf7f0;
  --root: #806552;
  --shadow: #5d5650;
  --ink: #2c2622;
  --muted: #6e655c;
  --faint: #9a9087;
  --line: #cdc4b2;
  --line-strong: #b3a892;
  --stone: #3d352f;
  --gold-1: #eece90;
  --gold-2: #cf9c55;
  --gold-3: #bb8648;
  --gold-4: #986125;
  --gold-5: #87582c;
  --font-display: 'Ivy Presto Display', Georgia, serif;
  --font-serif: 'Ivy Presto Text', Georgia, serif;
  --font-sans: 'Roboto', Arial, sans-serif;
  --title-size: clamp(2.2rem, 6vw, 6.1rem);
  --h2-size: clamp(1.7rem, 4.1vw, 3.9rem);
  --h3-size: clamp(1.05rem, 2.25vw, 1.85rem);
  --body-size: clamp(0.84rem, 1.25vw, 1.12rem);
  --small-size: clamp(0.62rem, 0.86vw, 0.78rem);
  --slide-padding: clamp(1.15rem, 4.6vw, 5.3rem);
  --content-gap: clamp(0.75rem, 2vw, 2.2rem);
  --ease: cubic-bezier(0.22, 0.61, 0.36, 1);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}
```

## Layout Rules
- Full-viewport slides with snap scrolling.
- Most slides use a centered editorial grid with generous negative space.
- Warm slides invert to cream text over dark red backgrounds.
- Light slides use paper backgrounds with faint grid texture and gold linework.
- Fixed Verve mark in the top-right, north star in the top-left.
- Animated starfield canvas sits behind content.

## Motion
- Animate.css `fadeIn` / `fadeInUp` is used for reveal sequencing.
- Starfield twinkles slowly, not aggressively.
- North star uses a soft pulse, with a muted light-slide variant.

## Visual Rules
- Serif headlines only; keep letter-spacing at `0`.
- Gold accents should stay restrained and thin.
- Avoid replacing brand marks with text.
- Avoid chips or UI garnish when the slide already has enough sentence structure.

