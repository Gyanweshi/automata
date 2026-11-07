"""Render every page of each PDF to JPEG and pull out its embedded images (Linux, macOS, Windows).

    python tools/pdf_utils/extract_furlove_pdf_assets.py --out DIR "Concept store France.pdf=concept" \
        "Introduction deck FURLOVE (1).pdf=intro"

Each argument is PDF_PATH=SLUG (SLUG defaults to the file name). Output: DIR/<slug>-pages/ and DIR/<slug>-images/.
"""
import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("pdfs", nargs="+", help="PDF_PATH or PDF_PATH=SLUG")
parser.add_argument("--out", type=Path, required=True, help="output folder")
args = parser.parse_args()

try:
    import fitz  # PyMuPDF; not in uv.lock yet
except ImportError:
    sys.exit("PyMuPDF is required: uv pip install pymupdf (see docs/DEPENDENCIES.md, known gaps)")

PDFS = []
for item in args.pdfs:
    path, _, slug = item.partition("=")
    PDFS.append((Path(path).expanduser(), slug or Path(path).stem))

OUT = args.out.expanduser()
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

