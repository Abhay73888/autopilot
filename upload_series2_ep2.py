#!/usr/bin/env python3
"""
upload_series2_ep2.py — Upload Version 1 (Video #166) to YouTube Shorts (Public).
With high-suspense call-to-action in caption and pinned comment as requested by user.
"""

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

# Fix Windows terminal UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.db import DB
from agents.publisher import YouTubePublisher

VID = 166

TITLE = "Raat Ke 2 Baje Meera Ka Message Aaya... 💬❤️ | JAB PYAAR ONLINE THA (Ep 2) #Shorts"
CAPTION = (
    "Lockdown ne sabko kamron mein qaid kiya tha... par hum dono ek doosre ki aadat ban chuke the. "
    "2020 ki sabse masoom aur emotional online love story. ❤️\n\n"
    "Aage kya hua dekhne ke liye COMMENT karein: 'PART 3' ya 'NEXT'! 👇✨"
)
COMMENT_BAIT = "Aage dekhne ke liye abhi COMMENT karein 'PART 3'! Kya Aarav aur Meera kabhi lockdown ke baad mil payenge? 👇❤️"
HASHTAGS = ["#JabPyaarOnlineTha", "#Series2", "#Episode2", "#Shorts", "#Romance", "#LoveStory", "#ShortsFeed"]

def main():
    print("\n" + "=" * 70)
    print(f"  🚀 UPLOADING SERIES 2 EPISODE 2 (VIDEO #{VID}) TO YOUTUBE SHORTS (PUBLIC)")
    print("=" * 70)

    db = DB()
    row = db.get_video(VID)
    if not row:
        print(f"❌ Video #{VID} not found in database.")
        sys.exit(1)

    script_data = json.loads(row["script_json"] or "{}")
    script_data["title"] = TITLE
    script_data["caption"] = CAPTION
    script_data["comment_bait"] = COMMENT_BAIT
    script_data["hashtags"] = HASHTAGS

    db.update_video(
        VID,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        script_json=script_data,
        status="approved"
    )

    out_dir = Path(row["video_path"]).parent
    manifest_file = out_dir / "manifest.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest["title"] = TITLE
        manifest["script"]["caption"] = CAPTION
        manifest["script"]["comment_bait"] = COMMENT_BAIT
        manifest["script"]["hashtags"] = HASHTAGS
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  📌 Title : {TITLE}")
    print(f"  📁 File  : {row['video_path']}")
    print(f"  💬 First Comment: {COMMENT_BAIT}")
    print("=" * 70 + "\n")

    t0 = time.time()
    pub = YouTubePublisher(db=db)

    print("🚀 Starting YouTube resumable upload (Public, Comments Enabled, Not Made For Kids)...")
    res = pub.publish(VID, privacy="public", pin_comment=True)

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 SERIES 2 EPISODE 2 SUCCESSFULLY PUBLISHED TO YOUTUBE SHORTS!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{VID}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  ⏱️ Upload Time: {elapsed}s")
    print("=" * 70 + "\n")
    return res

if __name__ == "__main__":
    main()
