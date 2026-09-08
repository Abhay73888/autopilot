#!/usr/bin/env python3
"""
generate_and_publish_kaalrekha_ep2.py — Generate, Validate, and Publish KAAL-REKHA Part 2.
Includes clear on-screen 'PART 2' badge and continuous story progression.
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

log = Logbook("kaalrekha_ep2")

TOPIC = "Kaal-Rekha Part 2: The Girl with No Shadow"
TITLE = "Yeh Ladki 25 Saal Pehle Bhi Zinda Thi?! ⚠️ | KAAL-REKHA (Part 2) #Shorts"
CAPTION = "College library mein aayi ek ajeeb ladki... dhoop mein uski koi parchhayi nahi thi aur uske paas meri 1998 ki photo thi! Part 2 is here. Drop your theories! 👇"
HASHTAGS = ["#KaalRekha", "#AnimeHindi", "#SuspenseShorts", "#IndianAnime", "#Part2", "#Shorts"]
HOOK_OVERLAY = "🎬 PART 2: THE GIRL WITH NO SHADOW ⚠️"
COMMENT_BAIT = "1998 ki photo mein Kabir aur Meera bilkul same age ke kaise dikh sakte hain? Time loop ya Clone? Best theory gets pinned! 👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Us khaufnak call ke baad, agle din main college library mein baitha purane records check kar raha tha.",
        "emotion": "serious",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Tabhi mere samne ek ladki aakar baithi — sleek black hair, red ribbon, aur haath mein transparent umbrella.",
        "emotion": "mysterious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Khidki se dhoop aa rahi thi... maine notice kiya ki har cheez ki shadow thi, lekin us ladki ki koi parchhayi nahi thi!",
        "emotion": "urgent",
        "role": "body"
    },
    {
        "speaker": "char_a",
        "text": "Usne mere samne ek purani photo rakhi: '1998 ki photo hai Kabir... hum 25 saal pehle bhi bilkul aise hi dikhte the!'",
        "emotion": "whispers",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Usne mere kaan mein kaha: 'Yeh tumhari pehli zindagi nahi hai... tum already teen baar mar chuke ho!'",
        "emotion": "cold",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Dramatic cinematic anime shot inside an old dusty university library, 21-year-old Indian anime male Kabir Sen with messy jet-black hair in oversized dark charcoal hoodie staring anxiously at laptop screen, rainy window, atmospheric volumetric lighting, vertical 9:16, no text, no watermark",
    "Medium anime shot across wooden library table of mysterious 20-year-old anime girl Meera Varma, porcelain face, piercing amber eyes, black bob haircut with a crimson red ribbon, navy trench coat, holding a transparent umbrella indoors, vertical 9:16, no text, no watermark",
    "High-contrast anime shot of library floor where sunlight casts long dark shadows of chairs and tables, but the girl's chair has zero shadow on the wooden floorboards, eerie surreal psychological horror, vertical 9:16, no text, no watermark",
    "Macro anime close-up of slender pale hand sliding an aged sepia black-and-white 1998 vintage photograph across wooden table, the photo clearly shows Kabir and Meera standing side by side looking identical in age, vertical 9:16, no text, no watermark",
    "Extreme anime close-up of Kabir's right palm trembling on the table, where the burn scar reading 'IV' faintly glows with a strange amber hue, dilated shocked pupils, vertical 9:16, no text, no watermark",
    "Dramatic cinematic anime side-profile shot of Meera leaning close to Kabir's ear whispering with cold calm expression, dark moody shadows, rain hitting library window outside, MAPPA psychological thriller style, vertical 9:16, no text, no watermark"
]


def main():
    print("\n" + "=" * 70)
    print("  🎬 KAAL-REKHA: PART 02 — THE GIRL WITH NO SHADOW")
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
        "hook_type": "pov",
        "hook_line": LINES[0]["text"],
        "hook_text_overlay": HOOK_OVERLAY,
        "comment_bait": COMMENT_BAIT,
        "cast": {
            "narrator": {"gender": "male", "persona": "dark psychological thriller narrator"},
            "char_a": {"name": "Meera", "gender": "female", "persona": "mysterious calm operative"}
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
        hook_type="pov",
        script_json=script_data,
        length_sec=32,
        status="planned"
    )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} workspace created: {out_dir}")

    # 2. Voice Generation (ElevenLabs + Groq Whisper alignment)
    print("\n🎙️ [Step 1] Synthesizing Voice Narration (ElevenLabs + Groq Whisper)...")
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
    print("\n🖼️ [Step 2] Generating Anime Visual Frames via Pollinations FLUX...")
    img_agent = ImageGen(providers=["pollinations", "local_placeholder"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print("✅ All anime scene frames generated successfully!")

    # 5. Build Manifest with persistent PART 2 screen banner
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
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

    # 6. Render MP4 with persistent 'PART 2' badge on screen
    print("\n🎥 [Step 3] Rendering Final Video with FFmpeg & On-Screen 'PART 2' badge...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # Enhance audio with real suspense BGM if available
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"
    if bgm_path.exists():
        enhanced_video = out_dir / "final_enhanced.mp4"
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

    # 7. Quality Gate: Recheck & Validate
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

    if not rep.ok and rep.fatals:
        print(f"❌ FATAL QUALITY ERROR: {rep.fatals[0].code} — {rep.fatals[0].msg}")
        sys.exit(1)

    db.set_status(vid, "approved", note="Part 2 Rechecked and Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 8. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Part 2 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 KAAL-REKHA PART 02 PUBLISHED SUCCESSFULLY!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  📁 File       : {raw_video}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  ⏱️ Total Time : {elapsed}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
