"""
pipeline/ragnarok_ch6_panel_slicer.py — Panel Slicer for Solo Leveling: Ragnarok Chapter 6.
"""

import sys
from pathlib import Path
from PIL import Image

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
OUT_BASE = ROOT / "output" / "solo_leveling_ragnarok_ch6"
RAW_DIR = OUT_BASE / "raw_strips"
PANELS_DIR = OUT_BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 6 strips into 36 cinematic wide panels...")

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

    # Strip 2 (1667 x 46707)
    crop_and_save(2, 2, 0, 12000, "Arise: shadows rising from goblin corpse")
    crop_and_save(2, 3, 12000, 22000, "Shadow Goblin Lv 1 Common Rank emerges")
    crop_and_save(2, 4, 22000, 33000, "Suho unimpressed, Beru sweats explaining shadow soldiers")
    crop_and_save(2, 5, 33000, 46707, "Disappears after 1 day, no storage, Suho hungry")

    # Strip 3 (1667 x 44425)
    crop_and_save(3, 6, 0, 12000, "Exiting Shadow Dungeon with key")
    crop_and_save(3, 7, 12000, 23000, "Suho devouring hospital food happily")
    crop_and_save(3, 8, 23000, 34000, "Mission 1: Hunt outer space monsters & level up like Jinwoo")
    crop_and_save(3, 9, 34000, 44425, "Mission 2: Find missing mother Cha Hae-In in dungeons")

    # Strip 4 (1667 x 46707)
    crop_and_save(4, 10, 0, 11000, "Mission 3: Recover Beru's Marshal power by eating magic")
    crop_and_save(4, 11, 11000, 23000, "Suho getting ready, needs hunter license")
    crop_and_save(4, 12, 23000, 34000, "Heading to Hunter Association, dreaming of S-rank")
    crop_and_save(4, 13, 34000, 46707, "Evaluation result: Mana 46, E-Rank Awakener!")

    # Strip 5 (1667 x 44978)
    crop_and_save(5, 14, 0, 12000, "Suho depressed outside association, Beru comforting")
    crop_and_save(5, 15, 12000, 24000, "E-ranks rarely hired in raids, can Suho protect Earth?")
    crop_and_save(5, 16, 24000, 34000, "Realization: Division of labor in dungeon raids")
    crop_and_save(5, 17, 34000, 44978, "Mining and Hauling teams accept E-ranks!")

    # Strip 6 (1667 x 42707)
    crop_and_save(6, 18, 0, 12000, "In crystal dungeon with pickaxe and hardhat")
    crop_and_save(6, 19, 12000, 23000, "Meeting Lim Dogyun, university teaching assistant")
    crop_and_save(6, 20, 23000, 33000, "Lim Dogyun apologizes for running away during attack")
    crop_and_save(6, 21, 33000, 42707, "Suho tells him to raise head: Association advises E-ranks to run")

    # Strip 7 (1667 x 46707)
    crop_and_save(7, 22, 0, 13000, "Lim Dogyun shocked: Suho's mana is lower than his?!")
    crop_and_save(7, 23, 13000, 25000, "Dogyun recalls seeing Suho fight on rooftop")
    crop_and_save(7, 24, 25000, 36000, "Chibi Beru pops out of collar: 'Young Monarch is extraordinary!'")
    crop_and_save(7, 25, 36000, 46707, "Lim Dogyun terrified, Suho explains summoner skill")

    # Strip 8 (1667 x 45300)
    crop_and_save(8, 26, 0, 12000, "Dogyun boasts running skill, Suho jokes, Beru smirks")
    crop_and_save(8, 27, 12000, 24000, "Suho looks deeper into the dungeon")
    crop_and_save(8, 28, 24000, 34000, "Strike squad ahead hunting wolf monsters, low loot")
    crop_and_save(8, 29, 34000, 45300, "Hunter finds hidden side path glowing red-purple")

    # Strip 9 (1667 x 46353)
    crop_and_save(9, 30, 0, 12000, "Ancient underground temple ruins discovered")
    crop_and_save(9, 31, 12000, 24000, "Giant demonic broadsword embedded in altar")
    crop_and_save(9, 32, 24000, 34000, "Strike squad rejoicing, thinking it's jackpot")
    crop_and_save(9, 33, 34000, 46353, "Kim Yongjun grabs hilt, ignores warnings, red aura erupts!")

    # Strip 10 (1667 x 45936)
    crop_and_save(10, 34, 0, 18000, "Giant shadowy beast jaws and amber eyes awaken under floor")
    crop_and_save(10, 35, 18000, 45936, "Kim Yongjun possessed: 'How dare you?', dark red slash erupts!")

    # Strip 11 (1667 x 10540)
    crop_and_save(11, 36, 0, 10540, "Colossal Lycan Beast Monarch: 'WHO DARES TO COVET THE SWORD OF THE MONARCH OF FANGS?'")

    print(f"\n✅ All 36 cinematic action panels sliced successfully into: {PANELS_DIR}")

if __name__ == "__main__":
    slice_panels()
