from pathlib import Path
from PIL import Image, ImageDraw

files = [Path("docs/fur-love-html-slide-shots") / f"slide-{i:02d}.png" for i in [2, 6, 7, 8, 9, 12, 13]]
thumbs = []
for p in files:
    im = Image.open(p).convert("RGB")
    im.thumbnail((420, 236), Image.Resampling.LANCZOS)
    thumbs.append((p, im.copy()))

w, h = 420, 270
canvas = Image.new("RGB", (w * 2, h * 4), "#f6f1e8")
draw = ImageDraw.Draw(canvas)
for idx, (p, im) in enumerate(thumbs):
    x = (idx % 2) * w
    y = (idx // 2) * h
    canvas.paste(im, (x, y))
    draw.text((x + 8, y + 240), p.name, fill="#161514")

canvas.save("docs/fur-love-key-slide-check.jpg", quality=90)
