"""
core/video_analyzer.py — Video DNA & Feature Extraction Engine.

Analyzes video assets (MP4, audio, script, and visual metadata) to extract
quantitative features for Machine Learning model training, retention prediction,
and continuous optimization.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core.db import DB
from core.logbook import Logbook

log = Logbook("video_analyzer")

# High-retention psychological trigger keywords for Indian/Global YouTube Shorts
CURIOSITY_TRIGGERS = [
    "rahasya", "secret", "never", "kabhi nahi", "shocking", "sach", "truth",
    "par kyun", "kya hoga", "mystery", "kisi ko nahi pata", "khaufnaak",
    "bhoot", "haunted", "warning", "dekho", "aakhir", "chupa hua"
]


class VideoAnalyzer:
    def __init__(self, db: DB | None = None):
        self.db = db or DB()

    def analyze_video(self, video_id: int) -> dict[str, Any]:
        """
        Database mein maujood video row aur output directory se full Video DNA extract karo.
        """
        row = self.db.get_video(video_id)
        if not row:
            raise ValueError(f"Video #{video_id} nahi mila")
        row = dict(row)

        topic = row.get("topic") or ""
        length_sec = float(row.get("length_sec") or 30.0)
        hook_type = row.get("hook_type") or "contrarian"
        template_id = row.get("template_id") or "noir_teal"
        voice_id = row.get("voice_id") or "gem_m_grave"

        from core.config import ROOT
        vdir = ROOT / "output" / f"video_{video_id:04d}"
        script_text = row.get("caption") or ""
        if row.get("script_json"):
            try:
                sdata = json.loads(row["script_json"])
                if isinstance(sdata, dict) and "script" in sdata:
                    script_text = sdata["script"]
                elif isinstance(sdata, list):
                    script_text = " ".join(s.get("text", "") for s in sdata)
                elif isinstance(sdata, str):
                    script_text = sdata
            except Exception:
                pass

        script_file = vdir / "script.json"
        if not script_text and script_file.exists():
            try:
                with open(script_file, encoding="utf-8") as sf:
                    sdata = json.load(sf)
                    if isinstance(sdata, dict) and "script" in sdata:
                        script_text = sdata["script"]
                    elif isinstance(sdata, list):
                        script_text = " ".join(s.get("text", "") for s in sdata)
            except Exception:
                pass
        scene_count = 7  # default standard pacing
        scenes_meta = []

        meta_file = vdir / "metadata.json"
        if meta_file.exists():
            try:
                with open(meta_file, encoding="utf-8") as f:
                    meta_data = json.load(f)
                    if "scenes" in meta_data and isinstance(meta_data["scenes"], list):
                        scenes_meta = meta_data["scenes"]
                        scene_count = len(scenes_meta)
            except Exception:
                pass

        return self.extract_features_from_data(
            topic=topic,
            script=script_text,
            length_sec=length_sec,
            hook_type=hook_type,
            template_id=template_id,
            voice_id=voice_id,
            scene_count=scene_count,
            scenes=scenes_meta
        )

    def extract_features_from_data(
        self,
        topic: str,
        script: str,
        length_sec: float = 32.0,
        hook_type: str = "contrarian",
        template_id: str = "noir_teal",
        voice_id: str = "gem_m_grave",
        scene_count: int = 7,
        scenes: list[dict] | None = None
    ) -> dict[str, Any]:
        """
        Script aur parameters se numerical & categorical feature vector generate karo.
        """
        length_sec = max(float(length_sec), 5.0)
        words = re.findall(r"\w+", script)
        word_count = len(words)
        wpm = round((word_count / length_sec) * 60.0, 1)

        # Hook analysis (first 1-2 lines)
        lines = [line.strip() for line in script.splitlines() if line.strip()]
        first_line = lines[0] if lines else ""
        hook_words = len(re.findall(r"\w+", first_line))

        # Curiosity trigger density
        script_lower = script.lower()
        trigger_hits = sum(1 for trig in CURIOSITY_TRIGGERS if trig in script_lower)
        curiosity_density = round(trigger_hits / max(word_count, 1) * 100, 2)

        # Visual pacing
        scene_count = max(int(scene_count), 1)
        avg_scene_duration = round(length_sec / scene_count, 2)
        cuts_per_min = round((scene_count / length_sec) * 60.0, 1)

        # Visual template score mapping
        template_energy_map = {
            "noir_teal": 0.85,
            "cinematic_warm": 0.75,
            "cyberpunk_neon": 0.90,
            "dark_fantasy": 0.80,
            "retro_anime": 0.70,
        }
        visual_energy = template_energy_map.get(template_id, 0.75)

        # Hook type one-hot encoding weights
        hook_weights = {
            "contrarian": 0.92,
            "specific_outcome": 0.88,
            "question": 0.78,
            "pov": 0.82
        }
        hook_score = hook_weights.get(hook_type, 0.80)

        # Character presence in scenes
        has_character = 0.0
        if scenes:
            has_character = 1.0 if any("character" in str(s).lower() or "person" in str(s).lower() for s in scenes) else 0.0
        elif "vikram" in script_lower or "kabir" in script_lower or "chintu" in script_lower:
            has_character = 1.0

        # Structured Video DNA Output
        dna = {
            "metrics": {
                "word_count": word_count,
                "speech_wpm": wpm,
                "length_sec": length_sec,
                "scene_count": scene_count,
                "avg_scene_duration": avg_scene_duration,
                "cuts_per_min": cuts_per_min,
                "hook_words": hook_words,
                "curiosity_score": trigger_hits,
                "curiosity_density": curiosity_density,
                "has_character": bool(has_character),
            },
            "categorical": {
                "hook_type": hook_type,
                "template_id": template_id,
                "voice_id": voice_id,
                "length_bucket": "sub_30s" if length_sec < 30 else ("30_45s" if length_sec <= 45 else "long"),
            },
            # Normalized flat feature vector for ML regression models
            "feature_vector": [
                round(min(wpm / 220.0, 1.5), 3),             # 0: Speech speed norm (optimal 150-180 wpm)
                round(min(cuts_per_min / 35.0, 1.5), 3),       # 1: Cuts per min norm (optimal 18-26 cpm)
                round(min(length_sec / 60.0, 1.0), 3),         # 2: Duration norm (20-45s)
                round(min(hook_words / 15.0, 1.5), 3),         # 3: Hook brevity norm (punchy < 10 words)
                round(min(curiosity_density / 5.0, 1.5), 3),   # 4: Psychological trigger density
                round(visual_energy, 3),                       # 5: Visual style energy
                round(hook_score, 3),                          # 6: Hook category baseline weight
                round(has_character, 1),                       # 7: Character anchor continuity
            ]
        }

        return dna
