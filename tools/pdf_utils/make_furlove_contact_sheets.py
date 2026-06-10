from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\openedswarm\docs\fur-love-assets\pdf")
OUT = Path(r"C:\openedswarm\docs\fur-love-assets")

GROUPS = [
    ("concept-pages", sorted((ROOT / "concept-pages").glob("*.jpg"))),
    ("intro-pages", sorted((ROOT / "intro-pages").glob("*.jpg"))),
    ("concept-images", sorted((ROOT / "concept-images").glob("*"))[:80]),
    ("intro-images", sorted((ROOT / "intro-images").glob("*"))[:100]),
]

def sheet(name, files, cols=4, thumb_w=360, thumb_h=230):
    rows = (len(files) + cols - 1) // cols
    label_h = 32
    canvas = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), "#f6f1e8")
    draw = ImageDraw.Draw(canvas)
    for i, path in enumerate(files):
        try:
            im = Image.open(path).convert("RGB")
        except Exception:
            continue
        im.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (i % cols) * thumb_w + (thumb_w - im.width) // 2
        y = (i // cols) * (thumb_h + label_h)
        canvas.paste(im, (x, y))
        draw.text(((i % cols) * thumb_w + 8, y + thumb_h + 6), path.name[:48], fill="#161514")
    out = OUT / f"contact-{name}.jpg"
    canvas.save(out, quality=88)
    print(out)

for name, files in GROUPS:
    sheet(name, files)

