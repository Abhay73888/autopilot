#!/usr/bin/env python3
"""
generate_series2_ep5.py — Generate & Validate SERIES 2 EPISODE 5: "SACH AUR AANSOO".
Features:
- Realistic Cinematic Indian Romance Drama
- Two-Character Emotional Movie Dialogue (Aarav & Meera)
- The In-Person Confrontation & Shocking Truth
- High-Tension Sound Design: Felt Piano Melancholy + Whoosh Transitions
- Kinetic Center-Pop Subtitles (Rose Pink & Gold)
- Auto-approves for YouTube Shorts publication
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

log = Logbook("series2_ep5")

SERIES_CODE = "SERIES_2"
EPISODE_NUM = 5
TOPIC = "2020 — Jab Pyaar Online Tha: Episode 5 — Sach Aur Aansoo"
TITLE = "Usne Sach Bataya Aur Sab Badal Gaya... 💔😭 | JAB PYAAR ONLINE THA (Ep 5) #Shorts"
CAPTION = (
    "Aarav bina bataye Meera ke sheher pahunch gaya... us photo ka sach poochne. "
    "Lekin jab sach saamne aaya, toh pairon tale zameen khisak gayi! 💔😭\n\n"
    "Kya sacha pyaar har galti ko maaf kar sakta hai? Agle episode ke liye COMMENT karein! 👇✨"
)
HASHTAGS = ["#JabPyaarOnlineTha", "#Series2", "#Episode5", "#Shorts", "#Romance", "#Heartbreak", "#LoveStory"]
HOOK_OVERLAY = "💔 SACH SAAMNE AAYA... (EPISODE 5) 😭"
COMMENT_BAIT = "Kya aap aise halat mein maaf kar paate? Aarav ko kya karna chahiye? COMMENT karo! 👇💔"

LINES = [
    {
        "speaker": "narrator",  # Aarav
        "text": "Maine aakhiri train pakdi aur seedha Meera ke college ke gate par khada ho gaya.",
        "emotion": "melancholic",
        "role": "hook"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Aarav? Tum yahan kaise... aur tumhari aankhon mein yeh gussa kyun hai?",
        "emotion": "sad",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Maine phone nikaal kar wahi photo saamne rakh di: 'Kaun hai yeh ladka, Meera?'",
        "emotion": "intense",
        "role": "body"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Meera ki aankhon se aansoo nikal pade: 'Aarav, yeh mera cousin brother hai jo hospital mein meri maa ke ilaaj ke paise laaya tha!'",
        "emotion": "crying",
        "role": "reveal"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Yeh sunte hi mere pairon tale zameen khisak gayi... main shak kar raha tha aur woh lad rahi thi.",
        "emotion": "shocked",
        "role": "climax"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "'Par tumne ek baar bhi sach sunne ki koshish nahi ki Aarav...' Agle episode ke liye COMMENT karein!",
        "emotion": "emotional",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Aarav standing outside foggy college gate at sunrise
    "Cinematic 8k photorealistic wide vertical shot: 19-year-old Indian boy Aarav wearing dark jacket with travel backpack standing outside college iron gates in cold morning mist, determined hurt expression, vertical 9:16, masterpiece, no text",
    
    # Scene 2: Meera dropping her college books in shock as she sees Aarav
    "Cinematic 8k photorealistic medium shot: beautiful 19-year-old Indian girl Meera dropping her notebook folder, looking up in absolute shock and emotional disbelief, morning golden sunlight, vertical 9:16, no text",
    
    # Scene 3: Aarav holding up glowing smartphone showing the photo
    "Dramatic 8k cinematic close up: male hand thrusting glowing smartphone screen forward, blurred emotional face in background, tension filled cinematic lighting, vertical 9:16, shallow depth of field, no text",
    
    # Scene 4: Meera breaking down in tears clutching her face
    "Heartbreaking 8k photorealistic close up: Meera breaking down in tears with trembling hands near her face, hospital documents in her bag, emotional vulnerability, vertical 9:16, cinematic masterpiece, no text",
    
    # Scene 5: Aarav standing stunned with regret on his face in crowd
    "Cinematic 8k medium vertical shot: Aarav frozen in pure shock and deep guilt, college students walking past blurred in motion, dramatic moody lighting, vertical 9:16, no text",
    
    # Scene 6: Meera walking away slowly under falling autumn leaves
    "Cinematic 8k melancholic vertical shot: Meera walking away with head down under falling orange leaves, Aarav looking at her from behind in heavy regret, cinematic cinema look, vertical 9:16, no text"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT 10X: GENERATING SERIES 2 EPISODE 5 (JAB PYAAR ONLINE THA)")
    print("=" * 75 + "\n")

    db = DB()
    t_start = time.time()

    vid = db.create_video(
        topic=TOPIC,
        hook_type="cliffhanger",
        voice_id="hi_m_narrator",
        template_id="warm_nostalgia",
        notes="Series 2 Episode 5: Sach Aur Aansoo"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n🎙️ [Step 1] Synthesizing Dual Character Voices (Aarav & Meera)...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_narrator")
    print(f"  ✅ Voiceover generated: {voice_res['duration_sec']:.2f}s, {len(voice_res['words'])} words synced.")

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
            "setting": "College gate, foggy morning, emotional confrontation",
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
        notes="Generated with 10x quality. Ready to publish."
    )
    db.close()

    total_sec = round(time.time() - t_start, 1)
    print(f"\n🎉 SERIES 2 EPISODE 5 READY in {total_sec}s! (Video #{vid})")
    return vid

if __name__ == "__main__":
    main()
