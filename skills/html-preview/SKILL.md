---
name: html-preview
description: >
  Take Playwright screenshots of any local HTML file to visually verify design changes
  without opening a browser manually. Use this after every CSS/HTML edit so you can
  see exactly what changed before declaring it done.
metadata:
  author: gyanweshi
  version: "1.0.0"
---

# html-preview — Visual verification for HTML files

Use this skill any time you edit an HTML file and need to verify the result visually
instead of guessing. Always screenshot BEFORE and AFTER a design change.

---

## How to use

Run the snippet below in a Bash tool, substituting the file path and slide count:

```python
import asyncio
from playwright.async_api import async_playwright

FILE = "file:///absolute/path/to/file.html"   # ← change this
SLIDES = [1, 2, 5, 8, 12]                     # ← which "screens" to capture
OUT = "/tmp/preview"                           # ← output prefix

async def go():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        await pg.goto(FILE)
        await pg.wait_for_timeout(2000)   # wait for fonts/animations

        current = 1
        for target in sorted(SLIDES):
            while current < target:
                await pg.keyboard.press("ArrowDown")
                await pg.wait_for_timeout(700)
                current += 1
            await pg.screenshot(path=f"{OUT}_s{target}.png")

        await b.close()
        print("done")

asyncio.run(go())
```

Then read each `/tmp/preview_sN.png` with the Read tool to inspect visually.

---

## For non-slide HTML (scroll pages)

Use `page.evaluate("window.scrollTo(0, N)")` instead of arrow keys,
or take a full-page screenshot with `full_page=True`.

---

## Prerequisites

- `playwright` Python package: `pip3 install playwright --break-system-packages`
- Google Chrome at `/usr/bin/google-chrome` (already installed on this machine)
- No need to run `playwright install` — we use system Chrome directly

---

## Workflow

1. Read the HTML file to understand current CSS
2. **Screenshot before** editing (capture the problem)
3. Make CSS edits
4. **Screenshot after** editing (verify the fix)
5. Read screenshots with the Read tool and describe what changed
6. Only declare the task done after visually confirming the result looks right

---

## Key readability checks to run on every slide deck

- Heading size: should NOT dominate >40% of slide height
- `--text-dim` value: should have WCAG AA contrast (≥4.5:1) against white background
- Body line-height: minimum 1.5 for readability, 1.55+ preferred
- Font weight: Inter body at weight 400 can look thin — use 500 for slides
- Letter spacing on display headings: -0.01em feels tighter, more modern
