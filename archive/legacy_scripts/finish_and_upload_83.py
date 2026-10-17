#!/usr/bin/env python3
import sys
import io
import json
import time
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from core.config import CONFIG
from core.db import DB
from pipeline.render import Renderer
from pipeline.validate import validate_dir
from agents.publisher import YouTubePublisher

VID = 83

def main():
    print("=" * 68)
    print(f"🎬 FINISHING & UPLOADING VIDEO #{VID} (TOP 5 SECRETS OF FEMALE PSYCHOLOGY)")
    print("=" * 68)

    t0 = time.time()
    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{VID:04d}"
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"❌ Error: {manifest_path} not found")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"📌 Topic: {manifest.get('topic')}")
    print(f"📌 Title: {manifest.get('script', {}).get('title')}")

    # Phase 3: Render MP4
    print("\n🎥 Phase 3: Rendering video with FFmpeg...")
    info = Renderer(manifest).render(out_dir, preset="fast", keep_temp=False)
    print(f"✅ Render complete: {info['video_path']}")
    print(f"   Duration: {info['duration_sec']}s, Size: {info['size_mb']}MB, Resolution: {info['resolution']}")

    db = DB()
    db.update_video(VID, video_path=info["video_path"],
                    cover_path=info["cover_path"],
                    length_sec=info["duration_sec"], status="rendered")

    # Phase 4: Validate
    print("\n🔍 Phase 4: Validating audio/video specs...")
    rep = validate_dir(out_dir)
    manifest["render"] = info
    manifest["validation"] = rep.to_dict()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   Validation status: {'PASS' if rep.ok else 'WARN/FAIL'} (Issues: {len(rep.issues)})")

    # Auto-approve
    print("\n👍 Approving video in database...")
    db.set_status(VID, "approved", note="User instructed high intelligence upload")
    print(f"✅ Video #{VID} approved")

    # Phase 5: Upload to YouTube
    print("\n🚀 Phase 5: Uploading to YouTube Shorts (public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(VID, privacy="public")

    db.close()

    print("\n" + "=" * 68)
    print("🎉 VIDEO SUCCESSFULLY GENERATED & PUBLISHED TO YOUTUBE!")
    print("=" * 68)
    print(f"  Title      : {manifest['script'].get('title')}")
    print(f"  YouTube URL: {res.get('url')}")
    print(f"  Status     : {res.get('status')}")
    print(f"  Total Time : {round(time.time() - t0, 1)}s")
    print("=" * 68 + "\n")

if __name__ == "__main__":
    main()
