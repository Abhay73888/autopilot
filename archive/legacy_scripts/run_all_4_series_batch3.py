#!/usr/bin/env python3
"""
run_all_4_series_batch3.py — Orchestrator to generate and immediately upload Batch 3.
Series 1 (Kaal-Rekha Part 10 - #193) is already uploaded.
This script generates and uploads:
1. Series 2: Jab Pyaar Online Tha (Episode 5)
2. Series 3: Chintu Ki Jadui Duniya (Episode 3 - Comment-Safe)
3. Series 4: Dimag Ka Dahi (Episode 3)
"""

from __future__ import annotations

import io
import os
import subprocess
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

from core.db import DB
from agents.publisher import YouTubePublisher

SCRIPTS = [
    ("Series 3: Chintu Ki Jadui Duniya (Episode 3)", "generate_series3_ep3.py"),
    ("Series 4: Dimag Ka Dahi (Episode 3)", "generate_series4_ep3.py"),
]

def main():
    root = Path(__file__).resolve().parent
    total_start = time.time()

    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT: GENERATING & PUBLISHING BATCH 3 EPISODES")
    print("=" * 75 + "\n")

    published = []

    for idx, (title, script_name) in enumerate(SCRIPTS, 1):
        script_path = root / script_name
        print("\n" + "#" * 75)
        print(f"  [{idx}/3] GENERATING: {title}")
        print("#" * 75 + "\n")

        t0 = time.time()
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(root),
            env=env,
        )

        elapsed = round(time.time() - t0, 1)
        if proc.returncode != 0:
            print(f"\n❌ {title} generation failed!")
            continue

        print(f"\n✅ {title} generated successfully in {elapsed}s! Uploading to YouTube...")

        # Find latest video created in DB for this series
        db = DB()
        row = db.conn.execute("SELECT id, title, video_path FROM videos WHERE status='approved' ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            print(f"❌ No approved video found to upload for {title}")
            db.close()
            continue

        vid = row["id"]
        print(f"  Uploading Video #{vid}: '{row['title']}'...")
        pub = YouTubePublisher(db=db)
        res = pub.publish(vid, privacy="public")
        db.close()

        print(f"  🎉 PUBLISHED: {res.get('url')}\n")
        published.append((title, vid, res.get('url')))

    print("\n" + "=" * 75)
    print("  BATCH 3 PUBLISH REPORT")
    print("=" * 75)
    print("  * Series 1: Kaal-Rekha (Part 10)       : #193 | https://youtube.com/shorts/SePr7LFoGbE (ALREADY LIVE)")
    for title, vid, url in published:
        print(f"  * {title:<36} : #{vid} | {url}")
    print("-" * 75)
    print(f"  Total Batch Time: {round((time.time() - total_start)/60, 1)} min")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
