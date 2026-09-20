#!/usr/bin/env python3
"""
publish_pending_batch.py — Instantly publish pre-rendered videos #284, #285, #286, #287
to YouTube Shorts with 2026 Viral Formula & 100% comments enabled.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.db import DB
from agents.publisher import YouTubePublisher

PENDING_IDS = [284, 285, 286, 287]

def main():
    print("=" * 80)
    print("  🚀 PUBLISHING REMAINING READY SHORTS (Videos #284 - #287)")
    print("=" * 80)

    db = DB()
    pub = YouTubePublisher(db=db)

    for vid in PENDING_IDS:
        row = db.get_video(vid)
        if not row:
            print(f"  ❌ Video #{vid} not found in DB")
            continue

        d = dict(row)
        title = d.get("title")
        status = d.get("status")
        series = d.get("series_name")
        ep = d.get("series_index")

        if status == "published" and d.get("yt_video_id"):
            print(f"  ⏭️ Video #{vid} ({series} Ep {ep}) already published: https://youtube.com/shorts/{d.get('yt_video_id')}")
            continue

        print(f"\n  Uploading Video #{vid}: [{series} Ep {ep}] {title}...")
        try:
            res = pub.publish(vid, privacy="public", pin_comment=True)
            print(f"  ✅ Published! URL: {res.get('url')}")
        except Exception as e:
            print(f"  ⚠️ Upload failed for #{vid}: {e}")

    db.close()
    print("\n" + "=" * 80)
    print("  ✨ Batch upload check finished.")
    print("=" * 80)

if __name__ == "__main__":
    main()
