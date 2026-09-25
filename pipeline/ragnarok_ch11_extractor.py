"""
pipeline/ragnarok_ch11_extractor.py — Extract high-resolution strips from Solo Leveling: Ragnarok Chapter 11 PDF.
"""

import sys
from pathlib import Path
import pymupdf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = Path(r"C:\Users\ABHAY MAURAYA\.gemini\antigravity-ide\brain\a6075157-dcd6-4aff-ac56-7ed16bcded0b\.user_uploaded\media_1790344299140.pdf")

OUT_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch11" / "raw_strips"

def extract_strips():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📖 Opening PDF: {PDF_PATH}")
    doc = pymupdf.open(str(PDF_PATH))
    print(f"📄 Total Pages: {len(doc)}")

    # Matrix 1.5 gives crisp 1080p resolution
    mat = pymupdf.Matrix(1.5, 1.5)

    for i, page in enumerate(doc, start=1):
        out_file = OUT_DIR / f"strip_{i:02d}.jpg"
        if out_file.exists() and out_file.stat().st_size > 10000:
            print(f"  ⏩ Strip {i:02d} already extracted ({out_file.stat().st_size / 1024:.1f} KB)")
            continue
        print(f"  ⚡ Rendering Page {i:02d}/{len(doc)}...")
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(str(out_file), "jpeg", jpg_quality=95)
        print(f"  ✓ Saved {out_file.name} ({pix.width}x{pix.height}, {out_file.stat().st_size / 1024:.1f} KB)")

    print(f"\n✅ All {len(doc)} strips extracted to {OUT_DIR}")

if __name__ == "__main__":
    extract_strips()
