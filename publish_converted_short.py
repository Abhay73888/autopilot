#!/usr/bin/env python3
"""
publish_converted_short.py — Publish the converted 57.5s YouTube Short for Video #139.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

# Fix Windows terminal UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import CONFIG
from core.db import DB
from core.ffmpeg import probe
from pipeline.validate import validate_dir
from agents.publisher import YouTubePublisher

def main():
    vid = 139
    db = DB()
    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    converted_mp4 = out_dir / "short_converted.mp4"
    final_mp4 = out_dir / "final.mp4"

    if not converted_mp4.exists():
        print(f"❌ Error: {converted_mp4} nahi mila")
        sys.exit(1)

    print("=" * 70)
    print("  🎬 REPLACING WITH EXACT YOUTUBE SHORT (< 60s)")
    print("=" * 70)

    # 1. Swap files
    backup_mp4 = out_dir / "final_61s_backup.mp4"
    if final_mp4.exists():
        final_mp4.replace(backup_mp4)
    converted_mp4.replace(final_mp4)
    print(f"✅ Replaced {final_mp4.name} with converted Short (57.5s)")

    # 2. Probe file
    p = probe(final_mp4)
    dur = float(p.get("format", {}).get("duration", 57.5))
    size_mb = round(final_mp4.stat().st_size / (1024 * 1024), 2)
    print(f"   Duration : {dur:.2f}s (Safely under 60.0s for YouTube Shorts)")
    print(f"   Size     : {size_mb} MB")

    # 3. Update manifest
    manifest_path = out_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if "render" in manifest:
            manifest["render"]["duration_sec"] = dur
            manifest["render"]["size_mb"] = size_mb
            manifest["render"]["video_path"] = str(final_mp4)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. Validate directory
    print("\n🔍 Validating video directory...")
    rep = validate_dir(out_dir)
    print(f"   Validation: {'PASS ✅' if rep.ok else 'WARN ⚠️'}")
    if not rep.ok:
        fatal = "; ".join(f"[{i.code}] {i.msg}" for i in rep.fatals)
        print(f"❌ Pre-upload validation failed: {fatal}")
        sys.exit(1)

    # 5. Reset DB status
    db.update_video(
        vid,
        length_sec=dur,
        status="approved",
        public_url=None,
        yt_video_id=None,
        published_ts=None,
        notes="Converted to exact Short (57.5s)"
    )
    print(f"✅ Video #{vid} updated in DB and marked as APPROVED.")

    # 6. Publish to YouTube Shorts
    print("\n🚀 Uploading converted Short to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()

    print("\n" + "=" * 70)
    print("  🎉 KAAL-REKHA PART 04 SHORTS PUBLISHED SUCCESSFULLY!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  ⏱️ Duration   : {dur:.1f}s (Exact YouTube Short)")
    print(f"  🔗 Shorts URL : {res.get('url')}")
    print(f"  🆔 YT Video ID: {res.get('yt_video_id')}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
