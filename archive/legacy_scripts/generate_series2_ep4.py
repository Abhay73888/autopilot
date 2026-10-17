#!/usr/bin/env python3
"""
generate_series2_ep4.py — Generate & Validate SERIES 2 EPISODE 4: "JO DIKH RAHA THA, WOH SACH NAHI THA".
Features:
- Realistic Cinematic Indian Romance Drama (7-Year Arc)
- Two-Character Emotional Movie Dialogue (Aarav & Meera)
- The Heartbreaking Long-Distance Misunderstanding
- High-Tension Sound Design: Felt Piano Melancholy + Whoosh Transitions
- Kinetic Center-Pop Subtitles (Emotion-coded Rose Pink & Gold)
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

log = Logbook("series2_ep4")

SERIES_CODE = "SERIES_2"
EPISODE_NUM = 4
TOPIC = "2020 — Jab Pyaar Online Tha: Episode 4 — Jo Dikh Raha Tha, Woh Sach Nahi Tha"
TITLE = "Jab Usne Kisi Aur Ke Saath Photo Daali... 💔🥺 | JAB PYAAR ONLINE THA (Ep 4) #Shorts"
CAPTION = (
    "Mohabbat mein fasle physical nahi hote... fasle tab aate hain jab baatein choti hone lagti hain. "
    "College badla, sheher badle... aur ek din Meera ne kisi aur ke saath photo post kar di. 💔🥺\n\n"
    "Aarav galat tha ya Meera ko explain karna chahiye tha? Agle episode (Part 5) ke liye COMMENT karein: 'PART 5'! 👇✨"
)
HASHTAGS = ["#JabPyaarOnlineTha", "#Series2", "#Episode4", "#Shorts", "#Romance", "#Heartbreak", "#LoveStory"]
HOOK_OVERLAY = "💔 JAB PYAAR ONLINE THA (EPISODE 4) 🥺"
COMMENT_BAIT = "Kya rishton mein shak pyaar ko khatam kar deta hai? Aarav galat tha ya Meera? COMMENT karo! 👇💔"

LINES = [
    {
        "speaker": "narrator",  # Aarav
        "text": "Mohabbat mein fasle sheheron se nahi aate... fasle tab aate hain jab ghanton ki baatein bas 'hmm' ban jaati hain.",
        "emotion": "melancholic",
        "role": "hook"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Aarav... main badli nahi hoon, meri family aur college mein bahut kuch chal raha hai.",
        "emotion": "sad",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Phir us shaam jab maine Instagram khola... Meera ki story par ek naye ladke ke saath photo thi.",
        "emotion": "intense",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Maine 10 baar call kiya... har baar phone busy aaya. Andar se aisi aag lagi ki maine likh diya: 'Shayad main hi bewakoof tha.'",
        "emotion": "angry",
        "role": "reveal"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Meera ka aakhri message aaya: 'Agar itne saalon baad bhi mujhpar bharosa nahi tha... toh alvida Aarav.'",
        "emotion": "crying",
        "role": "climax"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Story ka sach agle din pata chala... par tab tak bohot der ho chuki thi! Part 5 ke liye COMMENT karein!",
        "emotion": "shocked",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Aarav staring at dull blue light of smartphone in pitch-dark room
    "Cinematic 8k photorealistic close up: 18-year-old Indian boy Aarav lying alone in dark college hostel room, cold blue smartphone screen glowing on his heartbroken exhausted face, vertical 9:16, masterpiece, no text",
    
    # Scene 2: Meera sitting alone under heavy rain outside college library looking anxious
    "Cinematic 8k photorealistic shot: 18-year-old Indian girl Meera in simple kurti clutching her notebook under college porch during heavy monsoon rain, emotionally troubled eyes, vertical 9:16, realistic cinema, no text",
    
    # Scene 3: Instagram story interface on phone with smiling girl and male silhouette
    "Cinematic 8k realistic close up: cracked smartphone screen showing social media post with two people laughing under café lights, blurry background, vertical 9:16, shallow depth of field, no text",
    
    # Scene 4: Aarav's trembling fingers typing frantic aggressive texts
    "Dramatic 8k cinematic close up: male trembling fingers rapidly typing on chat keyboard, red unread notification badges, ambient dark shadow, vertical 9:16, no text",
    
    # Scene 5: Meera looking down at her phone with tears streaming down her cheeks
    "Heartbreaking 8k photorealistic close up: Meera's tear-streaked face reflecting phone screen, trembling lips, wearing delicate silver thread bracelet on wrist, vertical 9:16, emotional masterpiece, no text",
    
    # Scene 6: Aarav sitting on empty city staircase in rain with head in hands
    "Cinematic 8k wide vertical shot: lonely young Indian boy sitting on wet city staircase in pouring rain, head buried in hands, distant traffic headlights creating melancholic bokeh, vertical 9:16, no text"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT 10X: GENERATING SERIES 2 EPISODE 4 (JAB PYAAR ONLINE THA)")
    print("  Mode: GENERATE & PREPARE ONLY (NO UPLOAD - READY FOR TOMORROW)")
    print("=" * 75 + "\n")

    db = DB()
    t_start = time.time()

    # 1. Register Video in DB
    vid = db.create_video(
        topic=TOPIC,
        hook_type="cliffhanger",
        voice_id="hi_m_narrator",
        template_id="warm_nostalgia",
        notes=f"Series 2 Jab Pyaar Online Tha Episode 4 (10x Ultra HD & Dynamic Audio)"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Voice Generation
    print("\n🎙️ [Step 1] Synthesizing Dual Character Voices (Aarav & Meera)...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_narrator")
    print(f"  ✅ Voiceover generated: {voice_res['duration_sec']:.2f}s, {len(voice_res['words'])} words synced.")

    # 3. Image Generation (Flux 720x1280 HD)
    print("\n🎨 [Step 2] Generating 6 Ultra-HD Photorealistic Romance Scenes (Flux Engine)...")
    n_scenes = len(IMAGE_PROMPTS)
    dur_per_scene = voice_res["duration_sec"] / n_scenes

    motions = ["punch_in", "pan_left", "whip_zoom", "zoom_in_dramatic", "pan_right", "punch_in"]
    scenes = []
    for i, (prompt, motion) in enumerate(zip(IMAGE_PROMPTS, motions)):
        scenes.append({
            "n": i + 1,
            "file": f"scene_{i+1:02d}.jpg",
            "image_prompt": prompt,
            "motion": motion,
            "parallax": (i % 2 == 1),
            "dur": round(dur_per_scene, 3),
            "emotion": LINES[min(i, len(LINES)-1)].get("emotion", "emotional"),
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
            "hook_type": "cliffhanger",
            "hook_line": LINES[0]["text"],
            "hook_text_overlay": HOOK_OVERLAY,
            "comment_bait": COMMENT_BAIT,
            "cast": {
                "narrator": {"gender": "male", "persona": "Aarav"},
                "char_b": {"gender": "female", "persona": "Meera"}
            },
            "lines": LINES,
            "word_count": len(voice_res["words"]),
            "est_sec": voice_res["duration_sec"]
        },
        "narration": {
            "audio_path": voice_res["audio_path"],
            "duration_sec": voice_res["duration_sec"],
            "words_count": len(voice_res["words"]),
            "voice_id": "hi_m_narrator"
        },
        "words": voice_res["words"],
        "subtitles": {
            "style": "kinetic"
        },
        "effects": {
            "sound": {
                "heartbeat": True,
                "riser": False,
                "braam": False,
                "whoosh": True,
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "warm_nostalgia",
            "template_name": "Warm Nostalgic Indian Romance",
            "pacing": "medium",
            "setting": "College hostel, rainy city street, and smartphone screens",
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
    print(f"  🎉 SERIES 2 EPISODE 4 GENERATED & READY FOR TOMORROW!")
    print(f"  🎬 Video ID : #{vid}")
    print(f"  📁 Location : {render_info['video_path']}")
    print(f"  ⏱️ Time Taken: {total_sec}s")
    print(f"  📌 Status   : READY_TO_PUBLISH (No upload performed)")
    print("=" * 75 + "\n")

    return vid

if __name__ == "__main__":
    main()
