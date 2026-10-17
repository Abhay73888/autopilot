"""
publish_solo_leveling_ragnarok_ch2.py — YouTube Publisher for Solo Leveling: Ragnarok Chapter 2.

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

log = Logbook("solo_leveling_ragnarok_ch2_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch2"
VIDEO_PATH = VIDEO_DIR / "final.mp4"
COVER_PATH = VIDEO_DIR / "cover.jpg"

TITLE = "SOLO LEVELING: RAGNAROK Chapter 2 in Hindi ⚔️ | Suho Ka Maha-Awaken | Full Recap"

def build_description() -> str:
    return """⚔️ SOLO LEVELING: RAGNAROK Chapter 2 Full Story in Hindi | The Player Awakens!

Sung Suho ke saamne ruk gaya waqt!
System ka sunehra aadesh goonja: "Aapne secret quest 'COURAGE OF THE WEAK' poori kar li hai... Kya aap PLAYER banna chahte hain?"

Suho ne bina dare kaha: "ACCEPT!"
Aur tabhi phati sunehri roshni — Kandiaru ka aashirwaad, Longevity effect, aur legendary STATUS WINDOW khul gaya!
Active Skill: RULER'S AUTHORITY Lv. 1 (Sung Jin-Woo ki wahi telekinesis shakti)!

Suho ne nange haathon se ek-ek shot mein Mist Burn monsters ko uda diya!
Lekin D-Rank Demon Boss ne uski chaati par zaharile panje maare... par Longevity ne zahar ko pal bhar mein mita diya!
Suho ne saare stat points Strength mein jhonk diye — STRENGTH 11 se seedha 19!
Aur phir maara ek zameen-faad Finishing Punch jisne monster ke core ko chaknachoor kar diya!

Lekin aakhir mein campus par gira ek naya aazaab — C-RANK AWAKENED MIST BURN!
Dekhiye Solo Leveling Ragnarok Chapter 2 ki poori kahani Humanoid Voice aur 1080p cinematic animation ke saath!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - The Game Dream & Father Sung Jin-Woo
00:50 - Fire Extinguisher Charge & Mana Beast
01:30 - TIME STOPS! The System Invitation
02:15 - Kandiaru's Blessing & Status Window
02:55 - One-Punch Knockout on Mist Burn
03:40 - D-Rank Boss Attack & Longevity Poison Cure
04:30 - Stat Allocation: Strength 19!
05:15 - The Ground-Shattering Finishing Punch!
06:00 - Triple Level Up & Awakener Victory
06:35 - C-Rank Mist Burn Lands! Cliffhanger!
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Is Video Ki Khasiyat:
✅ Humanoid Voice Performance (Real Human-Like Hindi Delivery)
✅ Sliced High-Resolution Webtoon Panels with Dynamic Ken Burns Scroll
✅ Balanced 1.18x Anime Storytelling Pacing
✅ Procedural 3-Track Score + Custom SFX (Time Freeze, System Chime, Mega Punch)
✅ 1080p Full HD with Styled Cyan & Gold Subtitles

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video pasand aayi ho toh LIKE zaroor karein!
🔔 Chapter 3 ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment mein batao — kya Suho C-Rank Demon ko akele hara payega?

#SoloLevelingRagnarok #SoloLevelingHindi #SungSuho #SungJinWoo #SoloLevelingRagnarokChapter2 #AnimeRecapHindi #ManhwaHindi #RulersAuthority #ShadowMonarch
""".strip()

TAGS = [
    "solo leveling ragnarok",
    "solo leveling ragnarok hindi",
    "solo leveling ragnarok chapter 2",
    "solo leveling ragnarok episode 2",
    "sung suho",
    "sung jin woo",
    "anime in hindi",
    "manhwa in hindi",
    "solo leveling explain in hindi",
    "manhwa recap hindi",
    "anime recap hindi",
    "solo leveling ragnarok manhwa",
    "rulers authority",
    "courage of the weak",
    "status window solo leveling",
    "shadow monarch",
    "solo leveling sequel",
    "solo leveling ragnarok full story",
    "anime hindi recap"
]

FIRST_COMMENT = (
    "🔥 SUNG SUHO KA STATUS WINDOW DEKH KAR AAPKO KAISA LAGA?\n\n"
    "👇 Comment mein batao:\n"
    "🔴 RULER'S AUTHORITY — Papa ki shakti bete mein aa gayi, ab tabahi machegi!\n"
    "🟢 STRENGTH 19 — Abhi se itna overpowered, aage kya hoga?!\n\n"
    "⚔️ Solo Leveling: Ragnarok Chapter 3 ke liye LIKE & SUBSCRIBE thok do!"
)

def main():
    if not VIDEO_PATH.exists():
        print(f"❌ Video file nahi mili: {VIDEO_PATH}")
        sys.exit(1)

    vid_size_mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print("=" * 65)
    print("  🚀 YOUTUBE UPLOADER: SOLO LEVELING RAGNAROK CHAPTER 2")
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
        yt_id = result["yt_video_id"]
        url = f"https://www.youtube.com/watch?v={yt_id}"
        print("=" * 65)
        print("  🎉 UPLOAD SUCCESSFUL!")
        print(f"  📺 YouTube URL: {url}")
        print(f"  ⏱️ Upload Time: {result.get('upload_secs', '?')}s")
        print("=" * 65)

        # Post pinned first comment
        print("\n💬 Posting pinned first comment (comment bait)...")
        try:
            from core.oauth import api_request, authorize
            creds = authorize()
            comment_body = {
                "snippet": {
                    "videoId": yt_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": FIRST_COMMENT}
                    }
                }
            }
            api_request(
                creds,
                "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
                method="POST",
                body=comment_body
            )
            print("  ✅ First comment posted successfully!")
        except Exception as e:
            print(f"  ⚠️ Comment post warning: {e}")

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
                'Solo Leveling Ragnarok Chapter 2: The Player Awakens',
                TITLE,
                'Solo Leveling: Ragnarok Chapter 2 Full Story in Hindi following Sung Suho',
                result.get('upload_secs', 390.0),
                'SOLO_LEVELING_RAGNAROK',
                2,
                str(VIDEO_PATH),
                str(COVER_PATH),
                url,
                yt_id,
                now,
                1
            ))
            con.commit()
            print("  ✓ Database row recorded!")
        except Exception as e:
            print(f"  ⚠️ DB record warning: {e}")

        # Save receipt
        result_file = VIDEO_DIR / "upload_result.json"
        result["youtube_url"] = url
        result["title"] = TITLE
        result["comment_bait"] = FIRST_COMMENT
        result_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n📁 Upload result saved: {result_file}")
    else:
        print(f"❌ Upload failed: {result}")

if __name__ == "__main__":
    main()
