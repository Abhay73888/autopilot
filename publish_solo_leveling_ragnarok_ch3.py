"""
publish_solo_leveling_ragnarok_ch3.py — YouTube Publisher for Solo Leveling: Ragnarok Chapter 3.

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

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from agents.publisher import YouTubePublisher
from core.db import DB
from core.logbook import Logbook

log = Logbook("solo_leveling_ragnarok_ch3_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch3"
VIDEO_PATH = VIDEO_DIR / "solo_leveling_ragnarok_ch3_hindi.mp4"
COVER_PATH = VIDEO_DIR / "thumbnail.jpg"

TITLE = "SOLO LEVELING: RAGNAROK Chapter 3 in Hindi ⚔️ | Beru Ki Wapsi: Young Monarch | Full Recap"

def build_description() -> str:
    return """⚔️ SOLO LEVELING: RAGNAROK Chapter 3 Full Story in Hindi | Beru's Return!

Korea University of Arts par toota aazaab!
D-Rank Gate achanak Dungeon Break mein badal chuka tha aur association ka C-Rank Tank Hunter 'Kim Jongsu' is mist se infect ho gaya!
Uski vishaal kaali talwaar building ki concrete deewaron ko makkhan ki tarah kaat rahi thi!

Sung Suho ne dekha ki teen bebas ladkiyan khidki ke paas phas gayi hain!
Bina apni jaan ki parwah kiye, Suho ne mid-air dive maari aur superhuman fight shuru ho gayi!
Lekin C-Rank monster ke lohe jaise punches ne Suho ki haddiyan tod di!
System ka alert chamka: [HP: 1 / 140] aur [FATIGUE: 99]!

Suho zameen par bebas pada tha... aur monster ne apni giant sword dono haathon se upar utha li!
Jaise hi talwaar girne wali thi... BOOOOOOM!
Zameen phat gayi, ek vishaal kaala shadow panja nikal kar talwaar ko dhar dabochta hai!
Aur andhere se goonjti hai ek dahad:
"TUM TUCCH KEEDE... HAMARE YUVRAJ KO HAATH LAGANE KI JURRAT KAISE HUI?!"

SHADOW ANT KING — BERU IS BACK!
Beru ne palak jhapakte hi C-Rank monster ke hazaaron tukde kar diye aur Suho ke aage ghutne tek kar kaha:
"IT HAS BEEN A WHILE... YOUNG MONARCH."

Dekhiye Solo Leveling: Ragnarok Chapter 3 ki poori kahani Humanoid Voice aur 1080p Ultra-Wide animation ke saath!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - Dungeon Break & Rooftop Soldiers in Despair
00:42 - C-Rank Tank Hunter Kim Jongsu Infected!
01:25 - Suho Meets the Giant Awakened Mist Burn
02:05 - 3 Girls Trapped & Suho's Mid-Air Tackle!
02:50 - Fist vs Blade & HP 1 / 140 Critical State!
03:30 - Fatigue 99 & The Falling Execution Blade!
04:05 - KABOOM! The Black Talon of the Ant King!
04:35 - BERU'S FURY: "How Dare You Harm His Highness?!"
05:00 - Beru Kneels Before Suho: "Young Monarch..."
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Is Video Ki Khasiyat:
✅ 1080p Ultra-Wide Screen Panels (No thin images, bold 1250px framing)
✅ Humanoid Gemini Voice Performance (Real Emotional Hindi Delivery)
✅ Balanced Pacing (Strictly within 4-5 minute recap duration)
✅ Procedural Dark Synth Score & Realistic Sound Effects
✅ Styled Cyan & Gold ASS Subtitles

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video pasand aayi ho toh LIKE zaroor karein!
🔔 Solo Leveling: Ragnarok Chapter 4 ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment mein batao — Beru ki wapsi dekh kar kaisa laga?!

#SoloLevelingRagnarok #SoloLevelingHindi #SungSuho #Beru #ShadowMonarch #YoungMonarch #SoloLevelingRagnarokChapter3 #AnimeRecapHindi #ManhwaHindi
""".strip()

TAGS = [
    "solo leveling ragnarok",
    "solo leveling ragnarok hindi",
    "solo leveling ragnarok chapter 3",
    "solo leveling ragnarok episode 3",
    "beru",
    "beru solo leveling",
    "beru returns",
    "sung suho",
    "young monarch",
    "shadow monarch",
    "anime in hindi",
    "manhwa in hindi",
    "solo leveling explain in hindi",
    "manhwa recap hindi",
    "anime recap hindi",
    "solo leveling ragnarok manhwa",
    "solo leveling ragnarok full story",
    "anime hindi recap"
]

FIRST_COMMENT = (
    "🔥 BERU KI WAPSI DEKH KAR AAPKO KAISA LAGA?!\n\n"
    "👇 Comment mein batao:\n"
    "🔴 'YOUNG MONARCH' sunkar goosebumps aa gaye!\n"
    "🟢 Beru ne ek second mein C-Rank monster ke tukde kar dale, absolute GOAT!\n\n"
    "⚔️ Solo Leveling: Ragnarok Chapter 4 ke liye LIKE & SUBSCRIBE thok do!"
)

def main():
    if not VIDEO_PATH.exists():
        print(f"❌ Video file nahi mili: {VIDEO_PATH}")
        sys.exit(1)

    vid_size_mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print("=" * 65)
    print("  🚀 YOUTUBE UPLOADER: SOLO LEVELING RAGNAROK CHAPTER 3")
    print(f"  📁 File: {VIDEO_PATH.name} ({vid_size_mb:.1f} MB)")
    print(f"  🎬 Title: {TITLE}")
    print(f"  🖼️ Cover: {COVER_PATH.name} (exists={COVER_PATH.exists()})")
    print("=" * 65)

    pub = YouTubePublisher(db=DB())
    description = build_description()

    print("\n  📤 Uploading to YouTube (public, comments ON, selfDeclaredMadeForKids=False)...")
    result = pub.upload_file(
        path=VIDEO_PATH,
        title=TITLE,
        description=description,
        tags=TAGS,
        privacy="public",
        thumbnail=COVER_PATH if COVER_PATH.exists() else None,
        category="24",
        language="hi",
    )

    print()
    if not result.get("ok"):
        print(f"  ❌ Upload fail hua: {result.get('error')}")
        sys.exit(1)

    vid_id = result.get("video_id")
    watch_url = result.get("watch_url", f"https://www.youtube.com/watch?v={vid_id}")
    print(f"  ✅ Upload SUCCESSFUL!")
    print(f"  🆔 Video ID: {vid_id}")
    print(f"  🔗 Watch URL: {watch_url}")

    # Post engagement pinned first comment
    print("\n  💬 Posting engagement first comment...")
    try:
        service = pub._get_service()
        cmt_res = service.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": vid_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": FIRST_COMMENT
                        }
                    }
                }
            }
        ).execute()
        cmt_id = cmt_res.get("id")
        print(f"  ✓ First comment posted (id: {cmt_id})")
        print("  ✓ Zero Comment Lock Policy strictly satisfied: Comments are 100% ENABLED!")
    except Exception as e:
        print(f"  ⚠️ First comment note: {e}")

    print("\n" + "=" * 65)
    print(f"  🎉 CHAPTER 3 IS OFFICIALLY LIVE ON YOUTUBE!")
    print(f"  🔗 Link: {watch_url}")
    print("=" * 65)


if __name__ == "__main__":
    main()
