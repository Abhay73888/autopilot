#!/usr/bin/env python3
"""
Generate and auto-upload female psychology video to YouTube.
"""
import sys
import io
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
import time
from pathlib import Path

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook
from pipeline.render import Renderer
from pipeline.validate import validate_dir
from run_phase2 import make_video
from agents.publisher import YouTubePublisher

log = Logbook("auto_publisher")

TOPIC = "Top 5 Secret Psychological Facts About Women Jo 99% Log Nahi Jaante"

def main():
    print("\n" + "=" * 68)
    print("  🧠 GENERATING & AUTO-PUBLISHING FEMALE PSYCHOLOGY VIDEO")
    print("=" * 68 + "\n")

    t0 = time.time()
    
    # 1. Phase 2: Script, Audio, Images
    print("🎬 Phase 2: Generating script, narration & images...")
    manifest = make_video(TOPIC, dry_run=False, with_images=True)
    vid = manifest["video_id"]
    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    print(f"✅ Phase 2 complete for Video #{vid}")

    # 2. Phase 3: Render MP4
    print("\n🎥 Phase 3: Rendering video with FFmpeg...")
    info = Renderer(manifest).render(out_dir, preset="fast", keep_temp=False)
    
    db = DB()
    db.update_video(vid, video_path=info["video_path"],
                    cover_path=info["cover_path"],
                    length_sec=info["duration_sec"], status="rendered")
    print(f"✅ Render complete: {info['video_path']}")

    # 3. Phase 4: Validate
    print("\n🔍 Phase 4: Validating audio/video specs...")
    rep = validate_dir(out_dir)
    manifest["render"] = info
    manifest["validation"] = rep.to_dict()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. Auto-approve
    db.set_status(vid, "approved", note="Auto-approved by user command")
    print(f"✅ Video #{vid} approved in database")

    # 5. Phase 5: Auto-upload to YouTube
    print("\n🚀 Phase 5: Uploading to YouTube Shorts (public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")
    
    db.close()
    
    print("\n" + "=" * 68)
    print("  🎉 VIDEO SUCCESSFULLY PUBLISHED TO YOUTUBE!")
    print("=" * 68)
    print(f"  Title     : {manifest['script'].get('title')}")
    print(f"  YouTube URL: {res.get('url')}")
    print(f"  Total Time: {round(time.time() - t0, 1)}s")
    print("=" * 68 + "\n")

if __name__ == "__main__":
    main()
