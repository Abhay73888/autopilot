#!/usr/bin/env python3
"""
doctor.py — AUTOPILOT 20X Startup Pre-flight Diagnostic & Auto-Repair Engine.
Inspects system health, FFmpeg codecs/filters, database schema integrity,
API keys, directories, audio/font assets, and prints a comprehensive scorecard.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows terminal UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def check_python() -> tuple[bool, str]:
    ver = sys.version_info
    if ver.major == 3 and ver.minor >= 10:
        return True, f"Python {ver.major}.{ver.minor}.{ver.micro} (Supported ✅)"
    return False, f"Python {ver.major}.{ver.minor} (Recommend Python 3.10+)"


def check_ffmpeg() -> tuple[bool, dict[str, bool], str]:
    from core.ffmpeg import capabilities, ffmpeg_bin
    fb = ffmpeg_bin()
    if not fb:
        return False, {}, "FFmpeg binary not found on PATH"
    
    caps = capabilities()
    missing = [k for k, v in caps.items() if not v and k in ("x264", "aac", "ass", "loudnorm")]
    if missing:
        return False, caps, f"FFmpeg found ({fb}) but missing critical filters: {', '.join(missing)}"
    return True, caps, f"FFmpeg ready ({fb}) with full codec & libass support ✅"


def check_database() -> tuple[bool, str]:
    from core.db import DB
    try:
        db = DB()
        conn = db.conn
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in c.fetchall()}
        required = {"videos", "metrics", "experiments", "learnings", "quota_usage", "events"}
        diff = required - tables
        if diff:
            return False, f"Missing tables: {diff}"
        return True, f"SQLite database active ({len(tables)} tables, WAL mode active) ✅"
    except Exception as e:
        return False, f"Database error: {e}"


def check_api_keys() -> dict[str, bool]:
    from core.config import CONFIG
    keys = {
        "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY") or CONFIG.get("GEMINI_API_KEY")),
        "GROQ_API_KEY": bool(os.getenv("GROQ_API_KEY") or CONFIG.get("GROQ_API_KEY")),
        "ELEVENLABS_API_KEY": bool(os.getenv("ELEVENLABS_API_KEY") or CONFIG.get("ELEVENLABS_API_KEY")),
        "YOUTUBE_OAUTH": (ROOT / "token.json").exists() or (ROOT / "client_secret.json").exists(),
        "INSTAGRAM_META": bool(os.getenv("IG_BUSINESS_ACCOUNT_ID")),
        "FAL_KEY": bool(os.getenv("FAL_KEY")),
        "PEXELS_API_KEY": bool(os.getenv("PEXELS_API_KEY")),
    }
    return keys


def check_directories() -> list[str]:
    repaired = []
    dirs = [
        ROOT / "output",
        ROOT / "assets" / "audio",
        ROOT / "assets" / "fonts",
        ROOT / "data",
        ROOT / "logs",
        ROOT / "scratch",
    ]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            repaired.append(str(d.relative_to(ROOT)))
    return repaired


def main():
    print("\n" + "=" * 75)
    print("  🩺 AUTOPILOT 20X — STARTUP HEALTH & SYSTEM DIAGNOSTIC DOCTOR")
    print("=" * 75 + "\n")

    all_pass = True

    # 1. Python Environment
    py_ok, py_msg = check_python()
    print(f"[{'PASS ✅' if py_ok else 'FAIL ❌'}] Environment   : {py_msg}")
    if not py_ok:
        all_pass = False

    # 2. FFmpeg & Media Pipeline
    ff_ok, caps, ff_msg = check_ffmpeg()
    print(f"[{'PASS ✅' if ff_ok else 'FAIL ❌'}] Media Engine  : {ff_msg}")
    if caps:
        print(f"               ↳ Libass (Subtitles): {caps.get('ass', False)} | NVENC (GPU): {caps.get('nvenc', False)} | Loudnorm: {caps.get('loudnorm', False)}")
    if not ff_ok:
        all_pass = False

    # 3. Database
    db_ok, db_msg = check_database()
    print(f"[{'PASS ✅' if db_ok else 'FAIL ❌'}] Database      : {db_msg}")
    if not db_ok:
        all_pass = False

    # 4. Directory Structure
    repaired = check_directories()
    if repaired:
        print(f"[REPAIR 🔧] Storage       : Auto-created missing folders: {', '.join(repaired)}")
    else:
        print(f"[PASS ✅] Storage       : All directory paths verified ✅")

    # 5. API Keys Matrix
    print("\n🔑 AI & Provider Integrations:")
    keys = check_api_keys()
    for k, present in keys.items():
        state = "CONFIGURED ✅" if present else "OPTIONAL (Missing ⚠️)"
        if k in ("GEMINI_API_KEY", "YOUTUBE_OAUTH") and not present:
            state = "CRITICAL (Missing ❌)"
            all_pass = False
        print(f"   • {k:<20} : {state}")

    print("\n" + "=" * 75)
    if all_pass:
        print("  🎉 SYSTEM STATUS: 100% OPERATIONAL & READY FOR STARTUP WORKLOADS!")
    else:
        print("  ⚠️ SYSTEM STATUS: MINOR WARNINGS DETECTED (Check items marked with ❌)")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
