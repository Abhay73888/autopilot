#!/usr/bin/env python3
"""
generate_and_publish_series8_ep1.py — Generate, Validate, and Render SERIES 8: Episode 1.
'LEONARDO DA VINCI (1452–1519)': Episode 1 — 'THE MYSTERY OF LEONARDO: OMO SANZA LETTERE'

Ultra-cinematic historical documentary format:
  • Edge-TTS grave documentary narrator (hi-IN-MadhurNeural / en-US-ChristopherNeural)
  • 7 historically accurate Renaissance scenes (Candlelit workshop, mirror script, sfumato Mona Lisa, Florence dawn)
  • Dynamic Ken Burns camera framing
  • Gold-parchment ASS kinetic subtitles
  • Procedural & real ambient score mix (suspense_bgm.mp3)
  • YouTube Invariant compliance (Comments 100% ON, MadeForKids=False)

Usage:
  python generate_and_publish_series8_ep1.py
  python generate_and_publish_series8_ep1.py --upload
"""

from __future__ import annotations

import argparse
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

log = Logbook("series8_ep1")

TOPIC = "Leonardo da Vinci: Episode 1 — The Mystery of Leonardo ('Omo Sanza Lettere')"
TITLE = "Leonardo Da Vinci Ka Sabse Bada Chhippa Hua Raaz! 📜🎨 | LEONARDO (Ep 1) #Shorts"
CAPTION = (
    "500 saal pehle bina kisi university degree ke ek aam insaan ne duniya ka nazariya badal diya! "
    "Fewer than 20 paintings, 10,000+ notebook pages in mirror script, and the secret of 'Omo Sanza Lettere'. "
    "Watch the forensic documentary of Leonardo da Vinci. Episode 2 ke liye COMMENT karein! 👇"
)
HASHTAGS = [
    "#LeonardoDaVinci", "#Renaissance", "#MonaLisa", "#HistoryMystery",
    "#DocumentaryShorts", "#Series8", "#Episode1", "#Shorts", "#TrueHistory"
]
HOOK_OVERLAY = "📜 LEONARDO DA VINCI (EPISODE 1) 🏛️"
COMMENT_BAIT = "Kya aapko lagta hai Leonardo wakai ek sadharan insaan the ya unka dimaag sadiyon aage tha? Apni raye comment mein dein! 👇"

LINES_HI = [
    {
        "speaker": "narrator",
        "text": "Kaise 500 saal pehle ek aam insaan bina kisi degree ke painter, anatomist, engineer aur scientist sab kuch ban gaya?",
        "emotion": "serious",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Ye hai Leonardo da Vinci. Duniya unhe jadoogar samajhti hai, lekin asli sach unki chhippi hui diary mein darj hai.",
        "emotion": "mysterious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Unki poori zindagi mein unhone 20 se bhi kam paintings banayi... lekin unke haathon se likhe 10 hazar se zyada pages aaj bhi zinda hain.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Wo hamesha ulti handwriting mein likhte the — mirror script — jise sirf aaine ke saamne padha ja sakta tha!",
        "emotion": "amazed",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Unhone khud ko ek hi naam diya: 'Omo Sanza Lettere' — yaani ek anpadh insaan jise kitaabon ka gyaan nahi tha.",
        "emotion": "deep",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Ye kisi chamatkar ki kahani nahi hai... ye us method ki dastaan hai jisne insaniyat ka dekhne ka nazariya hamesha ke liye badal diya!",
        "emotion": "climax",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Mona Lisa ke us an-suljhe raaz aur Leonardo ke sach ko janne ke liye channel ko abhi subscribe karein!",
        "emotion": "serious",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    "Cinematic historical documentary frame, dark Renaissance workshop, single candle flame trembling in draft, macro of iron-gall ink blooming on antique linen paper, warm candlelight, 35mm anamorphic, vertical 9:16, no text, no watermark",
    "Atmospheric Renaissance study, Leonardo da Vinci mirror handwriting and reverse cursive script sketches covering rustic wooden table, antique magnifying glass, warm amber light, vertical 9:16, no text",
    "Extreme close-up macro of an ancient weathered leather-bound Renaissance notebook folio showing anatomical tendon sketches and water spiral diagrams, dust in the air, vertical 9:16, no text",
    "Mysterious half-lit portrait inspired by the Mona Lisa smile veiled in delicate sfumato shadow, soft candle glow, deep umber palette, Renaissance masterpiece framing, vertical 9:16, no text",
    "Breathtaking dawn over 15th century Florence, terracotta red curve of Brunelleschi dome emerging through morning mist over Arno river, historical accuracy, vertical 9:16, no text",
    "Dramatic silhouette of Leonardo da Vinci standing alone at heavy walnut workbench at dusk holding an antique brass mechanical gear, cinematic rim lighting, vertical 9:16, no text",
    "Monumental parchment title frame with weathered gold leaf Renaissance engraving aesthetic, candlelight flickers, museum grade archival lighting, vertical 9:16, no text"
]


def generate_episode(upload: bool = False):
    print("\n" + "=" * 75)
    print("  🏛️ SERIES 8: LEONARDO DA VINCI — EPISODE 01")
    print("  📜 Title : " + TITLE)
    print("  🏷️ Badge : " + HOOK_OVERLAY)
    print("  ⏱️ Target Duration: ~45-55s (Cinematic History Documentary)")
    print("=" * 75 + "\n")

    t0 = time.time()
    db = DB()

    lines = LINES_HI
    word_count = sum(len(l["text"].split()) for l in lines)
    est_duration = round(word_count / 2.3, 1)

    script_data = {
        "topic": TOPIC,
        "title": TITLE,
        "caption": CAPTION,
        "hashtags": HASHTAGS,
        "hook_type": "mystery",
        "hook_line": lines[0]["text"],
        "hook_text_overlay": HOOK_OVERLAY,
        "comment_bait": COMMENT_BAIT,
        "cast": {
            "narrator": {"gender": "male", "persona": "grave historical documentary narrator"}
        },
        "lines": lines,
        "word_count": word_count,
        "est_sec": est_duration
    }

    vid = db.create_video(
        TOPIC,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        hook_type="mystery",
        script_json=script_data,
        length_sec=int(est_duration),
        status="planned"
    )

    try:
        db.q(
            "UPDATE videos SET series_name = ?, series_index = ? WHERE id = ?",
            ("SERIES_8", 1, vid)
        )
    except Exception:
        pass

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video Project #{vid} created at: {out_dir}")

    # 1. Voice Narration Generation (Edge-TTS Grave Profile)
    print("\n🎙️ [Step 1/5] Synthesizing Voice Narration via Edge-TTS (hi_m_grave)...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(lines, out_dir, profile_id="hi_m_grave")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Narration Audio Generated: {dur:.1f}s, {len(words)} timed words!")
    print(f"   Audio file: {narration_info['audio_path']}")

    # 2. Scene Timing & Prompts
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    motions = ["zoom_in_slow", "pan_left", "zoom_in_dramatic", "pan_right", "zoom_out", "punch_in", "zoom_in_slow"]

    scenes = []
    for i, p in enumerate(IMAGE_PROMPTS):
        st = round(i * scene_dur, 3)
        en = round((i + 1) * scene_dur if i < n_scenes - 1 else dur, 3)
        scenes.append({
            "n": i + 1,
            "beat": f"act_1_scene_{i+1}",
            "image_prompt": p,
            "motion": motions[i % len(motions)],
            "parallax": (i % 2 == 1),
            "file": f"scene_{i+1:02d}.jpg",
            "seed": vid * 200 + i + 1,
            "start": st,
            "end": en,
            "dur": round(en - st, 3)
        })

    # 3. Generate AI Scene Images
    print(f"\n🖼️ [Step 2/5] Generating {n_scenes} authentic Renaissance scene frames...")
    img_agent = ImageGen(providers=["pollinations", "local_placeholder"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"✅ All {len(scenes_with_paths)} documentary visuals ready!")

    # 4. Build Manifest & Render
    manifest = {
        "video_id": vid,
        "series_code": "SERIES_8",
        "episode_num": 1,
        "topic": TOPIC,
        "title": TITLE,
        "script": script_data,
        "narration": narration_info,
        "scenes": scenes_with_paths,
        "aspect_ratio": "9:16",
        "resolution": [1080, 1920]
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n🎥 [Step 3/5] Compositing 60fps video with Ken Burns framing & karaoke subtitles...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # 5. Audio Mix with Documentary Suspense BGM
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"
    if bgm_path.exists():
        print(f"\n🎵 [Step 4/5] Mixing Cinematic Documentary Ambiance ({bgm_path.name})...")
        enhanced_video = out_dir / "final_with_doc_bgm.mp4"
        cmd = [
            "-i", str(raw_video),
            "-stream_loop", "-1", "-i", str(bgm_path),
            "-filter_complex",
            f"[1:a]volume=0.15,afade=t=in:st=0:d=2.0,afade=t=out:st={max(0.1, dur-3):.2f}:d=3[bgm];"
            "[0:a][bgm]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(enhanced_video)
        ]
        from core.ffmpeg import run
        try:
            run(cmd, what="documentary bgm master mix", timeout=300)
            if enhanced_video.exists() and enhanced_video.stat().st_size > 500000:
                raw_video.unlink(missing_ok=True)
                enhanced_video.rename(raw_video)
                print("✅ Cinematic documentary score mixed successfully!")
        except Exception as e:
            print(f"⚠️ BGM mix note: {e}")

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

    rep = validate_dir(out_dir)
    render_info["video_path"] = str(raw_video)
    render_info["duration_sec"] = final_dur
    render_info["size_mb"] = final_size_mb
    manifest["render"] = render_info
    manifest["validation"] = rep.to_dict()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 75)
    print("  🎉 SERIES 8: EPISODE 01 GENERATION COMPLETE!")
    print("=" * 75)
    print(f"  🎬 Video ID    : #{vid}")
    print(f"  📁 Output Video: {raw_video}")
    print(f"  ⏱️ Duration    : {final_dur:.1f}s ({final_dur/60:.2f} mins)")
    print(f"  📦 File Size   : {final_size_mb} MB")
    print(f"  ⏱️ Time Taken  : {elapsed}s")
    print(f"  🛡️ Validation  : {'PASS ✅' if rep.ok else 'WARN ⚠️'}")
    print("=" * 75 + "\n")

    if upload:
        print(f"🚀 Uploading Video #{vid} to YouTube...")
        db.set_status(vid, "approved", note="Approved for YouTube upload")
        pub = YouTubePublisher(db=db)
        res = pub.publish(vid, privacy="public")
        print(f"✅ Published: {res}")

    db.close()
    return {
        "ok": True,
        "video_id": vid,
        "video_path": str(raw_video),
        "duration": final_dur,
        "size_mb": final_size_mb
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Series 8 Episode 1")
    parser.add_argument("--upload", action="store_true", help="Upload directly to YouTube upon rendering")
    args = parser.parse_args()
    generate_episode(upload=args.upload)
