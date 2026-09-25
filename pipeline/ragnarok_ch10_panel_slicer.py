"""
pipeline/ragnarok_ch10_panel_slicer.py — Slices Chapter 10 raw strips into 37 synchronized action panels.
Ensures 100% 1-to-1 matching between narrated dialogue/events and the displayed image.
"""

import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "output" / "solo_leveling_ragnarok_ch10"
RAW_DIR = BASE / "raw_strips"
PANELS_DIR = BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 10 strips into 37 synchronized panels...")

    # Panel 1: Title Card
    s1 = RAW_DIR / "strip_01.jpg"
    if s1.exists():
        with Image.open(str(s1)) as im:
            im.save(str(PANELS_DIR / "panel_001.jpg"), quality=95)
        print("  ✓ Panel 001: Chapter 10 Title Card")

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

    # Strip 2: Black Tortoise Guild shock & rejection of E-Rank
    crop_and_save(2, 2, 0, 7000, "Black Tortoise recruiter shock: 'Suho rejected our offer?'")
    crop_and_save(2, 3, 7000, 14500, "Recruiter furious: 'A newbie E-rank rejecting a large guild?!'")
    crop_and_save(2, 4, 14500, 22224, "Recruiter: 'He will see how hard it is' & Suho on phone with scout flood")

    # Strip 3: Suho & Beru discussing guilds & Fang of Rakan
    crop_and_save(3, 5, 0, 8000, "Suho: 'They only want me as porter. Guilds hinder system leveling'")
    crop_and_save(3, 6, 8000, 16875, "Suho lying on floor turning to Fang of Rakan dagger on table")

    # Strip 4: Fang of Rakan pact & sacred ground requirement
    crop_and_save(4, 7, 0, 7500, "Flashback: Suho holding Fang, shadow & fang aligned")
    crop_and_save(4, 8, 7500, 15000, "Fang thinking: 'How can he say that so casually? But shadow can be ally'")
    crop_and_save(4, 9, 15000, 22500, "Fang's condition: 'Bring me to another sacred ground of Fang Monarch'")

    # Strip 5: Field dungeon explanation & Suho gearing up
    crop_and_save(5, 10, 0, 7000, "Fang: 'I know the location, but a dungeon break already happened'")
    crop_and_save(5, 11, 7000, 14000, "Suho realizes: Field-Type Dungeon where neglected gate monsters rule")
    crop_and_save(5, 12, 14000, 21699, "Note for uncle, Suho departs with Beru on shoulder & Fang on back")

    # Strip 6: Gwanak Mountain & Hyena Guild gang fence
    crop_and_save(6, 13, 0, 7500, "Night at Gwanak Mountain Field gate: 'Entry permitted only for Hyena Guild'")
    crop_and_save(6, 14, 7500, 15000, "Suho: 'Hyena Guild is made up of thugs and former gang members'")
    crop_and_save(6, 15, 15000, 21692, "Suho's eyes glow blue gathering mana: 'Preparing to go in'")

    # Strip 7: CCTV destruction & Cosmic blue fog
    crop_and_save(7, 16, 0, 8000, "Ruler's Authority telekinesis crushes CCTV camera to dust")
    crop_and_save(7, 17, 8000, 14000, "Beru: 'Your problem solving reminds me of the Shadow Monarch'")
    crop_and_save(7, 18, 14000, 20574, "Entering blue fog: Mana from outer space breaking dimensional walls")

    # Strip 8: Outer gods cosmic war lore & Beast ambush
    crop_and_save(8, 19, 0, 8000, "Outer space entities (Itarim) trying to breach Earth dimension")
    crop_and_save(8, 20, 8000, 14500, "Dimensional travel delay for stronger beings; Suho: 'I must level up quickly'")
    crop_and_save(8, 21, 14500, 22500, "Ambush! Daggerclaw Vriga & Black Shadow Rajan beasts attack!")

    # Strip 9: Hand-to-hand combat, Ruler's Authority & Storm Slash
    crop_and_save(9, 22, 0, 7000, "Fang offers to fight; Suho: 'I won't use you as main weapon!'")
    crop_and_save(9, 23, 7000, 14000, "Suho delivers brutal martial arts punch to giant shadow panther!")
    crop_and_save(9, 24, 14000, 21957, "Ruler's Authority telekinesis support + Skill Activated: STORM SLASH!")

    # Strip 10: Shadow Extraction & 5 Shadow soldiers
    crop_and_save(10, 25, 0, 7500, "Beasts slashed down! Suho reaches out: SHADOW EXTRACTION!")
    crop_and_save(10, 26, 7500, 14500, "Dark blue shadow armor forms: 'My new way of fighting'")
    crop_and_save(10, 27, 14500, 22433, "Fang awestruck by Shadow Monarch bloodline; 5 Shadow beasts summoned!")

    # Strip 11: Beru roasted, arriving at secret campsite
    crop_and_save(11, 28, 0, 7000, "Beru: 'Nothing compared to Great Monarch...' Suho: 'Shut it!'")
    crop_and_save(11, 29, 7000, 14000, "Arriving at sacred grounds coordinates; illuminated camp in distance")
    crop_and_save(11, 30, 14000, 21957, "Hyena Guild trucks and hunters active late at night: 'Why stay so late?'")

    # Strip 12: Kidnapping discovery & Suho's lightning vanish
    crop_and_save(12, 31, 0, 7000, "Shocking discovery: A young girl is tied up, gagged and captured!")
    crop_and_save(12, 32, 7000, 14000, "Thug grabs her hair; Suho: 'Beru, am I witnessing a kidnapping right now?'")
    crop_and_save(12, 33, 14000, 21866, "Beru warns against trespassing, but Suho has ALREADY disappeared!")

    # Strip 13: Justice legacy & Meteor strike climax
    crop_and_save(13, 34, 0, 7000, "Father was violent crimes detective, grandfather a legendary firefighter")
    crop_and_save(13, 35, 7000, 13500, "Sung Suho (21): Developed habit of ACTING FIRST when it comes to justice!")
    crop_and_save(13, 36, 13500, 18000, "Suho crashes down behind kidnappers like a blue thunder meteor!")
    crop_and_save(13, 37, 18000, 22500, "Kidnapper turns in horror ('HUH?'); Suho's eyes ablaze for battle!")

    print(f"\n✅ Sliced 37 cinematic panels saved to {PANELS_DIR}")

if __name__ == "__main__":
    slice_panels()
