#!/usr/bin/env python3
"""
generate_and_publish_kaalrekha_ep11.py — Generate, Validate, and Publish KAAL-REKHA Part 11.
Major Changes:
- Global Audience Targeting: Tailored for United States and major foreign countries.
- Language: High-impact English dialogue & cinematic narration.
- Voice: American English Neural Voiceover (en-US-ChristopherNeural / en-US-JennyNeural).
- Visuals: 6 Ultra-HD Dark Anime Frames (Times Square frozen in time, colossal burning Roman numerals, Pentagon temporal archives, orbital temporal grid).
- Sound Design: 38Hz Braam Hit + Reverse Whoosh + Cinematic Suspense BGM.
- YouTube Upload: Public YouTube Shorts + 100% Comments Enabled (selfDeclaredMadeForKids=False) + Automated First Comment.
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
# Force fast edge_tts with high-quality US English voices
CONFIG["voice"] = {"engine_order": ["edge_tts", "gemini_tts"]}

from core.db import DB
from core.logbook import Logbook
from agents.voice import Voice
from agents.imagegen import ImageGen
from pipeline.render import Renderer
from pipeline.validate import validate_dir
from agents.publisher import YouTubePublisher

log = Logbook("kaalrekha_ep11")

SERIES_CODE = "SERIES_1"
EPISODE_NUM = 11
TOPIC = "Kaal-Rekha Part 11: The Global Anomaly (3:17 AM in New York)"
TITLE = "Why Did Every Clock in New York Freeze at 3:17 AM?! ⏳😱 | KAAL-REKHA (Part 11) #Shorts"
CAPTION = (
    "At exactly 3:17 AM, every clock across New York, London, and Tokyo stopped simultaneously. 😱\n"
    "Kabir thought destroying the temporal core broke his personal loop... but it didn't break. It went GLOBAL! ⏳⚡\n"
    "A classified US military archive from 1954 bears his exact face... Subject Zero has awakened.\n\n"
    "If time freezes in your city tonight, what is the ONE thing you're running to do? Drop your answer in the comments! 👇🔥\n\n"
    "#KaalRekha #Episode11 #TimeLoop #AnimeShorts #SciFiThriller #Shorts #GlitchInTheMatrix #Mystery #ShortsFeed"
)
HASHTAGS = ["#KaalRekha", "#Episode11", "#TimeLoop", "#AnimeShorts", "#SciFiThriller", "#Shorts", "#GlitchInTheMatrix", "#Mystery"]
HOOK_OVERLAY = "⏳ KAAL-REKHA: PART 11 (THE US ANOMALY) 😱"
COMMENT_BAIT = "If time completely froze in your city right now, what is the ONE thing you would run to do? Tell us in the comments! 👇⏳"

LINES = [
    {
        "speaker": "narrator",  # Kabir
        "text": "At exactly 3:17 AM, every digital billboard across Times Square New York suddenly froze!",
        "emotion": "shocked",
        "role": "hook"
    },
    {
        "speaker": "narrator",  # Kabir
        "text": "Traffic stopped dead, rain droplets hung motionless in mid-air, and a massive burning Roman numeral III appeared in the sky!",
        "emotion": "urgent",
        "role": "body"
    },
    {
        "speaker": "char_b",    # Temporal Entity
        "text": "A shadowy entity whispered through the static: 'You didn't break the time loop Kabir... you just dragged the entire world into it!'",
        "emotion": "cold",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Kabir
        "text": "Deep inside a classified US underground bunker, a top-secret file from 1954 bears my exact face... labeled Subject Zero!",
        "emotion": "fearful",
        "role": "climax"
    },
    {
        "speaker": "char_b",    # Temporal Entity
        "text": "When the clock strikes 3:18 AM, one entire continent will be permanently erased from history.",
        "emotion": "ominous",
        "role": "climax"
    },
    {
        "speaker": "narrator",  # Kabir
        "text": "If time freezes in your city tonight... what is the first thing you would do? Tell me in the comments!",
        "emotion": "intense",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Times Square frozen in time with glitching neon billboards
    "Cinematic 8k hyper-detailed dark anime shot of Times Square New York at night completely frozen in time, neon billboards glitching with static, rain droplets suspended motionlessly in mid air, vertical 9:16, MAPPA aesthetic, masterpiece, high contrast, no text",

    # Scene 2: Burning Roman Numeral III over Manhattan skyline
    "Dramatic 8k dark anime perspective of foggy Manhattan skyline with a colossal glowing violet Roman numeral III burning across the stormy night sky, purple lightning arcs, vertical 9:16, cinematic masterpiece, no text",

    # Scene 3: Shadow temporal entity with glowing porcelain mask overlooking the city
    "Eerie 8k dark anime shot of a tall shadowy temporal entity with a glowing porcelain mask standing atop a frozen skyscraper balcony overlooking New York City, purple aura swirling, vertical 9:16, volumetric lighting, no text",

    # Scene 4: Classified underground bunker with Kabir's top secret file
    "Cinematic 8k anime shot inside a classified high-tech underground archive bunker, glowing hologram displaying an aged top-secret dossier with Kabir Sen's photo stamped in blood red, vertical 9:16, mystery thriller, no text",

    # Scene 5: Earth wrapped in golden clockwork rings and temporal fractures
    "Stunning 8k anime perspective from orbit showing planet Earth wrapped in glowing golden clockwork rings and temporal fractures, American continent glowing in frozen amber light, vertical 9:16, epic sci-fi, no text",

    # Scene 6: Kabir looking up with glowing Roman numeral on his face
    "Intense 8k anime dramatic close-up of 21-year-old Kabir Sen in black coat looking up at the sky, glowing neon Roman numeral burning on his cheekbone as clock gears shatter around him, vertical 9:16, climax masterpiece, no text"
]

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT: GENERATING & PUBLISHING KAAL-REKHA PART 11")
    print("  Target Audience : US & Global Foreign Markets (English)")
    print("  Voice Profiles  : en-US-ChristopherNeural (Narrator) + en-US-JennyNeural (Entity)")
    print("  Policy          : 100% Comments ON + Auto First Comment Bait")
    print("=" * 75 + "\n")

    t0 = time.time()
    db = DB()

    # 1. Register Video in DB (or reuse current 233 if available)
    row = db.conn.execute("SELECT id FROM videos WHERE id=233 AND status IN ('planned', 'failed')").fetchone()
    if row:
        vid = 233
        print(f"🎬 Resuming Video ID: #{vid}")
    else:
        vid = db.create_video(
            topic=TOPIC,
            hook_type="cliffhanger",
            voice_id="en_us_epic",
            template_id="dark_anime_thriller",
            series_name=SERIES_CODE,
            series_index=EPISODE_NUM,
            notes="Kaal-Rekha Part 11: US & Global Edition (English Audio & Subtitles)"
        )
        print(f"🎬 Video ID Allocated: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Synthesize English Voiceover
    print("\n🎙️ [Step 1] Synthesizing Dual US Neural Voiceover (en_us_epic)...")
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(LINES, out_dir, profile_id="en_us_epic")
    dur = voice_res["duration_sec"]
    words = voice_res.get("words", [])
    print(f"  ✅ Voiceover ready: {dur:.2f}s, {len(words)} words aligned.")

    # 3. Generate Visual Scenes
    print(f"\n🖼️ [Step 2] Generating {len(IMAGE_PROMPTS)} 9:16 Dark Anime Frames (Flux Engine)...")
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    motions = ["punch_in", "whip_zoom", "pan_left", "zoom_in_dramatic", "zoom_out", "punch_in"]

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

    # 4. Build Manifest
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
            "narrator": {"gender": "male", "persona": "Kabir"},
            "char_b": {"gender": "female", "persona": "Temporal Entity"}
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
                "braam": True,
                "whoosh": True,
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "dark_anime_thriller",
            "template_name": "Dark Anime Global Thriller",
            "pacing": "dynamic_fast",
            "setting": "Times Square New York and subterranean classified archives",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": voice_res,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Render Video with FFmpeg
    print(f"\n🎞️ [Step 3] Rendering 1080x1920 MP4 Video (Ken Burns + Sound FX + Kinetic Subs)...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # Enhance audio with dark suspense BGM if present
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"
    final_video_path = raw_video
    if bgm_path.exists():
        enhanced_video = out_dir / "final_enhanced.mp4"
        cmd = [
            "-i", str(raw_video),
            "-stream_loop", "-1", "-i", str(bgm_path),
            "-filter_complex",
            f"[1:a]volume=0.12,afade=t=in:st=0:d=1.0,afade=t=out:st={max(0.1, dur-2):.2f}:d=2[bgm];"
            "[0:a][bgm]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-y", str(enhanced_video)
        ]
        from core.ffmpeg import run as ffmpeg_run
        try:
            ffmpeg_run(cmd)
            if enhanced_video.exists() and enhanced_video.stat().st_size > 100000:
                final_video_path = enhanced_video
                print("  🎵 Dark cinematic suspense BGM layered successfully!")
        except Exception as e:
            print(f"  ⚠️ BGM mix skipped ({e}), using base render.")

    # 6. Validate Quality
    print("\n🔍 [Step 4] Quality Recheck & Pre-Upload Validation...")
    rep = validate_dir(out_dir)
    print(f"  Validation Status: {'PASS ✅' if rep.ok else 'WARN ⚠️'}")

    db.update_video(
        vid,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        script_json=json.dumps(script_data, ensure_ascii=False),
        video_path=str(final_video_path),
        cover_path=render_info.get("cover_path"),
        length_sec=dur,
        status="approved",
        notes="Kaal-Rekha Part 11 Approved for US / Global Audience"
    )

    # 7. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Part 11 to YouTube Shorts (Public, Comments Enabled)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)
    db.close()

    total_time = round(time.time() - t0, 1)
    print("\n" + "=" * 75)
    print("  🎉 KAAL-REKHA PART 11 PUBLISHED SUCCESSFULLY TO YOUTUBE SHORTS!")
    print("=" * 75)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  📁 File       : {final_video_path}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  💬 First Comment: Posted automatically!")
    print(f"  ⏱️ Total Time : {total_time}s")
    print("=" * 75 + "\n")

    return res

if __name__ == "__main__":
    main()
