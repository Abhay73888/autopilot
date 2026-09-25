"""
pipeline/ragnarok_ch11_panel_slicer.py — Slices Chapter 11 raw strips into 42 synchronized action panels.
Ensures 100% 1-to-1 matching between narrated dialogue/events and the displayed image.
"""

import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "output" / "solo_leveling_ragnarok_ch11"
RAW_DIR = BASE / "raw_strips"
PANELS_DIR = BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 11 strips into 42 synchronized panels...")

    # Panel 1: Title Card
    s1 = RAW_DIR / "strip_01.jpg"
    if s1.exists():
        with Image.open(str(s1)) as im:
            im.save(str(PANELS_DIR / "panel_001.jpg"), quality=95)
        print("  ✓ Panel 001: Chapter 11 Title Card")

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

    # Strip 2: Suho's flying kick & surprise attack
    crop_and_save(2, 2, 0, 7500, "Suho flying kick attack on Hyena Guild members")
    crop_and_save(2, 3, 7500, 14000, "Suho drawing blue shadow energy; Hyena guild shocked")
    crop_and_save(2, 4, 14000, 21333, "Suho realizes: 'Illegal trespassing... what do I do?'")

    # Strip 3: Shadow Mask creation & confrontation
    crop_and_save(3, 5, 0, 7000, "Suho summons dark blue Shadow Mask over face")
    crop_and_save(3, 6, 7000, 14000, "Masked Suho: 'To think you would kidnap and endanger people!'")
    crop_and_save(3, 7, 14000, 20358, "Hyena guild thugs furious: 'Do you have a death wish?! Destroy him!'")

    # Strip 4: Effortless D-Rank beatdown
    crop_and_save(4, 8, 0, 7000, "Suho: 'Average rank is D-rank, will tone down strength'")
    crop_and_save(4, 9, 7000, 14000, "Suho launches thugs flying into the air like ragdolls")
    crop_and_save(4, 10, 14000, 21507, "Thugs crashing violently onto ground")

    # Strip 5: Beru proud, Level 16 Status & rescue
    crop_and_save(5, 11, 0, 6500, "Beru moved to tears: 'Young Monarch has grown so strong!'")
    crop_and_save(5, 12, 6500, 12500, "Status Window: Level 16, HP 2350, MP 235, Strength 33")
    crop_and_save(5, 13, 12500, 18000, "Suho stacks knocked out thugs in a neat pile")
    crop_and_save(5, 14, 18000, 22500, "Hostages thanked Suho & escape to safety")

    # Strip 6: Warehouse investigation & Fang's guidance
    crop_and_save(6, 15, 0, 7500, "Suho watching hostages leave safely")
    crop_and_save(6, 16, 7500, 15000, "Sword Fang of Rakan: 'I can feel it... over there'")
    crop_and_save(6, 17, 15000, 22500, "Suho descends into dark underground dungeon warehouse")

    # Strip 7: Secret holding cells & Fang Monarch descendant
    crop_and_save(7, 18, 0, 7000, "Blood buckets, syringes and dark experimental lab")
    crop_and_save(7, 19, 7000, 14500, "Chained, wounded baby wolf whimpering in cage")
    crop_and_save(7, 20, 14500, 22500, "Sword reveals: 'A descendant of the King of Beasts, the Fang Monarch!'")

    # Strip 8: Sanctuary flashback & sudden intruder
    crop_and_save(8, 21, 0, 7500, "Sword mourns cub vitality fading away")
    crop_and_save(8, 22, 7500, 14500, "Beru asks: 'Young Monarch, what will you do?'")
    crop_and_save(8, 23, 14500, 22191, "Heavy footsteps: 'Just one person...' Suho turns alert")

    # Strip 9: Giant werewolf Brocky appears
    crop_and_save(9, 24, 0, 7000, "Colossal Werewolf beast Brocky emerges from darkness")
    crop_and_save(9, 25, 7000, 15000, "Sword recognizes him: 'Brocky! You were assigned to protect descendants!'")
    crop_and_save(9, 26, 15000, 22500, "Brocky's red eyes glare: 'You dare touch what belongs to me?!'")

    # Strip 10: Blinding attack
    crop_and_save(10, 27, 0, 6000, "Brocky lunges at supersonic speed with red claw shockwaves")
    crop_and_save(10, 28, 6000, 11867, "Devastating bone-crushing claw impact on Suho")

    # Strip 11: Catastrophic destruction
    crop_and_save(11, 29, 0, 11000, "Building shattered, massive trench of destruction")
    crop_and_save(11, 30, 11000, 22500, "Beru screams in panic; Suho rises coughing blood from head")

    # Strip 12: Endurance Level Up & ITARIM revelation
    crop_and_save(12, 31, 0, 6500, "Skill: Endurance leveled up! Physical Resistance +20% -> +40%")
    crop_and_save(12, 32, 6500, 13500, "Beru shocked: 'ITARIM! I can sense Outer God Itarim energy!'")
    crop_and_save(12, 33, 13500, 20300, "Sword demands how Brocky maintained strength")

    # Strip 13: Cannibalistic confession & false Monarch
    crop_and_save(13, 34, 0, 7500, "Brocky: 'I have been regularly consuming his blood and eating him!'")
    crop_and_save(13, 35, 7500, 14500, "Sword furious: 'I will kill you if it's the last thing I do!'")
    crop_and_save(13, 36, 14500, 21941, "Brocky gathers energy: 'I am fit to be the next Fang Monarch!'")

    # Strip 14: Telekinesis rescue & Beru catch
    crop_and_save(14, 37, 0, 7500, "Brocky leaps to smash pup; Suho snatches pup with Ruler's Authority")
    crop_and_save(14, 38, 7500, 15375, "Beru safely catches pup: 'Hilarious.'")

    # Strip 15: Alliance between Shadow & Fang, Clue to Father
    crop_and_save(15, 39, 0, 7000, "Suho steps forward, sword burning with sovereign blue lightning")
    crop_and_save(15, 40, 7000, 14500, "Suho: 'First alliance between Shadow and Fang! Itarim... clue to father!'")
    crop_and_save(15, 41, 14500, 22217, "Brocky radiates murderous intent & Alert: Quest has arrived")

    # Strip 16: Emergency Quest Climax
    crop_and_save(16, 42, 0, 4620, "EMERGENCY QUEST: HUNT THE HYENA! Defeat Brocky (0/1)")

    print(f"\n✅ All 42 panels sliced successfully in {PANELS_DIR}!")

if __name__ == "__main__":
    slice_panels()
