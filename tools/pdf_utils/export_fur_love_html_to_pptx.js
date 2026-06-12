const fs = require("fs");
const path = require("path");
const { chromium } = require("../OpenedSwarm/node_modules/playwright-core");
const pptxgen = require("../OpenedSwarm/node_modules/pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const HTML = path.join(ROOT, "docs", "fur-love-india-launch-strategy-frontend.html");
const OUT = path.join(ROOT, "docs", "fur-love-india-launch-strategy-frontend-export.pptx");
const SHOT_DIR = path.join(ROOT, "docs", "fur-love-html-slide-shots");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";

async function main() {
  fs.rmSync(SHOT_DIR, { recursive: true, force: true });
  fs.mkdirSync(SHOT_DIR, { recursive: true });

  const browser = await chromium.launch({
    executablePath: CHROME,
    headless: true,
    args: ["--disable-gpu", "--allow-file-access-from-files"],
  });
  const page = await browser.newPage({
    viewport: { width: 1600, height: 900 },
    deviceScaleFactor: 1,
  });

  await page.goto(`file:///${HTML.replace(/\\/g, "/")}`, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await page.addStyleTag({
    content: `
      html { scroll-behavior: auto !important; }
      .nav-dots, .progress { display: none !important; }
      .slide { scroll-snap-align: none !important; }
      .reveal { opacity: 1 !important; transform: none !important; filter: none !important; transition: none !important; }
    `,
  });

  const count = await page.locator(".slide").count();
  const shots = [];
  for (let i = 0; i < count; i += 1) {
    await page.evaluate((index) => {
      const slides = [...document.querySelectorAll(".slide")];
      document.documentElement.scrollTop = index * window.innerHeight;
      slides.forEach((s, n) => s.classList.toggle("visible", n === index));
      slides[index].scrollIntoView({ block: "start" });
    }, i);
    await page.waitForTimeout(180);
    const shot = path.join(SHOT_DIR, `slide-${String(i + 1).padStart(2, "0")}.png`);
    await page.screenshot({ path: shot, fullPage: false });
    shots.push(shot);
  }
  await browser.close();

  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Codex";
  pptx.company = "Fur Love";
  pptx.subject = "Fur Love India Launch Strategy";
  pptx.title = "Fur Love India Launch Strategy";
  pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
  pptx.layout = "CUSTOM_WIDE";

  for (const shot of shots) {
    const slide = pptx.addSlide();
    slide.background = { color: "F6F1E8" };
    slide.addImage({ path: shot, x: 0, y: 0, w: 13.333, h: 7.5 });
  }

  await pptx.writeFile({ fileName: OUT });
  console.log(`slides=${count}`);
  console.log(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
