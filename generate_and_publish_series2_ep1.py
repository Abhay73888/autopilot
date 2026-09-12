#!/usr/bin/env python3
"""
generate_and_publish_series2_ep1.py — Generate, Validate, and Publish SERIES 2: Episode 1.
'2020 — JAB PYAAR ONLINE THA': Episode 1 — 'SCREEN PAR PEHLI BAAR'
High-retention Indian coming-of-age romance (~52-55s) with 8 cinematic Makoto Shinkai-grade scenes,
on-screen '✨ 2020: JAB PYAAR ONLINE THA (EPISODE 1) 🎧' badge, and viral typing-dots cliffhanger.
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

log = Logbook("series2_ep1")

TOPIC = "2020 — Jab Pyaar Online Tha: Episode 1 (Screen Par Pehli Baar)"
TITLE = "2020 Ke Lockdown Mein Ek Ladki Par Dil Aa Gaya... ❤️ | JAB PYAAR ONLINE THA (Ep 1) #Shorts"
CAPTION = "2020 ke lockdown ki online class mein jab Meera ne camera on kiya... tab se zindagi hamesha ke liye badal gayi. JAB PYAAR ONLINE THA (Episode 1). Episode 2 ke liye abhi COMMENT karein! 👇"
HASHTAGS = ["#JabPyaarOnlineTha", "#Series2", "#Episode1", "#Shorts", "#Romance"]
HOOK_OVERLAY = "✨ 2020: JAB PYAAR ONLINE THA (EPISODE 1) 🎧"
COMMENT_BAIT = "Kya aapko bhi 2020 lockdown ki yaad aayi? Drop a ❤️ agar aapne bhi kisi ko online pehli baar dekha tha! Episode 2 ke liye COMMENT karein! 👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "2020 ke lockdown ne poori duniya ko qaid kar diya tha... par meri qaid mein ek aisi kahani shuru hone wali thi jo agle 7 saal chalegi.",
        "emotion": "nostalgic",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Subah ke 9 baje school ki online class chal rahi thi, aur main aalas mein microphone aur camera band karke screen ko ghoor raha tha.",
        "emotion": "calm",
        "role": "body"
    },
    {
        "speaker": "char_a",
        "text": "Tabhi teacher ki aawaz aayi: 'Everyone please turn your webcams ON!' Maine aalas mein screen dekhi...",
        "emotion": "neutral",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Aur achanak ek camera frame on hua... saamne Meera thi. Halka sa messy bun, pyari si muskaan, aur aankhon mein ajeeb si masoomiyat.",
        "emotion": "amazed",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "'Roll 14 Aarav?' 'Present ma'am.' 'Roll 29 Meera?' 'Present ma'am.' Aur dono ne screen par ek doosre ko dekhkar dheere se smile kiya.",
        "emotion": "sweet",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Us raat kamre ke andhere mein blanket ke andar mere kaanpte hue haath uske Instagram par follow button daba rahe the.",
        "emotion": "nervous",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Agle hi pal notification chamka: 'Meera accepted your follow request and followed you back.' Mera dil gale mein aa gaya!",
        "emotion": "excited",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Maine himmat karke likha 'Hi :)'... aur tabhi screen par teen typing dots flash hone lage. Kabhi-kabhi ek 'Hi' poori zindagi badal deta hai!",
        "emotion": "romantic",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Atmospheric cinematic anime wide shot of deserted rainy streets of Lucknow and New Delhi under 2020 lockdown, amber traffic light glowing in silent rain, rain puddles reflecting streetlamps, moody nostalgic cloudy sky, Makoto Shinkai aesthetic, vertical 9:16, no text, no watermark",
    "Cozy anime interior of 16-year-old Indian boy Aarav sitting at his bedroom study desk in soft morning light, messy black hair, casual t-shirt, glowing laptop screen displaying Google Meet virtual classroom, gentle raindrops hitting windowpane, vertical 9:16, no text, no watermark",
    "Cinematic anime close-up shot of laptop screen displaying teacher attendance grid, bright virtual classroom tiles activating with soft ambient lighting illuminating Aarav's room, vertical 9:16, no text, no watermark",
    "Breathtaking anime beauty portrait of 16-year-old Indian girl Meera appearing on webcam video frame, soft gentle smile, dark wavy hair in messy low bun, expressive brown eyes, wearing pastel yellow kurti, delicate silver bracelet visible on wrist, radiant golden-hour bedroom glow, vertical 9:16, no text, no watermark",
    "Romantic anime split-screen style frame: left showing Aarav blushing with nervous happy smile looking at monitor, right showing Meera unmuting mic with shy warm smile, golden morning sunlight and floating dust motes, vertical 9:16, no text, no watermark",
    "Moody anime night shot in dark cozy bedroom, Aarav lying in bed under blanket, smartphone screen casting soft blue-white glow on his face, Instagram profile page open with finger hovering nervously over blue Follow button, vertical 9:16, no text, no watermark",
    "Thrilling emotional anime close-up of phone screen glowing with notification alert banner: 'Meera accepted your follow request', Aarav sitting up suddenly with wide excited sparkling eyes, hand over chest feeling fast heartbeat, vertical 9:16, no text, no watermark",
    "Magical anime cliffhanger shot: Instagram direct message chat screen showing sent text 'Hi :)', below it three animated white typing dots pulsating in speech bubble, Aarav holding phone with bated breath, cinematic bokeh background, vertical 9:16, no text, no watermark"
]


def main():
    print("\n" + "=" * 70)
    print("  💖 SERIES 2: EPISODE 01 — 'SCREEN PAR PEHLI BAAR'")
    print("=" * 70)
    print(f"  📌 Title : {TITLE}")
    print(f"  🏷️ On-Screen Badge: {HOOK_OVERLAY}")
    print(f"  ⏱️ Target Duration: ~52-55s (Coming-of-Age Short)")
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
            "narrator": {"gender": "male", "persona": "youthful reflective Indian boy (Aarav)"},
            "char_a": {"name": "Teacher", "gender": "female", "persona": "strict polite online teacher"}
        },
        "lines": LINES,
        "word_count": sum(len(l["text"].split()) for l in LINES),
        "est_sec": 52.0
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
            length_sec=52,
            status="planned"
        )
        print(f"🔄 Resuming existing Video #{vid}...")
    else:
        vid = db.create_video(
            TOPIC,
            title=TITLE,
            caption=CAPTION,
            hashtags=HASHTAGS,
            hook_type="pov",
            script_json=script_data,
            length_sec=52,
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
    print("\n🖼️ [Step 2] Generating Makoto Shinkai Aesthetic Anime Frames via Pollinations AI...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print("✅ All 8 romantic scene frames generated successfully!")

    # 5. Build Manifest
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "title": TITLE,
        "script": script_data,
        "art": {
            "template_id": "warm_amber",
            "template_name": "Warm Amber Nostalgia",
            "pacing": "standard",
            "setting": "2020 lockdown online school romance",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4 with FFmpeg & on-screen SERIES 2 badge
    print("\n🎥 [Step 3] Rendering Final Video with FFmpeg & On-Screen 'SERIES 2' badge...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # Enhance audio with emotional romantic piano BGM
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "romance_bgm.mp3"
    if not bgm_path.exists():
        bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"

    if bgm_path.exists():
        enhanced_video = out_dir / "final_enhanced.mp4"
        cmd = [
            "-i", str(raw_video),
            "-stream_loop", "-1", "-i", str(bgm_path),
            "-filter_complex",
            f"[1:a]volume=0.15,afade=t=in:st=0:d=1.5,afade=t=out:st={max(0.1, dur-2):.2f}:d=2[bgm];"
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
                print("✅ Nostalgic Romance BGM successfully mixed!")
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

    if not rep.ok:
        fatal = "; ".join(f"[{i.code}] {i.msg}" for i in rep.fatals)
        print(f"❌ Pre-upload validation failed: {fatal}")
        sys.exit(1)

    db.set_status(vid, "approved", note="Series 2 Ep 1 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 8. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Series 2 Ep 1 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 SERIES 2: EPISODE 01 PUBLISHED SUCCESSFULLY!")
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
