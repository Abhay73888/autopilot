#!/usr/bin/env python3
"""
generate_and_publish_kaalrekha_ep7.py — Generate, Validate, and Publish KAAL-REKHA Part 7.
Features:
- God-Level Suspense Hook: Meera is frozen in time, but a warm tear falls from her eye!
- Psychological Twist: The mirror reflection speaks backwards with its own sinister voice.
- Time Reversal: Rain flies upward, Roman numeral burns backward from V to IV.
- Duration: High-retention sweet spot (~38-42s) with ~4s rapid cuts.
- Audio: Dual voices (Terrified Kabir + Sinister Mirror Self) + 38Hz Braam Hit + Heartbeat Pulse.
- Subtitles: Kinetic Center-Pop with Crimson & Amber highlights.
- Upload: YouTube Shorts (Public, Comments Enabled).
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

log = Logbook("kaalrekha_ep7")

TOPIC = "Kaal-Rekha Part 7: The Backward Timeline (Ulti Disha Mein Waqt)"
TITLE = "Waqt Freeze Tha... Toh Meera Ne Aansu Kyun Bahaya?! 😱 | KAAL-REKHA (Part 7) #Shorts"
CAPTION = (
    "Agar 3:18 AM par poori duniya freeze ho chuki thi... toh thami hui Meera ki aankh se aansu kyun gira?! "
    "Waqt ruka nahi tha... waqt ULTA chalne laga hai! ⏳⚡\n\n"
    "Kya Kabir is ulte waqt se bach payega? Agle episode (Part 8) ke liye abhi COMMENT karein! 👇🔥"
)
HASHTAGS = ["#KaalRekha", "#Part7", "#Season2", "#Shorts", "#TimeLoop", "#SciFi", "#Anime", "#ShortsFeed"]
HOOK_OVERLAY = "🎬 KAAL-REKHA: PART 7 (TIME RUNS BACKWARD) ⏳"
COMMENT_BAIT = "Agar aaine mein aapki parchhayi aapse alag behave kare... toh aap kya karenge? Part 8 ke liye COMMENT karein! 👇😱"

LINES = [
    {
        "speaker": "narrator",
        "text": "Agar 3:18 AM par poori duniya freeze ho chuki thi... toh saamne khadi Meera ki aankh se ek garam aansu kyun tapka?!",
        "emotion": "shocked",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Main kaanpte hue kadmon se uske paas gaya... Uski thami hui ungli meri taraf nahi, mere theek peeche aaine ki taraf ishara kar rahi thi!",
        "emotion": "suspense",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Maine aaine mein dekha... aur mera khoon jam gaya! Aaine mein mera chehra ghabraya hua nahi tha... wo ajeeb tarah se muskura raha tha!",
        "emotion": "panic",
        "role": "reveal"
    },
    {
        "speaker": "char_b",
        "text": "Aaine wale saaye ne kaha: 'Waqt ruka nahi hai Kabir... waqt ulti disha mein bhaagne laga hai!'",
        "emotion": "cold",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Achanak thami hui baarish ki boondein zameen se aasmaan ki taraf udne lagi! Aur meri chhati par dehakta Roman number V... ghatt kar IV ban gaya!",
        "emotion": "intense",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Ghadi ka kanta 3:18 se peeche 3:17 par chala gaya! Main wapas usi maut ke loop mein kheench raha tha... Part 8 ke liye COMMENT karein!",
        "emotion": "urgent",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Extreme close-up of Meera frozen, but a tear falling
    "Cinematic 8k photorealistic dark anime extreme close-up of medical doctor Meera standing completely motionless in frozen time, a single glistening warm teardrop rolling down her pale cheek, terrifying emotional eyes staring straight ahead, vertical 9:16, masterpiece, MAPPA dark fantasy aesthetic, no text, no watermark",
    
    # Scene 2: Kabir walking towards Meera in ruined corridor
    "Cinematic 8k photorealistic anime shot: 21-year-old Kabir Sen in ruined gothic university corridor, glowing amber Roman numeral V burning through his torn black jacket, trembling hand reaching out toward frozen Meera, volumetric dust motes suspended in air, vertical 9:16, photorealistic, no text",
    
    # Scene 3: Meera's pointing finger directed toward mirror
    "Cinematic 8k dark anime shot: over-the-shoulder perspective from Kabir looking past frozen Meera's pointing finger toward a cracked vintage gilded mirror hanging on the dark stone wall, ominous reflections, vertical 9:16, photorealistic, no text",
    
    # Scene 4: Kabir seeing mirror reflection moving independently
    "Terrifying 8k photorealistic psychological anime horror: Kabir staring into the cracked mirror, but his reflection is moving on its own: the reflection has pitch black shadowy eyes with a sinister cunning smirk, holding an antique bloody silver pocket watch, vertical 9:16, masterpiece, no text",
    
    # Scene 5: Mirror doppelganger speaking cold words
    "Cinematic 8k photorealistic close-up of the sinister mirror doppelganger's face grinning malevolently in dark emerald and crimson shadows, mouth parted speaking chilling words, temporal distortion glass cracks radiating outwards, vertical 9:16, no text",
    
    # Scene 6: Rain droplets defying gravity and flying upwards
    "Mind-bending surreal 8k anime wide shot of time running backwards: thousands of glowing rain droplets reversing direction, defying gravity, flying upwards toward stormy clouds in dark night sky, Kabir falling backwards in sheer disbelief, vertical 9:16, photorealistic, no text",
    
    # Scene 7: Roman numeral V changing to IV on chest
    "Cinematic 8k photorealistic extreme close-up of Kabir's bare chest: the glowing crimson Roman numeral V morphing and sizzling into Roman numeral IV, glowing ember embers and violet lightning radiating across his skin, vertical 9:16, hyperrealistic, no text",
    
    # Scene 8: Clock tower hands snapping backwards 3:18 -> 3:17
    "Dramatic 8k photorealistic anime shot of the colossal gothic clock tower face at night: the massive brass minute hand violently snapping backwards from 3:18 AM to 3:17 AM, sparks and golden temporal energy shattering around the clock face, vertical 9:16, no text",
    
    # Scene 9: Kabir being dragged back into the loop
    "Epic 8k photorealistic anime cliffhanger: 21-year-old Kabir being dragged backward into an abyssal temporal vortex of violet lightning and shattered glass clocks, shouting in desperation, pure cinematic tension, vertical 9:16, masterpiece, no text"
]


def main():
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  🎬 KAAL-REKHA: PART 07 — THE BACKWARD TIMELINE (SEASON 2 EPISODE 2)")
    print("  🔥 GOD-LEVEL SUSPENSE UPGRADE + DUAL NEURAL VOICEOVER")
    print("=" * 70)
    print(f"  📌 Title : {TITLE}")
    print(f"  🏷️ On-Screen Badge: {HOOK_OVERLAY}")
    print("=" * 70 + "\n")

    db = DB()

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
            "char_b": {"gender": "male", "persona": "sinister mirror doppelganger entity"}
        },
        "lines": LINES,
        "word_count": sum(len(ln["text"].split()) for ln in LINES),
        "est_sec": 38.0
    }

    vid = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        vid = int(sys.argv[1])
        db.update_video(
            vid,
            title=TITLE,
            caption=CAPTION,
            hashtags=HASHTAGS,
            script_json=script_data,
            length_sec=38,
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
            length_sec=38,
            status="planned"
        )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} workspace: {out_dir}")

    # 1. Synthesize 10x Voice Narration (Kabir + Sinister Mirror Doppelganger)
    print("\n🎙️ [Step 1] Synthesizing 10x Upgraded Neural Voiceover with Frame-Accurate Sync...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_intense")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Narration created: {dur:.1f}s, {len(words)} words ({narration_info['audio_path']})")
    print(f"   Engines used: {narration_info.get('engines_used')}")

    # 2. Scene Timings calculation (9 rapid cuts ~4.0s each)
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    scenes = []
    motions = ["zoom_in", "pan_left", "zoom_in_slow", "zoom_in", "zoom_in_slow", "pan_right", "zoom_in", "zoom_out", "zoom_in"]
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

    # 3. Generate Visual Frames via Pollinations Flux (Dark MAPPA/Ufotable Anime Style)
    print(f"\n🖼️ [Step 2] Generating {n_scenes} Dark Cinematic Anime Frames via Flux...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"✅ All {n_scenes} surreal dark anime frames generated successfully!")

    # 4. Build Manifest with Option A Viral Edit Engine
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
                "braam": True,     # Bone-rattling 38Hz hit on mirror reveal
                "whoosh": True,    # Rapid transition whooshes
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "crimson_alert",
            "template_name": "Crimson Alert Psychological Thriller",
            "pacing": "dynamic_fast",
            "setting": "frozen temporal university with backward time distortion",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Render MP4 with FFmpeg & on-screen badge
    print(f"\n🎥 [Step 3] Rendering Part 7 with FFmpeg (Pacing: ~{scene_dur:.1f}s/cut, Total: {dur:.1f}s)...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # Enhance audio with dark cinematic suspense BGM
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"
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
            run(cmd, what="suspense bgm master mix", timeout=240)
            if enhanced_video.exists() and enhanced_video.stat().st_size > 100000:
                raw_video.unlink(missing_ok=True)
                enhanced_video.rename(raw_video)
                print("✅ Dark Cinematic Suspense BGM successfully mixed!")
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

    # 6. Quality Gate: Validate
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
        yt_fatals = [i for i in rep.fatals if i.code != "IG_TOO_LONG"]
        if yt_fatals:
            fatal = "; ".join(f"[{i.code}] {i.msg}" for i in yt_fatals)
            print(f"❌ Pre-upload validation failed: {fatal}")
            sys.exit(1)

    db.set_status(vid, "approved", note="Part 7 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 7. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Part 7 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 KAAL-REKHA PART 07 PUBLISHED SUCCESSFULLY TO YOUTUBE SHORTS!")
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
