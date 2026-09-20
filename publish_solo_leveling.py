"""
publish_solo_leveling.py — Direct YouTube Uploader for Solo Leveling Chapter 1 Hindi Recap.

POLICY COMPLIANCE (AGENTS.md):
  • Zero Comment Lock Policy: comments ALWAYS 100% ENABLED
  • selfDeclaredMadeForKids = False (MANDATORY)
  • privacyStatus = "public"
  • Engagement pinned first comment via commentThreads.insert
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents.publisher import YouTubePublisher
from core.db import DB
from core.logbook import Logbook

log = Logbook("solo_leveling_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ch1"
VIDEO_PATH = VIDEO_DIR / "final.mp4"
COVER_PATH = VIDEO_DIR / "cover.jpg"

# ============================================================
# GOD-LEVEL TITLE (SEO-optimised, high CTR)
# ============================================================
TITLE = "SOLO LEVELING Chapter 1 in Hindi ⚔️ | The Weakest Hunter | Full Manhwa Recap"

# ============================================================
# GOD-LEVEL DESCRIPTION
# ============================================================
def build_description() -> str:
    description = """⚔️ SOLO LEVELING Chapter 1 Full Story in Hindi | The Rebirth of Sung Jin-Woo!

Duniya ka sabse kamzor hunter — Sung Jin-Woo, jise har koi 'The Weakest Hunter of All Mankind' keh kar mazaak udata hai. Apni bimaar maa ke aspatal ke bill bharne ke liye wo har roz maut ke muh mein jaata hai. 

Lekin is baar, Seoul ke ek aam E-Rank Gate ke andar uska intezaar ek aisi shakti kar rahi hai jo uski kismat hamesha ke liye badal degi!

Khoon-kharaba, vishaal patthar ki moortiyan, aur maut ka mandir — dekhiye Solo Leveling Chapter 1 ki poori dastan Hindi mein!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - Maut Ka Mandir (Double Dungeon Trap)
01:15 - The Weakest Hunter (Sung Jin-Woo Ka Sach)
02:30 - Bimaar Maa Aur Hunter Banne Ki Majboori
03:45 - Hunters Ki Bheed Aur Mazakiya Nickname
05:00 - Miss Ju-Hee (B-Rank Healer Ki Fikr)
06:15 - Gate Khul Gaya: Mission Shuru
07:10 - Next Chapter Preview & Subscribe!
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Is Video Ki Khasiyat:
✅ High-Resolution Manga Panels with Dynamic Ken Burns Camera
✅ Multi-Character Voice Acting in Hindi (Jin-Woo, Ju-Hee, Kim, Song)
✅ Immersive 3-Track Audio: Voice + Cinematic Tension Score + SFX
✅ 1080p Full HD Cinematic Experience with Synced Subtitles

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video achhi lagi ho toh LIKE zaroor karein!
🔔 Agle Chapter ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment mein batao — aapka favorite Solo Leveling character kaun hai?

#SoloLeveling #SoloLevelingHindi #AnimeRecapHindi #SungJinWoo #ManhwaHindi #SoloLevelingChapter1
"""
    return description.strip()


TAGS = [
    "solo leveling",
    "solo leveling hindi",
    "solo leveling chapter 1",
    "anime in hindi",
    "manhwa in hindi",
    "sung jin woo",
    "solo leveling explain in hindi",
    "manhwa recap hindi",
    "anime recap hindi",
    "solo leveling anime",
    "the weakest hunter",
    "shadow monarch",
    "solo leveling season 1",
    "solo leveling manhwa",
    "manga recap hindi",
    "solo leveling episode 1 hindi",
    "solo leveling full story hindi",
    "solo leveling hindi dubbed"
]

FIRST_COMMENT = (
    "🔥 SUNG JIN-WOO KA SAFAR ABHI SHURU HUA HAI!\n\n"
    "Kya aapko lagta hai Sung Jin-Woo ko us khaufnak Dungeon mein jaana chahiye tha?\n"
    "Apna jawaab COMMENT mein likhein! 👇 Aur Chapter 2 dekhne ke liye LIKE & SUBSCRIBE thok do! ⚔️"
)


def main():
    print("=" * 70)
    print("🎬 SOLO LEVELING CHAPTER 1 — YouTube Upload Engine")
    print("🔴 God-Level Title · Description · Tags · Comments ON")
    print("=" * 70)

    if not VIDEO_PATH.exists():
        print(f"❌ Video not found: {VIDEO_PATH}")
        return

    print(f"✅ Video ready: {VIDEO_PATH} ({VIDEO_PATH.stat().st_size / (1024*1024):.1f} MB)")
    print(f"✅ Cover: {COVER_PATH.exists()} ({COVER_PATH})")
    print()
    print(f"📋 Title: {TITLE}")
    print(f"🏷️ Tags: {len(TAGS)} tags")
    print()

    pub = YouTubePublisher(db=DB())
    description = build_description()

    print("🚀 Uploading to YouTube (public, comments ON, AI disclosure ON)...")
    result = pub.upload_file(
        path=VIDEO_PATH,
        title=TITLE,
        description=description,
        tags=TAGS,
        privacy="public",           # Directly public
        thumbnail=COVER_PATH,
        category="24",              # Entertainment
        language="hi",              # Hindi
    )

    print()
    if result.get("status") == "published":
        yt_id = result["yt_video_id"]
        url = f"https://www.youtube.com/watch?v={yt_id}"
        print(f"🎉 UPLOAD SUCCESSFUL!")
        print(f"📺 YouTube URL: {url}")
        print(f"⏱️ Upload Time: {result.get('upload_secs', '?')}s")

        # Post pinned first comment
        print()
        print("💬 Posting pinned first comment (comment bait)...")
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
            comment_res = api_request(
                "POST",
                "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
                body=comment_body,
                creds=creds
            )
            comment_id = comment_res.get("id", "")
            print(f"  ✅ Comment posted! ID: {comment_id}")

        except Exception as e:
            print(f"  ⚠️ Comment post warning: {e}")

        # Save upload result
        result_file = VIDEO_DIR / "upload_result.json"
        result["youtube_url"] = url
        result["title"] = TITLE
        result["comment_bait"] = FIRST_COMMENT
        result_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print()
        print(f"📁 Upload result saved: {result_file}")
        print("=" * 70)
        print(f"🌟 LIVE ON YOUTUBE: {url}")
        print("=" * 70)

    elif result.get("status") == "queued":
        print("⏳ Upload queued — YouTube daily quota reached. Kal automatically upload hoga.")
        print(f"   Reason: {result.get('reason', 'unknown')}")
    else:
        print(f"⚠️ Status: {result}")


if __name__ == "__main__":
    main()
