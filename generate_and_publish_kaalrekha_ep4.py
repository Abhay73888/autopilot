#!/usr/bin/env python3
"""
generate_and_publish_kaalrekha_ep4.py — Generate, Validate, and Publish KAAL-REKHA Part 4.
Longer, high-retention thriller episode (~55s) with 8 cinematic anime scenes,
on-screen 'PART 4: THE MASTERMIND REVEAL' badge, intense plot twist, and cliffhanger.
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

log = Logbook("kaalrekha_ep4")

TOPIC = "Kaal-Rekha Part 4: The Mastermind Reveal"
TITLE = "Main Khud Hi Apne Aap Ko Maar Raha Hoon?! 😱 | KAAL-REKHA (Part 4) #Shorts"
CAPTION = "Andhere mein jab library se bhagkar clock tower pahuncha, wahan meri 3 purani dead bodies mili... aur saamne khada tha mera hi 50 saal purana roop! KAAL-REKHA Part 4. Finale Part 5 ke liye COMMENT karein! 👇"
HASHTAGS = ["#KaalRekha", "#Part4", "#Shorts"]
HOOK_OVERLAY = "🎬 PART 4: THE MASTERMIND REVEAL ⚠️"
COMMENT_BAIT = "Kya Kabir apne 50 saal purane roop ko hara payega? Ya Loop 4 mein bhi uski maut hogi? Part 5 / Season Finale ke liye abhi COMMENT karein! 👇"

LINES = [
    {
        "speaker": "narrator",
        "text": "Library ki battiyan gul hote hi Meera ka scalpel mere gale ko chhoone hi wala tha, par meri hatheli ka nishaan aag ki tarah chamak utha!",
        "emotion": "urgent",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Maine andhere mein library ki khidki ka kaanch tod diya aur toofani baarish mein bahar kood gaya.",
        "emotion": "dramatic",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "University ke purane clock tower ki ghadi cheekh rahi thi: 3 bajkar 16 minute! Sirf ek minute bacha tha meri maut mein!",
        "emotion": "suspense",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Main jaan bachane ke liye clock tower ke andar bhaga, par wahan ka nazara dekhkar mere pairo tale zameen khisak gayi!",
        "emotion": "shocked",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Wahan teen kaanch ke chambers mein teen laashe rakhi thi... Loop 1, Loop 2, aur Loop 3 ke Kabir Sen ki laashe!",
        "emotion": "shocked",
        "role": "reveal"
    },
    {
        "speaker": "char_b",
        "text": "Tabhi peeche se ek bhaari aawaz aayi: 'Meera tumhe maar nahi rahi thi Kabir... wo tumhe mujhse bacha rahi thi!'",
        "emotion": "mysterious",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Peeche mudkar dekha toh mere hosh udd gaye... saamne khada shaks mera hi 50 saal purana roop tha, jiski aankhein laal angare jaisi thi!",
        "emotion": "shocked",
        "role": "climax"
    },
    {
        "speaker": "char_b",
        "text": "Usne ghadi ka lever kheenchkar kaha: 'Loop 4 khatam karne ka waqt aa gaya hai!' Kya Kabir bachega? Finale Part 5 ke liye COMMENT karein!",
        "emotion": "cold",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Extreme dramatic anime close-up of 21-year-old Indian male Kabir Sen dodging a gleaming surgical blade in pitch dark library, radiant glowing amber Roman numeral IV blazing on his palm casting orange reflections on his terrified eyes, dynamic action anime, vertical 9:16, no text, no watermark",
    "Dynamic full-body anime action shot of Kabir shattering heavy rainy glass window and leaping out into torrential thunderstorm, glass shards glittering under lightning strike, gothic university architecture, intense motion blur, vertical 9:16, no text, no watermark",
    "Ominous anime low-angle shot of a massive ancient stone clock tower illuminated by violent violet lightning, colossal clock hands ticking precisely at 3:16 AM, dark stormy clouds swirling, psychological thriller atmosphere, vertical 9:16, no text, no watermark",
    "Atmospheric anime interior of dusty vintage clock tower mechanism room, colossal bronze brass gears rotating heavily, Kabir Sen standing breathless and drenched in rain clutching his chest, shafts of eerie amber moonlight, vertical 9:16, no text, no watermark",
    "Terrifying anime wide shot inside hidden laboratory room showing three tall vertical glowing cyan cryogenic glass tanks, inside each tank floats a lifeless clone of Kabir Sen labeled LOOP I, LOOP II, LOOP III, psychological horror, vertical 9:16, no text, no watermark",
    "Shadowy silhouette of a tall mysterious sinister trench-coat figure emerging from the clock tower steam pipes, holding a glowing pocket watch, deep blue and crimson ambient neon lighting, vertical 9:16, no text, no watermark",
    "Chilling anime face-to-face reveal shot: 21-year-old terrified Kabir staring in absolute horror at a 50-year-old grizzled battle-scarred older version of himself with silver-streaked hair, cold cybernetic glowing crimson eye and identical scar, MAPPA style, vertical 9:16, no text, no watermark",
    "Cinematic anime climax shot of the older sinister Kabir pulling a massive iron clockwork lever as ancient bell strikes 3:17 AM, reality distorting into temporal fractures, intense cliffhanger anime art, vertical 9:16, no text, no watermark"
]


def main():
    print("\n" + "=" * 70)
    print("  🎬 KAAL-REKHA: PART 04 — THE MASTERMIND REVEAL")
    print("=" * 70)
    print(f"  📌 Title : {TITLE}")
    print(f"  🏷️ On-Screen Badge: {HOOK_OVERLAY}")
    print(f"  ⏱️ Target Duration: ~55s (Longer Short)")
    print("=" * 70 + "\n")

    t0 = time.time()
    db = DB()

    # 1. Register or Resume in Database
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
            "char_b": {"name": "Older Kabir", "gender": "male", "persona": "grizzled time-traveling antagonist"}
        },
        "lines": LINES,
        "word_count": sum(len(l["text"].split()) for l in LINES),
        "est_sec": 55.0
    }

    vid = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        vid = int(sys.argv[1])
    else:
        existing = db.get_video(139)
        if existing and dict(existing).get("status") in ("planned", "failed"):
            vid = 139

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
    print("\n🖼️ [Step 2] Generating Anime Visual Frames via Pollinations AI...")
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
            "setting": "stormy clocktower time paradox",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4 with FFmpeg & on-screen PART 4 badge
    print("\n🎥 [Step 3] Rendering Final Video with FFmpeg & On-Screen 'PART 4' badge...")
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

    db.set_status(vid, "approved", note="Part 4 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 8. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Part 4 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 KAAL-REKHA PART 04 PUBLISHED SUCCESSFULLY!")
    print("=" * 70)
    print(f"  🎬 Video ID   : #{vid}")
    print(f"  📌 Title      : {TITLE}")
    print(f"  📁 File       : {raw_video}")
    print(f"  🔗 YouTube URL: {res.get('url')}")
    print(f"  ⏱️ Total Time : {elapsed}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
