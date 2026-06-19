#!/usr/bin/env node
// Generic HTML slide-deck -> PPTX exporter. Renders each `.slide` element via
// headless Chromium screenshot and packs the images into a pptx.
//
// Usage:
//   node tools/pdf_utils/html_to_pptx.js --input deck.html --output deck.pptx
//
// Options:
//   --input <path>       HTML file to render (required)
//   --output <path>      Output .pptx path (required)
//   --scale <number>     deviceScaleFactor, default 1.5
//   --format png|jpeg    Screenshot format, default jpeg
//   --quality <0-100>    JPEG quality, default 90 (ignored for png)
//   --width <px>         Viewport width, default 1600
//   --height <px>        Viewport height, default 900
//   --wait <ms>          Delay after activating each slide, default 350
//   --selector <css>     Slide selector, default ".slide"
//   --keep-shots         Don't delete the intermediate screenshot folder

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
const pptxgen = require("pptxgenjs");

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    if (key === "keep-shots") {
      out.keepShots = true;
      continue;
    }
    out[key] = argv[i + 1];
    i += 1;
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.input || !args.output) {
    console.error("Usage: node html_to_pptx.js --input <html> --output <pptx> [options]");
    process.exit(1);
  }

  const HTML = path.resolve(args.input);
  const OUT = path.resolve(args.output);
  const SCALE = args.scale ? Number(args.scale) : 1.5;
  const FORMAT = args.format === "png" ? "png" : "jpeg";
  const QUALITY = args.quality ? Number(args.quality) : 90;
  const WIDTH = args.width ? Number(args.width) : 1600;
  const HEIGHT = args.height ? Number(args.height) : 900;
  const WAIT = args.wait ? Number(args.wait) : 350;
  const SELECTOR = args.selector || ".slide";
  const SHOT_DIR = path.join(path.dirname(OUT), `.${path.basename(OUT, ".pptx")}-shots`);

  if (!fs.existsSync(HTML)) {
    console.error(`Input not found: ${HTML}`);
    process.exit(1);
  }

  fs.rmSync(SHOT_DIR, { recursive: true, force: true });
  fs.mkdirSync(SHOT_DIR, { recursive: true });

  const browser = await chromium.launch({
    headless: true,
    args: ["--disable-gpu", "--allow-file-access-from-files", "--font-render-hinting=none"],
  });
  const page = await browser.newPage({
    viewport: { width: WIDTH, height: HEIGHT },
    deviceScaleFactor: SCALE,
  });

  await page.goto(`file:///${HTML.replace(/\\/g, "/")}`, { waitUntil: "load" });
  await page.evaluate(() => Promise.all([
    document.fonts.ready,
    ...Array.from(document.images).map((img) =>
      img.complete ? Promise.resolve() : new Promise((r) => { img.onload = r; img.onerror = r; })
    ),
  ]));
  await page.waitForTimeout(800);

  await page.addStyleTag({
    content: `
      html { scroll-behavior: auto !important; }
      .nav-dots, .progress-bar, .progress, #editorToolbar, .et-edit-badge { display: none !important; }
      .slide { scroll-snap-align: none !important; }
      .reveal { opacity: 1 !important; transform: none !important; filter: none !important;
                transition: none !important; animation-name: none !important; }
      .slide:not(.visible) .reveal { opacity: 1 !important; }
    `,
  });

  const count = await page.locator(SELECTOR).count();
  if (count === 0) {
    console.error(`No elements matched selector "${SELECTOR}" — nothing to export.`);
    await browser.close();
    process.exit(1);
  }
  console.log(`Found ${count} slides — screenshotting at ${SCALE}x (${FORMAT}, q${QUALITY})...`);

  const shots = [];
  for (let i = 0; i < count; i += 1) {
    await page.evaluate(({ index, selector }) => {
      const slides = [...document.querySelectorAll(selector)];
      slides.forEach((s, n) => s.classList.toggle("visible", n === index));
      slides[index].scrollIntoView({ block: "start" });
      document.documentElement.scrollTop = index * window.innerHeight;
    }, { index: i, selector: SELECTOR });
    await page.waitForTimeout(WAIT);

    const shot = path.join(SHOT_DIR, `slide-${String(i + 1).padStart(3, "0")}.${FORMAT}`);
    const screenshotOpts = { path: shot, fullPage: false, type: FORMAT };
    if (FORMAT === "jpeg") screenshotOpts.quality = QUALITY;
    await page.screenshot(screenshotOpts);
    shots.push(shot);

    if ((i + 1) % 20 === 0) console.log(`  ${i + 1}/${count} done`);
  }

  await browser.close();
  console.log(`Screenshots done -> ${SHOT_DIR}`);

  const pptx = new pptxgen();
  pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
  pptx.layout = "CUSTOM_WIDE";

  for (const shot of shots) {
    const slide = pptx.addSlide();
    slide.addImage({ path: shot, x: 0, y: 0, w: 13.333, h: 7.5 });
  }

  await pptx.writeFile({ fileName: OUT });

  if (!args.keepShots) fs.rmSync(SHOT_DIR, { recursive: true, force: true });

  const sizeMB = (fs.statSync(OUT).size / (1024 * 1024)).toFixed(1);
  console.log(`\nDone. ${count} slides -> ${OUT} (${sizeMB} MB)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
