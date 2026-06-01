# LHWRF Design System

A design system for **Lupin Human Welfare & Research Foundation (LHWRF)** — the social-impact and rural-development arm of the Lupin group. This system codifies the visual language the user specified: a confident green spectrum, a deep navy ground, a high-energy lime accent, and a distinctive **petal corner-radius motif** that nods to the lupin flower in the brand mark.

> **Source of truth:** the user-provided brief (tokens + structural rules) and the official LHWRF logo (`assets/lupin-foundation-logo.png`). No Figma file, codebase, or full media kit was attached, so visual elements beyond those are **interpretations**. See *Caveats* at the end.

---

## Index

- `README.md` — this file. Brand overview, content + visual foundations, iconography.
- `colors_and_type.css` — CSS custom properties for color and typography tokens (base + semantic).
- `Lupin Styleguide.html` — the **React Artifact styleguide** (Tailwind via CDN). The headline deliverable.
- `preview/` — small specimen cards rendered in the Design System tab (colors, type, components, brand).
- `assets/` — logos / marks / placeholder imagery.
- `ui_kits/marketing/` — interactive recreation of a Lupin-style marketing surface.
- `SKILL.md` — Agent-Skills front-matter so this folder is portable to Claude Code.

---

## Brand at a glance

LHWRF (Lupin Human Welfare & Research Foundation) is the corporate-social-responsibility and rural-development arm of the Lupin group. Its work spans agriculture, livelihoods, women's empowerment, education, and rural health across thousands of villages in India. The brand voice is **grounded, optimistic, and community-centered** — copy talks about *families*, *villages*, *livelihoods*, and *outcomes* rather than products. The official mark (`assets/lupin-foundation-logo.png`) sets two stacked lupin flowers above the **LUPIN** wordmark with the descriptor *Human Welfare & Research* and the word **FOUNDATION** anchoring the lockup. The dominant identity color is a vivid green, with darker greens for grounding contrast.

This design system distils that posture into reusable tokens and components.

---

## CONTENT FUNDAMENTALS

**Voice.** Plain, direct, grounded-but-warm. Sentences are short. Verbs are active ("we partner," "we train," "we work alongside"). Avoid marketing flourish — no "revolutionary," no "unleash," no exclamation points.

**Pronouns.** "We" for the foundation, "communities," "farmers," "families," or "you" for the audience. Never "I."

**Casing.** Sentence case for headlines and buttons. Title Case is reserved for proper nouns and product names. ALL-CAPS is used sparingly — only for tiny eyebrow labels (≤14px) and never for body copy.

**Numbers and claims.** Always concrete. "4,500+ villages," "1.5M+ lives touched," "Active in 16 states." Round numbers, no fake precision.

**Emoji.** Not used. Visual decoration is reserved for icons and the petal motif.

**Examples that fit the voice**

- ✅ "Stronger livelihoods for one and a half million rural families."
- ✅ "We work alongside farmers, women's collectives, and panchayats."
- ✅ "Read the 2024 impact report."
- ❌ "Unleash the power of rural transformation!" (too marketing)
- ❌ "We're SO excited about our journey 🚀" (wrong register, emoji)

**Microcopy.** Buttons are verbs: *Learn more*, *Read the report*, *Get involved*. Form errors name the problem and the fix: "Enter a valid email address." No cute error states.

---

## VISUAL FOUNDATIONS

### Color
- **Primary Green `#069c3c`** — main brand. CTAs, links, hero accents.
- **Dark Green `#08a240`** — hover/press states for primary, vertical-strip accents.
- **Deep Teal `#1b6b59`** — secondary surfaces, eyebrow text on light backgrounds.
- **Lime Accent `#e7ff00`** — energy. Used sparingly: one moment per screen, max. Keylines, single highlighted word, small badges.
- **Navy/Dark `#033943`** — grounding background. Footers, hero sections, dark-mode containers.
- **Off-white `#f6f7f4`** — page background. Never pure white; always a hint of warmth/green undertone.
- **Ink `#0e1a1f`** — body text on light. Near-black with a teal undertone.
- **Mute `#6b7a7e`** — secondary text, dividers.

The green-on-navy pairing is the system's signature combo. Lime appears as a **single accent**, never as an area fill.

### Typography
- **Display + body:** `font-sans` — system stack (Inter substitute). Weights 400 / 500 / 700 / 800.
- **Headline weights** are bold (700) or extra-bold (800) with **tight tracking** (`-0.02em`).
- **Body** is 400 with relaxed leading (1.6) for readability of clinical copy.
- **Eyebrow labels** use `text-xs uppercase tracking-[0.18em]` in Deep Teal or Lime depending on background.

> ⚠️ **Font substitution flagged.** Lupin's actual marketing site uses a custom or licensed sans (close to Inter / Plus Jakarta Sans). This system uses the **system sans-serif stack** as a stand-in. If the user has the licensed font files, drop them in `fonts/` and update `colors_and_type.css`.

### The petal motif
The signature gesture is **`border-top-right-radius: 3rem`** with all other corners square (or slightly rounded `0.25rem`). This single asymmetric corner mimics a lupin petal and is applied to: hero image masks, product cards, feature illustrations, large CTAs.

```css
.petal { border-radius: 0.25rem 3rem 0.25rem 0.25rem; }
```

It is **not** applied to: buttons, body text, form inputs, dialogs. The motif is reserved for "image-shaped" or "card-shaped" elements; over-using it dilutes the identity.

### Spacing
4-pt grid. Component padding clusters at `p-6` (24px) and `p-8` (32px) — **clinical whitespace** is core to the brand. No tight 8/12 padding except on small chips.

### Backgrounds
Three variants only:
1. **Off-white `#f6f7f4`** (default page).
2. **Navy `#033943`** (footer / dark hero / data section).
3. **Image-with-mask** — full-bleed photography clipped with the petal radius. Imagery skews **warm-clinical**: natural light, real people, soft greens. Never b&w, never grain, never gradients-as-decoration.

### Shadows
Restrained. One shadow only:
```css
--shadow-card: 0 1px 2px rgba(3,57,67,.06), 0 12px 32px -12px rgba(3,57,67,.18);
```
No glow, no neon, no inner-shadow, no neumorphism.

### Borders
1px, color `rgba(3,57,67,.10)` on light surfaces. On the navy ground, dividers are `rgba(255,255,255,.10)`.

### Corner radii
- `0.25rem` — buttons, inputs, chips.
- `0.5rem` — small cards.
- `3rem` on **top-right only** — petal motif (cards, image masks).

### Animation
- Easing: `cubic-bezier(0.2, 0.8, 0.2, 1)` (standard "decelerate"). Duration 200ms (UI) / 400ms (page-level).
- Hover: opacity to 0.9 **or** background darken to Dark Green. Never scale-up.
- Press: background darkens one notch; no shrink/scale.
- Page transitions: simple fade + 8px translate-up. No bounce, no parallax.

### Transparency / blur
Used only for sticky headers (a `backdrop-blur` over a translucent off-white). Never for decoration.

### Imagery — use real human photography
**This is non-negotiable.** Every image surface in an LHWRF design must use **real photography of real people from the field** — farmers, women's collective members, students, health workers, community leaders. The Foundation's credibility is built on actual outcomes in actual villages; generic stock imagery undermines that.

**Rules**
- ✅ Real photographs from LHWRF program sites: farmers in their fields, women in self-help group meetings, children in anganwadi centres, health workers on visits, panchayat members.
- ✅ Natural light, on-location, candid moments. Hands, faces at work, real environments.
- ✅ Subjects looking at their work or each other — not posed at the camera unless it's a deliberate portrait.
- ❌ **No generic stock photography.** No "diverse team in a glass conference room," no smiling-handshake business shots.
- ❌ **No AI-generated people.** Ever.
- ❌ No illustration substitutes for human subjects in primary content positions.
- ❌ No black-and-white, no heavy filters, no grain. Slight green-cool grade is fine; nothing more.

**Consent and dignity.** Photograph people as partners, not subjects. Names, villages and program context should accompany hero portraits where possible. Avoid "before/after" framings that dehumanise.

**While real photography is being sourced**, image slots in mocks should be left as styled placeholders (the green-gradient petal-masked block used throughout this system). Never substitute a stock photo or an AI image even temporarily — an obvious placeholder is more honest than a fake.

---

## ICONOGRAPHY

Lupin's site uses **outlined, 1.5–2px stroke** icons — minimal, geometric, no fills. We replicate this with **Lucide** via CDN, which is the closest open match (same stroke weight, same geometric construction).

> ⚠️ **Icon substitution flagged.** No Lupin icon set was provided. Lucide is the substitute. To swap, replace `<i data-lucide="...">` with the brand SVG and remove the Lucide CDN script.

**Rules**
- 1.5px stroke, 24px default (20px in dense UIs).
- Color follows text (`currentColor`). Never multicolor.
- Icons are **functional only** — paired with a label or attached to an action. No decorative icon strips.
- Emoji and unicode characters are **never** used as icons.

**Logos / marks.** The official LHWRF lockup is at **`assets/lupin-foundation-logo.png`** (145×52, transparent PNG). Use this on light backgrounds — the wordmark renders in dark grey/black so it needs a paper or white surface for legibility. For dark grounds, request a knock-out (white) version of the lockup; until that's supplied, the petal-shaped mark in `assets/lupin-petal-mark.svg` is a stand-in that works on navy.

---

## Caveats & open questions

- **Real LHWRF logo is included** (`assets/lupin-foundation-logo.png`) — light-background version only. A white/knock-out version for navy grounds is still needed.
- **No source files were attached** beyond the logo and the token brief. Visual decisions outside those are interpretations of the brand cues, not extractions.
- **No font files.** Substituted with the system sans stack.
- **No icon set.** Substituted with Lucide.
- **No photography.** Image slots are styled placeholders.

If you can share the LHWRF brand kit (full logo set including knock-out, type files, photography from the field, and any digital style guide), the system will lock in much tighter.
