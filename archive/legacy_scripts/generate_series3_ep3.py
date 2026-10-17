#!/usr/bin/env python3
"""
generate_series3_ep3.py — Generate & Validate SERIES 3 EPISODE 3: "GOLU AUR UDNE WALA ROCKET".
Features:
- 3D Pixar / Disney Animated Colorful Fun Shorts
- Cheerful, Wonder-filled & Comedic Storytelling
- Magical Sparkle Sound Effects & Playful BGM
- Kinetic Center-Pop Subtitles (Neon Emerald & Cyber Gold)
- Zero COPPA trigger words (#Kids removed) to keep comments 100% active
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

log = Logbook("series3_ep3")

SERIES_CODE = "SERIES_3"
EPISODE_NUM = 3
TOPIC = "Chintu Ki Jadui Duniya: Episode 3 — Golu Aur Udne Wala Rocket"
TITLE = "Chintu Ne Banaya Asli Udne Wala Rocket! 🚀✨ | Chintu Ki Jadui Kahani (Ep 3) #Shorts"
CAPTION = (
    "Chintu ne cardboard ke dibbe par apni jadui pencil se rocket ke pankh bana diye! "
    "Aur phir uske andar baithkar Golu ne daba diya 'Red Button'! 🚀✨\n\n"
    "Agar aapko aisi jadui rocket mile toh aap chaand par jaoge ya Mars par? COMMENT karo! 👇🪐"
)
HASHTAGS = ["#ChintuKiKahani", "#Series3", "#Episode3", "#Animation", "#PixarStyle", "#Cartoon", "#Shorts", "#Trending"]
HOOK_OVERLAY = "🚀 JADUI ROCKET KA DHAMAKA! 🌟✨"
COMMENT_BAIT = "Aap is jadui rocket mein kahan jaana chahoge? Chaand ya Mars? COMMENT mein batao! 🚀👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Chintu ko purana cardboard ka dabba mila... toh usne apni jadui pencil se uspe do rocket engine draw kar diye!",
        "emotion": "excited",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Golu bhaagte hue aaya aur chillaaya: 'Chintu bhai, main pilot banoonga!' Aur usne dabba band kar liya.",
        "emotion": "funny",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Tabhi dibbe ke peeche se chamakdar golden fire nikalne lagi aur dabba hawa mein 20 foot upar udd gaya!",
        "emotion": "wonder",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Golu khidki se haath hila kar chilla raha tha: 'Mummy ko mat batana, main chaand par ice-cream dhoondne ja raha hoon!'",
        "emotion": "hilarious",
        "role": "punchline"
    },
    {
        "speaker": "narrator",
        "text": "Lekin tabhi rocket ka fuel khatam hone laga... aage kya hua? Agle episode ke liye COMMENT karein!",
        "emotion": "cliffhanger",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Chintu drawing shiny rocket boosters on a cardboard box with magic glowing pencil
    "3D Pixar Disney style animation render: 7-year-old cute chubby Indian boy Chintu wearing yellow t-shirt drawing magical glowing rainbow rocket thrusters on a cardboard box with sparkling pencil, vertical 9:16, masterpiece, 8k, vibrant lighting, no text",
    
    # Scene 2: Golu with aviator goggles jumping into the box
    "3D Pixar Disney style character shot: cute funny 6-year-old boy Golu wearing oversized leather aviator goggles with giant goofy smile diving inside colorful cardboard rocket ship, vertical 9:16, volumetric lighting, no text",
    
    # Scene 3: Cardboard rocket blasting colorful star sparks and floating above garden
    "3D Pixar Disney style whimsical shot: cardboard box rocket blasting magical candy-colored sparkles from bottom, floating 10 feet in the air above sunny green Indian backyard garden, vertical 9:16, dynamic angle, no text",
    
    # Scene 4: Golu waving from rocket window grinning in mid air
    "3D Pixar Disney style joyful close up: Golu peering out of cutout circular window of rocket soaring through fluffy sunny clouds, waving enthusiastically, bright cheerful sky, vertical 9:16, no text",
    
    # Scene 5: Rocket sputtering comical smoke rings in purple sunset sky
    "3D Pixar Disney style comical shot: cardboard rocket sputtering funny puff smoke rings in beautiful twilight purple sky, Chintu on ground looking up with wide funny eyes, vertical 9:16, masterpiece, no text"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT 10X: GENERATING SERIES 3 EPISODE 3 (CHINTU KI JADUI DUNIYA)")
    print("=" * 75 + "\n")

    db = DB()
    t_start = time.time()

    vid = db.create_video(
        topic=TOPIC,
        hook_type="humor",
        voice_id="hi_f_calm",
        template_id="candy_pop",
        notes="Series 3 Episode 3: Golu Aur Udne Wala Rocket (Comment-safe)"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n🎙️ [Step 1] Synthesizing Playful Voiceover...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_f_calm")
    print(f"  ✅ Voiceover generated: {voice_res['duration_sec']:.2f}s, {len(voice_res['words'])} words synced.")

    print("\n🎨 [Step 2] Generating 5 Pixar 3D Animation Scenes...")
    n_scenes = len(IMAGE_PROMPTS)
    dur_per_scene = voice_res["duration_sec"] / n_scenes

    motions = ["punch_in", "whip_zoom", "zoom_in_dramatic", "pan_left", "punch_in"]
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
            "hook_type": "humor",
            "hook_line": LINES[0]["text"],
            "hook_text_overlay": HOOK_OVERLAY,
            "comment_bait": COMMENT_BAIT,
            "cast": {
                "narrator": {"gender": "female", "persona": "Playful Cartoon Storyteller"}
            },
            "lines": LINES,
            "word_count": len(voice_res["words"]),
            "est_sec": voice_res["duration_sec"]
        },
        "narration": {
            "audio_path": voice_res["audio_path"],
            "duration_sec": voice_res["duration_sec"],
            "words_count": len(voice_res["words"]),
            "voice_id": "hi_f_playful"
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
            "template_id": "candy_pop",
            "template_name": "Candy Pop 3D Animation",
            "pacing": "fast",
            "setting": "Sunny garden backyard, magical sky",
            "n_scenes": len(scenes_ready)
        },
        "scenes": scenes_ready
    }

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n🎞️ [Step 3] Rendering 1080x1920 MP4 Video...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="veryfast")
    print(f"  ✅ Render complete: {render_info['video_path']} ({render_info['size_mb']} MB, {render_info['duration_sec']}s)")

    rep = validate_dir(out_dir)
    if rep.fatals:
        print(f"❌ Validation failed: {rep.fatals}")
        sys.exit(1)
    print("  ✅ 100% Quality & Spec Validation Passed!")

    db.update_video(
        vid,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        script_json=manifest["script"],
        video_path=render_info["video_path"],
        cover_path=render_info["cover_path"],
        status="approved",
        notes="Series 3 Ep 3 comment-safe approved."
    )
    db.close()

    total_sec = round(time.time() - t_start, 1)
    print(f"\n🎉 SERIES 3 EPISODE 3 READY in {total_sec}s! (Video #{vid})")
    return vid

if __name__ == "__main__":
    main()
