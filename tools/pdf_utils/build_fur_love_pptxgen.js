const pptxgen = require("../OpenedSwarm/node_modules/pptxgenjs");
const sharp = require("../OpenedSwarm/node_modules/sharp");
const path = require("path");
const fs = require("fs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.subject = "Fur Love India Launch Strategy";
pptx.title = "Fur Love India Launch Strategy";
pptx.company = "Fur Love";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Bricolage Grotesque",
  bodyFontFace: "Inter",
  lang: "en-US",
};
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";
pptx.margin = 0;
pptx.layout = "LAYOUT_WIDE";

const OUT = path.resolve(__dirname, "../docs/fur-love-india-launch-strategy-deck.pptx");
const LOGO = path.resolve(__dirname, "../docs/fur-love-wordmark-corrected.png");
const LOGO_WHITE = path.join(path.resolve(__dirname, "../docs/fur-love-assets"), "fur-love-wordmark-white.png");
const VERVE_SRC_BLACK = "C:/Users/Devan/Downloads/verve-media-black.png.png";
const VERVE_SRC_WHITE = "C:/Users/Devan/Downloads/verve-media-white.png.png";
const HEAD = "Bricolage Grotesque";
const BODY = "Inter";
const SERIF = "Cormorant Garamond";
const ASSET_DIR = path.resolve(__dirname, "../docs/fur-love-assets");
const VERVE_BLACK = path.join(ASSET_DIR, "verve-media-black-deck.png");
const VERVE_WHITE = path.join(ASSET_DIR, "verve-media-white-deck.png");
const IMG = {
  towelDog: path.join(ASSET_DIR, "dog-white-towel.jpg"),
  grooming: path.join(ASSET_DIR, "dog-grooming-towel.jpg"),
  drying: path.join(ASSET_DIR, "dog-drying-deck.jpg"),
  capPink: path.join(ASSET_DIR, "luxury-cap-pink.jpg"),
  bottlesSatin: path.join(ASSET_DIR, "luxury-bottles-satin.jpg"),
  igGrid: path.resolve(__dirname, "../docs/fur-love-design-system/uploads/instagram_grid-1778594263300.png"),
  gradient: path.join(ASSET_DIR, "fur-love-gradient.png"),
};

const C = {
  cream: "F6F1E8",
  paper: "FAF8F4",
  oat: "EFE7D7",
  ink: "161514",
  ink2: "3C3935",
  lilac: "B8A3D6",
  lilacDark: "7A5BA8",
  lilacSoft: "EADEF3",
  petal: "E8C8C2",
  sage: "A8B398",
  honey: "D9A85A",
  line: "D9D3CA",
};

async function ensureDerivedAssets() {
  fs.mkdirSync(ASSET_DIR, { recursive: true });
  if (!fs.existsSync(LOGO_WHITE)) {
    await sharp(LOGO)
      .ensureAlpha()
      .negate({ alpha: false })
      .png({ compressionLevel: 9 })
      .toFile(LOGO_WHITE);
  }
  if (fs.existsSync(VERVE_SRC_BLACK) && !fs.existsSync(VERVE_BLACK)) {
    await sharp(VERVE_SRC_BLACK)
      .trim({ threshold: 8 })
      .resize({ width: 1200, withoutEnlargement: true })
      .png({ compressionLevel: 9 })
      .toFile(VERVE_BLACK);
  }
  if (fs.existsSync(VERVE_SRC_WHITE) && !fs.existsSync(VERVE_WHITE)) {
    await sharp(VERVE_SRC_WHITE)
      .trim({ threshold: 8 })
      .resize({ width: 1200, withoutEnlargement: true })
      .png({ compressionLevel: 9 })
      .toFile(VERVE_WHITE);
  }
  if (!fs.existsSync(IMG.gradient)) {
    const svg = `<svg width="1600" height="140" viewBox="0 0 1600 140" xmlns="http://www.w3.org/2000/svg">
      <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#6E3FA8"/><stop offset="45%" stop-color="#B8A3D6"/><stop offset="100%" stop-color="#E36BA4"/>
      </linearGradient></defs><rect width="1600" height="140" fill="url(#g)"/></svg>`;
    await sharp(Buffer.from(svg)).png().toFile(IMG.gradient);
  }
}

function addBg(slide, color = C.cream) {
  slide.background = { color };
}

function addLogo(slide, light = false) {
  slide.addImage({
    path: light && fs.existsSync(LOGO_WHITE) ? LOGO_WHITE : LOGO,
    x: 0.48, y: 0.31, w: 1.65, h: 0.25,
  });
}

function addAgencyLogo(slide, light = false) {
  const img = light ? VERVE_WHITE : VERVE_BLACK;
  if (!fs.existsSync(img)) return;
  slide.addImage({
    path: img,
    x: 11.05, y: 0.29, w: 1.48, h: 0.58,
  });
}

function addGradient(slide, x = 0, y = 0, w = 13.333, h = 0.12) {
  slide.addImage({ path: IMG.gradient, x, y, w, h });
}

function footer(slide, n, light = false) {
  slide.addShape(pptx.ShapeType.line, {
    x: 0.48, y: 6.86, w: 12.25, h: 0,
    line: { color: light ? "6B6660" : C.line, transparency: light ? 45 : 0, width: 0.55 },
  });
  slide.addText(String(n).padStart(2, "0"), {
    x: 12.28, y: 6.99, w: 0.35, h: 0.15,
    fontFace: BODY, fontSize: 7.5, color: light ? C.paper : "6B6660",
    margin: 0,
  });
}

function imageFrame(slide, label, opts = {}) {
  const {
    x = 0, y = 0, w = 13.333, h = 7.5,
    fill = C.oat, line = C.lilac, large = true,
    img = null,
  } = opts;
  if (img && fs.existsSync(img)) {
    slide.addImage({ path: img, x, y, w, h, sizing: { type: "cover", w, h } });
  } else {
    slide.addShape(pptx.ShapeType.rect, {
      x, y, w, h,
      fill: { color: fill },
      line: { color: line, transparency: 55, width: 0.7 },
    });
    slide.addShape(pptx.ShapeType.arc, {
      x: x + w * 0.67, y: y + h * 0.14, w: w * 0.18, h: h * 0.18,
      line: { color: C.petal, transparency: 20, width: 2 },
      adjustPoint: 0.2,
    });
    slide.addShape(pptx.ShapeType.line, {
      x: x + 0.35, y: y + 0.45, w: w - 0.7, h: h - 0.9,
      line: { color: C.lilac, transparency: 45, width: 0.9 },
    });
    slide.addText("IMAGE PLACEHOLDER", {
      x: x + 0.45, y: y + 0.42, w: Math.min(3.2, w - 0.9), h: 0.22,
      fontFace: BODY, fontSize: large ? 8 : 7,
      bold: true, charSpace: 1.1, color: C.lilacDark, margin: 0,
    });
    slide.addText(label, {
      x: x + 0.45, y: y + h - 0.72, w: w - 0.9, h: 0.38,
      fontFace: HEAD, fontSize: large ? 13 : 10,
      bold: true, color: C.ink, margin: 0.02,
    });
  }
}

function textBlock(slide, eyebrow, title, body, x, y, opts = {}) {
  const light = opts.light || false;
  const titleSize = opts.titleSize || 36;
  const width = opts.w || 5.25;
  const align = opts.align || "left";
  slide.addText(eyebrow.toUpperCase(), {
    x, y, w: width, h: 0.34,
    fontFace: BODY, fontSize: opts.eyebrowSize || 13.2, bold: true,
    color: light ? C.petal : C.lilacDark,
    charSpace: 1.0, margin: 0, align,
  });
  slide.addText(title, {
    x, y: y + 0.46, w: width, h: opts.titleH || 1.62,
    fontFace: HEAD, fontSize: titleSize, bold: true,
    color: light ? C.paper : C.ink,
    breakLine: false, margin: 0,
    valign: "top", align,
  });
  slide.addText(body, {
    x, y: y + (opts.bodyY || 2.28), w: opts.bodyW || Math.min(width, 4.8), h: opts.bodyH || 0.95,
    fontFace: BODY, fontSize: opts.bodySize || 15,
    color: light ? C.line : C.ink2,
    margin: 0, breakLine: false, align,
  });
}

function fullBleed(slide, n, imageLabel, overlay, textPos = "left", img = null, dark = false) {
  addBg(slide, C.cream);
  imageFrame(slide, imageLabel, { fill: C.oat, line: C.lilac, large: true, img });
  if (dark) {
    slide.addShape(pptx.ShapeType.rect, {
      x: 0, y: 0, w: 13.333, h: 7.5,
      fill: { color: C.ink, transparency: 10 },
      line: { color: C.ink, transparency: 100 },
    });
  }

  let box;
  if (textPos === "right") box = { x: 6.9, y: 0, w: 6.43, h: 7.5 };
  else if (textPos === "bottom") box = { x: 0, y: 4.05, w: 13.333, h: 3.45 };
  else if (textPos === "center") box = { x: 2.25, y: 1.1, w: 8.85, h: 5.15 };
  else box = { x: 0, y: 0, w: 6.45, h: 7.5 };

  slide.addShape(pptx.ShapeType.rect, {
    ...box,
    fill: { color: overlay.panelColor || (dark ? C.ink : (overlay.light ? C.paper : C.cream)), transparency: overlay.transparency ?? (dark ? 18 : 8) },
    line: { color: dark ? C.ink : (overlay.light ? C.paper : C.cream), transparency: 100 },
  });
  addGradient(slide, 0, 0, 13.333, 0.08);
  addLogo(slide, dark && !overlay.forceDarkLogo ? true : false);
  addAgencyLogo(slide, dark && !overlay.forceDarkLogo ? true : false);
  const x = textPos === "right" ? 7.45 : textPos === "center" ? 2.85 : 0.78;
  const y = textPos === "bottom" ? 4.45 : textPos === "center" ? 1.55 : 1.28;
  const light = dark && !overlay.forceDarkText;
  textBlock(slide, overlay.eyebrow, overlay.title, overlay.body, x, y, {
    w: textPos === "center" ? 7.65 : 5.35,
    titleSize: overlay.titleSize || (textPos === "center" ? 46 : 40),
    titleH: overlay.titleH || 2.05,
    bodyY: overlay.bodyY || 2.7,
    bodyW: overlay.bodyW || 5.0,
    bodySize: overlay.bodySize || 15,
    bodyH: overlay.bodyH || 1.0,
    align: textPos === "center" ? "center" : "left",
    light,
  });
  footer(slide, n, dark);
}

function titleSlide() {
  const s = pptx.addSlide();
  addBg(s, C.cream);
  addGradient(s, 0, 0, 13.333, 0.1);
  imageFrame(s, "Full-bleed hero dog portrait with product cue. Leave calm space on left.", {
    x: 5.65, y: 0, w: 7.683, h: 7.5, fill: C.oat, line: C.lilac, img: IMG.towelDog,
  });
  s.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 6.1, h: 7.5,
    fill: { color: C.cream, transparency: 0 },
    line: { color: C.cream, transparency: 100 },
  });
  addLogo(s);
  addAgencyLogo(s);
  s.addText("Fur Love,\nFor Love", {
    x: 0.72, y: 1.82, w: 5.25, h: 1.95,
    fontFace: HEAD, fontSize: 48, bold: true,
    color: C.ink, margin: 0,
  });
  s.addText("India launch strategy", {
    x: 0.78, y: 3.78, w: 3.4, h: 0.22,
    fontFace: BODY, fontSize: 8.3, bold: true,
    color: C.lilacDark, charSpace: 1.4, margin: 0,
  });
  s.addText("A beauty-led launch for dogs who are loved deeply.", {
    x: 0.78, y: 4.28, w: 4.45, h: 0.55,
    fontFace: BODY, fontSize: 14.8, color: C.ink2, margin: 0,
  });
  footer(s, 1);
}

function movementSlide() {
  const s = pptx.addSlide();
  addBg(s, C.paper);
  imageFrame(s, "Soft abstract ritual background: towel, fur, product edge. Very low contrast.", {
    x: 0, y: 0, w: 13.333, h: 7.5, fill: C.cream, line: C.line, img: IMG.grooming,
  });
  s.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 13.333, h: 7.5,
    fill: { color: C.paper, transparency: 14 },
    line: { color: C.paper, transparency: 100 },
  });
  addGradient(s, 0, 0, 13.333, 0.08);
  addLogo(s);
  addAgencyLogo(s);
  textBlock(
    s,
    "How the story moves",
    "Do not reveal everything at once.",
    "The launch should move like a luxury reveal, not a product catalogue.",
    0.78,
    1.04,
    { w: 7.2, titleSize: 40, titleH: 1.15, bodyY: 1.9, bodyW: 5.7, bodySize: 14.5, bodyH: 0.68 }
  );
  const acts = [
    ["01", "Create desire", "Something premium is coming."],
    ["02", "Show the gap", "Pet care can look better."],
    ["03", "Reveal ritual", "Texture, touch, dog, finish."],
    ["04", "Build recall", "Repeat until it feels familiar."],
  ];
  acts.forEach((a, i) => {
    const y = 3.25 + i * 0.72;
    s.addText(a[0], { x: 0.9, y, w: 0.45, h: 0.18, fontFace: BODY, fontSize: 9.2, bold: true, color: C.lilacDark, margin: 0 });
    s.addShape(pptx.ShapeType.line, { x: 1.48, y: y + 0.1, w: 0.6, h: 0, line: { color: C.lilac, width: 1.15 } });
    s.addText(a[1], { x: 2.28, y: y - 0.08, w: 2.6, h: 0.34, fontFace: HEAD, fontSize: 18, bold: true, color: C.ink, margin: 0 });
    s.addText(a[2], { x: 4.95, y: y - 0.02, w: 4.25, h: 0.3, fontFace: BODY, fontSize: 11.5, color: C.ink2, margin: 0 });
  });
  footer(s, 8);
}

function takeoverSlide() {
  const s = pptx.addSlide();
  addBg(s, C.ink);
  addGradient(s, 0, 0, 13.333, 0.1);
  imageFrame(s, "Luxury macro product-cap texture for the takeover world.", {
    x: 0, y: 0, w: 13.333, h: 7.5, fill: C.oat, line: C.lilac, img: IMG.capPink,
  });
  s.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 13.333, h: 7.5,
    fill: { color: C.ink, transparency: 22 },
    line: { color: C.ink, transparency: 100 },
  });
  addLogo(s, true);
  addAgencyLogo(s, true);
  textBlock(
    s,
    "Grand pre-launch activity",
    "The Fur Love\nTakeover",
    "A luxury outdoor teaser built to make people ask, 'what is this?' before the product is revealed.",
    0.78,
    0.98,
    { w: 4.9, titleSize: 38, titleH: 1.55, bodyY: 2.95, bodyW: 4.55, bodySize: 15.2, bodyH: 1.08, light: true }
  );
  s.addShape(pptx.ShapeType.rect, {
    x: 6.72, y: 0.92, w: 5.36, h: 5.25,
    fill: { color: C.paper },
    line: { color: C.paper, transparency: 100 },
    shadow: { type: "outer", color: "000000", opacity: 0.26, blur: 4, angle: 45, distance: 2 },
  });
  s.addImage({ path: LOGO, x: 7.08, y: 1.24, w: 1.72, h: 0.26 });
  s.addText("FUR LOVE,", { x: 7.06, y: 2.05, w: 4.2, h: 0.68, fontFace: HEAD, fontSize: 38, bold: true, color: C.ink, margin: 0 });
  s.addText("FOR LOVE", { x: 7.08, y: 2.72, w: 4.15, h: 0.62, fontFace: SERIF, fontSize: 31, italic: true, bold: true, color: C.lilacDark, margin: 0 });
  s.addShape(pptx.ShapeType.line, { x: 7.09, y: 3.72, w: 4.15, h: 0, line: { color: C.line, width: 0.8 } });
  s.addText("A citywide premium teaser:\nmacro caps, texture crops,\ncoat-finish portraits,\nand the line before the reveal.", {
    x: 7.1, y: 4.02, w: 4.15, h: 1.08,
    fontFace: BODY, fontSize: 15.5, color: C.ink2, margin: 0,
  });
  s.addShape(pptx.ShapeType.roundRect, { x: 10.78, y: 1.17, w: 0.72, h: 3.0, rectRadius: 0.04, fill: { color: C.lilacSoft }, line: { color: C.lilacSoft, transparency: 100 } });
  s.addText("OOH", { x: 10.92, y: 3.48, w: 0.32, h: 0.22, rotate: 270, fontFace: BODY, fontSize: 9.5, bold: true, color: C.lilacDark, margin: 0 });
  footer(s, 10, true);
}

function contentSystemSlide() {
  const s = pptx.addSlide();
  addBg(s, C.cream);
  imageFrame(s, "Blurred ritual/product background. Keep it light, clean, low contrast.", {
    x: 0, y: 0, w: 13.333, h: 7.5, fill: C.oat, line: C.line, img: IMG.bottlesSatin,
  });
  s.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 13.333, h: 7.5,
    fill: { color: C.cream, transparency: 18 },
    line: { color: C.cream, transparency: 100 },
  });
  addLogo(s);
  addAgencyLogo(s);
  textBlock(
    s,
    "Launch content system",
    "One launch. Three repeating assets.",
    "Enough structure to sustain the feed without making it feel mechanical.",
    0.78,
    1.0,
    { w: 6.3, titleSize: 39, titleH: 1.05, bodyY: 1.9, bodyW: 5.5, bodySize: 14.3, bodyH: 0.65 }
  );
  const cards = [
    ["Hero Film", "The full ritual and brand reveal.", C.lilacSoft],
    ["SKU Reels", "Use-led demos for each product.", C.petal],
    ["Creator First-Use", "Premium parent + dog reactions.", "E5E9DD"],
  ];
  cards.forEach((card, i) => {
    const x = 0.78 + i * 4.08;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y: 3.45, w: 3.55, h: 1.6,
      rectRadius: 0.06,
      fill: { color: card[2] },
      line: { color: C.line, transparency: 100 },
    });
    s.addText(card[0], { x: x + 0.26, y: 3.72, w: 2.75, h: 0.38, fontFace: HEAD, fontSize: 16.5, bold: true, color: C.ink, margin: 0 });
    s.addText(card[1], { x: x + 0.26, y: 4.34, w: 2.7, h: 0.42, fontFace: BODY, fontSize: 10.8, color: C.ink2, margin: 0 });
  });
  footer(s, 12);
}

function rhythmSlide() {
  const s = pptx.addSlide();
  addBg(s, C.paper);
  addGradient(s, 0, 0, 13.333, 0.08);
  imageFrame(s, "Soft product shelf and dog-care objects. Low contrast background image.", {
    x: 0, y: 0, w: 13.333, h: 7.5, fill: C.cream, line: C.line,
  });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.paper, transparency: 6 }, line: { color: C.paper, transparency: 100 } });
  addLogo(s);
  addAgencyLogo(s);
  textBlock(
    s,
    "Operating rhythm",
    "Sell a system, not a post list.",
    "The audience should feel the launch moving from desire to proof.",
    0.78,
    1.0,
    { w: 5.8, titleSize: 30, titleH: 1.0, bodyY: 1.72, bodyW: 5.0, bodySize: 13.2, bodyH: 0.55 }
  );
  const rows = [
    ["Pre-launch", "Desire + sightings"],
    ["Launch week", "Ritual + range"],
    ["Next 30 days", "Repeat + explain"],
    ["Always-on", "Proof + culture"],
  ];
  rows.forEach((r, i) => {
    const y = 3.04 + i * 0.68;
    s.addShape(pptx.ShapeType.roundRect, { x: 0.82, y, w: 1.85, h: 0.38, fill: { color: C.lilacSoft }, line: { color: C.lilacSoft, transparency: 100 } });
    s.addText(r[0], { x: 1.0, y: y + 0.09, w: 1.4, h: 0.18, fontFace: BODY, fontSize: 8.8, bold: true, color: C.lilacDark, margin: 0 });
    s.addText(r[1], { x: 3.1, y: y + 0.03, w: 3.4, h: 0.3, fontFace: HEAD, fontSize: 14.8, bold: true, color: C.ink, margin: 0 });
    s.addShape(pptx.ShapeType.line, { x: 6.9, y: y + 0.18, w: 4.7, h: 0, line: { color: C.line, width: 0.55 } });
  });
  footer(s, 14);
}

async function main() {
  await ensureDerivedAssets();
  titleSlide();
  fullBleed(pptx.addSlide(), 2, "Pet parent and dog, intimate close-up. Warm daylight.", {
    eyebrow: "The gap",
    title: "Pet love has changed.\nPet care has not caught up.",
    body: "This is the gap Fur Love can own in India.",
    titleSize: 43,
    titleH: 2.25,
    bodyY: 3.35,
    bodyH: 0.85,
  }, "right", IMG.drying, true);
  fullBleed(pptx.addSlide(), 3, "Pet grooming shelf/product clutter image. Leave calm zone on left.", {
    eyebrow: "The tension",
    title: "The category still looks functional.",
    body: "Most pet grooming launches look instructional, cute, or noisy. Fur Love should feel like a ritual people aspire to keep.",
    titleSize: 42,
    titleH: 1.8,
    bodyY: 2.88,
    bodySize: 15,
    bodyH: 1.1,
  }, "left", null, false);
  fullBleed(pptx.addSlide(), 4, "Beauty-style product texture with dog fur. Close crop.", {
    eyebrow: "The opening",
    title: "Make dog care feel like beauty care.",
    body: "Show texture, touch, packaging, coat finish, and softness before asking people to remember SKUs.",
    titleSize: 38,
    titleH: 1.12,
    bodyY: 1.95,
    bodyW: 7.2,
    bodySize: 15,
    bodyH: 0.65,
  }, "bottom", IMG.bottlesSatin, false);
  fullBleed(pptx.addSlide(), 5, "Dog face close-up, soft eye contact. Cream towel, no clutter.", {
    eyebrow: "Communication thought",
    title: "Fur Love,",
    body: "",
    titleSize: 62,
    titleH: 1.2,
    bodyY: 2.2,
    bodyW: 6.5,
    bodySize: 13,
    bodyH: 0.2,
  }, "center", IMG.towelDog, true);
  fullBleed(pptx.addSlide(), 6, "Dog face close-up, soft eye contact. Cream towel, no clutter.", {
    eyebrow: "Communication thought",
    title: "Fur Love,\nFor Love",
    body: "Not a line about grooming. A line about the standard of care love deserves.",
    titleSize: 54,
    titleH: 1.85,
    bodyY: 3.05,
    bodyW: 6.5,
    bodySize: 16,
    bodyH: 0.85,
  }, "center", IMG.towelDog, true);
  fullBleed(pptx.addSlide(), 7, "Clean bathroom ritual, towel, dog, product. Warm daylight.", {
    eyebrow: "The tone",
    title: "Premium, clinical, intimate.",
    body: "Warm enough to feel like love. Sharp enough to feel like skincare. Never kiddish, never pet-shop cute.",
    titleSize: 41,
    titleH: 1.45,
    bodyY: 2.72,
    bodySize: 15,
    bodyH: 0.95,
  }, "right", IMG.grooming, false);
  movementSlide();
  fullBleed(pptx.addSlide(), 9, "Mysterious product crop with fur and label. Premium teaser feel.", {
    eyebrow: "Phase 1",
    title: "Build sightings before explanation.",
    body: "Packaging crops, coat close-ups, texture videos, ritual fragments, countdown stories, and city sightings.",
    titleSize: 39,
    titleH: 1.55,
    bodyY: 2.85,
    bodySize: 15,
    bodyH: 0.92,
  }, "left", IMG.capPink, false);
  takeoverSlide();
  fullBleed(pptx.addSlide(), 11, "Hero film still: parent applying product to dog.", {
    eyebrow: "Launch",
    title: "Reveal the ritual, then the range.",
    body: "Move from touch to texture to coat finish, then make the products easy to understand.",
    titleSize: 40,
    titleH: 1.12,
    bodyY: 1.95,
    bodyW: 7.0,
    bodySize: 15,
    bodyH: 0.65,
  }, "bottom", IMG.grooming, true);
  contentSystemSlide();
  fullBleed(pptx.addSlide(), 13, "Real parent/dog testimonial or routine shot. Light, intimate, believable.", {
    eyebrow: "Sustainance",
    title: "Turn the launch into recall.",
    body: "Keep the feed moving with ritual series, better-care education, real parent use, packaging shots, and cultural moments.",
    titleSize: 41,
    titleH: 1.45,
    bodyY: 2.72,
    bodySize: 15,
    bodyH: 0.95,
  }, "right", IMG.drying, false);
  rhythmSlide();
  fullBleed(pptx.addSlide(), 15, "Final hero dog, polished coat, calm premium frame. Leave calm zone on left.", {
    eyebrow: "The takeaway",
    title: "Fur Love is the premium care brand for loved dogs.",
    body: "A beauty launch built around love, ritual, and proof.",
    titleSize: 46,
    titleH: 2.3,
    bodyY: 3.65,
    bodySize: 16,
    bodyH: 0.72,
  }, "left", IMG.towelDog, true);

  await pptx.writeFile({ fileName: OUT });
  console.log(`Wrote ${OUT}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
