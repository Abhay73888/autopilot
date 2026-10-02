#!/usr/bin/env python3
"""
publish_batch5.py — Publish Batch 5 (All 8 Active Series) to YouTube Shorts.

Videos:
  - 1000040: SERIES_1 (Kaal-Rekha) Ep 22
  - 1000041: SERIES_2 (Jab Pyaar Online Tha) Ep 18
  - 1000042: SERIES_3 (Chintu Ki Jadui Duniya) Ep 16
  - 1000043: SERIES_4 (Dimag Ka Dahi) Ep 16
  - 1000044: SERIES_5 (Ashwatthama 3049 AD) Ep 13
  - 1000045: SERIES_6 (The Observer Files) Ep 12
  - 1000046: SERIES_7 (Roblox Vault) Ep 10
  - 1000047: SERIES_8 (Leonardo da Vinci) Ep 2

POLICY COMPLIANCE (AGENTS.md):
  - Zero Comment Lock: comments 100% ON (selfDeclaredMadeForKids=False)
  - Privacy: Public
  - Pinned first comment bait on all uploads
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Fix Windows terminal UTF-8 encoding
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

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.db import DB
from agents.publisher import YouTubePublisher

BATCH_5_IDS = [
    1000040,  # SERIES_1 Ep 22
    1000041,  # SERIES_2 Ep 18
    1000042,  # SERIES_3 Ep 16
    1000043,  # SERIES_4 Ep 16
    1000044,  # SERIES_5 Ep 13
    1000045,  # SERIES_6 Ep 12
    1000046,  # SERIES_7 Ep 10
    1000047,  # SERIES_8 Ep 2
]


def main():
    print("=" * 80)
    print("  🚀 PUBLISHING BATCH 5 TO YOUTUBE SHORTS (ALL 8 SERIES)")
    print("=" * 80)

    db = DB()
    try:
        pub = YouTubePublisher(db=db)
    except Exception as e:
        print(f"\n❌ YouTube authorization error: {e}")
        print("   Pehele `python authorize_youtube.py --force` chalao aur Allow karo.")
        return 1

    success_count = 0
    fail_count = 0

    for vid in BATCH_5_IDS:
        row = db.get_video(vid)
        if not row:
            print(f"\n  ❌ Video #{vid} not found in DB")
            continue

        d = dict(row)
        title = d.get("title")
        status = d.get("status")
        series = d.get("series_name")
        ep = d.get("series_index")

        if status == "published" and d.get("yt_video_id"):
            print(f"\n  ⏭️ Video #{vid} ({series} Ep {ep}) already published: https://youtube.com/shorts/{d.get('yt_video_id')}")
            success_count += 1
            continue

        print(f"\n  🎬 Uploading Video #{vid}: [{series} Ep {ep}] {title[:50]}...")
        try:
            res = pub.publish(vid, privacy="public", pin_comment=True)
            if res.get("ok"):
                url = res.get("url") or f"https://youtube.com/shorts/{res.get('video_id')}"
                print(f"  ✅ Live on YouTube! URL: {url}")
                success_count += 1
            else:
                print(f"  ⚠️ Publish result not ok: {res}")
                fail_count += 1
        except Exception as e:
            print(f"  ❌ Upload failed for #{vid}: {e}")
            fail_count += 1

        time.sleep(3)

    db.close()

    print("\n" + "=" * 80)
    print(f"  ✨ Batch 5 Upload Complete! {success_count} published, {fail_count} failed.")
    print("=" * 80 + "\n")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
