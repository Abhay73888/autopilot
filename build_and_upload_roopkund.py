#!/usr/bin/env python3
"""
build_and_upload_roopkund.py — Generate and publish brand new viral mystery video to YouTube Shorts.
Topic: Roopkund Skeleton Lake Mystery (Himalaya Ki Kankalo Wali Jheel).
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

log = Logbook("auto_creator")

TOPIC = "Roopkund Lake: Himalaya Ki 16,000 Feet Unchai Par Mile 300 Kankalo Ka Khaufnak Sach"
TITLE = "Himalaya Ki Jheel Mein 300 Kankal: Aasmaan Se Giri Maut Ka Khaufnak Sach! 💀❄️ #Shorts"
CAPTION = "Himalaya ki 16,000 feet unchai par barf pighli to 300 insaani kankal tairte hue mile! Science ne jab DNA test kiya to hosh ud gaye! Dekhiye sach 👇"
HASHTAGS = ["#RoopkundMystery", "#SkeletonLake", "#MysteryShorts", "#HimalayaMystery", "#HindiMystery", "#Shorts", "#ViralShorts"]
HOOK_OVERLAY = "Skeleton Lake: 300 Kankal 💀"
COMMENT_BAIT = "Aapke hisaab se kya ye koi devik shraap tha ya aasmaani tufaan? Comment mein likhein!"

LINES = [
    {
        "speaker": "narrator",
        "text": "Himalaya ki 16,000 feet unchai par jab barf pighli, to ek jheel mein 300 se zyada insaano ke kankal tairte hue mile!",
        "emotion": "serious",
        "role": "hook"
    },
    {
        "speaker": "char_a",
        "text": "Shuru mein laga ki ye World War 2 ke sainik the, lekin carbon dating ne sabhi ke hosh uda diye... ye kankal 1200 saal purane hain!",
        "emotion": "nervous",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Sabse khaufnak baat ye thi ki har ek khopdi theek upar se tooti hui thi, jaise aasmaan se aayi kisi maut ne unhe mara ho!",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "char_a",
        "text": "Forensic jaanch mein khulasa hua: Achanak aasmaan se cricket ball jitne bade oley girne lage the, aur khule pahad par chhipne ki jagah tak nahi thi!",
        "emotion": "whispers",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Lekin ye 300 log itni khatarnak unchai par gaye kyun the? Aapka kya maanna hai?",
        "emotion": "cold",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Majestic frozen high-altitude turquoise lake nestled between towering dark snowy Himalayan peaks at twilight, eerie mist rising from the ice, dramatic cinematic lighting, flat 2D noir cartoon style, vertical 9:16, no text, no letters, no watermark",
    "Eerie ancient human skulls and skeletal remains frozen beneath crystal clear cracked blue glacial ice, haunting mysterious lighting, atmospheric suspense, vertical 9:16, no text, no letters, no watermark",
    "Close-up of a weathered ancient human skull held by a winter expedition scientist, showing a mysterious round impact fracture on the top of the skull, dramatic moody shadows, vertical 9:16, no text, no letters, no watermark",
    "Terrifying violent mountain blizzard storm in the Himalayas, giant cricket-ball sized hailstones crashing down furiously from pitch dark thunder clouds, vertical 9:16, no text, no letters, no watermark",
    "Silhouette of ancient travelers desperately running across a steep snow-covered Himalayan ridge in a deadly frozen storm, flying ice fragments, high suspense thriller, vertical 9:16, no text, no letters, no watermark",
    "Wide panoramic aerial shot of the mysterious Roopkund Skeleton Lake surrounded by immense jagged snowy Himalayan peaks under dark midnight sky and glowing crescent moon, vertical 9:16, no text, no letters, no watermark"
]


def main():
    print("\n" + "=" * 70)
    print("  🚀 AUTOPILOT: GENERATING & PUBLISHING VIRAL MYSTERY VIDEO TO YOUTUBE")
    print("=" * 70)
    print(f"  📌 Topic: {TOPIC}")
    print(f"  🎬 Title: {TITLE}")
    print("=" * 70 + "\n")

    t0 = time.time()
    db = DB()

    # 1. DB Record creation
    script_data = {
        "topic": TOPIC,
        "title": TITLE,
        "caption": CAPTION,
        "hashtags": HASHTAGS,
        "hook_type": "specific_outcome",
        "hook_line": LINES[0]["text"],
        "hook_text_overlay": HOOK_OVERLAY,
        "comment_bait": COMMENT_BAIT,
        "cast": {
            "narrator": {"gender": "male", "persona": "authoritative dark documentary narrator"},
            "char_a": {"name": "Researcher", "gender": "male", "persona": "astonished investigator"}
        },
        "lines": LINES,
        "word_count": sum(len(l["text"].split()) for l in LINES),
        "est_sec": 32.0
    }

    vid = db.create_video(
        TOPIC,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        hook_type="specific_outcome",
        script_json=script_data,
        length_sec=32,
        status="planned"
    )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} directory created: {out_dir}")

    # 2. Narration Audio Generation (Voice)
    print("\n🎙️ Generating narration audio via Edge-TTS...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_grave")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Narration ready: {dur:.1f}s, {len(words)} words ({narration_info['audio_path']})")

    # 3. Scene Timings calculation
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    scenes = []
    motions = ["zoom_in", "pan_left", "zoom_in_slow", "pan_right", "zoom_in", "zoom_out"]
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

    # 4. Generate Images (ImageGen)
    print("\n🖼️ Generating 6 atmospheric scenes via Pollinations...")
    img_agent = ImageGen(providers=["pollinations", "local_placeholder"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print("✅ All scene images generated successfully!")

    # 5. Build Manifest
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "script": script_data,
        "art": {
            "template_id": "noir_teal",
            "template_name": "Noir Teal",
            "pacing": "standard",
            "setting": "frozen himalayan skeleton lake",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4 with FFmpeg
    print("\n🎥 Rendering video with FFmpeg (effects, subtitles, audio design)...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)

    # Optional: Mix in real cinematic horror/suspense BGM if available
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"
    raw_video = Path(render_info["video_path"])

    if bgm_path.exists():
        print(f"\n🎵 Enhancing final audio with Real Cinematic Suspense BGM ({bgm_path.name})...")
        enhanced_video = out_dir / "final_with_bgm.mp4"
        cmd = [
            "ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(raw_video),
            "-stream_loop", "-1", "-i", str(bgm_path),
            "-filter_complex",
            f"[1:a]volume=0.18,afade=t=in:st=0:d=1.5,afade=t=out:st={max(0.1, dur-2):.2f}:d=2[bgm];"
            "[0:a][bgm]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(enhanced_video)
        ]
        from core.ffmpeg import run
        try:
            run(cmd, what="bgm master mix", timeout=180)
            if enhanced_video.exists() and enhanced_video.stat().st_size > 100000:
                raw_video.unlink(missing_ok=True)
                enhanced_video.rename(raw_video)
                print("✅ Real Cinematic Suspense BGM successfully mixed into final video!")
        except Exception as e:
            print(f"⚠️ BGM mix fallback: {e}")

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
    print(f"✅ Render complete: {raw_video}")
    print(f"   Duration: {final_dur:.1f}s, Size: {final_size_mb}MB")

    # 7. Validate specs
    print("\n🔍 Validating video specifications...")
    rep = validate_dir(out_dir)
    render_info["video_path"] = str(raw_video)
    render_info["duration_sec"] = final_dur
    render_info["size_mb"] = final_size_mb
    manifest["render"] = render_info
    manifest["validation"] = rep.to_dict()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   Validation: {'PASS ✅' if rep.ok else 'WARN ⚠️'}")

    # 8. Approve video in database
    db.set_status(vid, "approved", note="Auto-approved for direct YouTube upload")
    print(f"✅ Video #{vid} status set to APPROVED in database")

    # 9. Upload to YouTube Shorts
    print("\n🚀 Uploading to YouTube Shorts (public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()

    total_time = round(time.time() - t0, 1)
    print("\n" + "=" * 70)
    print("  🎉 CONGRATULATIONS! VIDEO SUCCESSFULLY PUBLISHED TO YOUTUBE!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  ⏱️ Time Taken : {total_time}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
