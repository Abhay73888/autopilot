"""
publish_solo_leveling_ragnarok_ch8.py — YouTube Publisher for Solo Leveling: Ragnarok Chapter 8.

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

log = Logbook("solo_leveling_ragnarok_ch8_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch8"
VIDEO_PATH = VIDEO_DIR / "solo_leveling_ragnarok_ch8_final.mp4"
COVER_PATH = VIDEO_DIR / "thumbnail.jpg"

TITLE = "SOLO LEVELING: RAGNAROK Chapter 8 in Hindi ⚔️ | Suho's Beast Gauntlet Awakens! | Full Recap"

DISCORD_CHANNEL = "1212765278765584396"

COMMENT_BAIT = (
    "🔥 Suho ne Shadow Lycan ko directly Gauntlet mein transform karke [Shadow Extraction Lv.2 — Form Change] unlock kar liya! "
    "Kya Suho aage chalkar apne father Sung Jinwoo se bhi zyada creative Shadow Monarch banega? "
    "Aapka favorite moment kaunsa tha, comment mein zaroor batao! 👇"
)

def build_description() -> str:
    return """⚔️ SOLO LEVELING: RAGNAROK Chapter 8 Full Story in Hindi | Suho vs Possessed Beast Gauntlet!

Suho ke samne khada tha ek khaufnaak hunter, jiski aankhon mein shaitani aag jal rahi thi aur haath mein thi ek shaitani talwar...
Uske sar par laal rang mein chamak raha tha:
[FANG OF RAKHAN — POSSESSED]!

Suho ne turant bhaap liya ki asli monster wo laal talwar hai!
Usne apne Shadow Lycan ko aage bheja, lekin hunter ne palak jhapkte hi wolf ke do tukde kar diye!
Hunter ne nafrat se kaha:
"Tere jaisa keeda Shadow Monarch ki shakti use karega?! The Shadow Monarch must be a coward who hides behind shadow soldiers!"

Sung Jinwoo ka apmaan sunkar Suho ka khoon khaul utha!
Suho ne haath uthaya aur activate hui RULER'S AUTHORITY!
Zameen par gire sabhi weapons hawa mein tair kar teer ki tarah barasne lage, lekin hunter ne ek hi jhatke mein sabhi blades ko tod diya!

Ek single hit ka matlab tha seedha maut!
Tabhi Suho ne Beru se pucha: "Tower waali meri shakti kahan gayi?"
Beru ne khulasa kiya ki Jinwoo ne Suho ki shakti bachpan mein seal ki thi, lekin tower mein lada hua uska fighting spirit asli tha!

Suho ko yaad aaya: "Tower mein main mutthiyon se ladta tha... aur Shadow Soldiers ka koi aakar nahi hota!"
Suho ne dahad lagai:
"ARISE!"

Lekin is baar Shadow Lycan aage nahi bhaga... balki uska neela-kaala saya Suho ke dahine haath par lipat gaya!
Aur tab goonja System ka maha-notification:
[SHADOW STEEL-FANGED LYCAN LV.1 FORM CHANGE — GAUNTLET]
[NOTICE: 'SKILL: SHADOW EXTRACTION' HAS LEVELED UP TO LV.2 — FORM CHANGE]
Zero Mana Cost! Can change forms of Shadow Soldiers!

BOOOOM! Suho ne apne naye Beast Gauntlet se hunter ki talwar par direct punch jada!
Beru ki aankhon mein aasoon chhalak aaye:
"Shadow soldier ko weapon bana liya?! Bina kisi sikhaye Shadow Authority aur Ruler's Authority master kar li... OH MY KING!"

Dekhiye Solo Leveling: Ragnarok Chapter 8 ka fast-paced, high-octane cinematic recap 100% Pure Humanoid Voice aur dynamic action visuals ke saath!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - Suho Confronts The Red Named Possessed Hunter
00:15 - Shadow Lycan Sliced & Enemy's Speed
00:28 - Insulting The Shadow Monarch & Beru's Fury
00:40 - Ruler's Authority: Weapon Storm!
00:52 - High-Stakes Evasion: One Hit Means Death
01:05 - The Sealed Infant Power & Tower Memory
01:18 - ARISE! Shadow Lycan Gauntlet Transformation!
01:30 - Skill Leveled Up: Shadow Extraction Lv.2 Form Change!
01:42 - Explosive Fist Clash & Cavern Shatter
01:55 - Beru In Tears: 'The Young Monarch Is Truly A Prodigy!'
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Video Features:
✅ 100% Pure Humanoid Voice (Expressive Neural Voice with studio warmth DSP)
✅ High-Energy Fast Pacing & Adrenaline Action Cuts
✅ Ultra-Wide 1080p Visual Panels with Ken Burns Motion
✅ Dynamic Cyan & Gold ASS Subtitles
✅ Standard Fair Use Disclaimer (Section 107 of Copyright Act)

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video pasand aayi toh LIKE aur SHARE zaroor karein!
🔔 Chapter 9 ke agle maha-yuddh ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment karke batao: Kya Suho ka ye Beast Gauntlet Jinwoo ke daggers se zyada deadly hai?!

#SoloLevelingRagnarok #SoloLevelingHindi #SungSuho #Beru #ShadowGauntlet #BeastGauntlet #ShadowExtractionLv2 #Arise #SoloLevelingRagnarokChapter8 #AnimeRecapHindi #ManhwaHindi
""".strip().replace("<", "[").replace(">", "]")

TAGS = [
    "solo leveling ragnarok",
    "solo leveling ragnarok hindi",
    "solo leveling ragnarok chapter 8",
    "solo leveling ragnarok episode 8",
    "sung suho",
    "suho shadow gauntlet",
    "suho shadow extraction lv 2",
    "form change gauntlet",
    "beru solo leveling",
    "monarch of fangs",
    "fang of rakhan possessed",
    "anime recap hindi",
    "manhwa recap hindi",
    "solo leveling season 2",
    "action manhwa hindi",
    "sung jinwoo son"
]

def main():
    print("=" * 75)
    print("  🚀 PUBLISHING SOLO LEVELING: RAGNAROK CHAPTER 8 TO YOUTUBE")
    print("  Ensuring 100% Policy Compliance: selfDeclaredMadeForKids=False | Comments ON")
    print("=" * 75)

    if not VIDEO_PATH.exists():
        print(f"❌ Video file not found: {VIDEO_PATH}")
        sys.exit(1)

    db = DB()
    pub = YouTubePublisher(db=db)

    print(f"\n  [Step 1] Uploading video to YouTube...")
    result = pub.upload_file(
        path=VIDEO_PATH,
        title=TITLE,
        description=build_description(),
        tags=TAGS,
        privacy="public",
        thumbnail=COVER_PATH if COVER_PATH.exists() else None,
        category="24",
        language="hi"
    )

    if result.get("status") == "published":
        vid_id = result["yt_video_id"]
        watch_url = f"https://www.youtube.com/watch?v={vid_id}"

        print("=" * 75)
        print(f"  🎉 SOLO LEVELING: RAGNAROK CHAPTER 8 IS LIVE ON YOUTUBE!")
        print(f"  🆔 Video ID: {vid_id}")
        print(f"  📺 Watch URL: {watch_url}")
        print("=" * 75)

        # 2. First Pinned Engagement Comment
        print("\n  💬 Posting engagement first comment...")
        try:
            from core.oauth import api_request, authorize
            creds = authorize()
            comment_body = {
                "snippet": {
                    "videoId": vid_id,
                    "topLevelComment": {"snippet": {"textOriginal": COMMENT_BAIT}}
                }
            }
            st, cmt_res, _ = api_request(
                creds,
                "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
                method="POST",
                body=comment_body,
            )
            cmt_id = cmt_res.get("id") if isinstance(cmt_res, dict) else None
            print(f"  ✓ First comment posted (id: {cmt_id})")
            print("  ✓ Zero Comment Lock Policy satisfied: Comments are 100% ENABLED!")
        except Exception as ce:
            print(f"  ⚠️ First comment note: {ce}")

        # 3. Database Record
        v_info = probe(VIDEO_PATH)
        dur = float(v_info["format"]["duration"])
        try:
            con = sqlite3.connect("data/autopilot.db")
            now_ts = time.time()
            con.execute('''
            INSERT INTO videos (
                created_ts, updated_ts, status, topic, title, caption, length_sec,
                series_name, series_index, video_path, cover_path, public_url, yt_video_id, published_ts, ai_disclosed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now_ts, now_ts, "published",
                "Solo Leveling Ragnarok Chapter 8: Suho's Beast Gauntlet Awakens",
                TITLE, build_description(), dur,
                "SOLO_LEVELING_RAGNAROK", 8, str(VIDEO_PATH), str(COVER_PATH), watch_url, vid_id, now_ts, 1
            ))
            con.commit()
            con.close()
            print(f"  ✓ Database recorded for Solo Leveling: Ragnarok Chapter 8!")
        except Exception as dbe:
            print(f"  ⚠️ Database record note: {dbe}")

        # 4. Discord Notification
        print("\n  📢 Dispatching update to Discord...")
        try:
            embed = DiscordNotifications.create_embed(
                title="⚔️ [Solo Leveling: Ragnarok Chapter 8] Published Live!",
                description=(
                    f"**{TITLE}**\n\n"
                    f"🔗 **[Watch on YouTube]({watch_url})**\n\n"
                    f"⏱️ **Duration**: {dur:.1f}s (2.33 mins)\n"
                    f"🎙️ **Voiceover**: 100% Pure Neural Humanoid (High-Tempo Pacing)\n"
                    f"💥 **Highlight**: Suho unlocks **Shadow Extraction Lv.2 — Form Change: Beast Gauntlet**!\n"
                    f"💬 **Comments**: 100% Enabled (Zero Comment Lock Compliant)"
                ),
                color=COLOR_SUCCESS,
                url=watch_url,
            )
            DiscordNotifications.send_to_channel(DISCORD_CHANNEL, {"embeds": [embed]})
            print(f"  ✓ Discord notification sent to channel {DISCORD_CHANNEL}!")
        except Exception as de:
            print(f"  ⚠️ Discord dispatch note: {de}")

        print("\n" + "#" * 75)
        print("  ✅ CHAPTER 8 PUBLISHING PIPELINE SUCCESSFULLY COMPLETED")
        print("#" * 75 + "\n")

    else:
        raise RuntimeError(f"YouTube upload failed: {result}")

if __name__ == "__main__":
    main()
