"""
pipeline/broll.py — Pexels Cinematic B-Roll Engine for Autopilot.

Automatically finds, downloads, and caches high-definition 1080x1920
vertical mystery/suspense B-Roll footage to enhance visual pacing.
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from core.config import CONFIG
from core.logbook import Logbook

log = Logbook("broll")

BROLL_CACHE_DIR = Path(CONFIG["_root"]) / "assets" / "broll"

# Default mystery search queries
MYSTERY_QUERIES = [
    "dark fog road vertical",
    "foggy forest atmospheric vertical",
    "rain window night vertical",
    "clock ticking suspense vertical",
    "old paper documents vintage vertical",
    "shadowy figure dark room vertical",
]


def fetch_broll_clip(query: str, out_path: str | Path, pexels_key: str | None = None) -> Path | None:
    """
    Search Pexels API for a vertical (portrait) video clip and save it.
    """
    out_path = Path(out_path)
    key = pexels_key or os.environ.get("PEXELS_API_KEY") or CONFIG.get("PEXELS_API_KEY")
    if not key:
        log.warn("PEXELS_API_KEY missing — B-roll skip ho gaya")
        return None

    # Check cache first
    BROLL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", query).strip("_").lower()
    cached_file = BROLL_CACHE_DIR / f"{slug}.mp4"
    if cached_file.exists() and cached_file.stat().st_size > 50000:
        log.ok(f"B-Roll cache hit: {cached_file.name}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path != cached_file:
            import shutil
            shutil.copyfile(cached_file, out_path)
        return out_path

    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page=5&orientation=portrait"
    req = urllib.request.Request(
        url,
        headers={"Authorization": key, "User-Agent": "Autopilot/1.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            videos = data.get("videos", [])
            if not videos:
                log.warn(f"Pexels pe query '{query}' ke liye video nahi mili")
                return None

            best_link = None
            for v in videos:
                files = v.get("video_files", [])
                # Look for 1080x1920 or portrait HD
                for f in files:
                    w = f.get("width") or 0
                    h = f.get("height") or 0
                    if w == 1080 and h == 1920:
                        best_link = f.get("link")
                        break
                    elif h > w and f.get("quality") == "hd":
                        best_link = f.get("link")
                if best_link:
                    break

            if not best_link and videos[0].get("video_files"):
                best_link = videos[0]["video_files"][0].get("link")

            if not best_link:
                return None

            log.info(f"Downloading B-roll for '{query}'...")
            dl_req = urllib.request.Request(best_link, headers={"User-Agent": "Autopilot/1.0"})
            with urllib.request.urlopen(dl_req, timeout=40) as dl_resp:
                video_data = dl_resp.read()
                if len(video_data) < 50000:
                    raise RuntimeError("Downloaded video too small")
                with open(cached_file, "wb") as f:
                    f.write(video_data)

            out_path.parent.mkdir(parents=True, exist_ok=True)
            if out_path != cached_file:
                import shutil
                shutil.copyfile(cached_file, out_path)

            log.ok(f"B-roll ready: {out_path.name} ({len(video_data) // 1024} KB)")
            return out_path
    except Exception as e:
        log.warn(f"Pexels B-roll download fail ({str(e)[:80]})")
        return None


def select_broll_for_scene(scene_text: str, out_path: str | Path) -> Path | None:
    """
    Select an appropriate B-roll clip based on scene keywords.
    """
    text = scene_text.lower()
    if any(w in text for w in ["raat", "andhera", "dark", "night"]):
        q = "moody night walk in foggy street"
    elif any(w in text for w in ["jungle", "ped", "forest", "wood"]):
        q = "foggy forest atmospheric"
    elif any(w in text for w in ["barish", "rain", "storm"]):
        q = "rain window dark"
    elif any(w in text for w in ["samay", "waqt", "clock", "time"]):
        q = "clock ticking suspense"
    elif any(w in text for w in ["file", "police", "saboot", "document", "paper"]):
        q = "vintage documents desk"
    else:
        q = "dark road fog mysterious"

    return fetch_broll_clip(q, out_path)
