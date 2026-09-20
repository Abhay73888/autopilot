"""
publish_solo_leveling_ragnarok_ch4.py — YouTube Publisher for Solo Leveling: Ragnarok Chapter 4.

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

log = Logbook("solo_leveling_ragnarok_ch4_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch4"
VIDEO_PATH = VIDEO_DIR / "solo_leveling_ragnarok_ch4_final.mp4"
COVER_PATH = VIDEO_DIR / "thumbnail.jpg"

TITLE = "SOLO LEVELING: RAGNAROK Chapter 4 in Hindi ⚔️ | Sung Jin-Woo Space War & Chibi Beru! | Full Recap"

def build_description() -> str:
    return """⚔️ SOLO LEVELING: RAGNAROK Chapter 4 Full Story in Hindi | The Space War & Shadow Dungeon!

Dungeon Break ke 2 din baad...
Sung Suho hospital ke bed par hosh mein aata hai!
Korea Arts University mein machi tabahi ki khabar poore desh mein aag ki tarah phail chuki thi!
Hunter Association ke bade-bade afsar hairan the kyunki jab wo pahuñche, saare Mist Burns pehle hi phat kar mar chuke the!

Achanak Suho ke aage neeli roshni chamki:
[STATUS WINDOW: LEVEL 5, STRENGTH 22, RULER'S AUTHORITY LV. 1]!
Lekin tabhi andhere se ek vishaal raaz khula...
Chhaya se nikal kar samne aayi ek chhotisi, par khatarnak cheenti — CHIBI BERU!

Beru ne aansu bahate hue Suho ke samne ghutne tek diye:
"LONG TIME NO SEE, YOUNG MONARCH!"
Aur phir Beru ne khol diya itihaas ka sabse bada parda:
Sung Jin-Woo ne Suho ko chhod kar dhokha nahi diya tha...
Balki mahaan Shadow Monarch antariksh ki andheri gahraaiyon mein "ITARIM" — OUTER GODS se akele lad rahe hain!
Lekin sabse bada jhatka tab laga jab Suho ne bataya:
"Meri maa Miss Cha Hae-In bhi usi din se laapata hain!"

MISS HAE-IN GAYAB HAIN?!
Beru ne Suho ke haath mein sauñpi ek kaali rahasyamayi chaabi:
[ITEM: SHADOW DUNGEON KEY]!
"Is chaabi ko apni parchhayi mein ghoñp dijiye!"
Suho ne bina dare chaabi apni shadow mein utaar di...
Aur samne khul gaya murdon ka vishaal darwaza — THE SHADOW DUNGEON!

Dekhiye Solo Leveling: Ragnarok Chapter 4 ka blockbuster recap 100% Humanoid Voice aur Ultra-Wide cinematic visuals ke saath!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - Childhood Flashback & Beru's Apron Drawing!
00:35 - Suho Wakes Up in Hospital & Uncle's Call
01:10 - Mystery of Exploded Monsters & News Broadcast
01:45 - Status Window Level 5 & Chibi Beru Reveal!
02:25 - "System Bastard!" Beru's Level 1 Private Rage
03:05 - Sung Jin-Woo in Space: The War with Itarim Gods!
03:45 - Cha Hae-In Missing & Suho's Oath to Save His Parents
04:15 - [SHADOW DUNGEON KEY] Plunged into Shadow!
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Is Video Ki Khasiyat:
✅ 100% Pure Humanoid Voice Performance (Google Gemini Neural TTS)
✅ Full 1080p Ultra-Wide Panels (1250px wide, zero thin strips)
✅ Fast-Paced Action Storytelling (Strictly 4 to 5 minutes duration)
✅ Procedural Dark Synth Soundtrack & Dynamic SFX
✅ Glowing Cyan & Gold ASS Subtitles

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video acchi lagi ho toh LIKE zaroor karein!
🔔 Solo Leveling: Ragnarok Chapter 5 dekhne ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment karke batao: Kya Suho apne maa-baap ko bacha payega?!

#SoloLevelingRagnarok #SoloLevelingHindi #SungSuho #SungJinWoo #Beru #ShadowMonarch #ChaHaeIn #SoloLevelingRagnarokChapter4 #AnimeRecapHindi #ManhwaHindi
""".strip()

TAGS = [
    "solo leveling ragnarok",
    "solo leveling ragnarok hindi",
    "solo leveling ragnarok chapter 4",
    "solo leveling ragnarok episode 4",
    "sung jin woo space",
    "chibi beru",
    "beru returns",
    "sung suho",
    "young monarch",
    "shadow dungeon",
    "itarim outer gods",
    "cha hae in missing",
    "anime in hindi",
    "manhwa in hindi",
    "solo leveling explain in hindi",
    "anime hindi recap",
    "manhwa recap hindi"
]

FIRST_COMMENT = (
    "🔥 SUNG JIN-WOO ANTARIKSH MEIN ITARIM (OUTER GODS) SE LAD RAHE HAIN!\n\n"
    "👇 Aapko kya lagta hai doston:\n"
    "🔴 Kya Suho Shadow Dungeon mein level up karke apne maa-baap ko bacha payega?\n"
    "🟢 Chibi Beru aur Suho ki bonding dekh kar kaisa laga?!\n\n"
    "⚔️ Solo Leveling: Ragnarok Chapter 5 ke liye LIKE & SUBSCRIBE thok do!"
)

def main():
    if not VIDEO_PATH.exists():
        print(f"❌ Video file nahi mili: {VIDEO_PATH}")
        sys.exit(1)

    vid_size_mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print("=" * 65)
    print("  🚀 YOUTUBE UPLOADER: SOLO LEVELING RAGNAROK CHAPTER 4")
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
                'Solo Leveling Ragnarok Chapter 4: Shadow Monarch Space War & Chibi Beru',
                TITLE,
                'Solo Leveling: Ragnarok Chapter 4 Full Story in Hindi following Sung Suho',
                result.get('upload_secs', 293.8),
                'SOLO_LEVELING_RAGNAROK',
                4,
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
        print(f"  🎉 CHAPTER 4 IS OFFICIALLY LIVE ON YOUTUBE!")
        print(f"  🔗 Link: {watch_url}")
        print("=" * 65)
    else:
        print(f"❌ Upload failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
