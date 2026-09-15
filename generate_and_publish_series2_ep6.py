#!/usr/bin/env python3
"""
generate_and_publish_series2_ep6.py — Generate & Publish SERIES 2 EPISODE 6: "THE AIRPORT CLIMAX".
Features:
- Realistic Cinematic Indian Romance Drama with Global Appeal
- Emotional Airport Departure Scene (Meera's flight abroad)
- Dual Emotional Dialogue: Aarav & Meera
- High-Tension Sound Design: Felt Piano Melancholy + Whoosh Transitions
- 1080x1920 MP4 Video with Kinetic Center-Pop Subtitles
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

log = Logbook("series2_ep6")

SERIES_CODE = "SERIES_2"
EPISODE_NUM = 6
TOPIC = "2020 — Jab Pyaar Online Tha: Episode 6 — The Airport Climax"
TITLE = "He Left Everything to Meet Her at Terminal 3... ✈️❤️ | JAB PYAAR ONLINE THA (Ep 6) #Shorts"
CAPTION = (
    "Meera ki London ki flight boarding hone wali thi... aur Aarav 400 kilometer door tha! "
    "Lekin jab aakhiri second par boarding gate par Meera ne peeche mud kar dekha... 😭💔\n\n"
    "Kya sacha pyaar waqt aur dooriyon ko hara sakta hai? Apni love story COMMENT karein! 👇✨\n\n"
    "#JabPyaarOnlineTha #Series2 #Episode6 #Romance #Shorts #LoveStory #Heartbreak #LongDistance"
)
HASHTAGS = ["#JabPyaarOnlineTha", "#Series2", "#Episode6", "#Romance", "#Shorts", "#LoveStory", "#Heartbreak", "#LongDistance"]
HOOK_OVERLAY = "✈️ TERMINAL 3 PAR AAKHIRI MULAKAAT... ❤️🥺"
COMMENT_BAIT = "Kya aap kisi ke liye airport tak bhaag kar ja sakte ho? Tell us your honest thoughts in comments! 👇❤️"

LINES = [
    {
        "speaker": "narrator",  # Aarav
        "text": "Display board par red letters mein likha tha: Flight BA-142 to London... Last Call For Boarding!",
        "emotion": "urgent",
        "role": "hook"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Saans phooli hui thi, shirt bheege hue baalon par chipak rahi thi... par meri nazar sirf Meera ko dhoondh rahi thi.",
        "emotion": "melancholic",
        "role": "body"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Boarding gate par khadi ladki ne achanak apna bag gira diya aur kaanpti aawaz mein boli: 'Aarav... tum pagal ho kya?!'",
        "emotion": "emotional",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Maine uska haath pakda aur kaha: 'Saalon se online dekha tha... bina gale lagaye jaane nahi dunga!'",
        "emotion": "passionate",
        "role": "climax"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Uski aankhon se aansu beh nikle: 'Par meri flight... mera career... sab wahan hai!'",
        "emotion": "vulnerable",
        "role": "climax"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Kya Meera rukegi ya chali jayegi? Aap hote toh kya karte? COMMENT mein vote karein!",
        "emotion": "desperate",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Giant glowing departures board at international airport terminal
    "Cinematic 35mm film still of a massive neon departures board inside modern international airport terminal, glowing amber text reading Flight BA-142 London Last Call, rainy night reflection outside glass, vertical 9:16, masterpiece, no text overlay",

    # Scene 2: Aarav breathless running through airport crowd
    "Emotional cinematic shot of handsome 22-year-old Indian boy in wet black jacket running breathlessly through crowded airport departure lounge, blurred background lights, cinematic lens flare, vertical 9:16, photorealistic romance drama, no text",

    # Scene 3: Meera at the boarding gate turning around in shock
    "Close up emotional portrait of beautiful 21-year-old Indian girl Meera with tears welling in her eyes turning around in utter disbelief at boarding gate, passport in trembling hand, soft airport terminal bokeh, vertical 9:16, cinematic masterpiece",

    # Scene 4: Aarav holding Meera's hands tightly in the terminal
    "Touching cinematic medium shot: Aarav gently holding Meera's delicate hands amidst bustling airport terminal, warm glowing overhead spotlights, intense romantic tension, tears on cheeks, vertical 9:16, photorealistic 8k romance",

    # Scene 5: Meera looking at boarding pass torn between love and dream
    "Dramatic close up of Meera's tearful face looking down at her boarding pass then into Aarav's eyes, emotional dilemma, cinematic rain streaked terminal glass in background, vertical 9:16, 8k resolution",

    # Scene 6: Dramatic silhouette of the two lovers under terminal lights
    "Breathtaking wide cinematic silhouette of Aarav and Meera standing close together under luminous golden airport gate lights, airplanes visible on tarmac through giant rain-soaked windows, vertical 9:16, climax emotional masterpiece"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT: GENERATING & PUBLISHING SERIES 2 EPISODE 6")
    print("  Title : He Left Everything to Meet Her at Terminal 3...")
    print("=" * 75 + "\n")

    t0 = time.time()
    db = DB()

    vid = db.create_video(
        topic=TOPIC,
        hook_type="cliffhanger",
        voice_id="hi_m_intense",
        template_id="cinematic_romance",
        series_name=SERIES_CODE,
        series_index=EPISODE_NUM,
        notes="Series 2 Episode 6: Terminal 3 Climax"
    )
    print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Synthesize Dual Voiceover
    print("\n🎙️ [Step 1] Synthesizing Dual Voiceover (Aarav + Meera)...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_intense")
    dur = voice_res["duration_sec"]
    words = voice_res.get("words", [])
    print(f"  ✅ Voiceover ready: {dur:.2f}s, {len(words)} words aligned.")

    # 2. Generate Visual Scenes
    print(f"\n🖼️ [Step 2] Generating {len(IMAGE_PROMPTS)} 9:16 Cinematic Frames...")
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    motions = ["punch_in", "pan_left", "zoom_in_dramatic", "pan_right", "zoom_in", "zoom_out"]

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
    print(f"  ✅ All {n_scenes} visual frames generated successfully!")

    # 3. Build Manifest
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
            "narrator": {"gender": "male", "persona": "Aarav"},
            "char_b": {"gender": "female", "persona": "Meera"}
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
                "heartbeat": True,
                "riser": True,
                "whoosh": True,
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "cinematic_romance",
            "template_name": "Cinematic Romance Drama",
            "pacing": "standard",
            "setting": "Modern international airport terminal",
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
        notes="Series 2 Episode 6 Approved for YouTube Upload"
    )

    # 6. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Series 2 Episode 6 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)
    db.close()

    total_time = round(time.time() - t0, 1)
    print("\n" + "=" * 75)
    print("  🎉 SERIES 2 EPISODE 6 PUBLISHED SUCCESSFULLY TO YOUTUBE SHORTS!")
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
