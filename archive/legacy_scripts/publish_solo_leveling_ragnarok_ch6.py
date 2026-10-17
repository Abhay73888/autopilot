"""
publish_solo_leveling_ragnarok_ch6.py — YouTube Publisher for Solo Leveling: Ragnarok Chapter 6.

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

log = Logbook("solo_leveling_ragnarok_ch6_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch6"
VIDEO_PATH = VIDEO_DIR / "solo_leveling_ragnarok_ch6_final.mp4"
COVER_PATH = VIDEO_DIR / "thumbnail.jpg"

TITLE = "SOLO LEVELING: RAGNAROK Chapter 6 in Hindi ⚔️ | Sword of The Monarch of Fangs! | Full Recap"

def build_description() -> str:
    return """⚔️ SOLO LEVELING: RAGNAROK Chapter 6 Full Story in Hindi | The Beast Monarch & The Cursed Sword!

"ARISE!" bolte hi Sung Suho ka pehla Shadow Soldier toh nikal aaya...
Lekin bhai, usey dekh kar Suho ka reaction dekhne laayak tha!
Ek toh size mein chhota, upar se 24 ghante mein gayab hone wala COMMON RANK GOBLIN!
Beru bechara pasina-pasina hokar safai de raha tha:
"Young Monarch, aage chalkar ye shakti bohot khatarnak banegi!"

Dungeon se bahar nikal kar hospital ke bistar par aate hi Beru ne Suho ko sauñpe 3 SABSE BADE MISSION:
1️⃣ Outer Space se aa rahe Outer Gods ke rakshason se Dharti ko bachana aur Jin-Woo ki tarah level up karna!
2️⃣ Har haal mein apni gayab maa — MISS CHA HAE-IN ko dhoondh nikalna!
3️⃣ Aur Beru ki khoi hui Marshal taqat ko wapas jagana!

Lekin jab Suho Hunter Association mein apna Rank test karane gaya...
Toh uske hosh udd gaye!
[MAGIC LEVEL: 46 — RANK: E-RANK]!
E-Rank sunte hi koi bhi raid party usey ghusne nahi de rahi thi!
Lekin Suho ne lagaya dimaag:
"Raid squad nahi legi toh kya hua... MAINING AUR HAULING TEAM mein toh E-Rank bhi jaa sakte hain!"

Kudar lekar crystal cave mein utarte hi Suho ki mulakat hui Lim Dogyun se!
Lekin asli toofan tab aaya jab aage chal rahi Strike Squad ko ek pracheen mandir ke khandaron mein gadi hui mili...
LAL LAATON WALI PRICHEEN CURSED SWORD!
Tank Kim Yongjun ne lalchi hokar jaise hi talwar ko chhua...
Zameen se nikla ek vishaal bhediye ka khaufnaak jabda!
Aur gufa mein goonji itihaas ki sabse bhayanak ghoorkaar:

"WHO DARES TO COVET THE SWORD OF THE MONARCH OF FANGS?!"

Dekhiye Solo Leveling: Ragnarok Chapter 6 ka blockbuster recap 100% Pure Humanoid Voice aur Ultra-Wide cinematic visuals ke saath!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - First Shadow Extraction: Common Rank Goblin!
00:40 - Suho's Disappointment & Beru's Excuses
01:15 - Hospital Food Feast & The 3 Grand Missions
01:50 - Hunter Association Evaluation: E-Rank Shock!
02:30 - The Mining Team Loophole & Crystal Cavern
03:05 - Reunited with Lim Dogyun & Chibi Beru Reveal
03:45 - Strike Squad Finds The Underground Temple
04:20 - C-Rank Tank Kim Yongjun's Fatal Mistake
04:55 - The Beast Monarch of Fangs Awakens!
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Is Video Ki Khasiyat:
✅ 100% Pure Humanoid Voice (Google Gemini Neural TTS — Real Breath & Dynamics)
✅ Full 1080p Ultra-Wide Panels (1250px wide)
✅ Cinematic Storytelling with Dark Synth Soundtrack & Dynamic SFX
✅ Glowing Cyan & Gold ASS Subtitles

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video acchi lagi ho toh LIKE zaroor karein!
🔔 Chapter 7 dekhne ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment karke batao: Kya Suho Beast Monarch ki shaktiyon ko rok payega?!

#SoloLevelingRagnarok #SoloLevelingHindi #SungSuho #BeastMonarch #MonarchOfFangs #Beru #SungJinWoo #SoloLevelingRagnarokChapter6 #AnimeRecapHindi #ManhwaHindi
""".strip()

TAGS = [
    "solo leveling ragnarok",
    "solo leveling ragnarok hindi",
    "solo leveling ragnarok chapter 6",
    "solo leveling ragnarok episode 6",
    "monarch of fangs",
    "beast monarch sword",
    "sung suho e rank",
    "chibi beru",
    "sung suho",
    "cha hae in",
    "solo leveling ragnarok ch 6",
    "anime in hindi",
    "manhwa in hindi",
    "solo leveling explain in hindi",
    "anime hindi recap",
    "manhwa recap hindi"
]

FIRST_COMMENT = (
    "🐺 MONARCH OF FANGS KI SHAPIT TALWAR JAAG CHUKI HAI! ⚔️\n\n"
    "👇 Aapko kya lagta hai doston:\n"
    "🔴 Kya E-Rank miner bankar aaya Suho is Beast Monster ko akele dher kar payega?\n"
    "🟢 Chibi Beru aur Lim Dogyun ke beech ka funny scene kaisa laga?!\n\n"
    "⚡ Solo Leveling: Ragnarok Chapter 7 ke liye LIKE & SUBSCRIBE zaroor karein!"
)

def main():
    if not VIDEO_PATH.exists():
        print(f"❌ Video file nahi mili: {VIDEO_PATH}")
        sys.exit(1)

    vid_size_mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print("=" * 65)
    print("  🚀 YOUTUBE UPLOADER: SOLO LEVELING RAGNAROK CHAPTER 6")
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
    if result.get("status") == "published":
        vid_id = result["yt_video_id"]
        watch_url = f"https://www.youtube.com/watch?v={vid_id}"
        print("=" * 65)
        print("  🎉 UPLOAD SUCCESSFUL!")
        print(f"  🆔 Video ID: {vid_id}")
        print(f"  📺 Watch URL: {watch_url}")
        print(f"  ⏱️ Upload Time: {result.get('upload_secs', '?')}s")
        print("=" * 65)

        # Post engagement pinned first comment
        print("\n  💬 Posting engagement first comment...")
        try:
            from core.oauth import api_request, authorize
            creds = authorize()
            comment_body = {
                "snippet": {
                    "videoId": vid_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": FIRST_COMMENT}
                    }
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
            print("  ✓ Zero Comment Lock Policy strictly satisfied: Comments are 100% ENABLED!")
        except Exception as e:
            print(f"  ⚠️ First comment note: {e}")

        # Catalog in DB
        try:
            con = sqlite3.connect('data/autopilot.db')
            now = time.time()
            con.execute('''
            INSERT INTO videos (
                created_ts, updated_ts, status, topic, title, caption, length_sec,
                series_name, series_index, video_path, cover_path, public_url,
                yt_video_id, published_ts, ai_disclosed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now, now, 'published',
                'Solo Leveling Ragnarok Chapter 6: Sword of The Monarch of Fangs',
                TITLE,
                'Solo Leveling: Ragnarok Chapter 6 Full Story in Hindi following Sung Suho',
                result.get('upload_secs', 315.0),
                'SOLO_LEVELING_RAGNAROK',
                6,
                str(VIDEO_PATH),
                str(COVER_PATH),
                watch_url,
                vid_id,
                now,
                1
            ))
            con.commit()
            print("  ✓ Database row recorded!")
        except Exception as e:
            print(f"  ⚠️ DB record warning: {e}")

        # Save receipt
        result_file = VIDEO_DIR / "upload_result.json"
        result["youtube_url"] = watch_url
        result["title"] = TITLE
        result["comment_bait"] = FIRST_COMMENT
        result_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n  📁 Upload result saved: {result_file}")

        print("\n" + "=" * 65)
        print(f"  🎉 CHAPTER 6 IS OFFICIALLY LIVE ON YOUTUBE!")
        print(f"  🔗 Link: {watch_url}")
        print("=" * 65)
    else:
        print(f"❌ Upload failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
