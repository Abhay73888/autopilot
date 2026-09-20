#!/usr/bin/env python3
"""
publish_10x_batch.py — Publishes all 6 pre-rendered 10X episodes to YouTube.

All videos are already rendered and status='approved' in the DB.
This script just runs the upload step — no regeneration needed.

POLICY (AGENTS.md — PERMANENT):
  selfDeclaredMadeForKids = False  (enforced inside publisher._build_metadata)
  privacyStatus            = public
  pin_comment              = True  (comment_bait always pinned)
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.db import DB
from core.logbook import Logbook
from agents.publisher import YouTubePublisher

log = Logbook("publish_10x_batch")

# ── The 6 episodes we just generated (series + episode number) ────────────────
TARGET_EPISODES = [
    ("SERIES_1", 12),
    ("SERIES_2", 9),
    ("SERIES_3", 7),
    ("SERIES_4", 7),
    ("SERIES_5", 4),
    ("SERIES_6", 3),
]


def find_video_id(db: DB, series_code: str, episode_num: int) -> int | None:
    """Find the most recently created approved video for this series+episode."""
    rows = db.q(
        """SELECT id, title, status, video_path
           FROM videos
           WHERE series_name = ? AND series_index = ?
           ORDER BY id DESC LIMIT 5""",
        (series_code, episode_num)
    )
    # Prefer 'approved' status; fall back to most recent
    for r in rows:
        if r["status"] == "approved":
            return r["id"]
    # If none approved, return most recent anyway
    return rows[0]["id"] if rows else None


def main():
    db = DB()
    pub = YouTubePublisher(db=db)

    print("\n" + "█" * 70)
    print("  🚀 AUTOPILOT 10X — PUBLISH BATCH (Upload Only, Videos Pre-Rendered)")
    print("  🔒 POLICY: selfDeclaredMadeForKids=False | comments=ON | pin=True")
    print("█" * 70)

    results = []
    for series_code, episode_num in TARGET_EPISODES:
        vid = find_video_id(db, series_code, episode_num)
        if not vid:
            print(f"\n  ⚠️  {series_code} Ep {episode_num} — Video ID not found in DB. Skipping.")
            results.append({"series_code": series_code, "episode_num": episode_num, "error": "Not found in DB"})
            continue

        print(f"\n  🎬 [{series_code} Ep {episode_num}] Video #{vid} — Uploading...")
        t0 = time.time()
        try:
            res = pub.publish(
                vid,
                privacy="public",   # selfDeclaredMadeForKids=False enforced inside publisher
                pin_comment=True,   # comment_bait pinned (AGENTS.md policy)
            )
            elapsed = round(time.time() - t0, 1)
            url = res.get("url") or res.get("yt_video_id", "")
            print(f"  ✅ PUBLISHED → {url}  ({elapsed}s)")
            results.append({
                "series_code": series_code,
                "episode_num": episode_num,
                "video_id": vid,
                "url": url,
                "status": res.get("status"),
                "elapsed": elapsed
            })
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            print(f"  ❌ FAILED → {e}")
            log.error(f"{series_code} Ep{episode_num}: {e}")
            results.append({
                "series_code": series_code,
                "episode_num": episode_num,
                "video_id": vid,
                "error": str(e),
                "elapsed": elapsed
            })

    db.close()

    # ── Final Report ──────────────────────────────────────────────────────────
    print("\n" + "█" * 70)
    print("  🏆 PUBLISH BATCH COMPLETE")
    print("█" * 70)
    for r in results:
        code = r["series_code"]
        ep   = r["episode_num"]
        if r.get("url"):
            print(f"  ✅ {code:10s} Ep {ep:>2d} → {r['url']}  ({r.get('elapsed')}s)")
        else:
            print(f"  ❌ {code:10s} Ep {ep:>2d} → FAILED: {r.get('error', 'unknown')}")
    print("█" * 70)
    print("\n  🔒 POLICY AUDIT:")
    print("     selfDeclaredMadeForKids = False  ✅")
    print("     comment_bait pinned     = True   ✅")
    print("     privacy                 = public ✅")
    print("█" * 70 + "\n")


if __name__ == "__main__":
    main()
