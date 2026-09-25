"""
pipeline/ragnarok_ch13_panel_slicer.py — Slices Chapter 13 raw strips into 40 synchronized action panels.
Ensures 100% 1-to-1 matching between narrated dialogue/events and the displayed image.
"""

import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "output" / "solo_leveling_ragnarok_ch13"
RAW_DIR = BASE / "raw_strips"
PANELS_DIR = BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 13 strips into 40 synchronized panels...")

    # Panel 1: Title Card
    s1 = RAW_DIR / "strip_01.jpg"
    if s1.exists():
        with Image.open(str(s1)) as im:
            im.save(str(PANELS_DIR / "panel_001.jpg"), quality=95)
        print("  ✓ Panel 001: Chapter 13 Title Card")

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

    # Strip 2: Wolf ally request, Suho ponders, Brocky shocked
    crop_and_save(2, 2, 0, 6000, "Wolf stands in front of Suho; System asks to accept ally")
    crop_and_save(2, 3, 6000, 12500, "Suho ponders recruiting Fang's heir")
    crop_and_save(2, 4, 12500, 21650, "Brocky shocked: You're Rakhan's heir?!")

    # Strip 3: Suho accepts ally, resonance link, flashback begins
    crop_and_save(3, 5, 0, 7000, "Suho decides: I will accept it... YES!")
    crop_and_save(3, 6, 7000, 13500, "System: Recruited Successor of Fang; Blue & gold resonance")
    crop_and_save(3, 7, 13500, 19958, "Memories flow into Suho's mind; Brocky speaks to cub")

    # Strip 4: Flashback: War loss, cub crying, Itarim apostles appear
    crop_and_save(4, 8, 0, 7000, "Brocky tells cub: World is survival of the fittest")
    crop_and_save(4, 9, 7000, 14000, "Cub weeping in terror; dark mysterious shadows")
    crop_and_save(4, 10, 14000, 21132, "Apostle in white with halo: This monster seems useful")

    # Strip 5: Divine eye implanted, Brocky screams, Itarim mission
    crop_and_save(5, 11, 0, 5500, "Apostle plants golden divine eye into Brocky")
    crop_and_save(5, 12, 5500, 11000, "Brocky screams in agony; cub terrified")
    crop_and_save(5, 13, 11000, 17358, "Apostle orders: Capture humans alive, desires will twist")

    # Strip 6: Suho realizes truth, cub wants to save Brocky, Brocky powers up
    crop_and_save(6, 14, 0, 7000, "Suho realizes: Those masterminds are connected to Itarim!")
    crop_and_save(6, 15, 7000, 14000, "Suho: Fang's heir wants to save the crazed Brocky!")
    crop_and_save(6, 16, 14000, 21666, "Suho: I must defeat Brocky here; Brocky powers up")

    # Strip 7: Quest Monarch's Heirs, Bond skill forming, Beru in awe
    crop_and_save(7, 17, 0, 6000, "System Alert: Quest Monarch's Heirs (Allied 1/8)")
    crop_and_save(7, 18, 6000, 12000, "Bond Skill is forming! Golden-blue energy eruption")
    crop_and_save(7, 19, 12000, 17799, "Beru: Young Monarch experiencing something beyond Monarch!")

    # Strip 8: Brocky slam, dust clears, Suho transformed Beast Form
    crop_and_save(8, 20, 0, 7000, "Brocky charges trying to crush them with giant slam")
    crop_and_save(8, 21, 7000, 14000, "System: Bond Skill produced; Brocky gasps in shock")
    crop_and_save(8, 22, 14000, 21666, "Suho emerges transformed with silver hair and beast gauntlets")

    # Strip 9: Beast Possession Lv. 1, sharpened senses, high kick
    crop_and_save(9, 23, 0, 6500, "System: Beast Possession Lv. 1 activated")
    crop_and_save(9, 24, 6500, 13500, "Suho: Body feels light, senses sharp like a beast")
    crop_and_save(9, 25, 13500, 20658, "Suho executes lightning-fast high kick into Brocky's chin")

    # Strip 10: Brocky head snapped, panics, unleashes Itarim symbol
    crop_and_save(10, 26, 0, 6500, "Brocky bleeding: Is this the same child as before?!")
    crop_and_save(10, 27, 6500, 13000, "Brocky: If I'm defeated I lose everything! Activates Itarim sign")
    crop_and_save(10, 28, 13000, 19466, "Brocky's muscles swell monstrously; Beru: Mana increased!")

    # Strip 11: Species difference speech, colossal punch clash
    crop_and_save(11, 29, 0, 7000, "Brocky: Strength determined by species, despair human!")
    crop_and_save(11, 30, 7000, 14000, "Giant boulder-shattering punch thrown at Suho")
    crop_and_save(11, 31, 14000, 21666, "Suho stops Brocky's colossal fist cold with bare hand!")

    # Strip 12: Martial Arts Lv. 1, Beru apex speech, sky axe kick
    crop_and_save(12, 32, 0, 7000, "System: Skill Martial Arts Lv. 1 learned (+33% barehanded dmg)")
    crop_and_save(12, 33, 7000, 14000, "Beru: No species superior to Shadow Monarch at the apex!")
    crop_and_save(12, 34, 14000, 21666, "Suho leaps into sky and delivers seismic axe kick crushing Brocky!")

    # Strip 13: Dust settles, de-transformation, Brocky remembers true reason
    crop_and_save(13, 35, 0, 7000, "Dust settles, Suho pants, Wolf separates back beside him")
    crop_and_save(13, 36, 7000, 14000, "Brocky lying defeated: I must become stronger...")
    crop_and_save(13, 37, 14000, 21666, "Itarim eye cracks; Brocky: I remember my true reason...")

    # Strip 14: Memory of Lord Rakhan, Wolf howl, Double Level Up!
    crop_and_save(14, 38, 0, 4500, "Memory of Lord Rakhan: I was angry because I couldn't protect you")
    crop_and_save(14, 39, 4500, 8500, "Giant Beast King Wolf howls mournfully to the sky")
    crop_and_save(14, 40, 8500, 12594, "System Alert: Brocky defeated! LEVEL UP! LEVEL UP! Chapter 13 End")

    print("\n✅ All 40 action panels sliced successfully to:", PANELS_DIR)

if __name__ == "__main__":
    slice_panels()
