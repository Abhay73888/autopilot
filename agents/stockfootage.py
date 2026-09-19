"""
agents/stockfootage.py — Free B-roll stock video provider for longform/shorts.

Features:
- Pexels Video API + Pixabay Video API (keys optional via env / config).
- Keyword search from scene beats / prompts.
- Downloads best <=1080p clip to local cache dir (data/stock_cache).
- Manifest marks each scene as type "stock" or "image".
- Graceful silent fallback to image generation if keys are missing or no results found.
- Stream-downloaded in chunks to keep memory usage minimal (<512MB RAM safe).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from core.config import CONFIG
from core.logbook import Logbook

log = Logbook("stockfootage")

CACHE_DIR = Path("data/stock_cache")


class StockFootageProvider:
    def __init__(
        self,
        cache_dir: Path | str = CACHE_DIR,
        pexels_key: str | None = None,
        pixabay_key: str | None = None,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pexels_key = (
            pexels_key if pexels_key is not None
            else (os.environ.get("PEXELS_API_KEY", "").strip() or CONFIG.get("pexels_api_key", ""))
        )
        self.pixabay_key = (
            pixabay_key if pixabay_key is not None
            else (os.environ.get("PIXABAY_API_KEY", "").strip() or CONFIG.get("pixabay_api_key", ""))
        )

    @property
    def has_keys(self) -> bool:
        return bool(self.pexels_key or self.pixabay_key)

    # ------------------------------------------------------------------
    # Keyword extraction
    # ------------------------------------------------------------------
    def extract_keywords(self, text: str, max_words: int = 3) -> str:
        """Extract high-relevance visual search terms from a scene description."""
        if not text:
            return "cinematic atmosphere"
        # Strip common prompt noise
        cleaned = re.sub(
            r"\b(cinematic|hyper-detailed|masterpiece|vertical|9:16|16:9|ultra|hd|8k|4k|no text|photo|realistic|shot of)\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        words = [
            w for w in re.findall(r"[a-zA-Z]{3,}", cleaned)
            if w.lower() not in {
                "the", "and", "with", "from", "for", "that", "this", "scene", "room",
                "character", "stands", "looks", "walking", "sitting", "there", "some"
            }
        ]
        return " ".join(words[:max_words]) if words else "cinematic nature"

    # ------------------------------------------------------------------
    # Pexels Video Search
    # ------------------------------------------------------------------
    def search_pexels(self, query: str, orientation: str = "landscape") -> str | None:
        """Search Pexels Video API for best <=1080p MP4."""
        if not self.pexels_key:
            return None
        orient = "portrait" if orientation in ("portrait", "9:16") else "landscape"
        url = (
            f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}"
            f"&per_page=5&orientation={orient}"
        )
        req = urllib.request.Request(url, headers={"Authorization": self.pexels_key})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            log.debug(f"Pexels search error for '{query}': {e}")
            return None

        videos = data.get("videos", [])
        if not videos:
            return None

        # Pick best video file <= 1080p (width <= 1920, height <= 1080 for landscape)
        for vid in videos:
            files = vid.get("video_files", [])
            # Filter mp4 files
            mp4s = [f for f in files if f.get("file_type") == "video/mp4" and f.get("link")]
            if not mp4s:
                continue
            # Sort by resolution descending, but cap at 1080p
            def _score(f: dict) -> int:
                w = f.get("width") or 0
                h = f.get("height") or 0
                if orient == "landscape" and (w > 1920 or h > 1080):
                    return -1
                if orient == "portrait" and (w > 1080 or h > 1920):
                    return -1
                return w * h

            valid = [f for f in mp4s if _score(f) > 0]
            if valid:
                valid.sort(key=_score, reverse=True)
                return valid[0]["link"]
            # Fallback to any valid link
            return mp4s[0]["link"]
        return None

    # ------------------------------------------------------------------
    # Pixabay Video Search
    # ------------------------------------------------------------------
    def search_pixabay(self, query: str) -> str | None:
        """Search Pixabay Video API for best <=1080p MP4."""
        if not self.pixabay_key:
            return None
        url = (
            f"https://pixabay.com/api/videos/?key={self.pixabay_key}"
            f"&q={urllib.parse.quote(query)}&video_type=all&per_page=5"
        )
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            log.debug(f"Pixabay search error for '{query}': {e}")
            return None

        hits = data.get("hits", [])
        if not hits:
            return None

        for hit in hits:
            vids = hit.get("videos", {})
            # Pixabay provides sizes: large, medium, small, tiny
            for size in ("medium", "large", "small"):
                item = vids.get(size)
                if item and item.get("url"):
                    w = item.get("width") or 0
                    h = item.get("height") or 0
                    if w <= 1920 and h <= 1080:
                        return item["url"]
            if vids.get("medium", {}).get("url"):
                return vids["medium"]["url"]
        return None

    # ------------------------------------------------------------------
    # Download & Cache
    # ------------------------------------------------------------------
    def download_clip(self, url: str) -> Path | None:
        """Download remote MP4 in chunks to cache_dir. Return cached Path."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        dest = self.cache_dir / f"broll_{url_hash}.mp4"
        if dest.exists() and dest.stat().st_size > 50000:
            return dest

        req = urllib.request.Request(url, headers={"User-Agent": "AUTOPILOT/2.0 VideoPipeline"})
        tmp_dest = self.cache_dir / f"tmp_{url_hash}.mp4"
        try:
            with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_dest, "wb") as f:
                while chunk := resp.read(64 * 1024):
                    f.write(chunk)
            if tmp_dest.stat().st_size > 50000:
                tmp_dest.replace(dest)
                return dest
            tmp_dest.unlink(missing_ok=True)
            return None
        except Exception as e:
            log.debug(f"Stock download failed for {url}: {e}")
            tmp_dest.unlink(missing_ok=True)
            return None

    # ------------------------------------------------------------------
    # Main B-Roll resolver per scene
    # ------------------------------------------------------------------
    def get_b_roll(self, scene: dict, orientation: str = "landscape") -> Path | None:
        """Find and download stock B-roll for a scene. Returns Path or None."""
        if not self.has_keys:
            return None

        text = scene.get("beat") or scene.get("image_prompt") or ""
        query = self.extract_keywords(text)
        if not query:
            return None

        # 1. Try Pexels first
        clip_url = self.search_pexels(query, orientation=orientation)
        # 2. Try Pixabay fallback
        if not clip_url:
            clip_url = self.search_pixabay(query)

        if not clip_url:
            return None

        return self.download_clip(clip_url)

    # ------------------------------------------------------------------
    # Manifest integration
    # ------------------------------------------------------------------
    def assign_manifest_scenes(
        self,
        scenes: list[dict],
        aspect: str = "16:9",
        max_stock_ratio: float = 0.5,
    ) -> list[dict]:
        """
        Mark each scene as type 'stock' or 'image'.
        If stock footage can be retrieved for eligible scenes, set type='stock' and 'path'.
        Otherwise set type='image' (graceful silent fallback to imagegen).
        """
        orient = "portrait" if aspect in ("9:16", "portrait") else "landscape"
        updated = []
        stock_count = 0
        max_stock = int(len(scenes) * max_stock_ratio)

        for i, sc in enumerate(scenes):
            sc_copy = dict(sc)
            # Reserve scene 1 and key character climax scenes for image generation
            is_first = (i == 0)
            is_candidate = (not is_first) and (stock_count < max_stock) and (i % 2 == 1)

            stock_path = None
            if is_candidate and self.has_keys:
                stock_path = self.get_b_roll(sc_copy, orientation=orient)

            if stock_path:
                sc_copy["type"] = "stock"
                sc_copy["stock_path"] = str(stock_path)
                stock_count += 1
                log.info(f"Scene {sc_copy.get('n', i+1)}: assigned stock B-roll ({stock_path.name})")
            else:
                sc_copy["type"] = "image"

            updated.append(sc_copy)

        return updated
