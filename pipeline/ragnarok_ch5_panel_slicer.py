"""
pipeline/ragnarok_ch5_panel_slicer.py — Panel Extractor and Slicer for Solo Leveling: Ragnarok Chapter 5.

Renders high-resolution pages and slices them into 35 focused cinematic action panels.
"""

import sys
from pathlib import Path
from PIL import Image

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
OUT_BASE = ROOT / "output" / "solo_leveling_ragnarok_ch5"
RAW_DIR = OUT_BASE / "raw_strips"
PANELS_DIR = OUT_BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 5 strips into 35 cinematic wide panels...")

    # Panel 1: Title Card
    s1_path = RAW_DIR / "strip_01.jpg"
    if s1_path.exists():
        with Image.open(str(s1_path)) as im:
            im.save(str(PANELS_DIR / "panel_001.jpg"), quality=95)
        print("  ✓ Panel 001: Chapter Title Card")

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

    # Strip 2 (1667 x 43098)
    crop_and_save(2, 2, 0, 11000, "Suho enters Shadow Dungeon with Beru")
    crop_and_save(2, 3, 11000, 24000, "Ruined city landscape of the Shadow Dungeon")
    crop_and_save(2, 4, 24000, 33000, "Suho in slippers walking through ruins, feeling familiar")
    crop_and_save(2, 5, 33000, 43098, "Quest Notice: Survive 4 Hours")

    # Strip 3 (1667 x 41953)
    crop_and_save(3, 6, 0, 11000, "Beru warns: Time of suffering will soon arrive")
    crop_and_save(3, 7, 11000, 22000, "Goblin Scout sudden axe attack, Suho dodges")
    crop_and_save(3, 8, 22000, 32000, "Goblin Scout revealed with weapon")
    crop_and_save(3, 9, 32000, 41953, "Suho sees colorless name, dashes forward")

    # Strip 4 (1667 x 44900)
    crop_and_save(4, 10, 0, 10000, "Suho wrestles stone axe from goblin scout")
    crop_and_save(4, 11, 10000, 20000, "Slaying goblin scout, Item: Goblin Stone Axe obtained")
    crop_and_save(4, 12, 20000, 30000, "2nd scout blows war horn from atop ruins")
    crop_and_save(4, 13, 30000, 44900, "Goblin Centurion and army emerge roaring")

    # Strip 5 (1667 x 42213)
    crop_and_save(5, 14, 0, 13000, "Suho asks Beru for help; Beru's mana excuses")
    crop_and_save(5, 15, 13000, 25000, "Horde leaps down; Suho prepares Ruler's Authority")
    crop_and_save(5, 16, 25000, 42213, "Telekinetic axe throw splits goblin; Ruler's Authority")

    # Strip 6 (1667 x 44005)
    crop_and_save(6, 17, 0, 13000, "Goblin archers attack; Suho catches and returns arrow")
    crop_and_save(6, 18, 13000, 24000, "Flashback: Baby Suho levitating toys & Beru")
    crop_and_save(6, 19, 24000, 33000, "Apostles of Itarim invasion & Suho's power purpose")
    crop_and_save(6, 20, 33000, 44005, "Level up & 10kg weight limit realization")

    # Strip 7 (1667 x 44900)
    crop_and_save(7, 21, 0, 13000, "Goblin swarm surrounds Suho")
    crop_and_save(7, 22, 13000, 26000, "Goblin Centurion steps forward, HP drops to 160")
    crop_and_save(7, 23, 26000, 44900, "Suho leaps into explosive aerial attack")

    # Strip 8 (1667 x 44182)
    crop_and_save(8, 24, 0, 12000, "Suho smiles feeling alive in battle")
    crop_and_save(8, 25, 12000, 28000, "Fierce slashing combat, HP drops 118 to 53")
    crop_and_save(8, 26, 28000, 44182, "Learned Resilience Lv. 1 & 4x Level Up")

    # Strip 9 (1667 x 42171)
    crop_and_save(9, 27, 0, 10000, "Ruins covered in goblin corpses after 4 hours")
    crop_and_save(9, 28, 10000, 22000, "Exhausted Suho panting; Beru crying praises")
    crop_and_save(9, 29, 22000, 32000, "Reward: Rune Stone Shadow Extraction")
    crop_and_save(9, 30, 32000, 42171, "Resilience stats & 'Shadow Silver Spoon' joke")

    # Strip 10 (1667 x 39619)
    crop_and_save(10, 31, 0, 15000, "Suho crushes Rune Stone, learns Shadow Extraction")
    crop_and_save(10, 32, 15000, 28000, "Approaches Goblin Centurion corpse; necromancy thoughts")
    crop_and_save(10, 33, 28000, 39619, "System asks for command word; Beru eagerly waits")

    # Strip 11 (1667 x 17053)
    crop_and_save(11, 34, 0, 7000, "Beru trembling with anticipation; Suho: 'It should be direct'")
    crop_and_save(11, 35, 7000, 17053, "Hand raised, blue-black shadows burst: 'Arise.'")

    print(f"\n✅ All 35 cinematic action panels sliced successfully into: {PANELS_DIR}")

if __name__ == "__main__":
    slice_panels()
