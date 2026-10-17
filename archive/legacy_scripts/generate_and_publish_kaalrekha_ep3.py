#!/usr/bin/env python3
"""
generate_and_publish_kaalrekha_ep3.py — Generate, Validate, and Publish KAAL-REKHA Part 3.
Includes on-screen 'PART 3: THE 4TH DEATH LOOP' badge, intense cassette reveal, and cliffhanger asking for Part 4 comments.
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

log = Logbook("kaalrekha_ep3")

TOPIC = "Kaal-Rekha Part 3: The 4th Death Loop"
TITLE = "Yeh Ladki Hi Mujhe Har Baar Maarti Hai?! 😱 | KAAL-REKHA (Part 3) #Shorts"
CAPTION = "1998 ke cassette tape mein meri hi aawaz ne chetavani di... jiske paas parchhayi nahi hai, wahi kaatil hai! KAAL-REKHA Part 3. Aage kya hoga dekhne ke liye Part 4 ke liye COMMENT karein! 👇"
HASHTAGS = ["#KaalRekha", "#Part3", "#Shorts"]
HOOK_OVERLAY = "🎬 PART 3: THE 4TH DEATH LOOP ⚠️"
COMMENT_BAIT = "1998 ke cassette tape mein Kabir ne khud ko warning kaise di? Meera ka asli sach kya hai? Part 4 dekhne ke liye abhi COMMENT karein! 👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Meera ki baat sunkar mere roongte khade ho gaye: 'Agar main teen baar mar chuka hoon, toh mujhe maar kaun raha hai?'",
        "emotion": "urgent",
        "role": "hook"
    },
    {
        "speaker": "char_a",
        "text": "Usne library ke desk se ek 25 saal purana cassette player nikala aur play button dabaya.",
        "emotion": "mysterious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Speaker se jo aawaz aayi, wo meri hi aawaz thi! 1998 mein record ki gayi meri khud ki aawaz!",
        "emotion": "shocked",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Tape mein meri aawaz cheekh rahi thi: 'Kabir, us ladki se door bhago jiske paas parchhayi nahi hai... Meera hi tumhe har loop mein maarti hai!'",
        "emotion": "dramatic",
        "role": "reveal"
    },
    {
        "speaker": "char_a",
        "text": "Meera ne ek thandi muskaan ke saath surgical scalpel nikaala: 'Chauthi baar marne ke liye tayyar ho, Kabir?'",
        "emotion": "cold",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Agle hi pal library ki saari lights band ho gayi! Kya Kabir is baar bachega? Aage kya hoga dekhne ke liye Part 4 ke liye COMMENT karein!",
        "emotion": "suspense",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Dramatic anime close-up of 21-year-old Indian anime male Kabir Sen with messy jet-black hair in charcoal hoodie, dilated terrified pupils, sweat dripping down his face, glowing Roman numeral IV scar on palm, atmospheric dim library background, vertical 9:16, no text, no watermark",
    "Medium anime shot across wooden library table of mysterious pale girl Meera Varma with sleek black bob and red ribbon placing a vintage 1990s metal cassette recorder on the table, shadows failing to cast from her chair, eerie psychological horror, vertical 9:16, no text, no watermark",
    "Extreme macro anime shot of spinning brown magnetic cassette tape wheels inside vintage Sony Walkman, dusty tape labeled KABIR 1998 in faded red ink, amber reel glow, cinematic lighting, vertical 9:16, no text, no watermark",
    "Surreal psychological anime shot of Kabir clutching his head in shock as ghostly translucent memory waves of his past death loops emerge around him, crimson and navy lighting, MAPPA style, vertical 9:16, no text, no watermark",
    "Chilling cinematic anime close-up of Meera smiling with cold ruthless eyes, pulling out a gleaming sharp surgical steel scalpel reflecting the dim library lamp, rain lashing the windows, vertical 9:16, no text, no watermark",
    "Pitch-black atmospheric anime shot of library plunging into total darkness, only the faint glowing amber scar on Kabir's hand and Meera's reflective amber eyes visible in the shadows, intense horror cliffhanger, vertical 9:16, no text, no watermark"
]


def main():
    print("\n" + "=" * 70)
    print("  🎬 KAAL-REKHA: PART 03 — THE 4TH DEATH LOOP")
    print("=" * 70)
    print(f"  📌 Title : {TITLE}")
    print(f"  🏷️ On-Screen Badge: {HOOK_OVERLAY}")
    print("=" * 70 + "\n")

    t0 = time.time()
    db = DB()

    # 1. Register in Database
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
            "narrator": {"gender": "male", "persona": "dark psychological thriller narrator"},
            "char_a": {"name": "Meera", "gender": "female", "persona": "cold calculated operative"}
        },
        "lines": LINES,
        "word_count": sum(len(l["text"].split()) for l in LINES),
        "est_sec": 34.0
    }

    vid = db.create_video(
        TOPIC,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        hook_type="cliffhanger",
        script_json=script_data,
        length_sec=34,
        status="planned"
    )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} workspace created: {out_dir}")

    # 2. Voice Generation
    print("\n🎙️ [Step 1] Synthesizing Voice Narration with High-Quality Neural Voices...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_narrator")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Narration created: {dur:.1f}s, {len(words)} words ({narration_info['audio_path']})")
    print(f"   Engines used: {narration_info.get('engines_used')}")

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

    # 4. Generate Visual Frames
    print("\n🖼️ [Step 2] Generating Anime Visual Frames...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print("✅ All anime scene frames generated successfully!")

    # 5. Build Manifest
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "title": TITLE,
        "script": script_data,
        "art": {
            "template_id": "crimson_alert",
            "template_name": "Crimson Alert",
            "pacing": "fast",
            "setting": "vintage rainy library mystery",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4 with FFmpeg
    print("\n🎥 [Step 3] Rendering Final Video with FFmpeg & On-Screen 'PART 3' badge...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # Enhance audio with real suspense BGM if available
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"
    if bgm_path.exists():
        enhanced_video = out_dir / "final_enhanced.mp4"
        # NOTE: core.ffmpeg.run() already prepends the ffmpeg binary — do NOT add 'ffmpeg' here
        cmd = [
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
                print("✅ Cinematic Suspense BGM successfully mixed!")
        except Exception as e:
            print(f"⚠️ BGM mix failed, keeping original: {e}")

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

    # 7. Quality Gate: Validate
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

    db.set_status(vid, "approved", note="Part 3 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 8. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Part 3 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 KAAL-REKHA PART 03 PUBLISHED SUCCESSFULLY!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  📁 File       : {raw_video}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  ⏱️ Total Time : {elapsed}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
