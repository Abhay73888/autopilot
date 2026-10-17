#!/usr/bin/env python3
"""
generate_and_publish_kaalrekha_ep1.py — Generate, Validate, and Publish KAAL-REKHA Part 1.
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

log = Logbook("kaalrekha_ep1")

TOPIC = "Kaal-Rekha: The Message at 3:17 AM"
TITLE = "Raat 3:17 Baje Mujhe Meri Hi Dead Body Dikhi... ⚠️ | KAAL-REKHA (Part 1) #Shorts"
CAPTION = "Theek 3:17 AM par cassette player apne aap chalu hua... aur neeche sadak par mujhe meri hi laash dikhi! Kaun tha woh? Drop your theories! 👇"
HASHTAGS = ["#KaalRekha", "#AnimeHindi", "#SuspenseShorts", "#HindiHorror", "#IndianAnime", "#Shorts"]
HOOK_OVERLAY = "3:17 AM: MY OWN DEAD BODY?!"
COMMENT_BAIT = "Phone par usne khud ko 'Number Three' bola jabki cassette par '04' likha tha... Kaun hai zinda Kabir? Drop your craziest theories! 👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Theek raat ke 3:17 AM par mere vintage cassette player par ek recording play hui: 'Kabir... balcony se mat dekhna!'",
        "emotion": "serious",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Lekin maine parda hataya... neeche barish mein ek unmarked black ambulance khadi thi.",
        "emotion": "mysterious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Do ajeeb logon ne ek yellow body-bag bahar nikala... aur uska zipper khul gaya.",
        "emotion": "urgent",
        "role": "body"
    },
    {
        "speaker": "char_a",
        "text": "Neeche jo laash padi thi... uska chehra, kapde, sab kuch mera tha!",
        "emotion": "panicked",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Tabhi mere phone par call aayi. Caller ID par mera hi naam tha: 'Main Kabir hoon... Number Three. Aur jo body tumne dekhi, woh tumhara kal hai!'",
        "emotion": "whispers",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Dramatic dark anime shot of a messy attic bedroom at 3:17 AM, glowing red digital clock numbers 03:17, heavy rain hitting window pane, cinematic anime lighting, MAPPA dark psychological thriller style, vertical 9:16, no text, no watermark",
    "Over-the-shoulder view of 21-year-old Indian anime boy Kabir Sen with messy jet-black hair in oversized charcoal hoodie staring at spinning vintage audio cassette player reels on wooden desk, amber light, vertical 9:16, no text, no watermark",
    "High-angle anime shot looking down from balcony into rain-slicked dark street, ominous unmarked black ambulance with flickering amber hazard lights, steam rising from puddles, vertical 9:16, no text, no watermark",
    "Close-up anime view in the rain on wet asphalt of a yellow body-bag slipped open, revealing pale lifeless anime male face matching protagonist under lightning flash, vertical 9:16, no text, no watermark",
    "Extreme close-up of panicked young anime male face with dilated dark brown eyes, sweat on forehead, terror expression, dramatic blue and crimson rim lighting, psychological horror anime, vertical 9:16, no text, no watermark",
    "Low angle anime shot of trembling hand holding glowing smartphone in pitch darkness, screen glowing bright showing incoming call 'KABIR SEN (Self)', blood red atmospheric shadows, vertical 9:16, no text, no watermark"
]


def main():
    print("\n" + "=" * 70)
    print("  🎬 KAAL-REKHA: PART 01 — FULL PRODUCTION PIPELINE")
    print("=" * 70)
    print(f"  📌 Title : {TITLE}")
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
            "char_a": {"name": "Kabir", "gender": "male", "persona": "terrified insomniac protagonist"}
        },
        "lines": LINES,
        "word_count": sum(len(l["text"].split()) for l in LINES),
        "est_sec": 30.0
    }

    vid = db.create_video(
        TOPIC,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        hook_type="pov",
        script_json=script_data,
        length_sec=30,
        status="planned"
    )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} workspace created: {out_dir}")

    # 2. Voice Generation with ElevenLabs + Groq Whisper
    print("\n🎙️ [Step 1] Synthesizing Voice Narration & Subtitle Timestamps...")
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

    # 5. Build Manifest
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "script": script_data,
        "art": {
            "template_id": "crimson_alert",
            "template_name": "Crimson Alert",
            "pacing": "fast",
            "setting": "dark urban rain attic",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4
    print("\n🎥 [Step 3] Rendering Final Video with FFmpeg...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # Optional: Enhance audio with real suspense BGM if available
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

    db.set_status(vid, "approved", note="Rechecked and Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 8. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 KAAL-REKHA PART 01 PUBLISHED SUCCESSFULLY!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  📁 File       : {raw_video}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  ⏱️ Total Time : {elapsed}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
