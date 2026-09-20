"""
pipeline/ragnarok_ch2_panel_slicer.py — Panel Slicer for Solo Leveling: Ragnarok Chapter 2.

Slices the 18 raw webtoon strips into 65 high-resolution scene panels.
"""

import os
import glob
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def slice_ch2_strips_to_panels(raw_dir: Path, out_dir: Path):
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
        valid_rows = np.where((row_means > 10) & (row_means < 245))[0]
        if len(valid_rows) > 100:
            top_margin = max(0, valid_rows[0] - 20)
            bot_margin = min(cropped.shape[0], valid_rows[-1] + 20)
            cropped = cropped[top_margin:bot_margin, :]

        out_path = out_dir / f"panel_{panel_id:03d}.jpg"
        cv2.imwrite(str(out_path), cropped)
        print(f"  ✓ Panel {panel_id:03d} saved: Strip {strip_num} [{y1}:{y2}] -> {cropped.shape[1]}x{cropped.shape[0]} ({desc})")

    # Strip 2 (800 x 12644): Prologue & Dream of Game Leveling
    crop_and_save(2, 2, 0, 3200, "Prologue: Dream Resembled A Game")
    crop_and_save(2, 3, 3200, 7500, "Fighting Floor by Floor: Level Up!")
    crop_and_save(2, 4, 7500, 12644, "Reaching Highest Floor Through Challenges")

    # Strip 3 (800 x 13388): The Final Boss & Father Sung Jin-Woo
    crop_and_save(3, 5, 0, 3500, "Final Boss Encountered: Powerful & Envious")
    crop_and_save(3, 6, 3500, 7500, "Final Boss Was Dad! Jin-Woo: Was Game Fun?")
    crop_and_save(3, 7, 7500, 10500, "Dad Who Was Strong and Reliable")
    crop_and_save(3, 8, 10500, 13388, "Back to Present: Grabbing Fire Extinguisher")

    # Strip 4 (800 x 13305): Extinguisher Charge & Reckless Attack
    crop_and_save(4, 9, 0, 4200, "Dad, You Would Have Done The Same!")
    crop_and_save(4, 10, 4200, 8500, "Smashing Extinguisher into Monster Face!")
    crop_and_save(4, 11, 8500, 13305, "Reckless Attack: No Mana Against Magic Beast!")

    # Strip 5 (800 x 14433): Time Freeze & Player Invitation
    crop_and_save(5, 12, 0, 3800, "Monster Deadly Claw Over Suho: ?!")
    crop_and_save(5, 13, 3800, 7000, "TIME STOPS! Girl and Monster Frozen!")
    crop_and_save(5, 14, 7000, 9500, "System Notice: Courage of the Weak Completed")
    crop_and_save(5, 15, 9500, 11800, "You Qualify to Become a Player: Accept?")
    crop_and_save(5, 16, 11800, 14433, "Like That Dream: No Reason Not To Accept!")

    # Strip 6 (800 x 14422): Acceptance & Status Window
    crop_and_save(6, 17, 0, 2500, "Suho Smirks: ACCEPT!")
    crop_and_save(6, 18, 2500, 5000, "Golden Light: You Have Become a Player!")
    crop_and_save(6, 19, 5000, 7800, "Quest Reward: Great Spellcaster Blessing & Longevity")
    crop_and_save(6, 20, 7800, 10500, "STATUS WINDOW: Level 1 & Ruler's Authority!")
    crop_and_save(6, 21, 10500, 12500, "Electric Blue Eyes: Just as I Thought!")
    crop_and_save(6, 22, 12500, 14422, "Quest Tutorial: Defeat Mist Burn & Level Up!")

    # Strip 7 (800 x 13555): Time Resumes & Monster Name Tags
    crop_and_save(7, 23, 0, 3200, "Time Resumes! Name Tag: D-Rank Mist Burn")
    crop_and_save(7, 24, 3200, 6000, "Suho: Run Quickly! Girl Escapes")
    crop_and_save(7, 25, 6000, 10000, "3 Possessed Beasts: If I Really Awakened...")
    crop_and_save(7, 26, 10000, 13555, "Suho Strikes with Fire Extinguisher!")

    # Strip 8 (800 x 12516): One-Punch Knockout
    crop_and_save(8, 27, 0, 3500, "Extinguisher Breaks: Charging with Bare Fist!")
    crop_and_save(8, 28, 3500, 7500, "Sorry! Massive Right Hook Punch!")
    crop_and_save(8, 29, 7500, 10500, "Possessed Student Sent Flying into Wall!")
    crop_and_save(8, 30, 10500, 12516, "Defeated Unawakened Mist Burn: In One Shot?!")

    # Strip 9 (800 x 14444): Second Kill, Level Up & D-Rank Boss
    crop_and_save(9, 31, 0, 4500, "Second Mist Burn Charges: Counter Punch!")
    crop_and_save(9, 32, 4500, 8000, "Defeated Mist Burn: LEVEL UP! Level 2 Attained")
    crop_and_save(9, 33, 8000, 10500, "Quest Completed: Check Your Reward?")
    crop_and_save(9, 34, 10500, 12500, "Suho: I Really Did Awaken!")
    crop_and_save(9, 35, 12500, 14444, "D-Rank Awakened Mist Burn Roars & Shockwave!")

    # Strip 10 (800 x 14161): Poison Claws & Longevity Healing
    crop_and_save(10, 36, 0, 3500, "Suho Blown Back: It Withstood That?!")
    crop_and_save(10, 37, 3500, 7500, "D-Rank Slashes Suho with Blue Flame Claws!")
    crop_and_save(10, 38, 7500, 10500, "Chest Slashed: URGH! Pushed Back!")
    crop_and_save(10, 39, 10500, 12500, "Suho: I'll Turn into a Beast if Wounded!")
    crop_and_save(10, 40, 12500, 14161, "Longevity Notice: Harmful Status Effect Lifted!")

    # Strip 11 (800 x 13916): Pinned Down & Desperate Struggle
    crop_and_save(11, 41, 0, 3500, "Green Healing Light: Longevity Blessing!")
    crop_and_save(11, 42, 3500, 7500, "D-Rank Monster Pins Suho to the Ground!")
    crop_and_save(11, 43, 7500, 11000, "Monster Snapping Jaws: GRAAAAH!")
    crop_and_save(11, 44, 11000, 13916, "Suho Struggling: There has to be something... AH!")

    # Strip 12 (800 x 13911): Stat Points Allocation (Strength 19!)
    crop_and_save(12, 45, 0, 3500, "ACCEPT REWARD! Stat Point +5, Strength +3")
    crop_and_save(12, 46, 3500, 7000, "STRENGTH: 11 -> 14 -> 19!")
    crop_and_save(12, 47, 7000, 10500, "URRAAAAAAH! Bench-Pressing Monster Away!")
    crop_and_save(12, 48, 10500, 13911, "Monster Lunges Again: Explosive Speed & Power!")

    # Strip 13 (800 x 13305): Breaking Limits & Power Surge
    crop_and_save(13, 49, 0, 4500, "Put All Remaining Points into Strength!")
    crop_and_save(13, 50, 4500, 9000, "An Awakener Who Levels Up? Breaking Ranks!")
    crop_and_save(13, 51, 9000, 13305, "Escaping the Damned Structure: Decisive Punch!")

    # Strip 14 (800 x 7272): Kinetic Shockwaves
    crop_and_save(14, 52, 0, 3600, "Sonic Clash: Walls and Floor Explode!")
    crop_and_save(14, 53, 3600, 7272, "Massive Shockwave Ripples Through Building!")

    # Strip 15 (800 x 13761): Decisive Finishing Blow
    crop_and_save(15, 54, 0, 4500, "Suho Channels Full Power: THE FINISHING PUNCH!")
    crop_and_save(15, 55, 4500, 9500, "Direct Skull Smash! Monster Core Shattered!")
    crop_and_save(15, 56, 9500, 13761, "Blue Flames Vanish: Suho Victorious!")

    # Strip 16 (800 x 14444): Victory, Triple Level Up & Awakener
    crop_and_save(16, 57, 0, 3500, "Notice: Defeated D-Rank Awakened Mist Burn!")
    crop_and_save(16, 58, 3500, 6500, "TRIPLE LEVEL UP! LEVEL UP! LEVEL UP!")
    crop_and_save(16, 59, 6500, 10500, "Suho: I Won... I'm an Awakener Now!")
    crop_and_save(16, 60, 10500, 14444, "I Can Save People and Solve This Crisis!")

    # Strip 17 (800 x 12094): Elite Hunter Hurled & C-Rank Mist Burn
    crop_and_save(17, 61, 0, 3800, "Checking Window: What's Happening Outside?!")
    crop_and_save(17, 62, 3800, 7500, "Elite Hunter Hurled Through Air, Crashes on Window!")
    crop_and_save(17, 63, 7500, 12094, "TITANIC SHADOW LANDS: C-RANK AWAKENED MIST BURN!")

    # Strip 18 (800 x 4327): Courtyard Explosion & Cliffhanger
    crop_and_save(18, 64, 0, 2200, "C-Rank Monster Roar & Earth-Shaking Explosion!")
    crop_and_save(18, 65, 2200, 4327, "SOLO LEVELING: RAGNAROK CH 2 CLIFFHANGER LOGO!")

    print(f"\n✅ All 65 panels successfully created in {out_dir}!")

if __name__ == "__main__":
    raw = Path("output/solo_leveling_ragnarok_ch2/raw_strips")
    out = Path("output/solo_leveling_ragnarok_ch2/panels")
    slice_ch2_strips_to_panels(raw, out)
