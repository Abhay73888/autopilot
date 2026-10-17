#!/usr/bin/env python3
"""
generate_series1_ep9.py — Generate & Validate SERIES 1 EPISODE 9: "LOOP KA ANTH YA MEERA KI MAUT?".
Features:
- Dark Anime Psychological Time-Loop Thriller (MAPPA aesthetic)
- Dual Voiceover (Terrified Kabir + Mysterious Temporal Entity)
- High-Tension Sound Design: 38Hz Braam Hit + Temporal Riser + Whooshes
- Kinetic Center-Pop Subtitles with semantic color coding
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

log = Logbook("series1_ep9")

SERIES_CODE = "SERIES_1"
EPISODE_NUM = 9
TOPIC = "Kaal-Rekha Part 9: The Impossible Choice (Loop Ka Anth Ya Meera Ki Maut?)"
TITLE = "Meera Ko Bachau Ya Time-Loop Todu?! 😱⏳ | KAAL-REKHA (Part 9) #Shorts"
CAPTION = (
    "Sach saamne aa chuka hai... time-loop kisi dushman ne nahi, Kabir ne khud Meera ko bachane ke liye banaya tha! "
    "Lekin ab Roman number III se ghatt kar II ho chuka hai. Agar loop toota... toh Meera mar jayegi! 😱⏳\n\n"
    "Grand Season Finale (Part 10) ke liye COMMENT karein: 'PART 10'! 👇🔥"
)
HASHTAGS = ["#KaalRekha", "#Series1", "#Part9", "#AnimeShorts", "#TimeLoop", "#Shorts", "#Trending"]
HOOK_OVERLAY = "⏳ KAAL-REKHA (PART 9: THE CHOICE) 😱"
COMMENT_BAIT = "Kabir ko kya karna chahiye? Loop tod kar aazad ho ya Meera ke liye hamesha qaid rahe? Vote in COMMENTS! 👇⏳"

LINES = [
    {
        "speaker": "narrator",  # Kabir
        "text": "Maine Meera ki maut ko rokne ke liye... waqt ko 3:17 AM par qaid kiya tha?!",
        "emotion": "shocked",
        "role": "hook"
    },
    {
        "speaker": "char_b",    # Temporal Entity
        "text": "Saaye ne aage badhkar kaha: 'Waqt ka kanta ghoom chuka hai Kabir... Roman number III ab II ban chuka hai!'",
        "emotion": "cold",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Kabir
        "text": "Deewaron par lagi hazaron ghadiyon ki suiyan ulti disha mein cheekhne lagi!",
        "emotion": "urgent",
        "role": "body"
    },
    {
        "speaker": "char_b",    # Temporal Entity
        "text": "'Agar tune temporal lever kheench kar loop toda... toh Meera usi second zameen par dum tod degi!'",
        "emotion": "intense",
        "role": "climax"
    },
    {
        "speaker": "narrator",  # Kabir
        "text": "Achanak hawa mein Meera ki kaanpti hui aawaz goonji: 'Kabir... mere liye khud ko mat mitana!'",
        "emotion": "vulnerable",
        "role": "climax"
    },
    {
        "speaker": "narrator",  # Kabir
        "text": "Haath kaanpte hue lever par chala gaya... loop todu ya Meera ko bachau? Finale Part 10 ke liye COMMENT karein!",
        "emotion": "desperate",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Kabir standing in front of the colossal glowing clock core
    "Cinematic 8k photorealistic dark anime shot of 21-year-old Kabir Sen in torn black jacket staring in sheer horror at a colossal glowing temporal core mechanism, violet lightning, vertical 9:16, MAPPA aesthetic, masterpiece, no text",
    
    # Scene 2: Mysterious masked entity pointing an ominous finger
    "Dramatic 8k anime shot of tall mysterious cloaked temporal entity with porcelain mask and glowing violet aura, pointing finger forward as Roman numeral II burns in thin air, volumetric lighting, vertical 9:16, no text",
    
    # Scene 3: Thousands of antique wall clocks ticking violently in reverse
    "Hyper-detailed 8k dark anime perspective of infinite cathedral walls lined with thousands of ornate brass grandfather clocks with spinning reverse needles, glowing sparks flying, vertical 9:16, cinematic masterpiece, no text",
    
    # Scene 4: Ominous crimson temporal lever mounted on stone pedestal
    "Cinematic 8k anime close up: ancient heavy crimson temporal lever with glowing mechanical gears and crackling violet electricity on an obsidian pedestal, vertical 9:16, high contrast, no text",
    
    # Scene 5: Ghostly translucent silhouette of weeping Meera suspended in air
    "Ethereal 8k anime shot of beautiful translucent ghostly silhouette of 20-year-old Indian girl Meera with glowing tears reaching out through purple temporal mist, vertical 9:16, emotional cinematic, no text",
    
    # Scene 6: Kabir's trembling hand gripping the crimson lever
    "Terrifying 8k anime dramatic close up of Kabir's determined sweat-drenched face with glowing Roman numeral II burning on his collarbone, gripping the heavy iron lever ready to pull, vertical 9:16, climax masterpiece, no text"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT 10X: GENERATING SERIES 1 EPISODE 9 (KAAL-REKHA)")
    print("  Mode: GENERATE & PREPARE ONLY (NO UPLOAD - READY FOR TOMORROW)")
    print("=" * 75 + "\n")

    db = DB()
    t_start = time.time()

    # 1. Register Video in DB
    vid = db.create_video(
        topic=TOPIC,
        hook_type="cliffhanger",
        voice_id="hi_m_intense",
        template_id="dark_anime_thriller",
        notes=f"Series 1 Kaal-Rekha Episode 9 (10x Ultra HD & Dynamic Audio)"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Voice Generation
    print("\n🎙️ [Step 1] Synthesizing Dual Voiceover (Kabir + Temporal Entity)...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_intense")
    print(f"  ✅ Voiceover generated: {voice_res['duration_sec']:.2f}s, {len(voice_res['words'])} words synced.")

    # 3. Image Generation (Flux 720x1280 HD)
    print("\n🎨 [Step 2] Generating 6 Ultra-HD Photorealistic Anime Scenes (Flux Engine)...")
    n_scenes = len(IMAGE_PROMPTS)
    dur_per_scene = voice_res["duration_sec"] / n_scenes

    motions = ["punch_in", "whip_zoom", "pan_left", "zoom_in_dramatic", "zoom_out", "punch_in"]
    scenes = []
    for i, (prompt, motion) in enumerate(zip(IMAGE_PROMPTS, motions)):
        scenes.append({
            "n": i + 1,
            "file": f"scene_{i+1:02d}.jpg",
            "image_prompt": prompt,
            "motion": motion,
            "parallax": (i % 2 == 1),
            "dur": round(dur_per_scene, 3),
            "emotion": LINES[min(i, len(LINES)-1)].get("emotion", "intense"),
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
                "narrator": {"gender": "male", "persona": "Kabir"},
                "char_b": {"gender": "male", "persona": "Entity"}
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
                "braam": True,
                "whoosh": True,
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "dark_anime_thriller",
            "template_name": "Dark Anime Psychological Thriller",
            "pacing": "fast",
            "setting": "Cathedral subterranean clock sanctuary",
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
    print(f"  🎉 SERIES 1 EPISODE 9 GENERATED & READY FOR TOMORROW!")
    print(f"  🎬 Video ID : #{vid}")
    print(f"  📁 Location : {render_info['video_path']}")
    print(f"  ⏱️ Time Taken: {total_sec}s")
    print(f"  📌 Status   : READY_TO_PUBLISH (No upload performed)")
    print("=" * 75 + "\n")

    return vid

if __name__ == "__main__":
    main()
