"""
pipeline/ragnarok_ch8_panel_slicer.py — Slices Chapter 8 raw strips into 20 cinematic panels.
"""

import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "output" / "solo_leveling_ragnarok_ch8"
RAW_DIR = BASE / "raw_strips"
PANELS_DIR = BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 8 strips into 20 cinematic panels...")

    # Panel 1: Title Card
    s1 = RAW_DIR / "strip_01.jpg"
    if s1.exists():
        with Image.open(str(s1)) as im:
            im.save(str(PANELS_DIR / "panel_001.jpg"), quality=95)
        print("  ✓ Panel 001: Chapter 8 Title Card")

    def crop_and_save(strip_num: int, panel_id: int, y1: int, y2: int, desc: str = ""):
        img_path = RAW_DIR / f"strip_{strip_num:02d}.jpg"
        if not img_path.exists():
            print(f"  ❌ Missing strip {strip_num}")
            return
        with Image.open(str(img_path)) as im:
            w, h = im.size
            top = max(0, min(y1, h - 1))
            bottom = max(top + 50, min(y2, h))
            cropped = im.crop((0, top, w, bottom))
            out_path = PANELS_DIR / f"panel_{panel_id:03d}.jpg"
            cropped.save(str(out_path), quality=95)
            print(f"  ✓ Panel {panel_id:03d}: Strip {strip_num:02d} [{top}:{bottom}] -> {w}x{bottom - top} ({desc})")

    # Strip 2: Suho facing Red Name & Beru observing Monarch spirit
    crop_and_save(2, 2, 0, 15000, "Suho facing red name, ready to fight and grow faster")
    crop_and_save(2, 3, 15000, 30510, "Beru watching: 'Young Monarch never runs away'")

    # Strip 3: Sword host analysis & Shadow Lycan attack
    crop_and_save(3, 4, 0, 15000, "Suho spots sword is the real monster, sends Shadow Lycan")
    crop_and_save(3, 5, 15000, 30698, "Enemy slices Shadow Lycan in half with terrifying speed")

    # Strip 4: Possessed hunter speaks & insults Shadow Monarch
    crop_and_save(4, 6, 0, 14000, "Possessed hunter mocks Suho, Beru furious at insult to Jinwoo")
    crop_and_save(4, 7, 14000, 29228, "Enemy unleashes crimson fang aura, exploratory clash begins")

    # Strip 5: Suho's Ruler's Authority telekinesis weapon storm
    crop_and_save(5, 8, 0, 16000, "Suho uses Ruler's Authority to levitate all weapons")
    crop_and_save(5, 9, 16000, 31455, "Weapons rain down, enemy unleashes brutal counter-deflection")

    # Strip 6: High-stakes evasion & Beru tower discussion
    crop_and_save(6, 10, 0, 15000, "Suho dodges lethal red slashes, knows one hit means death")
    crop_and_save(6, 11, 15000, 31253, "Enemy insults Jinwoo as coward, Suho questions sealed tower power")

    # Strip 7: Jinwoo's infant seal & astral form revelation
    crop_and_save(7, 12, 0, 16000, "Beru reveals Jinwoo sealed Suho's talent as infant")
    crop_and_save(7, 13, 16000, 31448, "Suho remembers fist combat in tower and cries ARISE")

    # Strip 8: The Shadow Lycan Gauntlet! Lv.2 Form Change
    crop_and_save(8, 14, 0, 16000, "Shadow Lycan wraps around Suho's right arm into beast gauntlet")
    crop_and_save(8, 15, 16000, 31455, "System Notice: Shadow Extraction Lv.2 Form Change! Suho strikes!")

    # Strip 9: Shockwave clash & Beru's tears of awe
    crop_and_save(9, 16, 0, 16000, "Beast Gauntlet punches enemy's blade, explosive shockwave")
    crop_and_save(9, 17, 16000, 31455, "Beru stunned: 'Mastering Shadow Authority alone... OH MY KING!'")

    # Strip 10: Savage beatdown & crushing the possessed hunter
    crop_and_save(10, 18, 0, 15000, "Suho leaps and hammers enemy through cavern walls")
    crop_and_save(10, 19, 15000, 29175, "Suho relentless dual offensive from above")

    # Strip 11: True Prodigy
    crop_and_save(11, 20, 0, 6416, "Suho glowing blue eyes; Beru: 'The Young Monarch is truly a prodigy!'")

    print(f"\n✅ Sliced 20 cinematic panels saved to {PANELS_DIR}")

if __name__ == "__main__":
    slice_panels()
