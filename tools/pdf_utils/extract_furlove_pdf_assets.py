from pathlib import Path
import fitz

PDFS = [
    (Path(r"C:\Users\Devan\Downloads\Concept store France.pdf"), "concept"),
    (Path(r"C:\Users\Devan\Downloads\Introduction deck FURLOVE (1).pdf"), "intro"),
]

OUT = Path(r"C:\openedswarm\docs\fur-love-assets\pdf")
OUT.mkdir(parents=True, exist_ok=True)

for pdf_path, slug in PDFS:
    doc = fitz.open(pdf_path)
    render_dir = OUT / f"{slug}-pages"
    image_dir = OUT / f"{slug}-images"
    render_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    print(f"{slug}: {len(doc)} pages")

    for page_index, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        page_out = render_dir / f"{slug}-page-{page_index:02d}.jpg"
        pix.save(page_out, jpg_quality=90)

        for img_index, info in enumerate(page.get_images(full=True), start=1):
            xref = info[0]
            try:
                extracted = doc.extract_image(xref)
            except Exception:
                continue
            ext = extracted.get("ext", "bin")
            data = extracted.get("image")
            if not data:
                continue
            image_out = image_dir / f"{slug}-p{page_index:02d}-img{img_index:02d}.{ext}"
            if not image_out.exists():
                image_out.write_bytes(data)

