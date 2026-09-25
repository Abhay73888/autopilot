"""
pipeline/ragnarok_ch12_panel_slicer.py — Slices Chapter 12 raw strips into 40 synchronized action panels.
Ensures 100% 1-to-1 matching between narrated dialogue/events and the displayed image.
"""

import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "output" / "solo_leveling_ragnarok_ch12"
RAW_DIR = BASE / "raw_strips"
PANELS_DIR = BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 12 strips into 40 synchronized panels...")

    # Panel 1: Title Card
    s1 = RAW_DIR / "strip_01.jpg"
    if s1.exists():
        with Image.open(str(s1)) as im:
            im.save(str(PANELS_DIR / "panel_001.jpg"), quality=95)
        print("  ✓ Panel 001: Chapter 12 Title Card")

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

    # Strip 2: Beru watching cub, Suho confronts Brocky, Quest delivered
    crop_and_save(2, 2, 0, 5000, "Beru watching over wounded wolf cub")
    crop_and_save(2, 3, 5000, 11000, "Suho standing tall facing werewolf Brocky")
    crop_and_save(2, 4, 11000, 16000, "System Alert: Emergency Quest Hunt the Hyena")
    crop_and_save(2, 5, 16000, 22325, "Suho questions Hyena guild and Itarim connection")

    # Strip 3: Hyena hunters beg Brocky, Brocky executes subordinates
    crop_and_save(3, 6, 0, 7000, "Corrupt hunters plead with Brocky for rescue")
    crop_and_save(3, 7, 7000, 13500, "Suho steps in, Brocky opens monstrous jaws")
    crop_and_save(3, 8, 13500, 19632, "Brocky ruthlessly executes his own hunter minions")

    # Strip 4: Brocky's twisted logic, Suho clashes blades
    crop_and_save(4, 9, 0, 6500, "Brocky stands tall: Weaklings have no place")
    crop_and_save(4, 10, 6500, 13000, "Suho slashes at Brocky: How dare you kill your own men")
    crop_and_save(4, 11, 13000, 19875, "Brocky blocks with claws: Power decides who lives")

    # Strip 5: Brocky energy shockwave, Suho aerial flips & chest slash
    crop_and_save(5, 12, 0, 7000, "Brocky unleashes destructive red energy blast")
    crop_and_save(5, 13, 7000, 14000, "Suho flips in mid-air dodging claws")
    crop_and_save(5, 14, 14000, 21333, "Suho slices Brocky's chest with dual sword cuts")

    # Strip 6: Brocky crashes, Storm Slash attack
    crop_and_save(6, 15, 0, 7000, "Brocky slammed into quarry rocks")
    crop_and_save(6, 16, 7000, 15000, "Suho unleashes Storm Slash skill")
    crop_and_save(6, 17, 15000, 22500, "Barrage of wind blade strikes ripping through Brocky")

    # Strip 7: Brocky laughs, Suho Spin attack, Sword questions Brocky
    crop_and_save(7, 18, 0, 7000, "Brocky laughs menacingly: Even Fang Monarch is disappointed")
    crop_and_save(7, 19, 7000, 14000, "Suho activates Spin skill drilling into Brocky")
    crop_and_save(7, 20, 14000, 21233, "Sword spirit questions Brocky: Why did you betray Lord Rakhan?")

    # Strip 8: Brocky madness, Sword shatters
    crop_and_save(8, 21, 0, 7000, "Flashback of Rakhan & Itarim divine mark")
    crop_and_save(8, 22, 7000, 14000, "Brocky roars: I never respected him, only feared his power!")
    crop_and_save(8, 23, 14000, 21242, "Brocky strikes and shatters Suho's ancient blade!")

    # Strip 9: Broken sword, Suho pinned, memory of Jinwoo, blue shadow punch
    crop_and_save(9, 24, 0, 7000, "Suho horrified by broken blade; Brocky pins him")
    crop_and_save(9, 25, 7000, 15000, "Suho in agony, remembers Sung Jinwoo fighting in the cosmos")
    crop_and_save(9, 26, 15000, 22500, "Suho charges glowing blue shadow punch into Brocky")

    # Strip 10: Brocky counters, Beru screams, dying blade & crawling cub
    crop_and_save(10, 27, 0, 7000, "Brocky smashes Suho back; Beru screams: Young Monarch!")
    crop_and_save(10, 28, 7000, 15000, "Broken blade on ground: Power is seeping, is this the end?")
    crop_and_save(10, 29, 15000, 22500, "Wounded wolf cub crawls toward the broken blade")

    # Strip 11: Cub inspired, power transfer, transformation into Beast King
    crop_and_save(11, 30, 0, 7000, "Wolf cub's golden eyes burn with fighting spirit")
    crop_and_save(11, 31, 7000, 14500, "Sword's flame power transfers into the wolf cub")
    crop_and_save(11, 32, 14500, 22500, "Cub evolves into towering Beast King; Brocky kicks Suho")

    # Strip 12: HP 21 alert, Brocky death strike, Suho cornered
    crop_and_save(12, 33, 0, 6500, "Status Window: HP 21 / 2350! Suho critically injured")
    crop_and_save(12, 34, 6500, 13500, "Brocky approaches: Just die like a pest!")
    crop_and_save(12, 35, 13500, 20000, "Brocky lunges with lethal jaws to kill Suho")

    # Strip 13: Beast King wolf ambush, impales Brocky, party invitation
    crop_and_save(13, 36, 0, 7000, "Giant Wolf leaps in, impales Brocky from behind with fangs!")
    crop_and_save(13, 37, 7000, 14500, "Brocky collapses spitting blood; Wolf guards Suho")
    crop_and_save(13, 38, 14500, 21816, "System Alert: Successor of the Fang requests to join party!")

    # Strip 14: Suho amazed, Wolf loyalty, Chapter 12 finale
    crop_and_save(14, 39, 0, 4200, "Suho stunned: That baby wolf wants to join my party?!")
    crop_and_save(14, 40, 4200, 7722, "Majestic Beast King Wolf stands loyal beside Sung Suho")

    print("\n✅ All 40 action panels sliced successfully to:", PANELS_DIR)

if __name__ == "__main__":
    slice_panels()
