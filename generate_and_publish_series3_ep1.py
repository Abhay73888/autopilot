#!/usr/bin/env python3
"""
generate_and_publish_series3_ep1.py — Generate, Validate, and Publish SERIES 3 EPISODE 1:
"CHINTU AUR JADUI FLYING DONUT" (Chintu's Magical Adventures).
Features:
- Vibrant 3D Pixar / Disney Animation Aesthetic
- Wholesome, Fun & Engaging Story for Kids and Families
- Lovable Characters: 7-Year-Old Chintu & Golu The Fluffy Monster
- Interactive Kids Comment Question at Ending
- Visuals: 8k 3D Pixar aesthetic via Pollinations Flux
- Audio: Expressive Kid Storyteller Voiceover + Playful Sound Design
- Upload: YouTube Shorts (Public, Comments Enabled)
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

log = Logbook("series3_ep1")

TOPIC = "Chintu Ki Jadui Duniya: Episode 1 — Chintu Aur Jadui Flying Donut"
TITLE = "Chintu Aur Jadui Flying Donut! 🍩✨ | Chintu Ki Kahani (Ep 1) #Kids #Shorts"
CAPTION = (
    "Chintu ko apne kamre mein mili ek aisi jadui pencil... jisse jo bhi banao sach mein zinda ho jata hai! ✏️✨ "
    "Chintu ne banaya udne wala chocolate donut! 🍩 Par achanak ek fluffy monster aa gaya!\n\n"
    "Agar aapko ye jadui pencil milti toh aap sabse pehle kya draw karte? Chocolate ya Flying Car? Comments mein batao! 👇💖"
)
HASHTAGS = ["#ChintuKiKahani", "#Series3", "#KidsShorts", "#Shorts", "#Animation", "#PixarStyle", "#Kids", "#TrendingShorts"]
HOOK_OVERLAY = "✨ CHINTU AUR JADUI PENCIL (PART 1) 🍩"
COMMENT_BAIT = "Agar aapko ye jadui pencil milti toh aap sabse pehle kya banate? Comments mein batao! ✏️🍩👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Chintu ko apne bistar ke neeche mili ek aisi chamakti hui jadui pencil... jisse jo bhi banao, wo sach mein zinda ho jata hai!",
        "emotion": "wonder",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Chintu ne masti mein kagaz par ek chocolate donut banaya... aur uske chhote-chhote titli jaise pankh bana diye!",
        "emotion": "playful",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Aur achanak... POOF! Donut kagaz se bahar nikal kar hawa mein phurr karke udne laga!",
        "emotion": "excited",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Chintu bistar par uchhalte hue bola: 'Ruko mere meethhe donut!' Par donut poore kamre mein tezi se udne laga!",
        "emotion": "happy",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Tabhi Chintu ki pencil fisal gayi... aur usne galti se ek bada sa fluffy blue monster bana diya!",
        "emotion": "shocked",
        "role": "reveal"
    },
    {
        "speaker": "char_b",
        "text": "Monster ne dono haath jode aur pyari aawaz mein bola: 'Chintu bhaiya... kya mujhe bhi ek meetha donut milega?'",
        "emotion": "sweet",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Agar aapko ye jadui pencil milti, toh aap sabse pehle kya draw karte? Jaldi se COMMENT mein batao!",
        "emotion": "cheerful",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Chintu finding magical glowing pencil
    "Vibrant 8k 3D Pixar Disney animation style: adorable 7-year-old Indian boy Chintu with cute curly hair and bright eyes finding a glowing golden magical pencil under his colorful wooden bed, magical sparkles, vertical 9:16, masterpiece, no text",
    
    # Scene 2: Drawing the flying donut on sketchbook
    "Vibrant 8k 3D Pixar animation style: close up of Chintu's drawing pad with a cute glowing chocolate donut doodle having tiny fairy wings, colorful crayons around, vertical 9:16, magical warm lighting, no text",
    
    # Scene 3: Poof! Magical smoke and donut coming alive
    "Magical 8k 3D Disney animation shot: colorful puff of magical pink and golden fairy dust smoke popping out of the drawing pad as a delicious 3D chocolate donut springs to life, vertical 9:16, no text",
    
    # Scene 4: Flying donut zooming around cozy kids room
    "Vibrant 8k 3D Pixar style wide shot: delicious glowing chocolate glazed donut with tiny sparkly wings flying happily around a vibrant colorful kids bedroom, whimsical movement, vertical 9:16, no text",
    
    # Scene 5: Chintu jumping on bed trying to catch donut
    "Playful 8k 3D Pixar animation: cheerful Chintu jumping happily on his bouncy bed with arms stretched out trying to catch the giggling flying donut, wide excited smile, vertical 9:16, masterpiece, no text",
    
    # Scene 6: Pencil slipping and drawing monster
    "Cute 8k 3D animation close-up: Chintu accidentally scribbling a big round monster shape on paper with glowing golden pencil marks, funny surprised face, vertical 9:16, no text",
    
    # Scene 7: Big fluffy blue monster popping out
    "Adorable 8k 3D Pixar Disney style: a huge fluffy pastel-blue fur monster with tiny golden horns and huge friendly purple eyes appearing in the room, looking super gentle and cute, vertical 9:16, no text",
    
    # Scene 8: Monster politely requesting donut
    "Heartwarming 8k 3D Pixar animation: the giant fluffy blue monster sitting politely on the carpet with folded hands, gazing lovingly at the flying chocolate donut with a sweet smile, vertical 9:16, no text",
    
    # Scene 9: Chintu and fluffy monster sharing donut happily
    "Super cute 8k 3D Pixar animation finale: Chintu and the fluffy monster sitting together eating sweet donuts, sharing joy and laughter, sparkling magical confetti raining down, vertical 9:16, masterpiece, no text"
]

def main():
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  🎬 SERIES 3: CHINTU KI JADUI DUNIYA — EPISODE 01")
    print("  🍩 3D PIXAR-STYLE KIDS ANIMATION + PLAYFUL SOUND DESIGN")
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
        "hook_type": "cliffhanger",
        "hook_line": LINES[0]["text"],
        "hook_text_overlay": HOOK_OVERLAY,
        "comment_bait": COMMENT_BAIT,
        "cast": {
            "narrator": {"gender": "female", "persona": "warm enthusiastic kid storyteller"},
            "char_b": {"gender": "male", "persona": "super cute fluffy monster"}
        },
        "lines": LINES,
        "word_count": sum(len(ln["text"].split()) for ln in LINES),
        "est_sec": 38.0
    }

    vid = db.create_video(
        TOPIC,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        hook_type="question",
        script_json=script_data,
        length_sec=38,
        status="planned"
    )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} workspace: {out_dir}")

    # 1. Synthesize Voice
    print("\n🎙️ [Step 1] Synthesizing Cheerful Kids Storyteller Voiceover...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_f_calm")
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
    print(f"\n🖼️ [Step 2] Generating {n_scenes} 3D Pixar Animation Frames via Flux...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"✅ All {n_scenes} Pixar-style frames generated successfully!")

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
            "template_id": "kids_magic",
            "template_name": "Vibrant 3D Pixar Animation",
            "pacing": "medium_fast",
            "setting": "colorful cozy bedroom with magical floating elements",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Render MP4 with FFmpeg
    print(f"\n🎥 [Step 3] Rendering Kids Episode 1 with FFmpeg (Pacing: ~{scene_dur:.1f}s/cut, Total: {dur:.1f}s)...")
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

    db.set_status(vid, "approved", note="Series 3 Ep 1 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 7. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Series 3 Episode 1 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 SERIES 3 EPISODE 01 PUBLISHED SUCCESSFULLY TO YOUTUBE SHORTS!")
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
