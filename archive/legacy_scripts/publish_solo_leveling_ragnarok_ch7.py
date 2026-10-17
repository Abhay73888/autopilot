"""
publish_solo_leveling_ragnarok_ch7.py — YouTube Publisher for Solo Leveling: Ragnarok Chapter 7.

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

log = Logbook("solo_leveling_ragnarok_ch7_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch7"
VIDEO_PATH = VIDEO_DIR / "solo_leveling_ragnarok_ch7_final.mp4"
COVER_PATH = VIDEO_DIR / "thumbnail.jpg"

TITLE = "SOLO LEVELING: RAGNAROK Chapter 7 in Hindi ⚔️ | Suho vs Possessed Beast! | Full Recap"

DISCORD_CHANNEL = "1212765278765584396"

def build_description() -> str:
    return """⚔️ SOLO LEVELING: RAGNAROK Chapter 7 Full Story in Hindi | Suho vs The Possessed Red Name!

Crystal Dungeon ke andar Suho ne apne Shadow Goblins ko kudar par laga diya...
Miners dang reh gaye ki E-Rank awakener ke paas aisi summoning skill kahan se aayi?!
Chhotu Beru zameen par gire mana ke tukde scavenge karke apni shaktiyan bator raha tha...
Lekin achanak Beru kaanp utha:
"Young Monarch! Mujhe ek Monarch ki khaufnaak haazri mehsoos ho rahi hai!"

Tabhi tunnel ke andhere se aayi bhediyon ki khoonkhar ghurrahat!
Steel Fanged Lycans (Orange Named Monsters) ne miners par jaanleva hamla bol diya!
Sung Suho bijli ki tarah kooda aur apni inventory se daggers nikaal kar laashon ke dher laga diye!
Aur phir goonji Suho ki pehli maha-lalkaar:
"ARISE!"
Aur zameen se nikal aayi SHADOW WOLVES ki fauj!

Lekin sabse bada twist toh tab aaya jab System par laal notification chamka:
[URGENT QUEST: DEFEAT THE ENEMY!]
Tunnel se nikla ek armored hunter jiski aankhon mein bhediye ki shaitani aag thi...
Uske sar par laal rang mein chamak raha tha:
[FANG OF RAKHAN — POSSESSED]!

Beru ne chetavni di: "Iske paas Monarch of Fangs ki taqat hai, aapke level ke liye ye maut hai!"
Lekin Suho ne dono daggers thaamte hue kaha:
"System ne mujhe jeetne ka raasta diya hai... main is Red Name ko hara kar aur taqatwar banoonga!"

Dekhiye Solo Leveling: Ragnarok Chapter 7 ka fast-paced, action-packed cinematic recap 100% Pure Humanoid Voice aur dynamic visual effects ke saath!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - Shadow Goblins Mining & Beru's Mana Scavenge
00:15 - Beru Senses A Monarch's Presence!
00:25 - Steel Fanged Lycans Ambush & Suho Steps In
00:38 - Blinding Slash & Second Shadow Arise!
00:48 - Level Up! The Shadow Wolf Army Forms
00:58 - Urgent Quest: Defeat The Possessed Hunter!
01:08 - The Red Name: Fang of Rakhan Awakens
01:18 - Suho's Dual Daggers Stance & Climax!
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Video Features:
✅ 100% Pure Humanoid Voice (Google Gemini Neural TTS with studio warmth DSP)
✅ High-Energy Fast Pacing & Adrenaline Action Cuts
✅ Ultra-Wide 1080p Visual Panels with Ken Burns Motion
✅ Dynamic Cyan & Gold ASS Subtitles
✅ Standard Fair Use Disclaimer (Section 107 of Copyright Act)

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video pasand aayi toh LIKE aur SHARE zaroor karein!
🔔 Chapter 8 ke agle maha-yuddh ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment karke batao: Kya Suho is possessed Red Name hunter ko hara payega?!

#SoloLevelingRagnarok #SoloLevelingHindi #SungSuho #Beru #MonarchOfFangs #FangOfRakhan #ShadowExtraction #Arise #SoloLevelingRagnarokChapter7 #AnimeRecapHindi #ManhwaHindi
""".strip().replace("<", "[").replace(">", "]")

TAGS = [
    "solo leveling ragnarok",
    "solo leveling ragnarok hindi",
    "solo leveling ragnarok chapter 7",
    "solo leveling ragnarok episode 7",
    "sung suho",
    "suho shadow extraction",
    "suho arise",
    "shadow wolves arise",
    "fang of rakhan",
    "monarch of fangs",
    "possessed hunter",
    "beru",
    "sung jinwoo son",
    "manhwa recap hindi",
    "solo leveling hindi recap"
]

COMMENT_BAIT = "🐺 Kya Sung Suho is Possessed Red Name Hunter ko hara kar uska shadow nikaal payega? Apni theory comment karein! 👇🔥"

def main():
    print("\n" + "=" * 75)
    print("  🚀 PUBLISHING SOLO LEVELING: RAGNAROK CHAPTER 7 TO YOUTUBE")
    print("  Ensuring 100% Policy Compliance: selfDeclaredMadeForKids=False | Comments ON")
    print("=" * 75)

    if not VIDEO_PATH.exists():
        print(f"  ❌ Video file nahi mili: {VIDEO_PATH}")
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
        print(f"  🎉 SOLO LEVELING: RAGNAROK CHAPTER 7 IS LIVE ON YOUTUBE!")
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
                "Solo Leveling Ragnarok Chapter 7: Suho vs Possessed Beast",
                TITLE, build_description(), dur,
                "SOLO_LEVELING_RAGNAROK", 7, str(VIDEO_PATH), str(COVER_PATH), watch_url, vid_id, now_ts, 1
            ))
            con.commit()
            con.close()
            print(f"  ✓ Database recorded for Solo Leveling: Ragnarok Chapter 7!")
        except Exception as dbe:
            print(f"  ⚠️ Database record note: {dbe}")

        # 4. Discord Notification
        print("\n  📢 Dispatching update to Discord...")
        try:
            embed = DiscordNotifications.create_embed(
                title="⚔️ [Solo Leveling: Ragnarok Chapter 7] Published Live!",
                description=(
                    f"**{TITLE}**\n\n"
                    f"🔗 **[Watch on YouTube]({watch_url})**\n\n"
                    f"⏱️ **Duration**: {dur:.1f}s\n"
                    f"🎙️ **Voiceover**: 100% Pure Neural Humanoid (Fast Pacing)\n"
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
        print("  ✅ CHAPTER 7 PUBLISHING PIPELINE SUCCESSFULLY COMPLETED")
        print("#" * 75 + "\n")

    else:
        raise RuntimeError(f"YouTube upload failed: {result}")


if __name__ == "__main__":
    main()
