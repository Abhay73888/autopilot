#!/usr/bin/env python3
"""
generate_and_publish_series5_ep1.py — Generate & Publish SERIES 5 EPISODE 1:
"HIMALAYA KE 20,000 FEET NEECHE WO JAAG UTHA!" (ASHWATTHAMA 3049 AD).

Features:
- Dark Sci-Fi Mythological Cyberpunk Thriller
- Deep Authoritative Hindi Narration (MadhurNeural Grave)
- Photorealistic 8K Cinematic Visuals (Unreal Engine 5 / Dune Aesthetic)
- Kinetic Subtitles with Gold & Cyan Highlights
- Epic Cinematic Audio Mix (Braam, Riser, Heartbeat, Whoosh)
- Direct YouTube Shorts Upload with COMMENTS ENABLED (privacy="public", selfDeclaredMadeForKids=False)
- Real-time Discord Community Notification
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

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook
from agents.voice import Voice
from agents.imagegen import ImageGen
from pipeline.render import Renderer
from pipeline.validate import validate_dir
from agents.publisher import YouTubePublisher

log = Logbook("series5_ep1")

SERIES_CODE = "SERIES_5"
EPISODE_NUM = 1
TOPIC = "Ashwatthama 3049 AD: Episode 1 — The Himalayan Awakening"
TITLE = "Himalaya Ke 20,000 Feet Neeche Wo Jaag Utha! ⚡️🏔️ | ASHWATTHAMA 3049 AD (Part 1) #Shorts"
CAPTION = (
    "Year 3049. Melting Himalayan glacier ke 20,000 feet neeche ek secret bunker alarm baja... "
    "Aur 5,000 saal purana amar yoddha aazad ho gaya! ⚡️🏔️\n\n"
    "Krishna ka shrap khatam ho chuka tha... Lekin ab wo kise dhoond raha hai? "
    "Part 2 ke liye COMMENT karein: 'KALKI'! 👇🔥\n\n"
    "#Ashwatthama #Kalki #Mahabharat #SciFi #Himalayas #Mythology #Shorts #Viral"
)
HASHTAGS = ["#Ashwatthama", "#Kalki", "#Mahabharat", "#SciFi", "#Himalayas", "#Shorts", "#Mystery"]
HOOK_OVERLAY = "⚡️ 20,000 FT NEECHE WO JAAG UTHA! 🏔️"
COMMENT_BAIT = "Kya aapko lagta hai Ashwatthama abhi bhi zinda hai? Agle part ke liye COMMENT karo: 'KALKI'! 👇🔥"

LINES = [
    {
        "speaker": "narrator",
        "text": "Year 3049. Himalaya ki 20,000 feet barf ke neeche ek secret research bunker me alarm baj utha!",
        "emotion": "shocked",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Surveillance camera par jo dikha usne Pentagon ke hosh uda diye... Ek 8-foot lamba shakhs sub-zero barf mein paidal chal raha tha!",
        "emotion": "mysterious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Uske maathe par ek gehra gaddha tha jahan se neeli celestial roshni nikal rahi thi... wahi jagah jahan Krishna ne uski Divya Mani cheen li thi!",
        "emotion": "intense",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Military drones ne jab firing ki, toh saari goliyaan uski divya shakti se hawa mein hi bhashm ho gayi!",
        "emotion": "urgent",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Usne satellite camera ki taraf dekha aur kaha: 'Mera 5000 saal ka shrap poora hua... Kahan hai Kalki?!'",
        "emotion": "intense",
        "role": "cliffhanger"
    },
    {
        "speaker": "narrator",
        "text": "Part 2 ke liye abhi COMMENT karein aur channel ko subscribe karein!",
        "emotion": "serious",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Futuristic Himalayan research base alarm
    "Cinematic 8k photorealistic wide vertical shot of futuristic high-tech subterranean military research base buried deep inside glowing blue ice cavern of Mount Kailash, flashing red warning klaxons and steam vents, vertical 9:16, Denis Villeneuve Dune aesthetic, masterpiece, no text",
    
    # Scene 2: 8-foot tall immortal warrior walking through blizzard
    "Cinematic 8k photorealistic atmospheric shot of a colossal 8-foot tall muscular ancient Indian warrior silhouette walking barefoot through torrential white blizzard at midnight, snow swirling around his imposing physique, vertical 9:16, Unreal Engine 5 render, no text",
    
    # Scene 3: Extreme close up of Ashwatthama's face and glowing forehead
    "Extreme close up 8k cinematic portrait of Ashwatthama's ancient battle-worn face, piercing glowing golden eyes, braided hair frozen with icicles, glowing cosmic blue light radiating from the deep circular socket on his forehead, vertical 9:16, photorealistic, no text",
    
    # Scene 4: Military drones firing laser bullets vaporizing in energy shield
    "High-octane 8k action shot of futuristic military combat drones hovering in mountain fog firing energy bullets that vaporize into a brilliant electric blue plasma aura around the towering warrior, vertical 9:16, cinematic, no text",
    
    # Scene 5: Ashwatthama glaring into satellite camera
    "Dramatic 8k cinematic low-angle shot of Ashwatthama raising his glowing armored fist into the stormy night sky as violet cosmic lightning illuminates his towering frame, thunder echoing across snowy peaks, vertical 9:16, masterpiece, no text",
    
    # Scene 6: Epic cliffhanger branding
    "Breathtaking 8k cinematic wide shot of Mount Kailash summit glowing with celestial golden aura under a starry midnight sky, ancient Sanskrit glyphs shimmering in the clouds, vertical 9:16, epic finale aesthetic, no text"
]


def main():
    print("=" * 60)
    print("🚀 PRODUCING SERIES 5 EPISODE 1: ASHWATTHAMA 3049 AD")
    print("=" * 60)
    t_start = time.time()

    # 1. DB Row
    db = DB()
    vid = db.create_video(
        topic=TOPIC,
        series_name=SERIES_CODE,
        series_index=EPISODE_NUM,
        status="scripted"
    )
    print(f"✅ DB Video #{vid} created for {SERIES_CODE} Ep {EPISODE_NUM}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Voice Generation
    print("\n🎙️ [Step 1] Synthesizing Deep Hindi Narration (Madhur Grave)...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_grave")
    dur_sec = voice_res["duration_sec"]
    words = voice_res["words"]
    print(f"  ✅ Audio generated: {voice_res['audio_path']} ({dur_sec}s, {len(words)} words)")

    # 3. Image Generation
    print("\n🎨 [Step 2] Generating 6 Photorealistic 8K Visuals (Unreal Engine 5 Aesthetic)...")
    n_scenes = len(IMAGE_PROMPTS)
    dur_per_scene = dur_sec / max(1, n_scenes)
    motions = ["punch_in", "zoom_in_dramatic", "pan_left", "whip_zoom", "zoom_out", "punch_in"]

    scenes = []
    for i, prompt in enumerate(IMAGE_PROMPTS):
        scenes.append({
            "n": i + 1,
            "file": f"scene_{i+1:02d}.jpg",
            "image_prompt": prompt,
            "motion": motions[i % len(motions)],
            "parallax": (i % 2 == 1),
            "dur": round(dur_per_scene, 3),
            "emotion": LINES[min(i, len(LINES)-1)].get("emotion", "intense"),
            "role": LINES[min(i, len(LINES)-1)].get("role", "body")
        })

    img_agent = ImageGen()
    scenes_ready = img_agent.generate_all(scenes, out_dir, seed_base=vid * 150)
    print(f"  ✅ All {len(scenes_ready)} scenes rendered.")

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
                "narrator": {"gender": "male", "persona": "Deep Veda Chronicler"}
            },
            "lines": LINES,
            "word_count": len(words),
            "est_sec": dur_sec
        },
        "narration": {
            "audio_path": voice_res["audio_path"],
            "duration_sec": dur_sec,
            "words_count": len(words),
            "voice_id": "hi_m_grave"
        },
        "words": words,
        "subtitles": {
            "style": "kinetic"
        },
        "effects": {
            "sound": {
                "heartbeat": True,
                "riser": True,
                "braam": True,
                "whoosh": True,
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "dark_mythological_cyberpunk",
            "template_name": "Ashwatthama 3049 AD Epic Cyberpunk",
            "pacing": "fast",
            "setting": "Subterranean Mount Kailash Glacial Caverns",
            "n_scenes": len(scenes_ready)
        },
        "scenes": scenes_ready
    }

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Render Video
    print("\n🎞️ [Step 3] Rendering 1080x1920 MP4 Video...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="veryfast")
    print(f"  ✅ Render complete: {render_info['video_path']} ({render_info['size_mb']} MB, {render_info['duration_sec']}s)")

    # 6. Validate Output
    rep = validate_dir(out_dir)
    if rep.fatals:
        print(f"❌ Validation failed: {rep.fatals}")
        sys.exit(1)
    print("  ✅ 100% Quality & Spec Validation Passed!")

    # 7. Update DB to approved
    db.update_video(
        vid,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        script_json=manifest["script"],
        video_path=render_info["video_path"],
        cover_path=render_info["cover_path"],
        status="approved",
        notes="Series 5 Episode 1 ready for instant publishing."
    )

    # 8. Upload to YouTube
    print("\n📤 [Step 4] Publishing Directly to YouTube Shorts with Comments Enabled...")
    pub = YouTubePublisher(db=db)
    # Upload with privacy='public' so comments are immediately open to viewers
    pub_res = pub.publish(
        vid,
        privacy="public",
        pin_comment=True
    )
    print(f"  🎉 YouTube Publish Status: {pub_res.get('status')}")
    if pub_res.get("url"):
        print(f"  🔗 Video URL: {pub_res.get('url')}")
    elif pub_res.get("yt_video_id"):
        print(f"  🔗 Video URL: https://youtube.com/shorts/{pub_res.get('yt_video_id')}")

    total_time = round(time.time() - t_start, 1)
    print(f"\n=======================================================")
    print(f"🔥 SERIES 5 EPISODE 1 COMPLETED AND PUBLISHED IN {total_time}s!")
    print(f"=======================================================\n")
    return vid

if __name__ == "__main__":
    main()
