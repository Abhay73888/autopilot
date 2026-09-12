#!/usr/bin/env python3
"""
run_all_4_series_batch2.py — Master orchestrator to generate & prepare all 4 series next episodes.
Mode: GENERATE & PREPARE ONLY (Strictly NO upload).
Runs:
1. Series 1: Kaal-Rekha (Part 9)
2. Series 2: 2020 — Jab Pyaar Online Tha (Episode 4)
3. Series 3: Chintu Ki Jadui Duniya (Episode 2)
4. Series 4: Dimag Ka Dahi (Episode 2)
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

SERIES_SCRIPTS = [
    ("Series 1: Kaal-Rekha (Part 9)", "generate_series1_ep9.py"),
    ("Series 2: Jab Pyaar Online Tha (Episode 4)", "generate_series2_ep4.py"),
    ("Series 3: Chintu Ki Jadui Duniya (Episode 2)", "generate_series3_ep2.py"),
    ("Series 4: Dimag Ka Dahi (Episode 2)", "generate_series4_ep2.py"),
]

def main():
    root = Path(__file__).resolve().parent
    total_start = time.time()

    print("\n" + "=" * 75)
    print("  🎬 AUTOPILOT 10X: GENERATING NEXT EPISODES FOR ALL 4 SERIES")
    print("  Constraint: GENERATE & PREPARE ONLY (NO YOUTUBE UPLOAD)")
    print("=" * 75 + "\n")

    results = []

    for idx, (title, script_name) in enumerate(SERIES_SCRIPTS, 1):
        script_path = root / script_name
        print("\n" + "#" * 75)
        print(f"  [{idx}/4] STARTING: {title}")
        print(f"  Script: {script_name}")
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
        if proc.returncode == 0:
            print(f"\n[OK] {title} COMPLETED SUCCESSFULLY IN {elapsed}s!\n")
            results.append((title, "SUCCESS (READY_TO_PUBLISH)", elapsed))
        else:
            print(f"\n[FAIL] {title} FAILED (exit code {proc.returncode}) after {elapsed}s!\n")
            results.append((title, f"FAILED (exit code {proc.returncode})", elapsed))

    total_time = round(time.time() - total_start, 1)

    print("\n" + "=" * 75)
    print("  ALL 4 SERIES BATCH 2 GENERATION REPORT")
    print("=" * 75)
    for title, status, elapsed in results:
        print(f"  * {title:<45} : {status} ({elapsed}s)")
    print("-" * 75)
    print(f"  Total Run Time: {total_time}s ({round(total_time/60, 1)} min)")
    print("  📌 All videos are stored in output/ and marked READY_TO_PUBLISH in database.")
    print("  🚀 Run 'python publish_batch2_tomorrow.py' whenever the user gives the signal tomorrow!")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
