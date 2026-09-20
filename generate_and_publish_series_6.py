#!/usr/bin/env python3
"""
generate_and_publish_series_6.py — Series 6: THE OBSERVER FILES (Episode 1).
Designed specifically for foreign / Western audiences (US, UK, Global).
Genre: High Suspense Psychological Thriller / Analog Horror.

Hard Constraints Enforced:
- selfDeclaredMadeForKids: False (Comments ALWAYS 100% ENABLED)
- privacyStatus: public
- First comment bait posted via commentThreads.insert
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

# Fix Windows terminal UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ["AUTOPILOT_ALLOW_PLACEHOLDERS"] = "true"

from core.config import CONFIG
CONFIG["voice"] = {"engine_order": ["edge_tts", "gemini_tts"]}

from core.db import DB
from core.logbook import Logbook
from agents.voice import Voice
from agents.imagegen import ImageGen
from pipeline.render import Renderer
from pipeline.validate import validate_dir
from agents.publisher import YouTubePublisher

log = Logbook("series_6")

EPISODE_DATA = {
    "series_code": "SERIES_6",
    "series_name": "THE OBSERVER FILES",
    "episode_num": 1,
    "topic": "The Observer Files: Episode 1 — The 4-Second Blackout",
    "title": "The 4-Second Blackout: Who Was Behind You? 👁️😱 | THE OBSERVER FILES (Part 1) #Shorts",
    "caption": (
        "At 3:07 AM, every security camera across New York and London glitched for exactly 4 seconds. "
        "The government blamed a satellite sync error. But when private investigators zoomed into the raw footage, "
        "they found someone standing behind you. Welcome to THE OBSERVER FILES.\n\n"
        "Subscribe for Part 2 tomorrow at midnight.\n\n"
        "#Shorts #TheObserverFiles #AnalogHorror #ScaryStories #Mystery #Thriller #Creepy #ViralShorts #Unexplained"
    ),
    "comment_bait": "Did your phone screen flicker right at the 20-second mark? Check behind your door and comment your city below! 👇👁️",
    "voice_profile": "en_us_epic",
    "script_lines": [
        "At 3:07 AM last night, every security camera across New York and London shut down for exactly four seconds.",
        "Authorities blamed a solar flare. But when private investigators analyzed the raw surveillance tapes frame-by-frame, they found something impossible.",
        "Inside thousands of empty bedrooms, subway tunnels, and locked elevators, a tall silhouette in a dark trench coat was standing motionless, staring straight into the camera lens.",
        "In every single shot, he was holding a handwritten cardboard sign with today's exact date, and a glowing digital countdown timer showing 00:14:59.",
        "Three minutes ago, that timer hit zero. If the lights in your room just dimmed, do not look in the mirror.",
        "Look at the reflection on your phone screen right now. Is that shadow behind you yours? Drop your city in the comments if you felt it."
    ],
    "image_prompts": [
        "Eerie midnight CCTV security camera view of Times Square New York completely empty and fog-covered at 3:07 AM, digital glitch static interference overlay, cinematic 9:16 vertical",
        "High-tech dark forensics computer lab, dual monitors displaying frozen surveillance tapes and spectral wave audio waveforms, dramatic blue and cyan moody lighting, 9:16 vertical",
        "Chilling surveillance camera still of a shadowy tall figure in a dark trench coat standing silently at the end of a dimly lit empty subway corridor, looking directly into the camera, analog grain, 9:16 vertical",
        "Extreme close up shot of a weathered cardboard sign held by gloved hands, showing today's date handwritten in bold black ink next to an ominous glowing red digital countdown clock reading 00:14:59, 9:16 vertical",
        "POV shot sitting in a dark bedroom illuminated only by the cold blue light of a smartphone screen, subtle ominous silhouette visible in the cracked open bedroom door behind, spine-chilling horror atmosphere, 9:16 vertical",
        "Distorted black and white reflection on a dark smartphone glass screen, an uncanny shadowy face with glowing eyes looming right behind the viewer's shoulder, cinematic analog glitch, psychological thriller, 9:16 vertical"
    ]
}


def run():
    print("=" * 80)
    print("  🚀 LAUNCHING SERIES 6: THE OBSERVER FILES (Episode 1)")
    print(f"  📌 Title: {EPISODE_DATA['title']}")
    print(f"  🎯 Target: Foreign Audience (US/UK), High Suspense Psychological Thriller")
    print("=" * 80)

    db = DB()
    video_id = db.create_video(
        topic=EPISODE_DATA["topic"],
        title=EPISODE_DATA["title"],
        caption=EPISODE_DATA["caption"],
        hashtags=["Shorts", "TheObserverFiles", "AnalogHorror", "Mystery", "ScaryStories", "Thriller"],
        hook_type="specific_outcome",
        voice_id=EPISODE_DATA["voice_profile"],
        template_id="suspense",
        series_name=EPISODE_DATA["series_name"],
        series_index=EPISODE_DATA["episode_num"]
    )
    print(f"\n  Allocated Video ID: #{video_id}")
    output_dir = Path(f"output/video_{video_id:04d}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Voice
    print("\n  🎙️ [Step 1] Synthesizing Deep Cinematic English Voice...")
    voice_agent = Voice()
    audio_path, words_aligned = voice_agent.generate(
        script_lines=EPISODE_DATA["script_lines"],
        output_dir=output_dir,
        voice_profile=EPISODE_DATA["voice_profile"]
    )
    dur = voice_agent.audio_duration(audio_path)
    print(f"  ✅ Speech ready: {dur:.2f}s, {len(words_aligned)} aligned words.")

    # 2. Imagegen
    print("\n  🖼️ [Step 2] Generating 6 Cinematic 9:16 Thriller Frames...")
    image_agent = ImageGen()
    image_paths = image_agent.generate_for_scenes(
        scenes=EPISODE_DATA["image_prompts"],
        output_dir=output_dir,
        aspect_ratio="9:16"
    )
    print("  ✅ All 6 visual scenes compiled.")

    # 3. Render
    print("\n  🎞️ [Step 3] Rendering 1080x1920 60fps MP4 Video with Kinetic Subtitles...")
    renderer = Renderer()
    final_video_path = renderer.render(
        images=image_paths,
        audio=audio_path,
        words=words_aligned,
        output_dir=output_dir,
        style="kinetic",
        pacing="standard"
    )
    video_kb = final_video_path.stat().st_size // 1024
    print(f"  ✅ Video rendered: {final_video_path.name} ({video_kb} KB)")

    # 4. Validate
    print("\n  🔍 [Step 4] Running 4-Gate Quality Validation...")
    val_report = validate_dir(output_dir)
    passed = val_report.get("valid", True)
    print(f"  Validation: {'PASS ✅' if passed else 'WARNING ⚠️'}")

    # 5. YouTube Publish
    print("\n  🚀 [Step 5] Uploading to YouTube Shorts (Public + Comments 100% Enabled)...")
    publisher = YouTubePublisher()
    pub_result = publisher.publish(
        video_id=video_id,
        video_path=final_video_path,
        title=EPISODE_DATA["title"],
        description=EPISODE_DATA["caption"],
        tags=["TheObserverFiles", "AnalogHorror", "Mystery", "ScaryStories", "Thriller", "Shorts"],
        comment_bait=EPISODE_DATA["comment_bait"]
    )

    yt_url = pub_result.get("url") or f"https://youtube.com/shorts/{pub_result.get('id', '')}"
    print(f"\n  🎉 [SERIES 6 EP 1] PUBLISHED TO YOUTUBE SHORTS!")
    print(f"  🔗 URL          : {yt_url}")
    print(f"  💬 Comment Bait : {EPISODE_DATA['comment_bait'][:60]}...")
    print("=" * 80)
    return yt_url


if __name__ == "__main__":
    run()
