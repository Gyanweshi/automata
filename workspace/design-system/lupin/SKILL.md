---
name: lupin-design
description: Use this skill to generate well-branded interfaces and assets for Lupin (a Lupin-Pharmaceuticals-inspired design system), either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.

Key files:
- `README.md` — brand overview, content fundamentals, visual foundations, iconography.
- `colors_and_type.css` — color + typography tokens (CSS custom properties).
- `Lupin Styleguide.html` — the canonical styleguide artifact (Tailwind, React, single-file).
- `ui_kits/marketing/` — interactive marketing-site recreation. Use as a reference for headers, heroes, product cards, footers.
- `assets/` — logo placeholder.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Non-negotiable rules

1. **The petal motif** — `border-radius: .25rem 3rem .25rem .25rem` (top-right only) is the single visual gesture that ties the brand together. Use it on image masks and cards. Never on buttons, inputs, or dialogs.
2. **Lime is a moment, not a fill.** One use per screen, max. Single highlighted word, small badge, single CTA.
3. **No emoji. No gradients-as-decoration. No glow shadows.** Pharma is regulated; the brand stays clinical.
4. **Clinical whitespace.** Component padding clusters at p-6 / p-8.
5. **Buttons have three roles**: primary (green), secondary (ink-outlined), accent (lime). Pick one per surface.
