"""
publish_solo_leveling_ragnarok_ch1.py — Direct YouTube Uploader for Solo Leveling: Ragnarok Chapter 1.

POLICY COMPLIANCE (AGENTS.md):
  • Zero Comment Lock Policy: comments ALWAYS 100% ENABLED (ON)
  • selfDeclaredMadeForKids = False (MANDATORY)
  • privacyStatus = "public"
  • Engagement pinned first comment via commentThreads.insert
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from agents.publisher import YouTubePublisher
from core.db import DB
from core.logbook import Logbook

log = Logbook("solo_leveling_ragnarok_ch1_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch1"
VIDEO_PATH = VIDEO_DIR / "final.mp4"
COVER_PATH = VIDEO_DIR / "cover.jpg"

# ============================================================
# TITLE (SEO-optimised, high CTR)
# ============================================================
TITLE = "SOLO LEVELING: RAGNAROK Chapter 1 in Hindi ⚔️ | Jin-Woo Ke Bete Ka Jaadu | Full Recap"

# ============================================================
# DESCRIPTION
# ============================================================
def build_description() -> str:
    description = """⚔️ SOLO LEVELING: RAGNAROK Chapter 1 Full Story in Hindi | The Shadow Prince Awakens!

Sung Jin-Woo ke baad ab shuru hoti hai unke bete — SUNG SUHO ki kahani!
Outer Gods (Supreme Beings) ne bramhand ke shatranj par kabza karne ke liye anant yudh chhed diya hai kyunki is dimension ka maalik mar chuka hai.

Duniya do hisson mein bat chuki hai: Awakened aur Non-Awakened.
Suho Seoul Arts University mein ek aam student ki tarah painting bana raha tha... aur anjaane mein usne Shadow Ant King BERU ka chitra bana diya!

Tabhi campus ke D-Rank Gate se ek khunkhar Blue Flame Monster nikal kar class ke andar kood padta hai!
Ek ladki zameen par gidgida rahi hai... aur aam insaan hone ke baawajood Suho haath mein Fire Extinguisher lekar monster se bhid jaata hai!

Aur tabhi... hawa mein chamakta hai legendary golden alert:
"YOU HAVE MET ALL REQUIREMENTS TO COMPLETE THE SECRET QUEST: COURAGE OF THE WEAK."

Dekhiye Solo Leveling Ragnarok Chapter 1 ki poori kahani ultra-cinematic 1080p animation ke saath!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - Outer Gods & The Cosmic Chessboard
00:45 - Sung Suho & High School Bully Lee Eunchul
01:30 - Bully Ka Awaken Hona & Locker Smash
02:15 - Two Years Later: Arts University & D-Rank Gate
03:00 - Society Divided: Ants vs Awakened Hunters
03:45 - Missing Parents: Jin-Woo & Cha Hae-In
04:15 - Subconscious Memory: Ant King Beru Sketch!
04:50 - Hunter Kim's Demonic Blue Flame Mutation
05:30 - Classroom Terror: Glass Shatter!
06:10 - Fire Extinguisher Strike & Courage of the Weak!
06:50 - The System Returns & Subscribe for Chapter 2!
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Is Video Ki Khasiyat:
✅ 10x Cinematic Visuals: Sliced High-Definition Webtoon Panels with Smooth Ken Burns Scroll
✅ Perfect Balanced Anime Recap Pacing (1.18x)
✅ Multi-Character Hindi Performance with Flawless Phonetics
✅ Immersive 3-Track Audio: Voice + Solo Leveling Procedural Score + Custom SFX
✅ 1080p Full HD Cinematic Experience with Synced ASS Subtitles

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video achhi lagi ho toh LIKE zaroor karein!
🔔 Chapter 2 ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment mein batao — kya Sung Suho apne papa Sung Jin-Woo se bhi zyada powerful ban payega?

#SoloLevelingRagnarok #SoloLevelingHindi #SungSuho #SungJinWoo #AnimeRecapHindi #ManhwaHindi #SoloLevelingRagnarokChapter1 #AnimeInHindi #ShadowMonarch
"""
    return description.strip()


TAGS = [
    "solo leveling ragnarok",
    "solo leveling ragnarok hindi",
    "solo leveling ragnarok chapter 1",
    "solo leveling ragnarok episode 1",
    "sung suho",
    "sung jin woo",
    "anime in hindi",
    "manhwa in hindi",
    "solo leveling explain in hindi",
    "manhwa recap hindi",
    "anime recap hindi",
    "solo leveling ragnarok manhwa",
    "outer gods solo leveling",
    "courage of the weak",
    "shadow monarch",
    "beru shadow monarch",
    "solo leveling sequel",
    "solo leveling ragnarok full story",
    "anime hindi recap"
]

FIRST_COMMENT = (
    "🔥 KYA SUNG SUHO APNE PAPA SUNG JIN-WOO SE BHI ZYADA KHATARNAK BANEGA?\n\n"
    "👇 Comment mein vote karo:\n"
    "🔴 HAAN — Kyunki wo Shadow Monarch aur Cha Hae-In dono ka beta hai!\n"
    "🟢 NAHI — Kyunki Sung Jin-Woo ki barabari bramhand mein koi nahi kar sakta!\n\n"
    "⚔️ Solo Leveling: Ragnarok Chapter 2 ke liye LIKE & SUBSCRIBE thok do!"
)


def main():
    if not VIDEO_PATH.exists():
        print(f"❌ Video file nahi mili: {VIDEO_PATH}")
        sys.exit(1)

    vid_size_mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print("=" * 65)
    print("  🚀 YOUTUBE UPLOADER: SOLO LEVELING RAGNAROK CHAPTER 1")
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

        # Save upload result
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
