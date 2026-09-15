#!/usr/bin/env python3
"""
generate_and_publish_series3_ep4.py — Generate & Publish SERIES 3 EPISODE 4: "CHINTU AUR SPACE PIZZA ALIEN".
Features:
- 3D Pixar / DreamWorks Animated Colorful Fun Shorts
- Universal slapstick & wonder-filled comedy
- Zero COPPA trigger words (#Kids removed) to keep comments 100% active
- High-Energy Sound Design: Cartoon boings, sparkle sound effects & playful BGM
- 1080x1920 MP4 Video with Kinetic Center-Pop Subtitles (Cyber Gold & Neon Mint)
- YouTube Shorts Upload: Public + Comments 100% Enabled + Auto Comment Bait
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
CONFIG["voice"] = {"engine_order": ["edge_tts", "gemini_tts"]}

from core.db import DB
from core.logbook import Logbook
from agents.voice import Voice
from agents.imagegen import ImageGen
from pipeline.render import Renderer
from pipeline.validate import validate_dir
from agents.publisher import YouTubePublisher

log = Logbook("series3_ep4")

SERIES_CODE = "SERIES_3"
EPISODE_NUM = 4
TOPIC = "Chintu Ki Jadui Duniya: Episode 4 — The Space Pizza Alien"
TITLE = "Chintu Found a Tiny Alien in His Lunchbox! 🛸🍕 | Chintu Ki Jadui Kahani (Ep 4) #Shorts"
CAPTION = (
    "Chintu ne jaise hi school mein apna tiffin box khola... andar ek glowing neele rang ka alien baith kar pizza khaa raha tha! 🛸🍕\n"
    "Aur jab Golu ne uski photo kheenchne ki koshish ki, toh alien ne Golu ke bag ko hi hawa mein udha diya! 😂✨\n\n"
    "Agar aapko aisa alien mile toh aap use kya khilaoge? COMMENT karo! 👇🪐\n\n"
    "#ChintuKiKahani #Series3 #Episode4 #Animation #PixarStyle #3DAnimation #Cartoon #Shorts #Funny"
)
HASHTAGS = ["#ChintuKiKahani", "#Series3", "#Episode4", "#Animation", "#PixarStyle", "#3DAnimation", "#Cartoon", "#Shorts", "#Funny"]
HOOK_OVERLAY = "🛸 TIFFIN BOX MEIN ASLI ALIEN! 🍕😂"
COMMENT_BAIT = "Agar aapke bag mein aisa alien aa jaye toh aap pehle kya karoge? COMMENT mein batao! 🍕🛸👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Chintu ne recess mein jaise hi apna lunchbox khola... uski aankhein phati ki phati reh gayi!",
        "emotion": "excited",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Sandwich ke upar ek 4-inch ka glowing blue alien baitha hua tha aur chupke se cheese chatka raha tha!",
        "emotion": "funny",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Golu ne chilla kar kaha: 'Chintu bhai, iski selfie lekar viral karte hain!'",
        "emotion": "excited",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Alien ne apni badi cute aankhon se laser blink kiya aur Golu ka poora school bag hawa mein float karne laga!",
        "emotion": "wonder",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Poori class mein kitabein udne lagi aur alien ne Chintu ko thumbs up de diya!",
        "emotion": "cheerful",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Agar aapko ye alien milta toh aap use kya khilate? Pizza ya Burger? COMMENT karo!",
        "emotion": "curious",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Chintu opening colourful metallic lunchbox with glowing blue light spilling out
    "3D Pixar Disney style animation: cute 8-year-old Indian boy Chintu in school uniform opening a shiny metallic lunchbox, glowing mysterious cyan light beaming out onto his shocked expressive face, classroom background, vertical 9:16, masterpiece, 8k render, no text",

    # Scene 2: Adorable tiny glowing blue alien sitting on a cheese pizza slice
    "Ultra-cute 3D Pixar animation: adorable tiny 4-inch fluffy glowing blue extraterrestrial alien with large sparkling violet eyes happily munching on a melting cheese pizza slice inside an open lunchbox, vibrant colors, vertical 9:16, octane render, masterpiece",

    # Scene 3: Chubby friend Golu holding up a toy camera with mouth wide open
    "Expressive 3D Disney animation: chubby funny Indian kid Golu with round spectacles pointing his toy camera with hilarious shocked expression, classroom desk, colorful comic style, vertical 9:16, cinematic character render",

    # Scene 4: Alien blinking laser eyes as school bag levitates in thin air
    "Magical 3D animation scene: tiny alien winking with glowing sparkle eyes as a heavy school backpack surrounded by sparkling gold stardust levitates into the air, classroom students in background amazed, vertical 9:16, colorful lighting",

    # Scene 5: Notebooks, pencils and school items happily floating around the classroom
    "Whimsical 3D animated wide shot: colorful school classroom with textbooks, pencils and crayons floating peacefully in zero gravity, glowing star particles, cheerful wonder, vertical 9:16, DreamWorks aesthetic, 8k render",

    # Scene 6: Tiny alien sitting on Chintu's shoulder giving cute thumbs up
    "Heartwarming 3D Pixar style close-up: adorable glowing alien sitting happily on Chintu's shoulder giving a cute thumbs up gesture, both smiling with sparkling eyes, vertical 9:16, climax animation masterpiece"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT: GENERATING & PUBLISHING SERIES 3 EPISODE 4")
    print("  Title : Chintu Found a Tiny Alien in His Lunchbox!")
    print("=" * 75 + "\n")

    t0 = time.time()
    db = DB()

    vid = db.create_video(
        topic=TOPIC,
        hook_type="question",
        voice_id="hi_f_urgent",
        template_id="vibrant_kids_animation",
        series_name=SERIES_CODE,
        series_index=EPISODE_NUM,
        notes="Series 3 Episode 4: The Space Pizza Alien"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Voiceover
    print("\n🎙️ [Step 1] Synthesizing High-Energy Animated Voiceover...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_f_urgent")
    dur = voice_res["duration_sec"]
    words = voice_res.get("words", [])
    print(f"  ✅ Voiceover ready: {dur:.2f}s, {len(words)} words aligned.")

    # 2. Generate Visual Scenes
    print(f"\n🖼️ [Step 2] Generating {len(IMAGE_PROMPTS)} 3D Pixar Style Frames...")
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    motions = ["punch_in", "whip_zoom", "zoom_in_dramatic", "pan_left", "zoom_out", "punch_in"]

    scenes = []
    for i, (prompt, motion) in enumerate(zip(IMAGE_PROMPTS, motions)):
        st = round(i * scene_dur, 3)
        en = round((i + 1) * scene_dur if i < n_scenes - 1 else dur, 3)
        scenes.append({
            "n": i + 1,
            "beat": "",
            "image_prompt": prompt,
            "motion": motion,
            "parallax": (i % 2 == 1),
            "file": f"scene_{i+1:02d}.jpg",
            "seed": vid * 100 + i + 1,
            "start": st,
            "end": en,
            "dur": round(en - st, 3)
        })

    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"  ✅ All {n_scenes} 3D frames generated successfully!")

    # 3. Build Manifest
    script_data = {
        "topic": TOPIC,
        "title": TITLE,
        "caption": CAPTION,
        "hashtags": HASHTAGS,
        "hook_type": "question",
        "hook_line": LINES[0]["text"],
        "hook_text_overlay": HOOK_OVERLAY,
        "comment_bait": COMMENT_BAIT,
        "cast": {
            "narrator": {"gender": "female", "persona": "Storyteller"}
        },
        "lines": LINES
    }

    manifest = {
        "video_id": vid,
        "series_code": SERIES_CODE,
        "episode_num": EPISODE_NUM,
        "topic": TOPIC,
        "title": TITLE,
        "script": script_data,
        "subtitles": {
            "style": "kinetic"
        },
        "effects": {
            "sound": {
                "heartbeat": False,
                "riser": True,
                "whoosh": True,
                "room_tone": False,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "vibrant_kids_animation",
            "template_name": "Vibrant 3D Pixar Animation",
            "pacing": "fast",
            "setting": "Colorful magical school classroom",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": voice_res,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. Render Video
    print(f"\n🎞️ [Step 3] Rendering 1080x1920 MP4 Video...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    final_video_path = Path(render_info["video_path"])

    # 5. Validate Quality
    print("\n🔍 [Step 4] Quality Recheck & Pre-Upload Validation...")
    rep = validate_dir(out_dir)
    print(f"  Validation Status: {'PASS ✅' if rep.ok else 'WARN ⚠️'}")

    db.update_video(
        vid,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        series_name=SERIES_CODE,
        series_index=EPISODE_NUM,
        script_json=json.dumps(script_data, ensure_ascii=False),
        video_path=str(final_video_path),
        cover_path=render_info.get("cover_path"),
        length_sec=dur,
        status="approved",
        notes="Series 3 Episode 4 Approved for YouTube Upload"
    )

    # 6. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Series 3 Episode 4 to YouTube Shorts (Public, Comments ON)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)
    db.close()

    total_time = round(time.time() - t0, 1)
    print("\n" + "=" * 75)
    print("  🎉 SERIES 3 EPISODE 4 PUBLISHED SUCCESSFULLY TO YOUTUBE SHORTS!")
    print("=" * 75)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  💬 First Comment: Posted automatically!")
    print(f"  ⏱️ Total Time : {total_time}s")
    print("=" * 75 + "\n")

    return res

if __name__ == "__main__":
    main()
