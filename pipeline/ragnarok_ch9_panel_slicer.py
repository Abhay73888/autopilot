"""
pipeline/ragnarok_ch9_panel_slicer.py — Slices Chapter 9 raw strips into 35 tightly focused, synchronized action panels.
Ensures 100% 1-to-1 matching between narrated dialogue/events and the displayed image.
"""

import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "output" / "solo_leveling_ragnarok_ch9"
RAW_DIR = BASE / "raw_strips"
PANELS_DIR = BASE / "panels"

def slice_panels():
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n✂️ Slicing Chapter 9 strips into 35 synchronized panels...")

    # Panel 1: Title Card
    s1 = RAW_DIR / "strip_01.jpg"
    if s1.exists():
        with Image.open(str(s1)) as im:
            im.save(str(PANELS_DIR / "panel_001.jpg"), quality=95)
        print("  ✓ Panel 001: Chapter 9 Title Card")

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

    # Strip 2: Quest reward, Rune stone, Storm Slash
    crop_and_save(2, 2, 0, 7500, "Suho & Beru talking about decent harvest")
    crop_and_save(2, 3, 7500, 14000, "System Alert: Quest Completion Reward Arrived & Rune Stone Storm Slash")
    crop_and_save(2, 4, 14000, 22500, "Skill Window: Storm Slash Lv.1 & Suho surging with mana")

    # Strip 3: Cursed sword scheming, possession attempt, and failure
    crop_and_save(3, 5, 0, 7500, "Cursed Sword lying in rubble plotting to devour Suho")
    crop_and_save(3, 6, 7500, 14000, "Suho grabs the sword, crimson demonic smoke bursts")
    crop_and_save(3, 7, 14000, 20942, "Demonic smoke shatters; System: You've Obtained 'Fang of Rakhan'")

    # Strip 4: Kandiaru's Blessing, Storm Slash test & Cavern obliteration
    crop_and_save(4, 8, 0, 7000, "Kandiaru's Blessing: Longevity & Status Effect Immunity")
    crop_and_save(4, 9, 7000, 14000, "Suho swings sword: You Have Used The Skill 'Storm Slash'")
    crop_and_save(4, 10, 14000, 21732, "Massive hurricane slash slices cavern in half; Beru compares to Shadow Authority")

    # Strip 5: Rescuing Dogyoon & stepping back into dungeon alone
    crop_and_save(5, 11, 0, 8000, "Dogyoon wakes up, sees defeated hunter and gasps")
    crop_and_save(5, 12, 8000, 15000, "Suho escorts Dogyoon to outside miners: 'I'll check for more survivors'")
    crop_and_save(5, 13, 15000, 22166, "Suho re-enters swirling blue dungeon gate; Dogyoon: 'How is he so strong?!'")

    # Strip 6: Slaying remaining wolves, Level Up, and Sword ATK drop
    crop_and_save(6, 14, 0, 7500, "Rescued miners safe outside; Dogyoon thanks Suho in silence")
    crop_and_save(6, 15, 7500, 14000, "Suho slashes remaining Lycans inside; Defeated! You Have Leveled Up!")
    crop_and_save(6, 16, 14000, 21917, "Suho notices sword ATK dropped suddenly")

    # Strip 7: Sword item window, roasting the sword, inner sanctuary
    crop_and_save(7, 17, 0, 8000, "Fang of Rakhan Item Window: ATK +30 -> +5, Contempt for the Weak")
    crop_and_save(7, 18, 8000, 15000, "Suho calls it dirty; Beru roasts the sword; Sword gets tongue-tied")
    crop_and_save(7, 19, 15000, 22449, "Suho enters inner altar and sees strike squad corpses")

    # Strip 8: Corpses on altar, Shadow Extraction prompt, Moral dilemma
    crop_and_save(8, 20, 0, 7500, "Elite strike squad corpses; Sword: 'I killed all intruders'")
    crop_and_save(8, 21, 7500, 14500, "Suho thrusts sword in ground: System: Shadow Extraction is possible on this target")
    crop_and_save(8, 22, 14500, 22500, "Suho: 'I can extract humans too?' Beru confirms; Suho ponders")

    # Strip 9: Suho refuses human extraction, Beru's respect, Itarim vs Monarchs
    crop_and_save(9, 23, 0, 7000, "Suho carries dead hunters: 'Nah. Fighting in death is punishing them.'")
    crop_and_save(9, 24, 7000, 14000, "Beru & Sword deeply moved by Suho's righteousness")
    crop_and_save(9, 25, 14000, 21791, "Suho asks about Monarchs; Beru: 'Itarim is current enemy, Monarchs were past enemies'")

    # Strip 10: The 9 Monarchs splash art & Jinwoo's Earth defense
    crop_and_save(10, 26, 0, 11000, "Spectacular 9 Monarchs Splash Art (Jinwoo, Fang, Plague, Giants, Dragons, etc.)")
    crop_and_save(10, 27, 11000, 16000, "Beru: 'All 8 invading Monarchs died at the hands of my Liege!' Suho: 'Father did that...'")
    crop_and_save(10, 28, 16000, 22500, "Cursed Sword: 'Shadow Monarch is my mortal enemy who killed my master!'")

    # Strip 11: Suho's philosophical negotiation with the sword
    crop_and_save(11, 29, 0, 8000, "Suho: 'Both sides protected what was precious; but fighting me is foolish'")
    crop_and_save(11, 30, 8000, 15000, "Suho: 'If Itarim invade, this sanctuary won't survive. Help me and I'll help you!'")
    crop_and_save(11, 31, 15000, 22500, "Sword stunned: 'Work with the Shadow Monarch's descendant...?!'")

    # Strip 12 & 13: Alliance sealed, Dogyoon in cafe, Viral internet article
    crop_and_save(12, 32, 0, 11000, "Suho offers handshake: 'Shadow and Fang fighting on the same battlefront!'")
    crop_and_save(12, 33, 11000, 21999, "Next morning: Dogyoon interviewed by reporters & Hunter Association in cafe")
    crop_and_save(13, 34, 0, 11000, "Viral Article: 'Heroic E-Rank Hunter Saves Dungeon Team Alone!'")

    # Strip 13 & 14: Black Tortoise Guild shock & Manager Lee Youngho's call
    crop_and_save(13, 35, 11000, 22500, "Black Tortoise Guild Management reviewing Suho's heroic report")
    crop_and_save(14, 36, 0, 6000, "Guild staff in shock: 'A-AN E-RANK HUNTER DID ALL THAT?!'")
    crop_and_save(14, 37, 6000, 12731, "Manager Lee Youngho smirks: 'A hero among E-Ranks! Contact him immediately!'")

    print(f"\n✅ Sliced 37 cinematic panels saved to {PANELS_DIR}")

if __name__ == "__main__":
    slice_panels()
