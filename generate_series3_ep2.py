#!/usr/bin/env python3
"""
generate_series3_ep2.py — Generate & Validate SERIES 3 EPISODE 2: "GOLU AUR CHOCOLATE KA BADAL".
Features:
- 3D Pixar / Disney Animated Colorful Kids Shorts (Chintu & Golu)
- Cheerful, Wonder-filled & Comedic Storytelling
- Magical Sparkle Sound Effects & Playful BGM
- Kinetic Center-Pop Subtitles (Neon Emerald & Cyber Gold)
- Status: READY_TO_PUBLISH (No YouTube Upload until user commands tomorrow)
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

log = Logbook("series3_ep2")

SERIES_CODE = "SERIES_3"
EPISODE_NUM = 2
TOPIC = "Chintu Ki Jadui Duniya: Episode 2 — Golu Aur Chocolate Ka Badal"
TITLE = "Golu Ke Ghar Par Chocolate Ki Baarish! 🍫☁️ | Chintu Ki Jadui Kahani (Ep 2) #Kids #Shorts"
CAPTION = (
    "Chintu ne apni jadui pencil se aasmaan mein ek chocolate ka badal draw kar diya! "
    "Aur phir aasmaan se shuru ho gayi garam chocolate aur marshmallows ki baarish! 🍫✨\n\n"
    "Agar aapke ghar ke upar aisi baarish ho, toh aap kis cheez mein chocolate bharoge? Bucket ya Mug? COMMENT karo! 👇😋"
)
HASHTAGS = ["#ChintuKiKahani", "#Series3", "#Episode2", "#KidsShorts", "#Animation", "#PixarStyle", "#Shorts"]
HOOK_OVERLAY = "🍫 JADUI CHOCOLATE KI BAARISH! ☁️✨"
COMMENT_BAIT = "Agar aasmaan se chocolate barse toh aap Bucket bharoge ya Tub? COMMENT mein batao! 🍫👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Jab Chintu ko bohot zoron ki bhook lagi... toh usne apni jadui pencil se aasmaan mein ek badal draw kiya!",
        "emotion": "excited",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Lekin ye koi aam badal nahi tha... ye tha poora CHOCOLATE ka badal!",
        "emotion": "cheerful",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Golu ne aasmaan ki taraf dekha aur tap-tap karke chocolate ki meethi boondein girne lagi!",
        "emotion": "sweet",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Phir aasmaan se hawa mein tairte hue giant marshmallow girne lage! Golu toh khushi se jump karne laga!",
        "emotion": "excited",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Lekin badal itna bada ho gaya ki poori gali mein chocolate ki nadi behne lagi!",
        "emotion": "funny",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Agar aapke ghar par aisi baarish ho toh aap Bucket bharoge ya Tub? Jaldi se COMMENT karke batao!",
        "emotion": "cheerful",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Chintu drawing in the sky with glowing magical pencil
    "Hyper-vibrant 3D Pixar Disney animation style: adorable 7-year-old Indian boy Chintu in bright red hoodie holding a glowing golden magical pencil, drawing a fluffy smiling cloud in vivid blue sky, vertical 9:16, 8k render, masterpiece, no text",
    
    # Scene 2: Giant chocolate brown cloud forming with delicious cocoa steam
    "Hyper-vibrant 3D Pixar style: massive fluffy delicious chocolate fudge cloud floating in sunny sky with sweet sparkling candy stars around it, warm golden lighting, vertical 9:16, masterpiece, no text",
    
    # Scene 3: Fluffy blue monster Golu looking up with giant happy eyes
    "Hyper-vibrant 3D animation style: adorable fluffy pastel-blue fur monster Golu with big twinkling purple eyes and tiny golden horns, opening mouth to catch delicious glossy chocolate drops, vertical 9:16, no text",
    
    # Scene 4: Giant fluffy marshmallows raining down gently
    "Hyper-detailed 3D Disney Pixar scene: giant soft white marshmallows and rainbow sprinkles gently raining down into a lush green colorful garden, magical sparkles, vertical 9:16, no text",
    
    # Scene 5: Chintu and Golu splashing joyfully in a flowing sweet chocolate river
    "Hyper-vibrant 3D animation: Chintu and Golu happily splashing and playing inside a smooth glossy chocolate stream flowing through playful cartoon neighborhood, vertical 9:16, no text",
    
    # Scene 6: Chintu holding up a giant colorful bucket with wide cheerful smile
    "Hyper-vibrant 3D Pixar character close up: cheerful Chintu holding up a bright yellow bucket overflowing with chocolate and candy, winking playfully at viewer, vertical 9:16, masterpiece, no text"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT 10X: GENERATING SERIES 3 EPISODE 2 (CHINTU KI JADUI DUNIYA)")
    print("  Mode: GENERATE & PREPARE ONLY (NO UPLOAD - READY FOR TOMORROW)")
    print("=" * 75 + "\n")

    db = DB()
    t_start = time.time()

    # 1. Register Video in DB
    vid = db.create_video(
        topic=TOPIC,
        hook_type="question",
        voice_id="hi_f_calm",
        template_id="pixar_kids_3d",
        notes=f"Series 3 Chintu Ki Jadui Duniya Episode 2 (10x Ultra HD & Dynamic Audio)"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Voice Generation
    print("\n🎙️ [Step 1] Synthesizing Cheerful Kids Storyteller Voice...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_f_calm")
    print(f"  ✅ Voiceover generated: {voice_res['duration_sec']:.2f}s, {len(voice_res['words'])} words synced.")

    # 3. Image Generation (Flux 720x1280 HD)
    print("\n🎨 [Step 2] Generating 6 Ultra-HD Pixar 3D Animated Scenes (Flux Engine)...")
    n_scenes = len(IMAGE_PROMPTS)
    dur_per_scene = voice_res["duration_sec"] / n_scenes

    motions = ["punch_in", "whip_zoom", "zoom_in_dramatic", "pan_left", "pan_right", "punch_in"]
    scenes = []
    for i, (prompt, motion) in enumerate(zip(IMAGE_PROMPTS, motions)):
        scenes.append({
            "n": i + 1,
            "file": f"scene_{i+1:02d}.jpg",
            "image_prompt": prompt,
            "motion": motion,
            "parallax": (i % 2 == 1),
            "dur": round(dur_per_scene, 3),
            "emotion": LINES[min(i, len(LINES)-1)].get("emotion", "cheerful"),
            "role": LINES[min(i, len(LINES)-1)].get("role", "body")
        })

    img_agent = ImageGen()
    scenes_ready = img_agent.generate_all(scenes, out_dir, seed_base=vid * 100)
    print(f"  ✅ All {len(scenes_ready)} scenes rendered in HD.")

    # 4. Build Manifest
    manifest = {
        "video_id": vid,
        "series_code": SERIES_CODE,
        "episode_num": EPISODE_NUM,
        "topic": TOPIC,
        "title": TITLE,
        "script": {
            "topic": TOPIC,
            "title": TITLE,
            "caption": CAPTION,
            "hashtags": HASHTAGS,
            "hook_type": "question",
            "hook_line": LINES[0]["text"],
            "hook_text_overlay": HOOK_OVERLAY,
            "comment_bait": COMMENT_BAIT,
            "cast": {
                "narrator": {"gender": "female", "persona": "Kids Storyteller"}
            },
            "lines": LINES,
            "word_count": len(voice_res["words"]),
            "est_sec": voice_res["duration_sec"]
        },
        "narration": {
            "audio_path": voice_res["audio_path"],
            "duration_sec": voice_res["duration_sec"],
            "words_count": len(voice_res["words"]),
            "voice_id": "hi_f_calm"
        },
        "words": voice_res["words"],
        "subtitles": {
            "style": "kinetic"
        },
        "effects": {
            "sound": {
                "heartbeat": False,
                "riser": False,
                "braam": False,
                "whoosh": True,
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "pixar_kids_3d",
            "template_name": "3D Pixar Kids Adventure",
            "pacing": "fast",
            "setting": "Colorful magical backyard with candy weather",
            "n_scenes": len(scenes_ready)
        },
        "scenes": scenes_ready
    }

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Render Video (FFmpeg + Kinetic Subtitles + Sound FX)
    print("\n🎞️ [Step 3] Rendering 1080x1920 MP4 Video (Ken Burns + Sound FX + Kinetic Subs)...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="veryfast")
    print(f"  ✅ Render complete: {render_info['video_path']} ({render_info['size_mb']} MB, {render_info['duration_sec']}s)")

    # 6. Validate Output
    rep = validate_dir(out_dir)
    if rep.fatals:
        print(f"❌ Validation failed with errors: {rep.fatals}")
        sys.exit(1)
    print("  ✅ 100% Quality & Spec Validation Passed!")

    # 7. Update Database with Ready-to-Publish Status
    db.update_video(
        vid,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        script_json=manifest["script"],
        video_path=render_info["video_path"],
        cover_path=render_info["cover_path"],
        status="approved",
        notes=f"Generated and set up with 10x quality. Waiting for user publish command."
    )
    db.close()

    total_sec = round(time.time() - t_start, 1)
    print("\n" + "=" * 75)
    print(f"  🎉 SERIES 3 EPISODE 2 GENERATED & READY FOR TOMORROW!")
    print(f"  🎬 Video ID : #{vid}")
    print(f"  📁 Location : {render_info['video_path']}")
    print(f"  ⏱️ Time Taken: {total_sec}s")
    print(f"  📌 Status   : READY_TO_PUBLISH (No upload performed)")
    print("=" * 75 + "\n")

    return vid

if __name__ == "__main__":
    main()
