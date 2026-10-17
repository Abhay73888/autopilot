#!/usr/bin/env python3
"""
run_all_4_series.py — Master orchestrator to generate and upload videos for all 4 series.
Runs each episode in an isolated process to ensure clean environment and resource cleanup.
"""

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
    ("Series 1: Kaal-Rekha (Part 8)", "generate_and_publish_kaalrekha_ep8.py"),
    ("Series 2: Jab Pyaar Online Tha (Episode 3)", "generate_and_publish_series2_ep3.py"),
    ("Series 3: Chintu Ki Jadui Duniya (Episode 1)", "generate_and_publish_series3_ep1.py"),
    ("Series 4: Dimag Ka Dahi (Episode 1)", "generate_and_publish_series4_ep1.py"),
]

def main():
    root = Path(__file__).resolve().parent
    total_start = time.time()

    print("\n" + "=" * 75)
    print("  AUTOPILOT: ALL 4 SERIES VIDEO GENERATION & YOUTUBE UPLOAD")
    print("  Fast Voiceover Speed Multiplier Active (1.20x)")
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
            results.append((title, "SUCCESS", elapsed))
        else:
            print(f"\n[FAIL] {title} FAILED (exit code {proc.returncode}) after {elapsed}s!\n")
            results.append((title, f"FAILED (exit code {proc.returncode})", elapsed))

    total_time = round(time.time() - total_start, 1)

    print("\n" + "=" * 75)
    print("  ALL 4 SERIES SUMMARY REPORT")
    print("=" * 75)
    for title, status, elapsed in results:
        print(f"  * {title:<45} : {status} ({elapsed}s)")
    print("-" * 75)
    print(f"  Total Run Time: {total_time}s ({round(total_time/60, 1)} min)")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
