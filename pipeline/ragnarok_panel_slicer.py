"""
pipeline/ragnarok_panel_slicer.py — Intelligent Panel Slicer for Solo Leveling: Ragnarok Chapter 1.

Takes the 19 raw webtoon strips (800 x 14000+ px) and slices them into perfectly
cropped, high-resolution scene panels for the cinematic video engine.
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

def slice_strips_to_panels(raw_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Strip 1: Title Card (1200x800) -> Crop/Pad to centered 1200x800 or 800x800
    s1 = cv2.imread(str(raw_dir / "strip_01.jpg"))
    if s1 is not None:
        cv2.imwrite(str(out_dir / "panel_001.jpg"), s1)
        print("  ✓ Panel 1 saved (Title Card)")

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
        
        # Trim pure black/white headers/footers if > 80px
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

    # Let's define the exact story beats and their pixel ranges across all strips
    # Strip 2 (800 x 14180): Outer Gods
    crop_and_save(2, 2, 0, 2400, "Outer Gods Title & Cosmic Beings")
    crop_and_save(2, 3, 2400, 4800, "Cosmic Clocks & Substance/Soul Creation")
    crop_and_save(2, 4, 4800, 7500, "Supreme Beings Boredom & Marionette")
    crop_and_save(2, 5, 7500, 10200, "Demonic Smile & Watching War")
    crop_and_save(2, 6, 10200, 12200, "Cosmic Chessboard & Endless Wars")
    crop_and_save(2, 7, 12200, 14180, "Absolute Being Killed By His Own Creation")

    # Strip 3 (800 x 15793): Outer Gods Assemble & Suho Uni
    crop_and_save(3, 8, 0, 2400, "Outer Gods Gathered Around Dimension")
    crop_and_save(3, 9, 2400, 5000, "Chess Pieces: Claim Ownerless Power")
    crop_and_save(3, 10, 5000, 8500, "Becomes Its Master! Cosmic Dragon Piece")
    crop_and_save(3, 11, 8500, 12000, "Solo Leveling Ragnarok Title Logo")
    crop_and_save(3, 12, 12000, 15793, "Korea National Univ of Arts & Suho in Class")

    # Strip 4 (800 x 15000): High School Friends & Bully
    crop_and_save(4, 13, 0, 3400, "Friends Congratulating Suho: Freed from Hell")
    crop_and_save(4, 14, 3400, 7200, "Bully Lee Eunchul Approaches")
    crop_and_save(4, 15, 7200, 11200, "Face to Face: Ruined My School Plan")
    crop_and_save(4, 16, 11200, 15000, "Students Gossiping: Harassing Pitiful Boy")

    # Strip 5 (800 x 14590): Bully Attacks & Instinctive Block
    crop_and_save(5, 17, 0, 4000, "Bully Attacks: Suho!")
    crop_and_save(5, 18, 4000, 7500, "Suho Instinctive Counter & Shock")
    crop_and_save(5, 19, 7500, 11000, "Suho: Let's Live Quietly Until Graduation")
    crop_and_save(5, 20, 11000, 14590, "Blue Lightning Sparks on Bully's Fist!")

    # Strip 6 (800 x 15000): Bully Awakens & Locker Smash
    crop_and_save(6, 21, 0, 4200, "Bully Charging with Red Eyes & Blue Mana")
    crop_and_save(6, 22, 4200, 8000, "Smashing Suho Into Wall & Lockers")
    crop_and_save(6, 23, 8000, 11500, "Bully Stunned by His Own Awakened Strength")
    crop_and_save(6, 24, 11500, 15000, "Suho Sitting by Broken Wall Unharmed")

    # Strip 7 (800 x 14575): Two Years Later & D-Rank Gate
    crop_and_save(7, 25, 0, 4200, "Two Years Later: University Campus")
    crop_and_save(7, 26, 4200, 8200, "Sung Suho Second-Year Student")
    crop_and_save(7, 27, 8200, 11500, "Campus Evacuation Announcement: D-Rank Gate")
    crop_and_save(7, 28, 11500, 14575, "Hunters Inside Gate for 8 Hours")

    # Strip 8 (800 x 14840): World Lore & Hunter Association
    crop_and_save(8, 29, 0, 3800, "Suho: Another Gate Huh?")
    crop_and_save(8, 30, 3800, 7800, "Gates Appeared 3 Years Ago & Monsters")
    crop_and_save(8, 31, 7800, 11500, "Awakened Hunters with Mana")
    crop_and_save(8, 32, 11500, 14840, "Woo Jinchul Forming Hunter Association")

    # Strip 9 (800 x 14395): Awakened vs Non-Awakened
    crop_and_save(9, 33, 0, 4500, "Society Divided: Awakened vs Non-Awakened")
    crop_and_save(9, 34, 4500, 9500, "Crawling Like Ants vs Limits of Humans")
    crop_and_save(9, 35, 9500, 14395, "Suho Painting in Art Class Contemplating Fate")

    # Strip 10 (800 x 14775): Missing Parents & Dad's Memory
    crop_and_save(10, 36, 0, 4500, "Non-Awakened Dependent on Hunters")
    crop_and_save(10, 37, 4500, 8500, "Flashback: Jin-woo & Hae-in with Baby Suho")
    crop_and_save(10, 38, 8500, 12000, "Sung Jin-woo's Silhouette: What Would Dad Do?")
    crop_and_save(10, 39, 12000, 14775, "Teacher Approaches Suho's Canvas")

    # Strip 11 (800 x 15000): Beru Sketch & Raid Team Exits
    crop_and_save(11, 40, 0, 5000, "Teacher: Is that an Ant Human?")
    crop_and_save(11, 41, 5000, 9000, "SHADOW ANT KING BERU DRAWING CLOSE-UP!")
    crop_and_save(11, 42, 9000, 12500, "Hunters Emerging from Gate victoriously")
    crop_and_save(11, 43, 12500, 15000, "Hunter Kim Welcomed by Staff")

    # Strip 12 (800 x 14250): New Monster Report & The Infection
    crop_and_save(12, 44, 0, 4500, "Hunter Kim: Blue Flame Humanoid Monster")
    crop_and_save(12, 45, 4500, 8500, "Monster Attack Flashback: Scratched My Leg")
    crop_and_save(12, 46, 8500, 12000, "Leg Scratch Glows with Blue Demonic Fire!")
    crop_and_save(12, 47, 12000, 14250, "Hunter Kim Collapses in Agony")

    # Strip 13 (800 x 12765): Blue Flame Eruption & Demon Mutation
    crop_and_save(13, 48, 0, 4200, "Are you... Hunter Kim?")
    crop_and_save(13, 49, 4200, 8500, "Mouth and Eyes Explode with Blue Flame!")
    crop_and_save(13, 50, 8500, 12765, "Mutating Into Blue Demon & Hunter Screams")

    # Strip 14 (800 x 13565): Courtyard Massacre & Classroom Alarm
    crop_and_save(14, 51, 0, 5000, "Massacre Outside: Guards Slashed and Hurled")
    crop_and_save(14, 52, 5000, 9000, "Suho and Students Looking Out Window in Horror")
    crop_and_save(14, 53, 9000, 13565, "Possessed Hunters Raging with Blue Fire")

    # Strip 15 (800 x 14340): Panic & Monster Crashes Through Window
    crop_and_save(15, 54, 0, 4800, "Instructor Im: But I'm only E-Rank!")
    crop_and_save(15, 55, 4800, 9500, "Monster Leaps From Rooftop")
    crop_and_save(15, 56, 9500, 14340, "GLASS SMASH! Monster Crashes Into Classroom!")

    # Strip 16 (800 x 13695): Classroom Terror & Helpless Girl
    crop_and_save(16, 57, 0, 4500, "Monster Roars in Room: GRAAAAH!")
    crop_and_save(16, 58, 4500, 9000, "Students Fleeing, Girl Collapses: Help Me!")
    crop_and_save(16, 59, 9000, 13695, "Suho Runs Out: I'll Get Hunters...")

    # Strip 17 (800 x 13945): Hallway Dilemma & Dad's Legacy
    crop_and_save(17, 60, 0, 4500, "Suho Stops: That's Asking Her to Die!")
    crop_and_save(17, 61, 4500, 9000, "If Dad Were Here, What Would He Do?!")
    crop_and_save(17, 62, 9000, 13945, "Jin-woo's Silhouette & Monster Approaching Girl")

    # Strip 18 (800 x 14685): Fire Extinguisher Strike & Quest Alert
    crop_and_save(18, 63, 0, 4500, "Monster Raises Claws to Kill Girl")
    crop_and_save(18, 64, 4500, 8500, "SUHO CHARGES WITH FIRE EXTINGUISHER!")
    crop_and_save(18, 65, 8500, 12000, "DIRECT FACE SMASH! If Dad Were Here...")
    crop_and_save(18, 66, 12000, 14685, "Static Glitches Across Vision")

    # Strip 19 (800 x 3313): System Window & Ending
    crop_and_save(19, 67, 0, 1800, "GOLDEN SYSTEM ALERT: COURAGE OF THE WEAK!")
    crop_and_save(19, 68, 1800, 3313, "SOLO LEVELING: RAGNAROK TITLE LOGO")

    print(f"\n✅ All panels successfully created in {out_dir}!")

if __name__ == "__main__":
    raw = Path("output/solo_leveling_ragnarok_ch1/raw_strips")
    out = Path("output/solo_leveling_ragnarok_ch1/panels")
    slice_strips_to_panels(raw, out)
