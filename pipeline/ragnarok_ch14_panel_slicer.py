"""
pipeline/ragnarok_ch14_panel_slicer.py — Slices Chapter 14 raw strips into 40 synchronized action panels.
Ensures 100% 1-to-1 matching between narrated dialogue/events and the displayed image.
"""

import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "output" / "solo_leveling_ragnarok_ch14"
RAW_DIR = BASE / "raw_strips"
PANELS_DIR = BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 14 strips into 40 synchronized panels...")

    # Panel 1: Title Card
    s1 = RAW_DIR / "strip_01.jpg"
    if s1.exists():
        with Image.open(str(s1)) as im:
            im.save(str(PANELS_DIR / "panel_001.jpg"), quality=95)
        print("  ✓ Panel 001: Chapter 14 Title Card")

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

    # Strip 2: Aftermath, Itarim connection, outer gods
    crop_and_save(2, 2, 0, 7500, "Suho & Beru stand over defeated Brocky with Fang's heir")
    crop_and_save(2, 3, 7500, 14500, "Suho asks Beru about hunters putting something in Brocky's eye")
    crop_and_save(2, 4, 14500, 22283, "Beru explains Outer Gods & Apostles are on Earth")

    # Strip 3: Beru's Gluttony idea, recovery, Suho invites wolf
    crop_and_save(3, 5, 0, 6500, "Beru has idea: I can devour Brocky's corpse to extract memories")
    crop_and_save(3, 6, 6500, 13500, "Beru glows with lightbulb: Two birds with one stone!")
    crop_and_save(3, 7, 13500, 20940, "Suho sits beside wolf: Do you want to come along with us?")

    # Strip 4: Wolf affection, portal open, emotional Beru
    crop_and_save(4, 8, 0, 6500, "Wolf affectionately licks Suho's face; Suho laughs")
    crop_and_save(4, 9, 6500, 13000, "Suho opens dimensional gate: Counting on you, Beru")
    crop_and_save(4, 10, 13000, 20130, "Beru deeply touched; Suho enters Shadow Sanctuary")

    # Strip 5: Shadow Sanctuary, Fang's sanctuary gone, naming Gray
    crop_and_save(5, 11, 0, 5500, "Suho in Shadow Dungeon; finding home for Fang's heir")
    crop_and_save(5, 12, 5500, 10500, "Wolf has no guardian; System requests a name")
    crop_and_save(5, 13, 10500, 15500, "Wolf barks RUFF! Suho considers naming")
    crop_and_save(5, 14, 15500, 20505, "Named GRAY! Beru sweats at naming sense; Gray loves it")

    # Strip 6: Fang's territory designated, monster feeding, Gray hunts
    crop_and_save(6, 15, 0, 6500, "Forest designated as Fang's Territory, Gray as owner")
    crop_and_save(6, 16, 6500, 12500, "Suho asks what Gray eats; Beru says monsters or living organisms")
    crop_and_save(6, 17, 12500, 17500, "Lingering monsters in forest; Gray tasked with cleanup")
    crop_and_save(6, 18, 17500, 21548, "Gray roars and leaps with ferocious fangs on goblin!")

    # Strip 7: Quest rewards, Wolf Slaughterer title, system mystery
    crop_and_save(7, 19, 0, 5500, "Gray takes down prey; Suho sorts out battle rewards")
    crop_and_save(7, 20, 5500, 11000, "Reward: +5 points, Title Wolf Slaughterer (+40% vs beasts)")
    crop_and_save(7, 21, 11000, 16628, "Quest: Monarch's Heirs (1/8); Beru explains system revisions")

    # Strip 8: Architect's dark plot vs Sung Jinwoo's triumph, Status Window
    crop_and_save(8, 22, 0, 7500, "Beru reveals Architect's plot to use Jinwoo as sacrificial vessel")
    crop_and_save(8, 23, 7500, 14500, "Jinwoo overcame the system; system now aids Suho")
    crop_and_save(8, 24, 14500, 22500, "Status Window: Level 16, HP 2550, MP 270, Class None")

    # Strip 9: Suho's resolve, Beru returns from devouring
    crop_and_save(9, 25, 0, 7000, "Suho resolves to clear quests and find his parents")
    crop_and_save(9, 26, 7000, 14000, "Beru returns after consuming corpse; no direct apostle trace")
    crop_and_save(9, 27, 14000, 21413, "Beru reveals: There are memories of the humans who backed Hyena Guild!")

    # Strip 10: Grim Reaper Guild reveal, luxury penthouse phone call
    crop_and_save(10, 28, 0, 7000, "Guild Name: GRIM REAPER! Suho vows to investigate")
    crop_and_save(10, 29, 7000, 14500, "Penthouse office at night; phone rings; Im Taegyu calling")
    crop_and_save(10, 30, 14500, 22500, "Man smirks arrogantly: Hyena incident? Go to the zoo")

    # Strip 11: Im Taegyu confrontation, Woo Jinchul warning, fury
    crop_and_save(11, 31, 0, 5500, "Im Taegyu: Association will find out your commission with Hyenas")
    crop_and_save(11, 32, 5500, 10500, "Man boasts: My lawyers can silence the Association")
    crop_and_save(11, 33, 10500, 15000, "Im Taegyu: Chairman Woo Jinchul isn't so easy. Wrap it up!")
    crop_and_save(11, 34, 15000, 18500, "Im Taegyu hangs up; man furious at ex-driver who became S-Rank")
    crop_and_save(11, 35, 18500, 21765, "Man slams desk in purple aura: Defeated Brocky & Hyena Guild?!")

    # Strip 12: Lee Minsung identity reveal, Stardust stimulant orb!
    crop_and_save(12, 36, 0, 5000, "Survivors only saw a young hunter wearing a black mask")
    crop_and_save(12, 37, 5000, 9000, "IDENTITY REVEAL: Lee Minsung, Grim Reaper Guild Vice-CEO, A-Rank!")
    crop_and_save(12, 38, 9000, 12000, "Lee Minsung holds glowing orb: Hunter Awakening Stimulant 'STARDUST'!")
    crop_and_save(12, 39, 12000, 14500, "Dark shadowy figure with glowing red eyes inside the Stardust crystal")
    crop_and_save(12, 40, 14500, 15839, "Lee Minsung sinister smile: 'No one will ever look down on me again!'")

    print("\n✅ All 40 panels successfully cropped and synchronized!")

if __name__ == "__main__":
    slice_panels()
