"""
pipeline/ragnarok_ch3_panel_slicer.py — Intelligent Wide-Panel Slicer for Solo Leveling: Ragnarok Chapter 3.

Fixes the "thin/small image" problem by cropping tightly focused action panels
(height 600-1100px), ensuring the foreground artwork appears wide, bold, and fills
the screen in 1080p widescreen video.
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def slice_ch3_strips_to_panels(raw_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    # Strip 1: Title Card (1200x800)
    s1 = cv2.imread(str(raw_dir / "strip_01.jpg"))
    if s1 is not None:
        cv2.imwrite(str(out_dir / "panel_001.jpg"), s1)
        print("  ✓ Panel 001 saved (Title Card)")

    def crop_and_save(strip_num: int, panel_id: int, y_start: int, y_end: int, desc: str = ""):
        img_path = raw_dir / f"strip_{strip_num:02d}.jpg"
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  ❌ Failed to load strip {strip_num}")
            return
        h, w = img.shape[:2]
        y1 = max(0, min(y_start, h - 1))
        y2 = max(y1 + 50, min(y_end, h))
        cropped = img[y1:y2, 0:w]

        # Trim blank margins
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        row_means = np.mean(gray, axis=1)
        valid_rows = np.where((row_means > 8) & (row_means < 248))[0]
        if len(valid_rows) > 60:
            top_margin = max(0, valid_rows[0] - 15)
            bot_margin = min(cropped.shape[0], valid_rows[-1] + 15)
            cropped = cropped[top_margin:bot_margin, :]

        out_path = out_dir / f"panel_{panel_id:03d}.jpg"
        cv2.imwrite(str(out_path), cropped)
        print(f"  ✓ Panel {panel_id:03d} saved: Strip {strip_num} [{y1}:{y2}] -> {cropped.shape[1]}x{cropped.shape[0]} ({desc})")

    # Strip 2 (800 x 14222): Siren & Soldiers Looking at Campus
    crop_and_save(2, 2, 0, 4800, "Emergency Sirens: Dungeon Break at Korea Arts Univ")
    crop_and_save(2, 3, 4800, 10500, "Soldiers on Rooftop Looking Down in Despair")
    crop_and_save(2, 4, 10500, 14222, "Hunter Association Assigning Rank B Hunter")

    # Strip 3 (800 x 14444): C-Rank Tank Kim Jongsu Infected & Suho Stunned
    crop_and_save(3, 5, 0, 5000, "Tablet Notice: C-Rank Tank Kim Jongsu Infected!")
    crop_and_save(3, 6, 5000, 10000, "Suho in Classroom: C-Rank Awakened Mist Burn with Sword!")
    crop_and_save(3, 7, 10000, 14444, "Suho: I leveled up, could I stand a chance?!")

    # Strip 4 (800 x 13800): Colossal Wind Blade & Building Slice
    crop_and_save(4, 8, 0, 6800, "Monster Slashes: Colossal Wind Blade Slices Walls!")
    crop_and_save(4, 9, 6800, 13800, "Suho: This is INSANE! Building is Tearing Apart!")

    # Strip 5 (800 x 12811): Hallway Sprint & 3 Trapped Girls
    crop_and_save(5, 10, 0, 6500, "Suho Sprints in Hallway: Need to Hold Out for B-Rank Hunter!")
    crop_and_save(5, 11, 6500, 12811, "Suho Freezes at Corner: 3 Female Classmates Trapped!")

    # Strip 6 (800 x 14444): Monster Leaps at Girls & Suho Resolves
    crop_and_save(6, 12, 0, 7200, "Monster Leaps Toward Girls to Slaughter Them!")
    crop_and_save(6, 13, 7200, 14444, "Suho Eyes Blaze Blue: No Time to Wait, I Must Stop Him!")

    # Strip 7 (800 x 14444): Mid-Air Tackle & Near Death Dodge
    crop_and_save(7, 14, 0, 7000, "Mid-Air Tackle! Suho Intercepts Monster!")
    crop_and_save(7, 15, 7000, 14444, "Monster Slashes Back: Millimeter Dodge! One Hit Kills Me!")

    # Strip 8 (800 x 9277): Superhuman Punch Barrage
    crop_and_save(8, 16, 0, 4800, "Suho Unleashes Rapid-Fire Superhuman Punch Barrage!")
    crop_and_save(8, 17, 4800, 9277, "Ducking and Weaving with High Agility!")

    # Strip 9 (800 x 14438): Counter-Strike & Stomach Smash
    crop_and_save(9, 18, 0, 7000, "Suho Strikes Monster Chin, But C-Rank Armor Absorbs It!")
    crop_and_save(9, 19, 7000, 14438, "Devastating Counter-Punch to Suho's Stomach: KGH!")

    # Strip 10 (800 x 13772): HP 1 / 140 & Lucking Out
    crop_and_save(10, 20, 0, 6800, "Suho Crashes in Rubble: SYSTEM ALERT HP 1 / 140!")
    crop_and_save(10, 21, 6800, 13772, "Suho Smirks: 1 HP Left... System Doesn't Want Me Dead Yet!")

    # Strip 11 (800 x 12894): Fatigue 99 & Falling Sword
    crop_and_save(11, 22, 0, 6500, "FATIGUE 99! Total Body Paralysis!")
    crop_and_save(11, 23, 6500, 12894, "Colossal Broadsword Drops for the Execution Strike!")

    # Strip 12 (800 x 13938): Explosion & Giant Shadow Claw
    crop_and_save(12, 24, 0, 7000, "KABOOM! Concrete Floor Explodes!")
    crop_and_save(12, 25, 7000, 13938, "Suho: An Ant...? Giant Shadow Claw Shields Him!")

    # Strip 13 (800 x 13311): BERU THE SHADOW ANT KING ARRIVES!
    crop_and_save(13, 26, 0, 4500, "Shadow Beast in Agony: NOO... ALL BECAUSE I WAS LATE...")
    crop_and_save(13, 27, 4500, 9000, "SHADOW ANT KING BERU! Eyes Blaze with Cosmic Purple Flames!")
    crop_and_save(13, 28, 9000, 13311, "YOU DARE HARM HIS HIGHNESS?! Instant C-Rank Monster Shred!")

    # Strip 14 (800 x 8250): B-Rank Hunter & Professor in Danger
    crop_and_save(14, 29, 0, 4200, "On Rooftop: B-Rank Hunter Arrives with Cigarette")
    crop_and_save(14, 30, 4200, 8250, "Mist Burn Attacks Professor: Beru Blitzes Across Sky!")

    # Strip 15 (800 x 10183): Berserk Shadow Shredding
    crop_and_save(15, 31, 0, 10183, "Purple Shadow Hurricane! Beru Tears Through Monsters in Air!")

    # Strip 16 (800 x 13938): Shocked Hunters & Beru Kneeling
    crop_and_save(16, 32, 0, 7000, "B-Rank Hunter & Soldiers Stare in Pure Disbelief!")
    crop_and_save(16, 33, 7000, 13938, "In the Crater: Shadow Ant King Gently Kneels Before Suho...")

    # Strip 17 (800 x 3968): Young Monarch & Chapter 3 Cliffhanger
    crop_and_save(17, 34, 0, 2200, "Beru Bows with Tears: 'IT HAS BEEN A WHILE... YOUNG MONARCH.'")
    crop_and_save(17, 35, 2200, 3968, "SOLO LEVELING: RAGNAROK CHAPTER 3 LOGO!")

    print(f"\n✅ All 35 wide-focus panels created in {out_dir}!")

if __name__ == "__main__":
    raw = Path("output/solo_leveling_ragnarok_ch3/raw_strips")
    out = Path("output/solo_leveling_ragnarok_ch3/panels")
    slice_ch3_strips_to_panels(raw, out)
