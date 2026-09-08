#!/usr/bin/env python3
"""
auto_produce_1h.py — Continuous 1-Hour Video Production Loop (No Upload).

Runs back-to-back video generation (TrendScout -> Script -> Narration -> AI Images -> FFmpeg Render -> Validate)
for exactly 1 hour (3600 seconds). All videos are saved to the database and output/ folder for review.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows terminal UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook
from run import one_video

log = Logbook("auto_produce")

DURATION_SECONDS = 3600  # 1 hour


def format_remaining(seconds: float) -> str:
    if seconds <= 0:
        return "0m 0s"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}m {s}s"


def main():
    start_time = time.time()
    end_time = start_time + DURATION_SECONDS
    end_dt = datetime.now() + timedelta(seconds=DURATION_SECONDS)

    print("\n" + "=" * 70)
    print("  🎬 AUTOPILOT: 1-HOUR CONTINUOUS PRODUCTION RUNNER (NO UPLOAD)")
    print("=" * 70)
    print(f"  ⏰ Start Time : {datetime.now().strftime('%H:%M:%S')}")
    print(f"  ⏳ End Time   : {end_dt.strftime('%H:%M:%S')} (~1 Ghanta)")
    print("  🛡️ Mode       : Production Only (Videos dashboard me review ke liye save honge)")
    print("=" * 70 + "\n")

    completed_videos: list[dict] = []
    iteration = 0

    try:
        while time.time() < end_time:
            iteration += 1
            remaining = end_time - time.time()
            rem_str = format_remaining(remaining)

            print("\n" + "#" * 70)
            print(f"  🚀 CYCLE #{iteration} | Bacha Hua Time: {rem_str}")
            print("#" * 70 + "\n")

            cycle_start = time.time()
            try:
                # one_video handles TrendScout -> Writer -> ArtDirector -> ImageGen -> TTS -> FFmpeg -> Validate
                info = one_video(
                    topic=None,
                    dry_run=False,
                    with_images=True,
                    preset="veryfast",
                    keep_temp=False,
                )

                if info:
                    completed_videos.append({
                        "cycle": iteration,
                        "video_path": info.get("video_path"),
                        "duration_sec": info.get("duration_sec"),
                        "size_mb": info.get("size_mb"),
                        "status": "validated",
                        "time_taken": round(time.time() - cycle_start, 1)
                    })
                    print(f"\n✅ Cycle #{iteration} Kamyab! Video ready hai: {info.get('video_path')}")
                else:
                    print(f"\n⚠️ Cycle #{iteration} mein video complete nahi ho saka (render/validation check karein).")

            except Exception as e:
                log.error(f"Cycle #{iteration} mein error aaya: {e}")
                print(f"\n❌ Error in Cycle #{iteration}: {e}")
                print("⏳ 10 seconds ruk kar agle video par proceed kar rahe hain...")
                time.sleep(10)

            remaining_now = end_time - time.time()
            if remaining_now <= 60:
                print(f"\n⏰ Sirf {format_remaining(remaining_now)} bache hain. 1 ghanta poora ho raha hai...")
                break

            print(f"\n💤 Next video agle 5 seconds me shuru hoga (Bacha hua time: {format_remaining(remaining_now)})...")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n⚠️ User ne 1 ghante se pehle rok diya (KeyboardInterrupt).")

    total_elapsed = round(time.time() - start_time, 1)
    print("\n" + "=" * 70)
    print("  🏁 1-HOUR AUTOPILOT PRODUCTION SUMMARY")
    print("=" * 70)
    print(f"  ⏱️ Total Time Elapsed  : {format_remaining(total_elapsed)} ({total_elapsed}s)")
    print(f"  🎬 Total Videos Created: {len(completed_videos)}")
    print("-" * 70)

    for i, v in enumerate(completed_videos, 1):
        print(f"  {i}. {v['video_path']} ({v['duration_sec']}s, {v['size_mb']}MB, {v['time_taken']}s me bana)")

    print("-" * 70)
    print("  📌 Sabhi videos 'output/' folder aur database me save ho chuke hain.")
    print("  🌐 Dekhne/Approve karne ke liye dashboard chalayein: python -m web.server")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
