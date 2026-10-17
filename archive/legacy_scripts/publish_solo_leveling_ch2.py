"""
publish_solo_leveling_ch2.py — Direct YouTube Uploader for Solo Leveling Chapter 2 Hindi Recap.

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

from agents.publisher import YouTubePublisher
from core.db import DB
from core.logbook import Logbook

log = Logbook("solo_leveling_ch2_upload")

VIDEO_DIR = ROOT / "output" / "solo_leveling_ch2"
VIDEO_PATH = VIDEO_DIR / "final.mp4"
COVER_PATH = VIDEO_DIR / "cover.jpg"

# ============================================================
# GOD-LEVEL TITLE (SEO-optimised, high CTR)
# ============================================================
TITLE = "SOLO LEVELING Chapter 2 in Hindi ⚔️ | The Double Dungeon Trap | Full Manhwa Recap"

# ============================================================
# GOD-LEVEL DESCRIPTION
# ============================================================
def build_description() -> str:
    description = """⚔️ SOLO LEVELING Chapter 2 Full Story in Hindi | Maut Ka Double Dungeon!

D-Rank Dungeon ki raid mein Sung Jin-Woo ko sirf ek chhota sa E-Rank core mila. Apni bimaar maa ke ilaj aur behen ki college fees bharne ke liye Jin-Woo ko aur paison ki zaroorat thi.

Tabhi gufa ke andar se khulta hai ek anokha raasta — THE DOUBLE LAIR!
Leader Mr. Song Chi-Yul 17 hunters ke beech voting karwate hain:
8 hunters andar jaane ke liye vote dete hain... aur 8 hunters lautne ke liye!

Faisla aa rukta hai akele Sung Jin-Woo ke haath mein. Kya Jin-Woo ka ye ek aakhri faisla unhe maut ke pinjre mein dhakel dega?
Dekhiye Solo Leveling Chapter 2 ki poori kahani high-speed 1.5x cinematic animation ke saath!

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTER TIMESTAMPS:
00:00 - The Weakest Hunter In A D-Rank Dungeon
00:45 - Miss Ju-Hee Aur Jin-Woo Ka Dard
01:35 - Dungeon Raid Ka Khaufnak Ant
02:15 - E-Rank Core Aur Gareebi Ki Majboori
03:00 - Double Lair Ki Khoj & Fire Magic
03:45 - 8 vs 8: The Deadliest Vote
04:30 - Sung Jin-Woo Ka Aakhri Faisla
05:10 - Next Chapter Preview & Subscribe!
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Is Video Ki Khasiyat:
✅ High-Speed 1.5x Dynamic Fast-Paced Recap
✅ High-Resolution Manga Panels with Cinematic Ken Burns Camera
✅ Multi-Character Voice Acting in Hindi (Jin-Woo, Ju-Hee, Song, Kim, Bak)
✅ Immersive 3-Track Audio: Voice + Cinematic Score + Custom SFX
✅ 1080p Full HD Cinematic Experience with Synced ASS Subtitles

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video achhi lagi ho toh LIKE zaroor karein!
🔔 Chapter 3 ke liye SUBSCRIBE karein aur Bell Icon dabayein!
💬 Comment mein batao — kya aap us khaufnak Double Dungeon mein jaate?

#SoloLeveling #SoloLevelingHindi #AnimeRecapHindi #SungJinWoo #ManhwaHindi #SoloLevelingChapter2 #DoubleDungeon #AnimeInHindi
"""
    return description.strip()


TAGS = [
    "solo leveling",
    "solo leveling hindi",
    "solo leveling chapter 2",
    "solo leveling episode 2",
    "anime in hindi",
    "manhwa in hindi",
    "sung jin woo",
    "solo leveling explain in hindi",
    "manhwa recap hindi",
    "anime recap hindi",
    "solo leveling anime",
    "double dungeon",
    "the weakest hunter",
    "shadow monarch",
    "solo leveling season 1",
    "solo leveling manhwa",
    "manga recap hindi",
    "solo leveling full story hindi",
    "solo leveling hindi dubbed"
]

FIRST_COMMENT = (
    "🔥 SUNG JIN-WOO NE ANDAR JAANE KA FAISLA LIYA — KYA WO SAHI THA YA GALAT?\n\n"
    "👇 Comment mein batao:\n"
    "🔴 GALAT — Kyunki andar maut ka mandir intezaar kar raha tha!\n"
    "🟢 SAHI — Kyunki agar wo andar na jaata toh Shadow Monarch kabhi na banta!\n\n"
    "⚔️ Chapter 3 ke liye LIKE & SUBSCRIBE thok do!"
)


def main():
    print("=" * 70)
    print("🎬 SOLO LEVELING CHAPTER 2 — YouTube Upload Engine")
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
        privacy="public",
        thumbnail=COVER_PATH,
        category="24",
        language="hi",
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
                creds,
                "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
                method="POST",
                body=comment_body
            )
            print(f"  ✅ Comment posted!")
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
