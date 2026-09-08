#!/usr/bin/env python3
"""
upload_video_88.py — Upload approved Video #88 (Bhangarh Fort Mystery) to YouTube Shorts (Public).
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

VID = 88

def main():
    print("\n" + "=" * 70)
    print(f"  🚀 UPLOADING APPROVED VIDEO #{VID} TO YOUTUBE SHORTS (PUBLIC)")
    print("=" * 70)

    db = DB()
    row = db.get_video(VID)
    if not row:
        print(f"❌ Video #{VID} not found in database.")
        sys.exit(1)

    print(f"  📌 Title : {row['title']}")
    print(f"  📁 File  : {row['video_path']}")
    print(f"  💬 Status: {row['status']}")
    print("=" * 70 + "\n")

    t0 = time.time()
    pub = YouTubePublisher(db=db)

    print("🚀 Starting YouTube resumable upload (Public, Comments Enabled, Not Made For Kids)...")
    res = pub.publish(VID, privacy="public")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 VIDEO #88 SUCCESSFULLY PUBLISHED TO YOUTUBE SHORTS!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{VID}")
    print(f"  📌 Title      : {row['title']}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  ⏱️ Upload Time: {elapsed}s")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
