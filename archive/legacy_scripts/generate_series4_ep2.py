#!/usr/bin/env python3
"""
generate_series4_ep2.py — Generate & Validate SERIES 4 EPISODE 2: "DUNIYA KA SABSE CHAALAAK SAWAL".
Features:
- High-Energy Viral Interactive Comedy Shorts (Dimag Ka Dahi)
- 5-Second Ticking Countdown Timer with High-Tension SFX
- Hilarious Punchline Reveal
- Kinetic Center-Pop Subtitles (Neon Emerald, Cyber Gold, Comic Pop)
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

log = Logbook("series4_ep2")

SERIES_CODE = "SERIES_4"
EPISODE_NUM = 2
TOPIC = "Dimag Ka Dahi: Episode 2 — Subah 4 Taang, Dopahar 2 Taang, Shaam 3 Taang"
TITLE = "Dimag Hil Jayega! 95% Log Fail Ho Gaye! 😂🧠 | Dimag Ka Dahi (Ep 2) #Shorts"
CAPTION = (
    "Aisa sawal jiska jawab sabke paas hai... par pehli baar mein 95% log galat sochte hain! 😂 "
    "Aisi kaun si cheez hai jo subah 4 taangon par, dopahar ko 2 par, aur shaam ko 3 par chalti hai? 🧠🔥\n\n"
    "Sach-sach batao kisne galat socha tha? Bina sharmaye COMMENT karo apna score! 👇😂"
)
HASHTAGS = ["#DimagKaDahi", "#Series4", "#Episode2", "#FunnyShorts", "#Paheliyan", "#Riddles", "#Quiz", "#Shorts"]
HOOK_OVERLAY = "🧠 DIMAG KA DAHI: 95% FAIL! 😂🔥"
COMMENT_BAIT = "Sach-sach batao, kisne pehle galat socha tha? Bina sharmaye COMMENT karo apna score! 😂👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Duniya ki sabse mashhoor paheli... jisme bade-bade topper fail ho jaate hain!",
        "emotion": "excited",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Aisi kaun si cheez hai jo subah ko chaar taangon par, dopahar ko do taangon par, aur shaam ko teen taangon par chalti hai?!",
        "emotion": "teasing",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Aur pehle hi sun lo! Koi ajeeb jaanwar ya robot mat bolna, wo jawab bilkul galat hai!",
        "emotion": "funny",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Sochne ke liye milte hain 5 second! Paanch... Chaar... Teen... Do... Ek... STOP!",
        "emotion": "intense",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Asli jawab hai: INSAAN! Bachpan mein ghutno par 4 taang, jawani mein 2 pair, aur budhape mein lathi ke sahare 3 taang!",
        "emotion": "climax",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Ab sach-sach batao, kisne pehle galat socha tha? Bina sharmaye COMMENT karke apna score batao!",
        "emotion": "cheerful",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Funny perplexed 3D character scratching head with giant question marks
    "Hyper-expressive 3D cartoon character with wide bulging eyes and funny hair, scratching head with hands in sheer comic confusion, giant glowing neon question marks hovering, vibrant pop studio lighting, vertical 9:16, masterpiece, no text",
    
    # Scene 2: Surreal comic clock showing sunrise, noon sun, and evening moon in split panel
    "Hyper-colorful 3D pop art illustration showing morning golden sunrise, bright noon sun, and glowing twilight moon in vibrant comic layout, playful cartoon clouds, vertical 9:16, 8k render, no text",
    
    # Scene 3: Hilarious robot and funny monster waving arms saying 'wrong'
    "Funny 3D animated cartoon robot and adorable silly monster wearing big comical glasses shaking heads vigorously with funny red X signs, vertical 9:16, high energy comedy, no text",
    
    # Scene 4: Giant glowing neon 5-second countdown clock vibrating intensely
    "Dramatic high-voltage 3D neon countdown timer glowing with vibrant cyan and electric gold sparks, speed motion lines, energetic studio setting, vertical 9:16, no text",
    
    # Scene 5: Beautiful heartwarming 3-stage cartoon illustration: cute crawling baby, confident walking youth, and smiling grandfather with cane
    "Heartwarming 3D Pixar character montage in warm sunny park: adorable baby crawling on all fours, energetic cheerful young student walking, and sweet kind elderly grandfather smiling with walking stick, vertical 9:16, masterpiece, no text",
    
    # Scene 6: Witty quizmaster laughing playfully pointing directly at camera
    "Hyper-expressive 3D animated character holding a golden microphone, laughing joyfully and pointing finger playfully at the camera, confetti and golden stars bursting, vertical 9:16, masterpiece, no text"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT 10X: GENERATING SERIES 4 EPISODE 2 (DIMAG KA DAHI)")
    print("  Mode: GENERATE & PREPARE ONLY (NO UPLOAD - READY FOR TOMORROW)")
    print("=" * 75 + "\n")

    db = DB()
    t_start = time.time()

    # 1. Register Video in DB
    vid = db.create_video(
        topic=TOPIC,
        hook_type="question",
        voice_id="hi_m_intense",
        template_id="quiz_pop",
        notes=f"Series 4 Dimag Ka Dahi Episode 2 (10x Ultra HD & Dynamic Audio)"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Voice Generation
    print("\n🎙️ [Step 1] Synthesizing High-Energy Quizmaster Voice...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_intense")
    print(f"  ✅ Voiceover generated: {voice_res['duration_sec']:.2f}s, {len(voice_res['words'])} words synced.")

    # 3. Image Generation (Flux 720x1280 HD)
    print("\n🎨 [Step 2] Generating 6 Ultra-HD 3D Comic Scenes (Flux Engine)...")
    n_scenes = len(IMAGE_PROMPTS)
    dur_per_scene = voice_res["duration_sec"] / n_scenes

    motions = ["punch_in", "whip_zoom", "pan_left", "zoom_in_dramatic", "pan_right", "punch_in"]
    scenes = []
    for i, (prompt, motion) in enumerate(zip(IMAGE_PROMPTS, motions)):
        scenes.append({
            "n": i + 1,
            "file": f"scene_{i+1:02d}.jpg",
            "image_prompt": prompt,
            "motion": motion,
            "parallax": (i % 2 == 1),
            "dur": round(dur_per_scene, 3),
            "emotion": LINES[min(i, len(LINES)-1)].get("emotion", "excited"),
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
                "narrator": {"gender": "male", "persona": "Quizmaster"}
            },
            "lines": LINES,
            "word_count": len(voice_res["words"]),
            "est_sec": voice_res["duration_sec"]
        },
        "narration": {
            "audio_path": voice_res["audio_path"],
            "duration_sec": voice_res["duration_sec"],
            "words_count": len(voice_res["words"]),
            "voice_id": "hi_m_intense"
        },
        "words": voice_res["words"],
        "subtitles": {
            "style": "kinetic"
        },
        "effects": {
            "sound": {
                "heartbeat": True,
                "riser": True,
                "braam": False,
                "whoosh": True,
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "quiz_pop",
            "template_name": "High Energy Comedy Quiz",
            "pacing": "fast",
            "setting": "Colorful 3D comic quiz studio with pop art elements",
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
    print(f"  🎉 SERIES 4 EPISODE 2 GENERATED & READY FOR TOMORROW!")
    print(f"  🎬 Video ID : #{vid}")
    print(f"  📁 Location : {render_info['video_path']}")
    print(f"  ⏱️ Time Taken: {total_sec}s")
    print(f"  📌 Status   : READY_TO_PUBLISH (No upload performed)")
    print("=" * 75 + "\n")

    return vid

if __name__ == "__main__":
    main()
