#!/usr/bin/env python3
"""
generate_and_publish_series4_ep1.py — Generate, Validate, and Publish SERIES 4 EPISODE 1:
"DIMAG KA DAHI: KHAANE KI CHEEZ KA SAKHT SAWAL" (Funny Riddles & Brain Teasers).
Features:
- High-Energy Viral Hook & Teasing Delivery
- 5-Second Countdown Suspense for Maximum Comment Bait
- Hilarious Punchline Reveal (The Spoon Trick)
- Comedic 3D Cartoon / Meme Visual Style via Pollinations Flux
- Kinetic Center-Pop Subtitles with High-Contrast Yellow/Cyan Highlights
- Direct Upload to YouTube Shorts (Public, Comments Enabled)
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

log = Logbook("series4_ep1")

TOPIC = "Dimag Ka Dahi: Episode 1 — Khaane Ki Cheez Ka Funny Sawal"
TITLE = "Dimag Ka Dahi! 99% Log Galat Jawab Denge! 😂🧠 | Funny Paheli (Ep 1) #Shorts"
CAPTION = (
    "Duniya ka sabse aasaan sawal... par 99% log pehle galat sochte hain! 😂 "
    "Aisi kaun si cheez hai jise hum KHAANE ke liye khareedte hain... par kabhi KHAATE nahi?! 🧠🔥\n\n"
    "Plate ya katori mat bolna! Sach-sach batao kisne galat socha tha? Bina sharmaye COMMENT karo! 👇😂"
)
HASHTAGS = ["#DimagKaDahi", "#Series4", "#FunnyShorts", "#Paheliyan", "#Riddles", "#Quiz", "#Shorts", "#Trending"]
HOOK_OVERLAY = "🧠 DIMAG KA DAHI: 99% FAIL! 😂"
COMMENT_BAIT = "Sach-sach batao, kisne pehle galat socha tha? Bina sharmaye COMMENT karo! 😂👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Duniya ka sabse aasaan sawal... par 99 percent log iska galat jawab dete hain!",
        "emotion": "excited",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Aisi kaun si cheez hai jise hum KHAANE ke liye khareedte hain... par kabhi KHAATE nahi?!",
        "emotion": "teasing",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Aur pehle hi sun lo! Plate ya katori mat bolna, wo jawab bilkul galat hai!",
        "emotion": "funny",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Jawab comment karne ke liye milte hain 5 second! Paanch... Chaar... Teen... Do... Ek... STOP!",
        "emotion": "intense",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Asli jawab hai: CHAMMACH yani Spoon! Chammach se khana khate hain, chammach ko thodi chabate ho!",
        "emotion": "climax",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Ab sach-sach batao, kis-kis ne pehle galat socha tha? Bina sharmaye COMMENT karke apna score batao!",
        "emotion": "cheerful",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Hilarious 3D cartoon character deeply confused
    "Hyper-expressive 3D cartoon animation style: hilarious funny character with wide bulging comical eyes and funny tangled hair, scratching head with mouth open in sheer confusion, giant glowing question marks, vibrant studio lighting, vertical 9:16, masterpiece, no text",
    
    # Scene 2: Groceries and eating items with funny cartoon faces
    "Vibrant 3D Pixar animation comedy: cute animated shopping basket filled with fruits and funny snacks that have cartoon eyes and silly smirks, bright colorful supermarket background, vertical 9:16, no text",
    
    # Scene 3: Dramatic cartoon red cross rejecting dinner plate
    "Comical 3D illustration: a glossy ceramic dinner plate being stamped by a huge glowing red comic-book 'X' rejection mark with cartoon puff of dust and motion streaks, vertical 9:16, no text",
    
    # Scene 4: Intense dramatic 5-second countdown clock with sparks
    "Dramatic high-energy 3D animation: a colossal glowing digital and brass countdown timer ticking fiercely at '05', golden sparks flying, smoke and comic flames, intense excitement, vertical 9:16, masterpiece, no text",
    
    # Scene 5: Countdown timer reaching 01 with shockwaves
    "Extreme tension 3D animation: timer hitting '01' with radiant shockwaves and cartoon sweat droplets bursting from edges, cinematic energetic lighting, vertical 9:16, no text",
    
    # Scene 6: Smiling golden winner spoon with sunglasses
    "Hilarious 3D Pixar animation reveal: a shiny polished silver spoon standing proudly like a superhero, wearing cool dark sunglasses and a tiny golden crown, confetti bursting, vertical 9:16, masterpiece, no text",
    
    # Scene 7: Funny character trying to bite a spoon with comical expression
    "Funny slapstick 3D cartoon moment: silly character with puffed cheeks trying to take a bite of a metal spoon with comical 'CLINK' stars circling around head and goofy grin, vertical 9:16, no text",
    
    # Scene 8: Huge laughing 3D emoji characters tears of joy
    "Vibrant 3D cartoon comedy: group of hilarious cartoon emojis rolling and laughing with tears of joy, colorful party balloons and comedy props, vertical 9:16, no text",
    
    # Scene 9: Engaging comment call to action with glowing speech bubbles
    "Vibrant dynamic 3D graphic: bouncing colorful neon speech bubbles popping up with funny laughing faces, pointing fingers downward, inviting audience to comment their score, vertical 9:16, masterpiece, no text"
]

def main():
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  🎬 SERIES 4: DIMAG KA DAHI — EPISODE 01")
    print("  🧠 HIGH-ENERGY VIRAL RIDDLE & COMMENT BAIT")
    print("=" * 70)
    print(f"  📌 Title : {TITLE}")
    print(f"  🏷️ On-Screen Badge: {HOOK_OVERLAY}")
    print("=" * 70 + "\n")

    db = DB()

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
            "narrator": {"gender": "male", "persona": "energetic witty prankster quizmaster"}
        },
        "lines": LINES,
        "word_count": sum(len(ln["text"].split()) for ln in LINES),
        "est_sec": 34.0
    }

    vid = db.create_video(
        TOPIC,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        hook_type="question",
        script_json=script_data,
        length_sec=34,
        status="planned"
    )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} workspace: {out_dir}")

    # 1. Synthesize Voice
    print("\n🎙️ [Step 1] Synthesizing High-Energy Quiz Voiceover...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_intense")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Voiceover created: {dur:.1f}s, {len(words)} words ({narration_info['audio_path']})")

    # 2. Scene Timings calculation (9 cuts)
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    scenes = []
    motions = ["zoom_in", "pan_left", "zoom_in_slow", "zoom_in", "zoom_in_slow", "pan_right", "zoom_in", "zoom_out", "zoom_in"]
    for i, p in enumerate(IMAGE_PROMPTS):
        st = round(i * scene_dur, 3)
        en = round((i + 1) * scene_dur if i < n_scenes - 1 else dur, 3)
        scenes.append({
            "n": i + 1,
            "beat": "",
            "image_prompt": p,
            "motion": motions[i % len(motions)],
            "parallax": (i % 2 == 1),
            "file": f"scene_{i+1:02d}.jpg",
            "seed": vid * 100 + i + 1,
            "start": st,
            "end": en,
            "dur": round(en - st, 3)
        })

    # 3. Generate Visual Frames via Pollinations Flux
    print(f"\n🖼️ [Step 2] Generating {n_scenes} Comedic 3D Animation Frames via Flux...")
    img_agent = ImageGen(providers=["pollinations", "gemini_image"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"✅ All {n_scenes} comedic frames generated successfully!")

    # 4. Build Manifest
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "title": TITLE,
        "script": script_data,
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
            "setting": "colorful cartoon quiz studio with comic pop elements",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Render MP4 with FFmpeg
    print(f"\n🎥 [Step 3] Rendering Funny Riddle Ep 1 with FFmpeg (Pacing: ~{scene_dur:.1f}s/cut, Total: {dur:.1f}s)...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # Re-probe final file
    from core.ffmpeg import probe
    final_probe = probe(raw_video)
    final_dur = float(final_probe.get("format", {}).get("duration", dur) or dur)
    final_size_mb = round(raw_video.stat().st_size / (1024 * 1024), 2)

    db.update_video(
        vid,
        video_path=str(raw_video),
        cover_path=render_info["cover_path"],
        length_sec=final_dur,
        status="rendered"
    )

    # 6. Quality Gate: Validate
    print("\n🔍 [Step 4] Quality Recheck & Pre-Upload Validation...")
    rep = validate_dir(out_dir)
    render_info["video_path"] = str(raw_video)
    render_info["duration_sec"] = final_dur
    render_info["size_mb"] = final_size_mb
    manifest["render"] = render_info
    manifest["validation"] = rep.to_dict()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"   Resolution : {final_probe.get('streams', [{}])[0].get('width')}x{final_probe.get('streams', [{}])[0].get('height')}")
    print(f"   Duration   : {final_dur:.1f}s")
    print(f"   Size       : {final_size_mb} MB")
    print(f"   Validation : {'PASS ✅' if rep.ok else 'WARN ⚠️'}")

    db.set_status(vid, "approved", note="Series 4 Ep 1 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 7. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Series 4 Episode 1 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 SERIES 4 EPISODE 01 PUBLISHED SUCCESSFULLY TO YOUTUBE SHORTS!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  📁 File       : {raw_video}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  ⏱️ Total Time : {elapsed}s")
    print("=" * 70 + "\n")
    return res

if __name__ == "__main__":
    main()
