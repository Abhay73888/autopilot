#!/usr/bin/env python3
"""
publish_series_batch.py — Uploads all 7 pre-rendered next series episodes (#308 - #314) to YouTube Shorts.

Videos:
  #308: SERIES_1 (Kaal-Rekha) Ep 14
  #309: SERIES_2 (Jab Pyaar Online Tha) Ep 10
  #310: SERIES_3 (Dimag Ka Dahi) Ep 8
  #311: SERIES_4 (The Secret You Weren't Supposed To Know) Ep 8
  #312: SERIES_5 (Ashwatthama 3049 AD) Ep 5
  #313: SERIES_6 (The Observer Files) Ep 4
  #314: SERIES_7 (Roblox Vault) Ep 2

INVARIANTS (AGENTS.md):
  - selfDeclaredMadeForKids = False (COMMENTS ALWAYS 100% ON)
  - privacy = "public"
  - pin_comment = True (comment_bait posted & pinned)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.db import DB
from core.logbook import Logbook
from agents.publisher import YouTubePublisher

log = Logbook("publish_series_batch")

TARGET_VIDEOS = [308, 309, 310, 311, 312, 313, 314]

def main():
    print("\n" + "=" * 80)
    print("  🚀 AUTOPILOT — PUBLISHING NEXT EPISODES BATCH (Videos #308 - #314)")
    print("  🔒 POLICY: selfDeclaredMadeForKids=False | comments=ON | privacy=public")
    print("=" * 80 + "\n")

    db = DB()
    pub = YouTubePublisher(db=db)

    results = []

    for idx, vid in enumerate(TARGET_VIDEOS, 1):
        row = db.get_video(vid)
        if not row:
            print(f"[{idx}/{len(TARGET_VIDEOS)}] ❌ Video #{vid} not found in DB!")
            results.append({"video_id": vid, "ok": False, "error": "Not found in DB"})
            continue

        d = dict(row)
        title = d.get("title")
        series = d.get("series_name")
        ep = d.get("series_index")
        status = d.get("status")
        yt_id = d.get("yt_video_id")

        if status == "published" and yt_id:
            url = f"https://youtube.com/shorts/{yt_id}"
            print(f"[{idx}/{len(TARGET_VIDEOS)}] ⏭️ Video #{vid} ({series} Ep {ep}) ALREADY PUBLISHED: {url}")
            results.append({
                "video_id": vid,
                "series": series,
                "ep": ep,
                "title": title,
                "ok": True,
                "url": url,
                "note": "Already published"
            })
            continue

        print(f"[{idx}/{len(TARGET_VIDEOS)}] 🎬 Uploading Video #{vid} [{series} Ep {ep}]: {title[:60]}...")
        t0 = time.time()
        try:
            res = pub.publish(
                vid,
                privacy="public",
                pin_comment=True
            )
            elapsed = round(time.time() - t0, 1)
            url = res.get("url") or f"https://youtube.com/shorts/{res.get('yt_video_id')}"
            print(f"  ✅ SUCCESS! Published: {url} ({elapsed}s)")
            results.append({
                "video_id": vid,
                "series": series,
                "ep": ep,
                "title": title,
                "ok": True,
                "url": url,
                "elapsed": elapsed
            })
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            print(f"  ❌ FAILED Video #{vid}: {e} ({elapsed}s)")
            log.error(f"Upload failed for #{vid}: {e}")
            results.append({
                "video_id": vid,
                "series": series,
                "ep": ep,
                "title": title,
                "ok": False,
                "error": str(e),
                "elapsed": elapsed
            })

        # Pause slightly between uploads to be gentle on YouTube API
        if idx < len(TARGET_VIDEOS):
            print("  ⏳ Waiting 6 seconds before next upload...\n")
            time.sleep(6)

    db.close()

    print("\n" + "=" * 80)
    print("  📋 FINAL BATCH PUBLISH SUMMARY")
    print("=" * 80)
    success_count = sum(1 for r in results if r.get("ok"))
    fail_count = len(results) - success_count

    for r in results:
        vid = r["video_id"]
        series = r.get("series", "Unknown")
        ep = r.get("ep", "?")
        if r.get("ok"):
            url = r.get("url")
            note = f" ({r.get('note')})" if r.get("note") else ""
            print(f"  ✅ Video #{vid:3d} [{series} Ep {ep:>2}] -> {url}{note}")
        else:
            err = r.get("error", "Unknown error")
            print(f"  ❌ Video #{vid:3d} [{series} Ep {ep:>2}] -> FAILED: {err}")

    print("-" * 80)
    print(f"  Total: {success_count} published, {fail_count} failed")
    print("=" * 80 + "\n")

    return fail_count == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
