#!/usr/bin/env python3
"""
publish_forbidden_vault.py — Generate and publish brand new viral mystery video to YouTube Shorts.
Topic: Padmanabhaswamy Temple Vault B Mystery.
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
from core.logbook import Logbook
from agents.voice import Voice
from agents.imagegen import ImageGen
from pipeline.render import Renderer
from pipeline.validate import validate_dir
from agents.publisher import YouTubePublisher

log = Logbook("auto_creator")

TOPIC = "Padmanabhaswamy Temple Vault B: Wo Rahasyamayi Darwaza Jise Kholne Se Sabhi Darte Hain"
TITLE = "Duniya Ka Sabse Rahasyamayi Darwaza: Vault B Ka Khaufnak Sach! 🐍 #Shorts"
CAPTION = "Padmanabhaswamy Mandir ke Vault B ka rahasya jo aaj tak koi nahi suljha paya! Kya is darwaze ke peeche khazana hai ya shraap? 👇"
HASHTAGS = ["#PadmanabhaswamyTemple", "#VaultBMystery", "#MysteryShorts", "#HindiMystery", "#Shorts", "#ViralShorts"]
HOOK_OVERLAY = "Vault B: The Forbidden Door 🐍"
COMMENT_BAIT = "Aapke hisaab se kya is darwaze ko kabhi kholna chahiye? Comment mein batao!"

LINES = [
    {
        "speaker": "narrator",
        "text": "Is mandir ke aakhri darwaze ke peeche arbon ka khazana hai ya seedhi maut?",
        "emotion": "serious",
        "role": "hook"
    },
    {
        "speaker": "char_a",
        "text": "Padmanabhaswamy mandir ke paanch gupt kamre khol diye gaye, lekin Vault B ko chhoone se bhi sab darte hain.",
        "emotion": "cold",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Is darwaze par na koi tala hai na chaabi, ise sirf pracheen Naga Bandham mantra se seal kiya gaya tha.",
        "emotion": "mysterious",
        "role": "body"
    },
    {
        "speaker": "char_a",
        "text": "Kehte hain jo bhi ise zabardasti kholne gaya, uske saath ajeeb haadse hone lage!",
        "emotion": "whispers",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Kya ye darwaza sach mein kisi bhyanak shraap ki hifazat kar raha hai?",
        "emotion": "cold",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Majestic ancient Indian temple stone corridors at night, mystical fog, glowing oil lamps, dramatic shadows, dark noir teal cartoon style, cinematic composition, vertical 9:16, no text, no letters",
    "Massive mysterious iron vault door carved with two gigantic King Cobras, forbidden sealed ancient vault B, dramatic golden torchlight, eerie dark shadows, vertical 9:16, no text, no letters",
    "Ancient Sanskrit glowing symbols floating in dark mystical air around a sealed temple door guarded by cobras, eerie atmospheric suspense, vertical 9:16, no text, no letters",
    "Silhouette of an archaeologist in fear standing in front of a dark cursed forbidden door, flickering torchlight, high suspense, vertical 9:16, no text, no letters",
    "Extreme dramatic close-up of ancient iron cobra sculpture on forbidden vault gate, glowing sinister eyes, dark stone texture, vertical 9:16, no text, no letters",
    "Outer view of grand majestic Hindu temple under dark stormy midnight sky, lightning in background, golden aura, cinematic suspense, vertical 9:16, no text, no letters"
]


def main():
    print("\n" + "=" * 70)
    print("  🚀 AUTOPILOT: GENERATING & PUBLISHING BRAND NEW TOPIC TO YOUTUBE")
    print("=" * 70)
    print(f"  📌 Topic: {TOPIC}")
    print(f"  🎬 Title: {TITLE}")
    print("=" * 70 + "\n")

    t0 = time.time()
    db = DB()

    # 1. DB Video Record creation
    script_data = {
        "topic": TOPIC,
        "title": TITLE,
        "caption": CAPTION,
        "hashtags": HASHTAGS,
        "hook_type": "contrarian",
        "hook_line": LINES[0]["text"],
        "hook_text_overlay": HOOK_OVERLAY,
        "comment_bait": COMMENT_BAIT,
        "cast": {
            "narrator": {"gender": "male", "persona": "gambhir mystery narrator"},
            "char_a": {"name": "Archaeologist", "gender": "male", "persona": "curious researcher"}
        },
        "lines": LINES,
        "word_count": sum(len(l["text"].split()) for l in LINES),
        "est_sec": 26.0
    }

    vid = db.create_video(
        TOPIC,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        hook_type="contrarian",
        script_json=script_data,
        length_sec=26,
        status="planned"
    )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} directory created: {out_dir}")

    # 2. Narration Audio Generation (Voice)
    print("\n🎙️ Generating narration audio via Voice agent...")
    voice_agent = Voice(db=db)
    # Generate audio
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_grave")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Narration ready: {dur:.1f}s, {len(words)} words ({narration_info['audio_path']})")

    # 3. Scene Timings calculation
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    scenes = []
    for i, p in enumerate(IMAGE_PROMPTS):
        st = round(i * scene_dur, 3)
        en = round((i + 1) * scene_dur if i < n_scenes - 1 else dur, 3)
        scenes.append({
            "n": i + 1,
            "beat": "",
            "image_prompt": p,
            "motion": ["zoom_in", "pan_left", "zoom_out", "pan_right", "zoom_in", "pan_left"][i % 6],
            "parallax": (i % 2 == 1),
            "file": f"scene_{i+1:02d}.jpg",
            "seed": vid * 100 + i + 1,
            "start": st,
            "end": en,
            "dur": round(en - st, 3)
        })

    # 4. Generate Images (ImageGen)
    print("\n🖼️ Generating 6 atmospheric scenes via Pollinations...")
    img_agent = ImageGen(providers=["pollinations", "local_placeholder"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print("✅ All scene images generated successfully!")

    # 5. Build Manifest
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "script": script_data,
        "art": {
            "template_id": "noir_teal",
            "template_name": "Noir Teal",
            "pacing": "standard",
            "setting": "ancient temple vault",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4 (Renderer)
    print("\n🎥 Rendering full video with FFmpeg (effects, audio, subtitles)...")
    render_info = Renderer(manifest).render(out_dir, preset="fast", keep_temp=False)
    db.update_video(
        vid,
        video_path=render_info["video_path"],
        cover_path=render_info["cover_path"],
        length_sec=render_info["duration_sec"],
        status="rendered"
    )
    print(f"✅ Render complete: {render_info['video_path']}")
    print(f"   Duration: {render_info['duration_sec']}s, Size: {render_info['size_mb']}MB")

    # 7. Validate specs
    print("\n🔍 Validating video specifications...")
    rep = validate_dir(out_dir)
    manifest["render"] = render_info
    manifest["validation"] = rep.to_dict()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   Validation: {'PASS ✅' if rep.ok else 'WARN ⚠️'}")

    # 8. Approve video in database
    db.set_status(vid, "approved", note="Auto-approved for direct YouTube upload")
    print(f"✅ Video #{vid} status set to APPROVED in database")

    # 9. Upload to YouTube Shorts
    print("\n🚀 Uploading to YouTube Shorts (public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()

    total_time = round(time.time() - t0, 1)
    print("\n" + "=" * 70)
    print("  🎉 CONGRATULATIONS! VIDEO SUCCESSFULLY PUBLISHED TO YOUTUBE!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  ⏱️ Time Taken : {total_time}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
