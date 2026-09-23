"""
pipeline/ragnarok_ch7_panel_slicer.py — Slices Chapter 7 raw strips into high-action cinematic panels.
"""

import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "output" / "solo_leveling_ragnarok_ch7"
RAW_DIR = BASE / "raw_strips"
PANELS_DIR = BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 7 strips into 20 cinematic panels...")

    # Panel 1: Title Card
    s1 = RAW_DIR / "strip_01.jpg"
    if s1.exists():
        with Image.open(str(s1)) as im:
            im.save(str(PANELS_DIR / "panel_001.jpg"), quality=95)
        print("  ✓ Panel 001: Chapter 7 Title Card")

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

    # Strip 2: Suho's Goblins mining blue mana crystals, miners shocked
    crop_and_save(2, 2, 0, 11000, "Goblins mining crystals, miners stunned by summoning skill")
    crop_and_save(2, 3, 11000, 22041, "Suho enjoying convenient goblin labor")

    # Strip 3 & 4: Beru eating mana crumbs & sensing Beast Monarch
    crop_and_save(3, 4, 12000, 22500, "Beru scavenging mana crumbs off the ground")
    crop_and_save(4, 5, 0, 11000, "Beru chills: 'I felt the presence of a Monarch!'")
    crop_and_save(4, 6, 11000, 21350, "Screams from attack squad tunnel, beasts incoming")

    # Strip 5 & 6: Steel Fanged Lycans attack & Suho intercepts
    crop_and_save(5, 7, 0, 12000, "Red-eyed Steel Fanged Lycans lunge at miners")
    crop_and_save(6, 8, 0, 10000, "Suho intercepts beast: 'I'll buy time, run outside!'")
    crop_and_save(6, 9, 10000, 17091, "Suho spots ORANGE name: Steel Fanged Lycan")

    # Strip 7 & 8: Suho inventory weapons & First Arise!
    crop_and_save(7, 10, 0, 12000, "Suho commands goblins to guard Dogyun, draws daggers")
    crop_and_save(7, 11, 12000, 21033, "Suho charges at blinding speed")
    crop_and_save(8, 12, 0, 12000, "Suho slashes Lycan in half, notification: Defeated!")
    crop_and_save(8, 13, 12000, 22067, "Suho commands: ARISE! Shadow Wolf extracts!")

    # Strip 9 & 10: Army expansion, Level Up & Urgent Quest!
    crop_and_save(9, 14, 0, 13000, "Second wolf extracted, Beru amazed by combat growth")
    crop_and_save(10, 15, 0, 11000, "Level Up! Suho stands with Shadow Wolf pack")
    crop_and_save(10, 16, 11000, 21875, "URGENT QUEST: Defeat the enemy that wishes to kill you!")

    # Strip 11 & 12: Possessed Hunter arrives & devastating slash
    crop_and_save(11, 17, 0, 17000, "Armored hunter emerges with demonic glowing eyes")
    crop_and_save(12, 18, 0, 17042, "Lethal decapitation strike dodged! Suho saves Dogyun")

    # Strip 13 & 14 & 15: Deep RED Name & Monarch of Fangs aura
    crop_and_save(13, 19, 0, 12000, "RED NAME: FANG OF RAKHAN (POSSESSED)!")
    crop_and_save(13, 20, 12000, 22133, "Beru warns: 'He carries the aura of a Monarch!'")
    crop_and_save(14, 21, 0, 18833, "Shadow wolves clash against red beast aura")
    crop_and_save(15, 22, 0, 18791, "Suho locks dual daggers stance: 'I will defeat this Red Name and get strong!'")

    print(f"\n✅ All 22 action panels sliced into: {PANELS_DIR}")

if __name__ == "__main__":
    slice_panels()
