"""
Modular PDF Extraction Utility.
Extracts pages and embedded images from PDFs using PyMuPDF (fitz).
"""
import sys
import argparse
from pathlib import Path
import fitz

def extract_pdf_assets(pdf_path: str | Path, output_dir: str | Path, prefix: str = "doc") -> None:
    """
    Extracts high quality page renders and embedded images from a PDF.
    
    Args:
        pdf_path: Path to the PDF file.
        output_dir: Directory to save the extracted assets.
        prefix: Prefix for the output files.
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
    render_dir = output_dir / f"{prefix}-pages"
    image_dir = output_dir / f"{prefix}-images"
    render_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(str(pdf_path))
    print(f"Extracting {len(doc)} pages from {pdf_path.name}...")
    
    for page_index, page in enumerate(doc, start=1):
        # Render full page
        pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        page_out = render_dir / f"{prefix}-page-{page_index:02d}.jpg"
        pix.save(str(page_out), jpg_quality=90)
        
        # Extract embedded images
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
                
            image_out = image_dir / f"{prefix}-p{page_index:02d}-img{img_index:02d}.{ext}"
            if not image_out.exists():
                image_out.write_bytes(data)
                
    print(f"Extraction complete. Assets saved to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Extract pages and images from a PDF.")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--out", "-o", default="./pdf-extracts", help="Output directory")
    parser.add_argument("--prefix", "-p", default="asset", help="Prefix for extracted files")
    
    args = parser.parse_args()
    
    try:
        extract_pdf_assets(args.pdf_path, args.out, args.prefix)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
