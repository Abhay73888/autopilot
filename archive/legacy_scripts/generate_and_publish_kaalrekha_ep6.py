#!/usr/bin/env python3
"""
generate_and_publish_kaalrekha_ep6.py — Generate, Validate, and Publish KAAL-REKHA Part 6 (Season 2 Premiere).
Features the new Option A Viral Edit Engine:
- Kinetic Center-Pop Subtitles (1-2 words, scale bounce, keyword colors)
- Transition Whooshes on every scene cut
- Deep 38Hz Cinematic Braam Sub-Drop on the Shadow Wraith reveal
- Dark anime MAPPA/Ufotable aesthetic 9:16 vertical video (~55s)
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

log = Logbook("kaalrekha_ep6")

TOPIC = "Kaal-Rekha Part 6: The Frozen Timeline (Season 2 Premiere)"
TITLE = "Waqt 3:18 AM Par Kyun Ruk Gaya?! 😱 | KAAL-REKHA (Part 6) #Shorts"
CAPTION = "Maine socha tha 3:17 AM ka loop todkar main azaad ho gaya... par 3:18 AM aate hi poori duniya freeze ho gayi! KAAL-REKHA Season 2 shuru ho chuka hai. Part 7 ke liye COMMENT karein! 👇"
HASHTAGS = ["#KaalRekha", "#Season2", "#Part6", "#Shorts", "#Anime"]
HOOK_OVERLAY = "🎬 SEASON 2: THE FROZEN TIMELINE ⏳"
COMMENT_BAIT = "Kya Kabir is freeze waqt se nikal payega? Part 7 ke liye abhi COMMENT karein! 👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Maine socha tha clock tower ka crystal todkar loop hamesha ke liye khatam ho gaya... par meri asli aazmaish toh ab shuru honi thi!",
        "emotion": "shocked",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "University ke courtyard mein kadam rakhte hi mere rongte khade ho gaye... hawa mein girta hua patta theek mere saamne freeze ho gaya tha!",
        "emotion": "mysterious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Barasti hui baarish ki boondein kaanch ke motiyon ki tarah thami hui thi... na koi aawaz, na koi saans!",
        "emotion": "suspense",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Maine ghabra kar phone dekha: 3 bajkar 18 minute 00 second! Seconds ka kanta hil hi nahi raha tha!",
        "emotion": "shocked",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Main bhagta hua medical wing pahuncha... Meera wahan kisi murti ki tarah khadi thi, uski aankhon mein khauf tha aur ungli meri taraf ishara kar rahi thi!",
        "emotion": "urgent",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Maine peeche mud kar deewar par dekha... wahan meri parchhayi nahi thi! Ek vishaal kaala saya tha jiski chhati par Roman number V dehak raha tha!",
        "emotion": "shocked",
        "role": "climax"
    },
    {
        "speaker": "char_b",
        "text": "Us saaye ne kaha: 'Tumne loop nahi toda Kabir... tumne waqt ka pahiya hi tod diya! Ab tum is thame hue waqt ke qaid mein ho!'",
        "emotion": "cold",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Tabhi meri chhati par aag ki tarah nishaan banne laga: Roman number V! Kya Kabir freeze waqt se nikal payega? Part 7 ke liye COMMENT karein!",
        "emotion": "intense",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Cinematic anime exterior shot of 21-year-old Kabir Sen stepping out of the ruined gothic clock tower into a mist-covered university courtyard at dawn, morning golden light piercing thick grey fog, dramatic atmosphere, vertical 9:16, no text, no watermark",
    "Surreal anime extreme close-up of a falling autumn leaf frozen completely motionless in mid-air right before Kabir's wide astonished eyes, atmospheric depth of field, sharp anime linework, Makoto Shinkai meets MAPPA style, vertical 9:16, no text, no watermark",
    "Breathtaking anime wide shot of rainstorm frozen in time: thousands of crystal rain droplets suspended motionless in the air like floating glass beads, Kabir walking between floating water droplets in total silence, surreal temporal distortion, vertical 9:16, no text, no watermark",
    "Tense anime close-up of Kabir's trembling hand holding a glowing smartphone screen displaying precisely 3:18:00 AM, the seconds digits glowing red and flickering with temporal glitch artifacts, hyper-detailed anime art, vertical 9:16, no text, no watermark",
    "Chilling anime shot inside dimly lit university corridor: medical doctor Meera standing completely frozen like a porcelain statue in mid-motion, terrified expressive eyes, pointing her trembling finger directly behind Kabir, cold cyan lighting, vertical 9:16, no text, no watermark",
    "Terrifying anime psychological horror reveal: Kabir turning around to see his shadow on the stone wall morphing into a towering sinister shadowy wraith with glowing crimson eyes and a blazing amber Roman numeral V burning on its chest, vertical 9:16, no text, no watermark",
    "Epic dark fantasy anime shot of the temporal shadow entity wielding a colossal crystalline temporal scythe, time-space fracturing in black and crimson lightning behind it, imposing dark silhouette, vertical 9:16, no text, no watermark",
    "Shocking anime climax cliffhanger: 21-year-old Kabir falling back as an intense burning crimson Roman numeral V begins blazing painfully onto the skin of his chest, emitting violet smoke and sparks, dramatic camera angle, vertical 9:16, no text, no watermark"
]


def main():
    print("\n" + "=" * 70)
    print("  🎬 KAAL-REKHA: PART 06 — THE FROZEN TIMELINE (SEASON 2 PREMIERE)")
    print("=" * 70)
    print(f"  📌 Title : {TITLE}")
    print(f"  🏷️ On-Screen Badge: {HOOK_OVERLAY}")
    print(f"  ✨ Edit Engine: Option A (Kinetic Center-Pop Subtitles + Braam Drops + Whooshes)")
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
            "narrator": {"gender": "male", "persona": "terrified time-trapped hero (Kabir)"},
            "char_b": {"name": "Shadow Wraith", "gender": "male", "persona": "sinister temporal entity with deep booming voice"}
        },
        "lines": LINES,
        "word_count": sum(len(l["text"].split()) for l in LINES),
        "est_sec": 55.0
    }

    vid = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        vid = int(sys.argv[1])

    if vid:
        db.update_video(
            vid,
            title=TITLE,
            caption=CAPTION,
            hashtags=HASHTAGS,
            script_json=script_data,
            length_sec=55,
            status="planned"
        )
        print(f"🔄 Resuming existing Video #{vid}...")
    else:
        vid = db.create_video(
            TOPIC,
            title=TITLE,
            caption=CAPTION,
            hashtags=HASHTAGS,
            hook_type="cliffhanger",
            script_json=script_data,
            length_sec=55,
            status="planned"
        )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} workspace: {out_dir}")

    # 2. Voice Generation
    timing_file = out_dir / "timing.json"
    audio_file = out_dir / "narration.mp3"
    if timing_file.exists() and audio_file.exists() and audio_file.stat().st_size > 10000:
        print("\n🎙️ [Step 1] Reusing existing synthesized Voice Narration from disk...")
        timing_data = json.loads(timing_file.read_text(encoding="utf-8"))
        narration_info = timing_data
        dur = narration_info["duration_sec"]
        words = []
        for line in narration_info.get("lines", []):
            words.extend(line.get("words", []))
        if not words:
            words = narration_info.get("words", [])
        print(f"✅ Narration loaded: {dur:.1f}s, {len(words)} words ({audio_file})")
    else:
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
    motions = ["zoom_in", "pan_left", "zoom_in_slow", "pan_right", "zoom_in", "pan_left", "zoom_in_slow", "zoom_out"]
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
    print("\n🖼️ [Step 2] Generating Ultra God-Level Anime Frames via Pollinations AI...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print("✅ All 8 anime scene frames generated successfully!")

    # 5. Build Manifest with Kinetic Subtitles & Option A Sound
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "title": TITLE,
        "script": script_data,
        "subtitles": {
            "style": "kinetic"   # Option A Kinetic Center-Pop Subtitles
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
            "template_id": "crimson_alert",
            "template_name": "Crimson Alert",
            "pacing": "fast",
            "setting": "frozen university time paradox",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4 with FFmpeg & on-screen SEASON 2 badge
    final_file = out_dir / "final.mp4"
    cover_file = out_dir / "cover.jpg"
    if final_file.exists() and final_file.stat().st_size > 5000000:
        print(f"\n🎥 [Step 3] Reusing already rendered Final Video: {final_file} ({final_file.stat().st_size // 1024} KB)")
        raw_video = final_file
        render_info = {
            "video_path": str(raw_video),
            "cover_path": str(cover_file),
            "duration_sec": dur,
            "size_mb": round(raw_video.stat().st_size / (1024 * 1024), 2)
        }
    else:
        print("\n🎥 [Step 3] Rendering Final Video with Kinetic Subtitles & Option A SFX...")
        renderer = Renderer(manifest)
        render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
        raw_video = Path(render_info["video_path"])

        # Enhance audio with real suspense BGM if available
        bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"
        if bgm_path.exists():
            enhanced_video = out_dir / "final_enhanced.mp4"
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
                run(cmd, what="bgm master mix", timeout=240)
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
    yt_fatals = [i for i in rep.fatals if i.code != "IG_TOO_LONG"]
    if yt_fatals:
        fatal = "; ".join(f"[{i.code}] {i.msg}" for i in yt_fatals)
        print(f"❌ Pre-upload validation failed: {fatal}")
        sys.exit(1)

    db.set_status(vid, "approved", note="Part 6 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for YouTube upload (Duration: {final_dur:.1f}s).")

    # 8. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Part 6 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 KAAL-REKHA PART 06 (SEASON 2 PREMIERE) PUBLISHED SUCCESSFULLY!")
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
