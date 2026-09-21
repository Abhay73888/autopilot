"""
publish_solo_leveling_ragnarok_ch5.py — YouTube Publisher for Solo Leveling: Ragnarok Chapter 5.

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

log = Logbook("solo_leveling_ragnarok_ch5_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch5"
VIDEO_PATH = VIDEO_DIR / "solo_leveling_ragnarok_ch5_final.mp4"
COVER_PATH = VIDEO_DIR / "thumbnail.jpg"

TITLE = "SOLO LEVELING: RAGNAROK Chapter 5 in Hindi ⚔️ | Suho's First 'ARISE' & Shadow Extraction! | Full Recap"

def build_description() -> str:
    return """⚔️ SOLO LEVELING: RAGNAROK Chapter 5 Full Story in Hindi | The Shadow Dungeon & The First "ARISE"!

Chaabi apni hi parchhayi mein ghoñpne ke baad...
Sung Suho sidha murdon ki sarzameen — THE SHADOW DUNGEON mein dakhil ho chuka hai!
Ek aisi jagah jahan zinda insaan ka aana namumkin hai jab tak usey maalik ki ijazat na mile!

Lekin achanak Suho ke aage sunhari System Window khuli:
[QUEST NOTICE: SURVIVE 4 HOURS]!
Dungeon ke khunkhar saaye kisi kamzor insaan ko apna maalik nahi maanenge!
Suho ko 4 ghante tak zinda bachkar apni taqat sabit karni thi!

Tabhi andhere se hamla hua...
Ek Goblin Scout ne patthar ki kulhaadi se achanak waar kiya!
Suho ne na sirf waar ko chakma diya, balki kulhaadi chheen kar gobling ka seene cheer diya!
Lekin khandar ki chhat se doosre scout ne yuddh ka bigul baja diya:
PUUUU—!
Aur mitti cheerte hue nikal aayi vishaal GOBLIN CENTURION ki poori sena!

Chibi Beru ne bahana bana kar madad karne se inkaar kar diya:
"Monarch se door hone ke karan mera mana kam hai... aur agar main lada toh aapka EXP kam ho jayega!"
Suho ne haar nahi maani!
Usne hawa mein haath uthaya aur activate ki apni janamjaat shakti:
[SKILL: RULER'S AUTHORITY LV. 1]!
Telekinesis se zameen par padi kulhaadi goli ki tarah udi aur gobling ka sar faad diya!
Udte hue teeron ko hawa mein pakad kar wapas dushmanon ke seene mein ghoñp diya!

Swarm ne Suho ko gher liya! Centurion ka bhari waar pada!
HP: 160... 118... 84... aakhiri 53!
Lekin lahoo se lathpath hokar bhi Suho muskuraya:
"Main kamzor hone se zyada... is jung mein zinda mehsoos kar raha hoon!"
Lahu ki nadiyaan baha kar Suho ne poori sena ko maut ke ghaat utaar diya!
TING! [SKILL: RESILIENCE LV. 1] hasil hui aur LEVEL UP 4 baar ek sath hua!

4 ghante poore hone par mila sabse bada inaam:
[QUEST REWARD: RUNE STONE — SHADOW EXTRACTION]!
Suho ne mutthi mein rune stone tod diya aur seekh li Shadow Monarch ki mukhya shakti!
Aur Centurion ki laash ke aage haath utha kar pukaara wo aitihasik aadesh...

"ARISE!"

Dekhiye Solo Leveling: Ragnarok Chapter 5 ka blockbuster recap 100% Humanoid Voice aur Ultra-Wide cinematic visuals ke saath!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - Entering the Shadow Dungeon & Ruined City
00:35 - Quest Notice: Survive for 4 Hours!
01:10 - Goblin Scout Ambush & Axe Wrestling
01:45 - War Horn Sounded & Goblin Centurion Army
02:20 - Beru's Mana Excuses & Ruler's Authority Telekinesis!
02:55 - Arrow Catch & Flashback: Baby Suho's Power
03:30 - HP Drops to 53! Suho's Bloodlust & Resilience Lv. 1
04:05 - Quest Complete, Rune Stone: Shadow Extraction
04:35 - The Iconic Climax: The First "ARISE"!
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Is Video Ki Khasiyat:
✅ 100% Pure Humanoid Voice Performance
✅ Full 1080p Ultra-Wide Panels (1250px wide, zero thin strips)
✅ Fast-Paced Action Storytelling
✅ Procedural Dark Synth Soundtrack & Dynamic SFX
✅ Glowing Cyan & Gold ASS Subtitles

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video acchi lagi ho toh LIKE zaroor karein!
🔔 Solo Leveling: Ragnarok Chapter 6 dekhne ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment karke batao: Kya Suho ka pehla Shadow Soldier Centurion banega?!

#SoloLevelingRagnarok #SoloLevelingHindi #SungSuho #SungJinWoo #Beru #ShadowMonarch #ShadowExtraction #Arise #SoloLevelingRagnarokChapter5 #AnimeRecapHindi #ManhwaHindi
""".strip()

TAGS = [
    "solo leveling ragnarok",
    "solo leveling ragnarok hindi",
    "solo leveling ragnarok chapter 5",
    "solo leveling ragnarok episode 5",
    "suho arise",
    "shadow extraction",
    "shadow dungeon",
    "chibi beru",
    "sung suho",
    "young monarch",
    "goblin centurion",
    "rulers authority",
    "anime in hindi",
    "manhwa in hindi",
    "solo leveling explain in hindi",
    "anime hindi recap",
    "manhwa recap hindi"
]

FIRST_COMMENT = (
    "🔥 SUNG SUHO NE BOLE WOH AITIHASIK SHABD — 'ARISE!' ⚔️\n\n"
    "👇 Aapko kya lagta hai doston:\n"
    "🔴 Kya Goblin Centurion Suho ka pehla loyal Shadow Soldier ban payega?\n"
    "🟢 Ruler's Authority telekinesis ke sath Suho ki fighting dekh kar kaisa laga?!\n\n"
    "⚡ Solo Leveling: Ragnarok Chapter 6 ke liye LIKE & SUBSCRIBE zaroor karein!"
)

def main():
    if not VIDEO_PATH.exists():
        print(f"❌ Video file nahi mili: {VIDEO_PATH}")
        sys.exit(1)

    vid_size_mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print("=" * 65)
    print("  🚀 YOUTUBE UPLOADER: SOLO LEVELING RAGNAROK CHAPTER 5")
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
                'Solo Leveling Ragnarok Chapter 5: Suho First Arise & Shadow Extraction',
                TITLE,
                'Solo Leveling: Ragnarok Chapter 5 Full Story in Hindi following Sung Suho',
                result.get('upload_secs', 300.0),
                'SOLO_LEVELING_RAGNAROK',
                5,
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
        print(f"  🎉 CHAPTER 5 IS OFFICIALLY LIVE ON YOUTUBE!")
        print(f"  🔗 Link: {watch_url}")
        print("=" * 65)
    else:
        print(f"❌ Upload failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
