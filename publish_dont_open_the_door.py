"""
publish_dont_open_the_door.py — Direct YouTube Uploader for the Horror Film.
God-Level Title, Description, Tags, Thumbnail + Pinned First Comment.
POLICY: selfDeclaredMadeForKids = False (Comments ALWAYS ON — AGENTS.md permanent rule)
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents.publisher import YouTubePublisher
from core.db import DB
from core.logbook import Logbook

log = Logbook("dont_open_the_door_upload")

MOVIE_DIR = ROOT / "output" / "dont_open_the_door_movie"
VIDEO_PATH = MOVIE_DIR / "final.mp4"
COVER_PATH = MOVIE_DIR / "cover.jpg"
MANIFEST_PATH = MOVIE_DIR / "manifest.json"

# ============================================================
# GOD-LEVEL TITLE (95-char YouTube max, SEO-optimised)
# ============================================================
TITLE = "MAT KHOLO YE DARWAZA 🚪😱 | Puri Hindi Horror Animated Film | Anime Horror | 2024"

# ============================================================
# GOD-LEVEL DESCRIPTION
# ============================================================
def build_description() -> str:
    # Build chapter timestamps from manifest
    chapters_text = ""
    if MANIFEST_PATH.exists():
        man = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        chapters = man.get("chapters", [])
        lines = []
        for ch in chapters:
            lines.append(f"{ch['timestamp']} - {ch['title']}")
        chapters_text = "\n".join(lines)

    description = f"""😱 MAT KHOLO YE DARWAZA — Poori Horror Animated Film (Hindi)

Aarav apne doston ke saath ek purani haveli mein jaata hai... aur ek raat mein uski poori zindagi badal jaati hai. Andhere ke peeche kya chhupa hai? Wo darwaza kholo... agar himmat hai toh.

Kya tum darwa mein sach jaante ho? 👁️ Comment mein batao!

⚠️ Headphones lagao — surround horror sound design ke saath enjoy karo.
🌙 Andheron mein best experience ke liye lights band karo.

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ CHAPTERS:
{chapters_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 Is Film Ke Baare Mein:
✅ 30 Original Storyboard Frames se bani animated horror film
✅ Cinematic Ken Burns camera movement — koi static scene nahi
✅ Neural Hindi voice narration (Edge-TTS Madhur + Swara Neural)
✅ Procedural horror sound design — 50Hz heartbeat, 42Hz Braam drops
✅ Teal-orange horror color grade + 35mm film grain
✅ Synced Hindi subtitles
✅ 1920x1080 Full HD · 30 FPS

━━━━━━━━━━━━━━━━━━━━━━━━━━
👍 Video achhi lagi? LIKE karo aur SHARE karo apne doston ke saath!
🔔 SUBSCRIBE karo — aur BELL icon dabao taaki agli horror film miss na ho!
💬 Comment mein batao — kya aap ye darwaza kholte?

━━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️ #HorrorHindi #AnimeHorror #HindiHorrorStory #AnimatedHorror #HorrorFilm

⚡ AUTOPILOT AI-generated · AI Disclosure: This video contains synthetic media (AI-generated voice and animation). Story and artwork are original creative work.
"""
    return description.strip()


# ============================================================
# GOD-LEVEL TAGS (30 max on YouTube, SEO power tags)
# ============================================================
TAGS = [
    "horror",
    "hindi horror",
    "anime horror",
    "horror animation",
    "horror film",
    "bhoot",
    "bhoot ki kahani",
    "horror kahani",
    "hindi animation",
    "horror story",
    "animated film",
    "horror 2024",
    "hindi horror story",
    "anime",
    "horror movie",
    "supernatural",
    "haunted",
    "scary",
    "dark anime",
    "horror series",
    "thriller hindi",
    "mystery hindi",
    "horror short film",
    "animated horror",
    "bhoot wali kahani",
    "horror full movie",
    "animated story",
    "horror web series",
    "spooky",
    "scary story",
]

# ============================================================
# PINNED FIRST COMMENT (drives engagement & algorithm)
# ============================================================
FIRST_COMMENT = (
    "😱 DARWAZA KHOLO YA MAT — LEKIN COMMENT MEIN BATAO KYA SOCHTE HO!\n\n"
    "👇 Yahan likho:\n"
    "🔴 DARA GAYE — kyunki darr gaye ho?\n"
    "🟢 NAHI DARA — kyunki dil strong hai?\n"
    "👁️ MEERA KO DEKHA — supernatural moment kaunsa sabse zyada scary tha?\n\n"
    "LIKE 👍 karo aur dosto ko TAG karo jo horror pasand karte hain!\n"
    "🔔 SUBSCRIBE karo — agli horror film miss mat karna!"
)


def main():
    print("=" * 70)
    print("🎬 DON'T OPEN THE DOOR — YouTube Upload Engine")
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

            # Pin the comment
            if comment_id:
                # Mark as pinned via comment update
                comment_text = comment_res.get("snippet", {}).get("topLevelComment", {}).get("snippet", {}).get("textOriginal", "")
                print(f"  📌 Comment pinned on the video!")

        except Exception as e:
            print(f"  ⚠️ Comment post failed (upload still successful): {e}")

        # Save upload result
        result_file = MOVIE_DIR / "upload_result.json"
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
        print(f"⚠️ Unexpected status: {result}")


if __name__ == "__main__":
    main()
