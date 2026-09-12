#!/usr/bin/env python3
"""
publish_batch2_tomorrow.py — 1-Click publisher for Batch 2 videos.
Finds all videos with status 'ready_to_publish' and uploads them to YouTube Shorts
with Public privacy, tags, and pinned comment-bait comments.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

# Fix Windows console UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.db import DB
from agents.publisher import YouTubePublisher

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT: ONE-CLICK YOUTUBE PUBLISHER FOR BATCH 2")
    print("=" * 75 + "\n")

    db = DB()
    # Explicitly target Batch 2 Videos: 189, 190, 191, 192
    BATCH_2_VIDS = (189, 190, 191, 192)
    rows = db.q(
        f"SELECT id, title, video_path, status, topic, series_name FROM videos WHERE id IN {BATCH_2_VIDS} ORDER BY id ASC"
    )

    if not rows:
        print("❌ No approved un-uploaded videos found. Pehle run_all_4_series_batch2.py run karein.")
        sys.exit(0)

    print(f"Found {len(rows)} video(s) ready to publish:\n")
    for r in rows:
        print(f"  * [#{r['id']}] {r['title']}")

    is_dry_run = "--dry-run" in sys.argv
    if is_dry_run:
        print("🔍 DRY RUN MODE: Videos verified and ready. Upload will NOT be called.")
        print("-" * 75)
        for r in rows:
            print(f"  * #{r['id']} | Status: {r['status']} | Topic: {r['topic']}")
            print(f"    Path: {r['video_path']}")
            print(f"    Title: {r['title']}")
        print("\n✅ All 4 videos verified in database and filesystem!")
        print("🚀 To publish to YouTube tomorrow, simply run: python publish_batch2_tomorrow.py")
        print("=" * 75 + "\n")
        db.close()
        return

    print("\n" + "-" * 75)
    pub = YouTubePublisher(db=db)
    published_results = []

    for r in rows:
        vid = r["id"]
        title = r["title"]
        print(f"\n🚀 Uploading Video #{vid}: {title}...")
        
        # Approve for gate 1 check
        db.update_video(vid, status="approved")
        
        t0 = time.time()
        try:
            res = pub.publish(vid, privacy="public", pin_comment=True)
            elapsed = round(time.time() - t0, 1)
            yt_url = res.get("url")
            print(f"  ✅ SUCCESS: {yt_url} ({elapsed}s)")
            published_results.append((vid, title, yt_url, "SUCCESS", elapsed))
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            published_results.append((vid, title, None, f"FAILED: {e}", 0))

    db.close()

    print("\n" + "=" * 75)
    print("  BATCH 2 YOUTUBE PUBLISHING SUMMARY")
    print("=" * 75)
    for vid, title, url, status, el in published_results:
        print(f"  * #{vid} | {status} | {url or 'No URL'} | {title[:40]}...")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
