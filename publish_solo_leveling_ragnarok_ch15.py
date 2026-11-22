"""
publish_solo_leveling_ragnarok_ch15.py — YouTube Publisher for Solo Leveling: Ragnarok Chapter 15.

POLICY COMPLIANCE (AGENTS.md):
  • Zero Comment Lock Policy: comments ALWAYS 100% ENABLED (ON)
  • selfDeclaredMadeForKids = False (MANDATORY)
  • privacyStatus = "public"
  • Engagement pinned first comment via commentThreads.insert
  • Transformative Commentary & Fair Use (Section 107 of Copyright Act)
"""

import sys
import json
import time
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agents.publisher import YouTubePublisher
from core.db import DB
from core.logbook import Logbook
from core.ffmpeg import probe
from core.discord_service import DiscordNotifications, COLOR_SUCCESS

log = Logbook("solo_leveling_ragnarok_ch15_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch15"
VIDEO_PATH = VIDEO_DIR / "solo_leveling_ragnarok_ch15_final.mp4"
COVER_PATH = VIDEO_DIR / "thumbnail.jpg"

TITLE = "SOLO LEVELING: RAGNAROK Chapter 15 in Hindi ⚔️ | Stardust Secret & Shadow Monarch Awakening! | Full Recap"

DISCORD_CHANNEL = "1212765278765584396"

COMMENT_BAIT = (
    "⚡ Sung Jinwoo ke divine shadow presence aur Lee Minsung ke Stardust mutant form ki ladayi kaisi lagi? "
    "Kya Suho agle chapter mein Outer Gods ke Apostles ko dhoondh payega? "
    "Apni raye comments mein zaroor batayein aur subscribe karein agle episode ke liye! 👇"
)

TAGS = [
    "Solo Leveling",
    "Solo Leveling Ragnarok",
    "Solo Leveling Ragnarok Chapter 15",
    "Sung Suho",
    "Sung Jinwoo",
    "Shadow Monarch",
    "Beru",
    "Grim Reaper Guild",
    "Lee Minsung",
    "Stardust Mutant",
    "Anime Recap Hindi",
    "Manhwa Explained in Hindi",
    "Solo Leveling Season 2",
    "Itarim Outer Gods",
    "Anime India",
    "Solo Leveling Hindi",
    "Shadow Army"
]

DESCRIPTION = f"""SOLO LEVELING: RAGNAROK Chapter 15 Full Hindi Recap & Breakdown! ⚔️🔥

Grim Reaper Guild ka Vice-CEO Lee Minsung Stardust crystal khaakar ek khaufnaak Apostle mutant mein tabdeel ho jata hai! Suho, Gray aur Beru par jaanleva hamla hota hai, par tabhi khulta hai dimensional gate aur ubharta hai asli SHADOW MONARCH — Sung Jinwoo ka krodh! Dekhiye Chapter 15 ka sabse shandaar breakdown Hindi mein!

⏰ CHAPTER TIMESTAMPS:
00:00 - Introduction & Recap of Chapter 14 Cliffhanger
00:40 - Infiltrating Grim Reaper's Subterranean Lab
01:25 - Mutated Hyena Hunters Ambush Suho
02:10 - Suho & Gray Dual Assault with Beast Buff
02:55 - Lee Minsung Swallows Stardust Crystal
03:35 - The Awakening of the Shadow Monarch — Sung Jinwoo!
04:15 - Final Blow, Level 18 Upgrade & Chapter 16 Teaser

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📢 ENGAGEMENT:
{COMMENT_BAIT}

⚠️ DISCLAIMER & FAIR USE NOTICE:
This video provides transformative commentary, educational review, and narrative analysis under Section 107 of the Copyright Act 1976. All rights and credits belong to original creators: Chugong, Redice Studio, and D&C Media. No copyright infringement intended.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#SoloLeveling #SoloLevelingRagnarok #SungJinwoo #AnimeHindi #ManhwaExplained
"""

def main():
    print("\n" + "=" * 70)
    print("  🚀 SOLO LEVELING: RAGNAROK CHAPTER 15 YOUTUBE PUBLISHER")
    print("=" * 70)

    if not VIDEO_PATH.exists():
        print(f"❌ Error: Video file not found at {VIDEO_PATH}")
        sys.exit(1)

    info = probe(VIDEO_PATH)
    dur = float(info.get("format", {}).get("duration", 0.0))
    size_mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print(f"  🎬 Video File: {VIDEO_PATH.name} ({dur:.1f}s, {size_mb:.1f} MB)")
    print(f"  🖼️ Thumbnail:  {COVER_PATH.name if COVER_PATH.exists() else 'N/A'}")
    print(f"  🏷️ Title:      {TITLE}")

    # Initialize publisher
    publisher = YouTubePublisher()

    print("\n  Uploading to YouTube...")
    try:
        res = publisher.publish(
            video_path=str(VIDEO_PATH),
            title=TITLE,
            description=DESCRIPTION,
            tags=TAGS,
            thumbnail_path=str(COVER_PATH) if COVER_PATH.exists() else None,
            category_id="24",  # Entertainment
            privacy_status="public",
            comment_bait=COMMENT_BAIT
        )
        print(f"\n  ✅ Upload Successful! YouTube Video ID: {res.get('video_id')}")
        print(f"  🔗 Watch Link: https://www.youtube.com/watch?v={res.get('video_id')}")

        # Dispatch Discord Notification
        try:
            dn = DiscordNotifications()
            dn.send_embed(
                channel_id=DISCORD_CHANNEL,
                title="🔥 NEW EPISODE UPLOADED: SOLO LEVELING RAGNAROK CH 15",
                description=(
                    f"**{TITLE}**\n\n"
                    f"⏱️ **Duration**: {dur:.1f}s ({dur/60:.2f} mins)\n"
                    f"🔗 **YouTube Link**: https://www.youtube.com/watch?v={res.get('video_id')}\n"
                    f"💬 **Comments**: 100% ENABLED (Zero Comment Lock Compliant)"
                ),
                color=COLOR_SUCCESS
            )
            print("  ✓ Discord announcement dispatched!")
        except Exception as de:
            print(f"  ⚠️ Discord notice: {de}")

    except Exception as e:
        print(f"\n  ⚠️ Upload halted: {e}")
        print("  (Video is rendered locally and ready for staging or live publish upon approval.)")

if __name__ == "__main__":
    main()
