"""
pipeline/ragnarok_ch4_panel_slicer.py — Panel Extractor and Slicer for Solo Leveling: Ragnarok Chapter 4.

Renders high-resolution pages from media_1789896824855.pdf (15 pages) and slices them
into 32 focused action panels with wide aspect ratios for cinematic video compositing.
"""

import sys
from pathlib import Path
import fitz  # PyMuPDF
import cv2
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = Path(r"C:\Users\ABHAY MAURAYA\.gemini\antigravity-ide\brain\11c61c0d-2f7d-4c00-a86e-9ed2ef84b02c\.user_uploaded\media_1789896824855.pdf")
OUT_BASE = ROOT / "output" / "solo_leveling_ragnarok_ch4"
RAW_DIR = OUT_BASE / "raw_strips"
PANELS_DIR = OUT_BASE / "panels"

def extract_pdf_pages():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📄 Opening PDF: {PDF_PATH}")
    doc = fitz.open(str(PDF_PATH))
    print(f"  Total pages: {len(doc)}")

    for i, page in enumerate(doc, start=1):
        target_img = RAW_DIR / f"strip_{i:02d}.jpg"
        if target_img.exists() and target_img.stat().st_size > 50000:
            print(f"  ✓ Strip {i:02d} already extracted ({target_img.stat().st_size // 1024} KB)")
            continue

        # Render page
        pix = page.get_pixmap(dpi=150)
        pix.save(str(target_img))
        print(f"  ✓ Rendered Strip {i:02d}: {pix.width}x{pix.height} ({target_img.stat().st_size // 1024} KB)")

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing strips into 32 cinematic wide panels...")

    # Strip 1: Title Card (Reaper x Flame Solo Leveling Ragnarok Season 1 Ch 4)
    s1 = cv2.imread(str(RAW_DIR / "strip_01.jpg"))
    if s1 is not None:
        cv2.imwrite(str(PANELS_DIR / "panel_001.jpg"), s1)
        print("  ✓ Panel 001: Chapter Title Card")

    def crop_save(strip_num: int, panel_id: int, y1: int, y2: int, desc: str = ""):
        img_path = RAW_DIR / f"strip_{strip_num:02d}.jpg"
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  ❌ Missing strip {strip_num}")
            return
        h, w = img.shape[:2]
        c_y1 = max(0, min(y1, h - 1))
        c_y2 = max(c_y1 + 50, min(y2, h))
        cropped = img[c_y1:c_y2, 0:w]

        # Auto-trim extreme blank headers/footers
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        row_means = np.mean(gray, axis=1)
        valid = np.where((row_means > 10) & (row_means < 245))[0]
        if len(valid) > 80:
            top_m = max(0, valid[0] - 20)
            bot_m = min(cropped.shape[0], valid[-1] + 20)
            cropped = cropped[top_m:bot_m, :]

        out_path = PANELS_DIR / f"panel_{panel_id:03d}.jpg"
        cv2.imwrite(str(out_path), cropped)
        print(f"  ✓ Panel {panel_id:03d}: Strip {strip_num:02d} [{y1}:{y2}] -> {cropped.shape[1]}x{cropped.shape[0]} ({desc})")

    # Strip 2 (1112 x 18727): Suho's childhood drawing of Beru in apron & Suho in hospital
    crop_save(2, 2, 0, 5800, "Young Suho drawing Shadow Soldiers on paper")
    crop_save(2, 3, 5800, 12000, "Drawing of Beru wearing flower apron; Beru crying tears of joy")
    crop_save(2, 4, 12000, 18727, "Adult Suho waking up in hospital with bandaged cheek")

    # Strip 3 (1112 x 19560): Hospital room, phone call with uncle, TV news
    crop_save(3, 5, 0, 6000, "Suho in hospital bed looking out window: 'An... Ant...?'")
    crop_save(3, 6, 6000, 12800, "Phone call with panicked uncle; Suho calms him down")
    crop_save(3, 7, 12800, 19560, "TV News Broadcast: Casualties and mystery of the incident")

    # Strip 4 (1112 x 19823): Association baffled; all Mist Burns exploded
    crop_save(4, 8, 0, 6500, "News: Mist Burns infected university students")
    crop_save(4, 9, 6500, 13000, "Hunters arrived: all monsters were already dead and blown apart")
    crop_save(4, 10, 13000, 19823, "Suho in hospital bed: 'As expected, my awakening wasn't a dream...'")

    # Strip 5 (1112 x 14814): Status Window & Beru's voice from shadows
    crop_save(5, 11, 0, 6500, "STATUS WINDOW: Level 5, Strength 22, Ruler's Authority Lv. 1")
    crop_save(5, 12, 6500, 10500, "Suho wonders how he survived; Voice: 'That is because I, Beru, got rid of them'")
    crop_save(5, 13, 10500, 14814, "Shadow emerges: 'LONG TIME NO SEE, YOUNG MONARCH.'")

    # Strip 6 (1112 x 16782): Memories flooding back & Chibi Beru crying
    crop_save(6, 14, 0, 5500, "Beru overwhelmed with emotion looking at grown-up Suho")
    crop_save(6, 15, 5500, 11500, "Suho's memories flood back: 'I know this ant... he was with me when I was young'")
    crop_save(6, 16, 11500, 16782, "Beru with tears: 'I have crossed dimensions to meet you, Young Monarch'")

    # Strip 7 (1112 x 17553): Tiny Chibi Beru & Beru furious at System
    crop_save(7, 17, 0, 5500, "Suho pokes tiny Beru: 'From what I recall, weren't you bigger?'")
    crop_save(7, 18, 5500, 10500, "System Window: Beru Lv. 1 Private Grade! Beru: 'KIEKKK! System Bastard!'")
    crop_save(7, 19, 10500, 17553, "Beru boasts as skilled healer; reveals mission: 'I came to unseal you'")

    # Strip 8 (1112 x 20062): Sung Jin-Woo, Sealed Powers & Outer Space War
    crop_save(8, 20, 0, 6500, "Beru reveals: Great Shadow Monarch Sung Jin-Woo sealed Suho's powers for normal life")
    crop_save(8, 21, 6500, 13000, "Suho: 'My dad?! He didn't abandon us, he went to outer space?!'")
    crop_save(8, 22, 13000, 20062, "Beru: Shadow Monarch is fighting invaders in deep outer space to protect Earth")

    # Strip 9 (1112 x 18803): The Itarim (Outer Gods) & Cha Hae-In Missing!
    crop_save(9, 23, 0, 6000, "Beru explains: 'Itarim' — the Gods of outer space are invading through Gates")
    crop_save(9, 24, 6000, 12500, "Beru tore apart countless enemies crossing dimensions")
    crop_save(9, 25, 12500, 18803, "Suho: 'Did mother go with him? She disappeared on the same day...'")

    # Strip 10 (1112 x 18688): Beru Shocked! Cha Hae-In Missing & Suho's Resolve
    crop_save(10, 26, 0, 6000, "Beru in sheer shock: 'KIEKKK?! MISS HAEIN IS MISSING?!'")
    crop_save(10, 27, 6000, 12000, "Suho: 'I have been alone for so many years... I will meet them again!'")
    crop_save(10, 28, 12000, 18688, "Beru: 'The Lord cannot return now... but the Young Monarch can rescue her!'")

    # Strip 11 (1112 x 19421): Let's Level Up & The Shadow Dungeon Key
    crop_save(11, 29, 0, 6500, "Beru points claw: 'LET'S LEVEL UP.' Alert: A QUEST HAS ARRIVED!")
    crop_save(11, 30, 6500, 13000, "ITEM: SHADOW DUNGEON KEY! 'Stick that key into your shadow!'")

    # Strip 12-15 (1112 x ~18000 each): Plunging Key & Entering Shadow Dungeon
    crop_save(12, 31, 0, 9500, "Suho pushes the key into his shadow: Portal of swirling darkness tears open!")
    crop_save(14, 32, 10000, 16828, "Beru vows to protect Suho: Entering THE SHADOW DUNGEON — Land of the Dead!")

    print(f"\n✅ All 32 cinematic action panels sliced successfully into: {PANELS_DIR}")

if __name__ == "__main__":
    extract_pdf_pages()
    slice_panels()
