#!/usr/bin/env python3
"""
generate_and_publish_kaalrekha_ep5.py — Generate, Validate, and Publish KAAL-REKHA Part 5 (Season Finale).
Epic conclusion to the time-loop sci-fi thriller (~55-58s) with 8 cinematic anime scenes,
on-screen 'SEASON FINALE: THE TIME LOOP SHATTERS' badge, emotional climax, and resolution.
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

log = Logbook("kaalrekha_ep5")

TOPIC = "Kaal-Rekha Part 5: The Time Loop Shatters (Season Finale)"
TITLE = "Mera 50 Saal Purana Roop... Loop Hamesha Ke Liye Toot Gaya! 💥 | KAAL-REKHA (Finale Part 5) #Shorts"
CAPTION = "Clock tower ke 3:17 AM par maine apne hi 50 saal purane roop ke saamne temporal core par vaar kiya... aur hamesha ke liye Kaal-Rekha ka time loop toot gaya! KAAL-REKHA SEASON FINALE. Kaisi lagi series? Comment karein! 👇"
HASHTAGS = ["#KaalRekha", "#SeasonFinale", "#Part5", "#Shorts", "#Anime"]
HOOK_OVERLAY = "🎬 SEASON FINALE: THE TIME LOOP SHATTERS ⚡"
COMMENT_BAIT = "Kya aapko lagta hai Kaal-Rekha ka Season 2 aana chahiye? Drop a 🔥 aur apna review comment karein! 👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Older Kabir ne jaise hi 3:17 AM ka lever kheencha, clock tower ke saare pahiye cheekhte hue aag ugalne lage!",
        "emotion": "urgent",
        "role": "hook"
    },
    {
        "speaker": "char_b",
        "text": "Usne rote hue kaha: 'Maine Meera ko bachaane ke liye har loop mein tumhe qurban kiya Kabir... par ab ye dukh main aur nahi jhel sakta!'",
        "emotion": "emotional",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Tabhi meri daayi hatheli par bana Roman number IV sooraj ki tarah dehak utha, aur poore chamber mein sunehri roshni phail gayi!",
        "emotion": "dramatic",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Clock tower ke theek beech mein temporal core ka neela crystal dhadak raha tha... wahi tha is anant kaal-chakra ka dil!",
        "emotion": "suspense",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Bhagne ke bajaye, maine apni aag ugalte haath ko us vishaal ghoomte hue pendulum aur core ki taraf jhonk diya!",
        "emotion": "intense",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Jaise hi ghadi ne 3:17:00 bajaye, meri mutthi ne temporal crystal ko hazaron tukdon mein chaknachoor kar diya!",
        "emotion": "shocked",
        "role": "climax"
    },
    {
        "speaker": "char_b",
        "text": "Saari machinery sunehri dhool ban kar udne lagi... Older Kabir ne muskurakar kaha: 'Shukriya Kabir... aakhirkar hum azaad ho gaye!'",
        "emotion": "peaceful",
        "role": "resolution"
    },
    {
        "speaker": "narrator",
        "text": "Subah ki dhoop mein jab aankh khuli, mere phone par 3 bajkar 18 minute ho rahe the... 4 saal baad waqt aage badh chuka tha!",
        "emotion": "triumphant",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Hyper-dramatic anime interior wide shot of ancient gothic clock tower at 3:16 AM, colossal glowing brass gears turning with sparks flying, older 50-year-old Kabir Sen in rugged trench coat gripping a massive steam-powered iron lever, temporal distortions tearing purple cracks in the air, vertical 9:16, no text, no watermark",
    "Emotional anime close-up of the 50-year-old battle-scarred Kabir Sen with silver-streaked hair, tears trickling down his wrinkled scarred cheek, glowing cybernetic crimson eye flickering with deep sorrow and regret, atmospheric rain and steam mist, vertical 9:16, no text, no watermark",
    "Epic anime hero shot of 21-year-old Kabir Sen standing defiant, his right palm ablaze with an intensely radiant golden Roman numeral IV emitting solar energy flames and amber lightning arcs, determined fearless expression, vertical 9:16, no text, no watermark",
    "Breathtaking anime detailed shot of the central temporal machine: a colossal pulsing luminescent cyan crystal core suspended inside massive interlocking bronze astronomical clock rings, energy tendrils crackling across the chamber, vertical 9:16, no text, no watermark",
    "Dynamic anime action frame of young Kabir leaping through the air with extreme speed blur, fist wrapped in blazing golden solar fire aimed directly at the pulsating blue temporal crystal, high cinematic angle, vertical 9:16, no text, no watermark",
    "Spectacular cosmic impact anime shot: Kabir's burning golden fist violently shattering the colossal cyan crystal into millions of glittering crystalline shards and shockwaves, time-space fracturing in brilliant ultraviolet and amber light, vertical 9:16, no text, no watermark",
    "Touching emotional anime wide shot of the clock tower dissolving into millions of floating golden stardust particles, the 50-year-old Kabir smiling peacefully as his silhouette fades away into light, sense of liberation and closure, vertical 9:16, no text, no watermark",
    "Peaceful cinematic anime dawn shot: gentle golden morning sunlight streaming across a ruined stone balcony, 21-year-old Kabir sitting alive and breathing fresh air, looking at his clean unblemished palm, smartphone screen beside him displaying 3:18 AM, beautiful sunrise clouds in sky, Makoto Shinkai aesthetic, vertical 9:16, no text, no watermark"
]


def main():
    print("\n" + "=" * 70)
    print("  🎬 KAAL-REKHA: PART 05 — THE TIME LOOP SHATTERS (SEASON FINALE)")
    print("=" * 70)
    print(f"  📌 Title : {TITLE}")
    print(f"  🏷️ On-Screen Badge: {HOOK_OVERLAY}")
    print(f"  ⏱️ Target Duration: ~55s (Climactic Short)")
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
            "narrator": {"gender": "male", "persona": "emotional heroic anime protagonist"},
            "char_b": {"name": "Older Kabir", "gender": "male", "persona": "grizzled time-traveler seeking peace"}
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
    motions = ["zoom_in", "pan_left", "zoom_in_slow", "pan_right", "zoom_in", "pan_left", "zoom_in", "zoom_out"]
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
    print("\n🖼️ [Step 2] Generating Ultra God-Level Anime Visual Frames via Pollinations AI...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print("✅ All 8 anime scene frames generated successfully!")

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
            "setting": "clocktower finale time loop shatter",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4 with FFmpeg & on-screen SEASON FINALE badge
    print("\n🎥 [Step 3] Rendering Final Video with FFmpeg & On-Screen 'SEASON FINALE' badge...")
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
    print(f"   Validation : {'PASS ✅' if rep.ok else 'WARN ⚠️'}")

    if not rep.ok:
        fatal = "; ".join(f"[{i.code}] {i.msg}" for i in rep.fatals)
        print(f"❌ Pre-upload validation failed: {fatal}")
        sys.exit(1)

    db.set_status(vid, "approved", note="Part 5 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 8. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Part 5 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 KAAL-REKHA PART 05 (SEASON FINALE) PUBLISHED SUCCESSFULLY!")
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
