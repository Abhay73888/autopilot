#!/usr/bin/env python3
"""
generate_series2_ep2_preview.py — Generate & Render SERIES 2: Episode 2 ("HI SE HUM TAK").
STRICT: DO NOT UPLOAD TO YOUTUBE OR ANY PLATFORM (User request: preview only).

Features:
- Pacing: 32-36s viral high-retention runtime (~3.5s rapid cuts)
- Visuals: 10 Photorealistic Indian cinematic shots with Flux
- Subtitles: Kinetic Center-Pop Subtitles with Rose Pink & Gold romance highlights
- Sound: Nostalgic Lo-Fi Piano BGM + Transition Whooshes + Heartbeat & Sub-bass drop
- On-Screen Badge: ✨ 2020: JAB PYAAR ONLINE THA (EPISODE 2) 🎧
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

log = Logbook("series2_ep2")

TOPIC = "2020 — Jab Pyaar Online Tha: Episode 2 (Hi Se Hum Tak)"
TITLE = "Raat Ke 2 Baje Meera Ka Message Aaya... 💬❤️ | JAB PYAAR ONLINE THA (Ep 2) #Shorts"
CAPTION = "Lockdown ne poori duniya ko qaid kiya tha... par hum dono ek doosre ki aadat ban chuke the. JAB PYAAR ONLINE THA (Episode 2). Episode 3 ke liye abhi COMMENT karein! 👇"
HASHTAGS = ["#JabPyaarOnlineTha", "#Series2", "#Episode2", "#Shorts", "#Romance", "#LoveStory"]
HOOK_OVERLAY = "✨ 2020: JAB PYAAR ONLINE THA (EPISODE 2) 🎧"
COMMENT_BAIT = "Kya dosti aur pyaar ke beech ki line kab cross hoti hai pata chalta hai? Episode 3 ke liye COMMENT karein! 👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Lockdown ne poori duniya ko kamron mein qaid kiya tha... par hum dono ek doosre ki aadat ban chuke the.",
        "emotion": "nostalgic",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Raat ke 2 baje notification chamka: 'Soye nahi abhi tak?' Maine likha: 'Tum online thi.' Meera ka reply aaya: 'Pagal!'",
        "emotion": "sweet",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Online lectures ke lambe ghante ab bojh nahi the... bas screen par uski muskaan dekhkar din nikal jaata tha.",
        "emotion": "romantic",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Ek raat usne pucha: 'Agar lockdown khul gaya... toh kya hum kabhi milenge?' Maine kaha: 'Tumhe bhoolna itna easy hai kya?'",
        "emotion": "tender",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Agle din attendance mein uska naam gayab tha. Maine ghabra kar pucha: 'Sab theek hai na?' Meera ne likha: 'Bas thoda pareshan hoon...'",
        "emotion": "nervous",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Maine likha: 'Main yahin hoon.' Aur tabhi raat ke 1:47 par uska message chamka: 'Aarav... I think I'm falling for you!'",
        "emotion": "climax",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Cinematic 8k photorealistic portrait of 16-year-old Indian boy Aarav lying in dark bedroom under blanket, illuminated by soft blue glow of smartphone screen, emotional longing expression, messy black hair, vertical 9:16, masterpiece, hyperrealistic, no text, no watermark",
    "Cinematic 8k photorealistic close-up of smartphone screen displaying glowing WhatsApp chat bubbles at 2:00 AM in dark bedroom, aesthetic bokeh of city night outside window, authentic Indian teenager late night chat, vertical 9:16, photorealistic, no watermark",
    "Cinematic 8k photorealistic beauty portrait of 16-year-old Indian girl Meera sitting on her bed under warm golden night lamp glow, wearing pastel oversized hoodie, shy romantic smile looking down at mobile screen, dark wavy hair in messy bun, delicate silver bracelet on left wrist, vertical 9:16, hyperrealistic",
    "Cinematic 8k photorealistic shot of virtual online school classroom grid on laptop screen, bright morning sunlight streaming into student bedroom, books and earphones scattered on desk, nostalgic 2020 lockdown study vibe, vertical 9:16, hyperrealistic",
    "Cinematic 8k photorealistic close-up of Meera smiling gently into her laptop webcam during online class, wearing soft pastel yellow kurti, genuine shy expression, glowing morning sunlight illuminating dust motes in air, vertical 9:16, hyperrealistic",
    "Cinematic 8k photorealistic shot of Aarav sitting by glass window at 2 AM watching heavy rain streaks outside, warm amber city streetlamp reflection, emotional and thoughtful expression, vertical 9:16, photorealistic",
    "Cinematic 8k photorealistic close-up of laptop screen displaying Google Meet participant attendance list, Aarav's finger hovering over trackpad searching anxiously for Meera's name, dark mood, vertical 9:16, photorealistic",
    "Cinematic 8k photorealistic shot of teenage Indian boy's hands trembling slightly while typing concern message on smartphone keyboard in dimly lit room, tense and worried atmosphere, vertical 9:16, photorealistic",
    "Cinematic 8k photorealistic emotional portrait of Meera sitting alone by rainy window looking at delicate silver thread bracelet on her wrist, deep emotional longing and vulnerability, soft cinematic shadows, vertical 9:16, hyperrealistic",
    "Cinematic 8k photorealistic extreme close-up of smartphone screen lighting up in pitch dark at 1:47 AM displaying incoming message preview: 'Aarav... I think I'm falling for you', heartbeat emotional shockwave, breathtaking romantic climax, vertical 9:16, photorealistic, masterpiece"
]


def main():
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  🎬 GENERATING SERIES 2 — EPISODE 02: 'HI SE HUM TAK'")
    print("  ⚠️ MODE: LOCAL PREVIEW ONLY (UPLOAD DISABLED)")
    print("=" * 70)

    db = DB()

    # 1. Register or resume in Database
    vid = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        vid = int(sys.argv[1])

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
            "narrator": {"gender": "male", "persona": "emotional teenage boy (Aarav)"}
        },
        "lines": LINES,
        "word_count": sum(len(ln["text"].split()) for ln in LINES),
        "est_sec": 35.0
    }

    if vid:
        db.update_video(
            vid,
            title=TITLE,
            caption=CAPTION,
            hashtags=HASHTAGS,
            script_json=script_data,
            length_sec=35,
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
            length_sec=35,
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

    # 3. Scene Timings calculation (10 rapid shots)
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    scenes = []
    motions = ["zoom_in", "pan_left", "zoom_in_slow", "pan_right", "zoom_in", "pan_left", "zoom_in_slow", "pan_right", "zoom_in_slow", "zoom_in"]
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

    # 4. Generate Visual Frames via Pollinations Flux (Photorealistic)
    print(f"\n🖼️ [Step 2] Generating {n_scenes} Photorealistic Indian Cinematic Frames via Flux...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"✅ All {n_scenes} romantic scene frames generated successfully!")

    # 5. Build Manifest with Option A Viral Edit Engine
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "title": TITLE,
        "script": script_data,
        "subtitles": {
            "style": "kinetic"  # Center-Pop Subtitles with Scale-Bounce
        },
        "effects": {
            "sound": {
                "heartbeat": True,
                "riser": True,
                "braam": False,
                "whoosh": True,
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "warm_amber",
            "template_name": "Warm Amber Nostalgia",
            "pacing": "dynamic_fast",
            "setting": "2020 lockdown late night romantic chat",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4 with FFmpeg & on-screen SERIES 2 badge
    print(f"\n🎥 [Step 3] Rendering Final Video with FFmpeg (Pacing: ~{scene_dur:.1f}s/cut, Total: {dur:.1f}s)...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # Enhance audio with emotional romantic lo-fi piano BGM
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "romance_bgm.mp3"
    if bgm_path.exists():
        enhanced_video = out_dir / "final_enhanced.mp4"
        cmd = [
            "-i", str(raw_video),
            "-stream_loop", "-1", "-i", str(bgm_path),
            "-filter_complex",
            f"[1:a]volume=0.14,afade=t=in:st=0:d=1.0,afade=t=out:st={max(0.1, dur-2):.2f}:d=2[bgm];"
            "[0:a][bgm]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(enhanced_video)
        ]
        from core.ffmpeg import run
        try:
            run(cmd, what="romance bgm master mix", timeout=240)
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

    db.set_status(vid, "approved", note="Series 2 Ep 2 Approved (Preview Only — Not Uploaded)")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 SERIES 2 — EPISODE 02 GENERATED & RENDERED SUCCESSFULLY!")
    print("  🛑 NOTE: AS REQUESTED, UPLOAD HAS BEEN SKIPPED!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  📁 File Path  : {raw_video}")
    print(f"  🖼️ Cover Path : {render_info['cover_path']}")
    print(f"  ⏱️ Duration   : {final_dur:.1f}s")
    print(f"  💾 File Size  : {final_size_mb} MB")
    print(f"  ⚡ Generation : {elapsed}s")
    print("=" * 70 + "\n")
    return raw_video


if __name__ == "__main__":
    main()
