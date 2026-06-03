# Layouts

## Deck Shell
- File: `gitshare/altara-launch-strategy-v4/altara-launch-strategy-v4.html`
- Description: single-file slide deck with fixed overlays, per-slide sections, and JS-driven navigation.

Key shell elements:
- `progress-bar`
- `starfield`
- `north-star`
- `nav-dots`
- `verve-mark`
- `main > section.slide`

Representative structure:
```html
<body>
  <div class="progress-bar" aria-hidden="true"></div>
  <canvas class="starfield" aria-hidden="true"></canvas>
  <div class="north-star" aria-hidden="true"></div>
  <nav class="nav-dots" aria-label="Slide navigation"></nav>
  <img class="verve-mark" src="altara-pitch-assets/verve-media-white.png" alt="Verve Media">
  <main>
    <section class="slide ...">...</section>
    ...
  </main>
</body>
```

