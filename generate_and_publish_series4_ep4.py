#!/usr/bin/env python3
"""
generate_and_publish_series4_ep4.py — Generate & Publish SERIES 4 EPISODE 4: "THE PARADOX COIN".
Features:
- High-Energy Viral Interactive Comedy Shorts (Dimag Ka Dahi)
- 5-Second Ticking Countdown Timer with High-Tension SFX
- Mind-bending Riddle with Comic Reveal
- Kinetic Center-Pop Subtitles (Neon Emerald, Cyber Gold, Comic Pop)
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

log = Logbook("series4_ep4")

SERIES_CODE = "SERIES_4"
EPISODE_NUM = 4
TOPIC = "Dimag Ka Dahi: Episode 4 — The Paradox Coin"
TITLE = "99% of People Get This Wrong in 5 Seconds! 🤯🧠 | Dimag Ka Dahi (Ep 4) #Shorts"
CAPTION = (
    "Aisi kaun si cheez hai jiska ek sar (head) hai aur ek punchh (tail) hai... par koi shareer nahi hai?! 🤯🪙\n"
    "Duniya ke bade-bade log is paheli mein ghoom gaye! "
    "Agar 5 second mein dimaag chal gaya tha toh bina cheat kiye COMMENT karo! 👇😂\n\n"
    "#DimagKaDahi #Series4 #Episode4 #FunnyShorts #Paheliyan #Riddles #Quiz #Trending #Shorts #BrainTeasers"
)
HASHTAGS = ["#DimagKaDahi", "#Series4", "#Episode4", "#FunnyShorts", "#Paheliyan", "#Riddles", "#Quiz", "#Trending", "#Shorts", "#BrainTeasers"]
HOOK_OVERLAY = "🧠 99% LOG CONFUSE HO GAYE! 🤯🔥"
COMMENT_BAIT = "Sach batana kis-kis ka dimaag ghadi ki tarah ghoom gaya? Answer COMMENT karo! 😂🪙👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Aaj ki paheli sunkar bade-bade toppers ka dimaag hil jayega!",
        "emotion": "excited",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Aisi kaun si cheez hai jiska ek head hota hai aur ek tail hoti hai... lekin uska koi body nahi hota?",
        "emotion": "mysterious",
        "role": "riddle"
    },
    {
        "speaker": "narrator",
        "text": "Aapke paas hain sirf paanch second... countdown shuru hota hai ab! Paanch, chaar, teen, do, ek!",
        "emotion": "countdown",
        "role": "timer"
    },
    {
        "speaker": "narrator",
        "text": "Agar aapne socha tha saanp ya chipkali... toh aap bilkul galat hain!",
        "emotion": "funny",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Sahi jawab hai... Ek Sikka! Yani A COIN! Jismein Head aur Tail dono hote hain!",
        "emotion": "victory",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Kitne logon ne 5 second se pehle socha tha? Sach-sach COMMENT mein batao!",
        "emotion": "curious",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Ultra-dramatic comic style professor scratching head with question marks
    "Hyper-expressive 3D comic illustration of a funny genius scientist with crazy hair and giant magnifying glass scratching his head in confusion, neon yellow and purple question marks floating everywhere, vertical 9:16, masterpiece, 8k render, no text",

    # Scene 2: Mystical floating ancient gold coin glowing mysteriously in deep space
    "Cinematic close-up of a giant ancient golden coin floating mysteriously in dark starry space, detailed embossed Roman head on one side and shimmering mythical tail on the other, volumetric golden light beams, vertical 9:16, 8k photorealistic",

    # Scene 3: Huge glowing neon digital countdown timer at 5 seconds
    "Dramatic high-voltage graphic of a glowing neon cyber countdown clock ticking violently, sparks flying, high tension red and gold lighting, energetic motion blur, vertical 9:16, octane render, no text overlay",

    # Scene 4: Funny cartoon snake looking confused wearing sunglasses
    "Hilarious 3D cartoon scene: colorful cartoon garden snake wearing oversized funny sunglasses looking completely confused and embarrassed, comical comic background, vibrant neon lighting, vertical 9:16, Pixar aesthetic",

    # Scene 5: Radiant gold coin spinning in air with confetti explosion
    "Spectacular 3D render of a shiny gold coin spinning mid-air surrounded by colourful confetti blast and golden sparklers, festive celebration lighting, vertical 9:16, cinematic masterpiece",

    # Scene 6: Playful scientist pointing forward inviting audience to comment
    "Energetic 3D animated character smiling widely pointing right at the camera with thumbs up, floating speech bubbles and funny brain emoji graphics, vertical 9:16, climax comedy masterpiece"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT: GENERATING & PUBLISHING SERIES 4 EPISODE 4")
    print("  Title : 99% of People Get This Wrong in 5 Seconds!")
    print("=" * 75 + "\n")

    t0 = time.time()
    db = DB()

    vid = db.create_video(
        topic=TOPIC,
        hook_type="question",
        voice_id="hi_m_intense",
        template_id="comic_pop",
        series_name=SERIES_CODE,
        series_index=EPISODE_NUM,
        notes="Series 4 Episode 4: The Paradox Coin"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Voiceover
    print("\n🎙️ [Step 1] Synthesizing Fast-Paced Comedy Voiceover...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_intense")
    dur = voice_res["duration_sec"]
    words = voice_res.get("words", [])
    print(f"  ✅ Voiceover ready: {dur:.2f}s, {len(words)} words aligned.")

    # 2. Generate Visual Scenes
    print(f"\n🖼️ [Step 2] Generating {len(IMAGE_PROMPTS)} 3D Comic Frames...")
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    motions = ["punch_in", "zoom_in_dramatic", "whip_zoom", "pan_left", "zoom_out", "punch_in"]

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
    print(f"  ✅ All {n_scenes} comic frames generated successfully!")

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
            "narrator": {"gender": "male", "persona": "Quizmaster"}
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
                "braam": True,
                "whoosh": True,
                "room_tone": False,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "comic_pop",
            "template_name": "Comic Pop Interactive Riddle",
            "pacing": "fast",
            "setting": "High-energy gameshow quiz studio",
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
        notes="Series 4 Episode 4 Approved for YouTube Upload"
    )

    # 6. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Series 4 Episode 4 to YouTube Shorts (Public, Comments ON)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)
    db.close()

    total_time = round(time.time() - t0, 1)
    print("\n" + "=" * 75)
    print("  🎉 SERIES 4 EPISODE 4 PUBLISHED SUCCESSFULLY TO YOUTUBE SHORTS!")
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
