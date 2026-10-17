#!/usr/bin/env python3
"""
generate_series4_ep3.py — Generate & Validate SERIES 4 EPISODE 3: "NA LOG NA SADKEIN".
Features:
- High-Energy Viral Interactive Comedy Shorts (Dimag Ka Dahi)
- 5-Second Ticking Countdown Timer with High-Tension SFX
- Mind-bending Riddle with Comic Reveal
- Kinetic Center-Pop Subtitles (Neon Emerald, Cyber Gold, Comic Pop)
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

log = Logbook("series4_ep3")

SERIES_CODE = "SERIES_4"
EPISODE_NUM = 3
TOPIC = "Dimag Ka Dahi: Episode 3 — Na Log Hain Na Sadkein"
TITLE = "Bade-Bade IAS Fail Ho Gaye! 99% Log Galat Sochte Hain! 😂🧠 | Dimag Ka Dahi (Ep 3) #Shorts"
CAPTION = (
    "Aisa kaun sa sheher hai jahan sheher toh hai par log nahi, jungle toh hai par ped nahi, aur nadi toh hai par paani nahi? 🧠🔥\n\n"
    "Agar 5 second mein answer pata chal gaya tha toh sach-sach COMMENT karo! 👇😂"
)
HASHTAGS = ["#DimagKaDahi", "#Series4", "#Episode3", "#FunnyShorts", "#Paheliyan", "#Riddles", "#Quiz", "#Trending", "#Shorts"]
HOOK_OVERLAY = "🧠 99% LOG GALAT SOCHENGE! 😂🔥"
COMMENT_BAIT = "Sach batana kis-kis ne Google kiya tha? Apna answer COMMENT karo! 😂👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Aaj ki paheli sunkar aapke dimaag ke fuse udd jayenge!",
        "emotion": "excited",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Aisa kaun sa sheher hai jahan sheher toh hai par insaan nahi... jungle hai par ped nahi... aur nadi hai par ek boond paani nahi?",
        "emotion": "mysterious",
        "role": "riddle"
    },
    {
        "speaker": "narrator",
        "text": "Sochne ke liye milte hain sirf paanch second... time shuru hota hai ab! Paanch, chaar, teen, do, ek!",
        "emotion": "countdown",
        "role": "timer"
    },
    {
        "speaker": "narrator",
        "text": "Jawab hai: NAKSHA yaani MAP! Jahan sab kuch hota hai par asliyat mein kuch nahi!",
        "emotion": "punchline",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Bina sharmaye sach-sach COMMENT mein batao kisne pehle galat socha tha!",
        "emotion": "hilarious",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Ultra dramatic glowing neon brain with smoking gears
    "Cinematic 3D render: glowing neon holographic brain with golden gears spinning and playful cartoon steam coming out of ears, dark moody cyberpunk studio background, vertical 9:16, 8k, masterpiece, no text",
    
    # Scene 2: Surreal miniature city with crystal buildings and dry glowing riverbed
    "Surreal cinematic fantasy shot: tiny miniature empty city glowing on wooden table, empty tiny streets with glowing streetlights, dry blue crystal riverbed, vertical 9:16, tilt-shift photography, macro lens, no text",
    
    # Scene 3: Huge glowing neon digital countdown timer (5... 4... 3...)
    "Dynamic 3D high-energy shot: giant glowing holographic digital clock ticking with red and amber lightning sparks, tension-filled cinematic lighting, vertical 9:16, masterpiece, no text",
    
    # Scene 4: An ancient ornate treasure map unfolding with miniature 3D mountains and oceans popping out
    "Cinematic close up 3D render: old vintage pirate paper map unfolding on rustic oak table, 3D tiny paper mountains and ink rivers standing up, golden warm light, vertical 9:16, hyperdetailed, no text",
    
    # Scene 5: Cartoon 3D mascot laughing holding his stomach in tears of laughter
    "3D Pixar style character render: funny colorful quirky character clutching his stomach laughing hysterically with tears rolling, bright neon studio background, vertical 9:16, vibrant lighting, no text"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT 10X: GENERATING SERIES 4 EPISODE 3 (DIMAG KA DAHI)")
    print("=" * 75 + "\n")

    db = DB()
    t_start = time.time()

    vid = db.create_video(
        topic=TOPIC,
        hook_type="humor",
        voice_id="hi_m_intense",
        template_id="comic_pop",
        notes="Series 4 Episode 3: Na Log Na Sadkein (Map Riddle)"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n🎙️ [Step 1] Synthesizing Energetic Host Voiceover...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_intense")
    print(f"  ✅ Voiceover generated: {voice_res['duration_sec']:.2f}s, {len(voice_res['words'])} words synced.")

    print("\n🎨 [Step 2] Generating 5 Comedy / Riddle 3D Scenes...")
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
                "narrator": {"gender": "male", "persona": "Energetic Quiz Host"}
            },
            "lines": LINES,
            "word_count": len(voice_res["words"]),
            "est_sec": voice_res["duration_sec"]
        },
        "narration": {
            "audio_path": voice_res["audio_path"],
            "duration_sec": voice_res["duration_sec"],
            "words_count": len(voice_res["words"]),
            "voice_id": "hi_m_energetic"
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
            "template_id": "comic_pop",
            "template_name": "Comic Pop Quiz Show",
            "pacing": "fast",
            "setting": "Neon quiz studio, mystical miniature city",
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
        notes="Series 4 Ep 3 approved."
    )
    db.close()

    total_sec = round(time.time() - t_start, 1)
    print(f"\n🎉 SERIES 4 EPISODE 3 READY in {total_sec}s! (Video #{vid})")
    return vid

if __name__ == "__main__":
    main()
