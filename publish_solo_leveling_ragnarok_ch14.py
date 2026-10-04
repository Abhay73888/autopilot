"""
publish_solo_leveling_ragnarok_ch14.py — YouTube Publisher for Solo Leveling: Ragnarok Chapter 14.

POLICY COMPLIANCE (AGENTS.md):
  • Zero Comment Lock Policy: comments ALWAYS 100% ENABLED (ON)
  • selfDeclaredMadeForKids = False (MANDATORY)
  • privacyStatus = "public"
  • Engagement pinned first comment via commentThreads.insert
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

log = Logbook("solo_leveling_ragnarok_ch14_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch14"
VIDEO_PATH = VIDEO_DIR / "solo_leveling_ragnarok_ch14_final.mp4"
COVER_PATH = VIDEO_DIR / "thumbnail.jpg"

TITLE = "SOLO LEVELING: RAGNAROK Chapter 14 in Hindi ⚔️ | Suho Names Gray & Grim Reaper Guild Conspiracy! | Full Recap"

DISCORD_CHANNEL = "1212765278765584396"

COMMENT_BAIT = (
    "⚡ Sung Jinwoo ke purane dushmano aur Architect ke raaz ke baare mein Beru ka khulasa kaisa laga? "
    "Aur Grim Reaper Guild ke Lee Minsung ke paas jo 'STARDUST' crystal hai, kya wo seedhe Itarim se juda hai? "
    "Apni raye comment mein zaroor batayein! 👇"
)

TAGS = [
    "Solo Leveling",
    "Solo Leveling Ragnarok",
    "Solo Leveling Ragnarok Chapter 14",
    "Sung Suho",
    "Sung Jinwoo",
    "Shadow Monarch",
    "Fang Monarch",
    "Gray the Wolf",
    "Wolf Slaughterer",
    "Status Window",
    "Architect",
    "Grim Reaper Guild",
    "Lee Minsung",
    "Im Taegyu",
    "Woo Jinchul",
    "Stardust Stimulant",
    "Itarim",
    "Beru",
    "Manhwa Hindi Recap",
    "Anime Recap in Hindi",
    "Solo Leveling Hindi",
    "anime recap hindi",
    "manhwa recap hindi",
    "action manhwa hindi",
    "sung jinwoo son"
]

def build_description() -> str:
    return """⚔️ SOLO LEVELING: RAGNAROK Chapter 14 Full Story in Hindi | Suho Names Gray & Grim Reaper Guild Conspiracy!

Hyena Brocky ke khatme ke baad, Sung Suho ne Fang ke vanshaj ko di nayi azaadi aur naya aashiyana!
Beru ne khulaasa kiya ki Outer Gods (Itarim) ke Apostles zameen par faile hue hain, aur Brocky ki laash ko nigalkar uski yaadein nikaalne ka anokha plan banaya!

Suho ne Fang ke waris ko Shadow Dungeon ki sanctuary mein laakar naam diya: "GRAY"!
Aur dharohar ke taur par forest ko ghoshit kiya Fang's Territory!
Gray ne aate hi khaufnaak raftaar se jangal ke monsters ka shikaar kiya, aur Suho ko mila naya khitaab:
[TITLE: WOLF SLAUGHTERER (+40% Stats Against Beast Monsters)]!

Iske baad Beru ne khola Sung Jinwoo ke zamane ka sabse khaufnaak raaz:
Kaisi thi Architect ki saazish Jinwoo ki aatma ko mitaakar use sirf ek vessel banane ki, aur kaise Jinwoo ne system ke iraadon ko ulat kar khud Shadow Monarch ka taaj jeeta!
Suho ne kholi apni Level 16 Status Window, aur sankalp liya ki sabhi Monarch Heirs ko dhoondh kar wo ek din apne Mata-Pita se zaroor milega!

Lekin tabhi Beru ne lauta kar bomb phoda:
Brocky ko chalane wale koi gair-mulki monster nahi, balki Seoul ki ek top human guild ke log the:
"GRIM REAPER GUILD"!

Penthouse ke andhere mein Grim Reaper Guild ka Vice-CEO aur A-Rank Hunter Lee Minsung, S-Rank Hunter Im Taegyu se bhid gaya!
Aur Lee Minsung ke haath mein chamak utha ek rahasyamayi baingani crystal:
[HUNTER AWAKENING STIMULANT: "STARDUST"]!
Jiske andar qaid hai Itarim ki khaufnaak laal aankhon wali aatma!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - Aftermath of Brocky's Defeat & The Itarim Question
00:35 - Beru's Gluttony Memory Devour Plan
01:10 - Inviting the Fang's Heir to the Shadow Sanctuary
01:45 - Naming the Wolf: Meet "GRAY"!
02:20 - Designating the Fang's Territory in the Shadow Dungeon
02:55 - Gray's First Monster Hunt & Title: Wolf Slaughterer (+40% vs Beasts)
03:30 - The Architect's Secret Scheme & Sung Jinwoo's Triumph
04:05 - Suho's Level 16 Status Window & Beru's Memory Extraction
04:35 - Grim Reaper Guild Conspiracy & Lee Minsung's Stardust Stimulant!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⚖️ COPYRIGHT & FAIR USE DISCLAIMER:
Under Section 107 of the Copyright Act 1976, allowance is made for "fair use" for purposes such as criticism, commentary, news reporting, teaching, scholarship, and research.
Original Story by Chugong & Daul | Art Adaptation by Dangdo & REDICE Studio / D&C Media.
This video provides transformative narrative recap, original voice acting, lore analysis, and educational storytelling in Hindi.

━━━━━━━━━━━━━━━━━━━━━━━━━━
#SoloLeveling #SoloLevelingRagnarok #SungSuho #SungJinwoo #ShadowMonarch #AnimeRecapHindi #ManhwaRecap
"""

def register_in_db() -> int:
    db = DB()
    series_name = "SOLO_LEVELING_RAGNAROK"
    series_index = 14

    existing = db.q(
        "SELECT id, status, yt_video_id FROM videos WHERE series_name = ? AND series_index = ?",
        (series_name, series_index)
    )

    if existing:
        vid_id = existing[0]["id"]
        db.update_video(
            vid_id,
            title=TITLE,
            caption="Solo Leveling: Ragnarok Chapter 14 full recap in Hindi.",
            video_path=str(VIDEO_PATH),
            cover_path=str(COVER_PATH),
            status="approved",
            notes="Ready for Chapter 14 publication"
        )
        print(f"  ✓ Updated existing Video #{vid_id} in DB to 'approved'")
    else:
        vid_id = db.create_video(
            topic="Solo Leveling: Ragnarok Chapter 14",
            title=TITLE,
            caption="Solo Leveling: Ragnarok Chapter 14 full recap in Hindi.",
            video_path=str(VIDEO_PATH),
            cover_path=str(COVER_PATH),
            status="approved"
        )
        db.q(
            "UPDATE videos SET series_name = ?, series_index = ?, length_sec = 270.0 WHERE id = ?",
            (series_name, series_index, vid_id)
        )
        print(f"  ✓ Created new Video #{vid_id} in DB as 'approved'")

    db.close()
    return vid_id

def publish_video(vid_id: int):
    print("\n" + "=" * 75)
    print("  🚀 PUBLISHING SOLO LEVELING: RAGNAROK CHAPTER 14 TO YOUTUBE")
    print(f"  Video ID: #{vid_id}")
    print(f"  Title   : {TITLE}")
    print("  Policy  : selfDeclaredMadeForKids=False | Comments=ON | Public")
    print("=" * 75 + "\n")

    pub = YouTubePublisher()
    desc = build_description()

    res = pub.upload_file(
        path=VIDEO_PATH,
        title=TITLE,
        description=desc,
        tags=TAGS,
        privacy="public",
        thumbnail=COVER_PATH,
        category="24"
    )

    yt_id = res.get("yt_video_id")
    if not yt_id:
        raise RuntimeError(f"Upload failed: {res}")

    url = f"https://www.youtube.com/watch?v={yt_id}"
    print(f"\n✅ Video Live on YouTube: {url} (ID: {yt_id})")

    # Post Pinned First Comment
    try:
        print(f"📌 Posting first comment bait: '{COMMENT_BAIT[:60]}...'")
        from core.oauth import api_request
        API = "https://www.googleapis.com/youtube/v3"
        api_request(
            pub.creds,
            f"{API}/commentThreads?part=snippet",
            method="POST",
            body={
                "snippet": {
                    "videoId": yt_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": COMMENT_BAIT}
                    }
                }
            }
        )
        print("  ✓ First comment posted successfully!")
    except Exception as e:
        print(f"  ⚠️ First comment note: {e}")

    # Update DB
    db = DB()
    db.update_video(
        vid_id,
        yt_video_id=yt_id,
        status="published",
        notes=f"Live on YouTube: {url}"
    )
    db.close()

    # Discord Notification
    try:
        from core.discord_service import send_embed, COLOR_SUCCESS
        embed = {
            "title": f"⚔️ SOLO LEVELING: RAGNAROK CHAPTER 14 IS LIVE!",
            "description": f"**{TITLE}**\n\nFull chapter recap in Hindi is now live on YouTube!\n\n▶️ **Watch Now**: {url}",
            "color": COLOR_SUCCESS,
            "fields": [
                {"name": "📺 YouTube URL", "value": f"[Watch Video]({url})", "inline": True},
                {"name": "⏱️ Duration", "value": "4.50 Minutes (270.2s)", "inline": True},
                {"name": "🐺 Franchise", "value": "Solo Leveling: Ragnarok (Ch 14)", "inline": True},
                {"name": "🛡️ Comments Status", "value": "100% ENABLED (Zero Lock Policy)", "inline": False},
                {"name": "💎 Story Highlights", "value": "• Suho recruits Fang's Heir & names him Gray\n• Designating Fang's Territory in Shadow Dungeon\n• Title: Wolf Slaughterer (+40% vs Beasts)\n• Beru reveals Architect's plot against Sung Jinwoo\n• Level 16 Status Window\n• Grim Reaper Guild & Lee Minsung's Stardust Stimulant", "inline": False}
            ],
            "footer": {"text": "AUTOPILOT Autonomous Swarm · Chapter 14 Broadcast"}
        }
        send_embed(embed, channel_id=DISCORD_CHANNEL)
        print("  ✓ Discord announcement dispatched!")
    except Exception as e:
        print(f"  ⚠️ Discord note: {e}")

    return yt_id, url

def main():
    if not VIDEO_PATH.exists():
        print(f"❌ Video not found at {VIDEO_PATH}")
        sys.exit(1)

    vid_id = register_in_db()
    yt_id, url = publish_video(vid_id)

    print("\n" + "=" * 75)
    print("  🎉 CHAPTER 14 PRODUCTION & PUBLISHING COMPLETE!")
    print(f"  ▶️ URL: {url}")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
