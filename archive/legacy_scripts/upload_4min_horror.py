#!/usr/bin/env python3
"""
upload_4min_horror.py — Direct YouTube Publisher for 4-Minute Kuldhara Horror Special (#301).

Guarantees:
  - 100% Comments Section ENABLED (selfDeclaredMadeForKids = False)
  - Public Privacy Status
  - Pinned First Comment / Comment Bait
  - AI Disclosure Flag (containsSyntheticMedia = True)

Usage:
  python upload_4min_horror.py
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

VID = 301

def main():
    print("\n" + "=" * 75)
    print(f"  🚀 AUTOPILOT: UPLOADING 4-MINUTE HORROR FILM (VIDEO #{VID}) TO YOUTUBE")
    print("=" * 75)

    db = DB()
    row = db.get_video(VID)
    if not row:
        print(f"❌ Video #{VID} not found in database.")
        db.close()
        sys.exit(1)

    # Approve video in DB so publisher accepts it
    db.set_status(VID, "approved", note="User approved for direct YouTube upload")

    title = row["title"]
    video_path = row["video_path"]
    duration = row["length_sec"]

    print(f"  📌 Title   : {title}")
    print(f"  📁 File    : {video_path}")
    print(f"  ⏱️ Duration: {duration}s ({duration/60:.2f} mins)")
    print(f"  💬 Comments: 100% ENABLED (Zero Lock Policy)")
    print("=" * 75 + "\n")

    t0 = time.time()
    pub = YouTubePublisher(db=db)

    print("🚀 Starting Resumable YouTube Upload (Public)...")
    try:
        res = pub.publish(VID, privacy="public", pin_comment=True)
        db.close()
        elapsed = round(time.time() - t0, 1)

        print("\n" + "=" * 75)
        print("  🎉 VIDEO SUCCESSFULLY PUBLISHED TO YOUTUBE!")
        print("=" * 75)
        print(f"  🎬 Video ID   : #{VID}")
        print(f"  📌 Title      : {title}")
        print(f"  🔗 Watch URL  : {res.get('url')}")
        print(f"  ⏱️ Upload Time: {elapsed}s")
        print("=" * 75 + "\n")
    except Exception as e:
        db.close()
        print(f"\n❌ Upload Error: {e}")
        print("\n💡 Agar token expired ho to pehle ye run karein: python authorize_youtube.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
