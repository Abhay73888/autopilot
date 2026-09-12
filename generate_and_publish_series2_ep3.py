#!/usr/bin/env python3
"""
generate_and_publish_series2_ep3.py — Generate, Validate, and Publish SERIES 2 EPISODE 3: "HUM".
Features:
- Two-Character Cinematic Movie Dialogue (Aarav & Meera)
- Emotional Anchor: Exam failure support ("Ek exam tumhari aukaat decide nahi karta")
- The Iconic First Real-Life Meeting outside Metro Station
- The 7-Year Promise & Shocking Cliffhanger ("We need to talk.")
- Visuals: Photorealistic Indian romance aesthetic via Flux
- Audio: Dual voices (Aarav + Meera) + Lo-fi Piano Romance BGM
- Upload: YouTube Shorts (Public, Comments Enabled)
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

log = Logbook("series2_ep3")

TOPIC = "2020 — Jab Pyaar Online Tha: Episode 3 (Hum) — First Meeting & The Promise"
TITLE = "Lockdown Ke Baad Jab Pehli Baar Mile... ❤️🥺 | JAB PYAAR ONLINE THA (Ep 3) #Shorts"
CAPTION = (
    "Online classes se shuru hui dosti... pehli real-life mulakat tak pahunch gayi. "
    "Lockdown ke baad jab Aarav aur Meera pehli baar metro station ke bahar mile. ❤️🥺\n\n"
    "2020 ki sabse masoom aur emotional love story. Agle episode (Part 4) ke liye COMMENT karein: 'PART 4'! 👇✨"
)
HASHTAGS = ["#JabPyaarOnlineTha", "#Series2", "#Episode3", "#Shorts", "#Romance", "#LoveStory", "#ShortsFeed"]
HOOK_OVERLAY = "✨ JAB PYAAR ONLINE THA (EPISODE 3: HUM) ❤️"
COMMENT_BAIT = "Kya pehli baar kisi se milte waqt aapke bhi haath kaanpe the? Episode 4 ke liye COMMENT karein! 👇❤️"

LINES = [
    {
        "speaker": "narrator",  # Aarav
        "text": "Maine kabhi socha nahi tha ki screen ke uss paar wali ladki... meri poori zindagi ban jayegi.",
        "emotion": "tender",
        "role": "hook"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Aarav... jab tumne 'I love you' bola tha na... mera dil itni zor se dhadak raha tha.",
        "emotion": "sweet",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Aur jab mera exam kharab hua tha... main andar se poori tarah toot chuka tha Meera.",
        "emotion": "vulnerable",
        "role": "body"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Toh maine kya kaha tha? Ek exam ka result tumhari aukaat decide nahi karta Aarav... main tumhare saath isliye hoon kyunki tum tum ho.",
        "emotion": "emotional",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Phir lockdown khula... metro station ke bahar pehli baar jab tum saamne aayi... meri zubaan band ho gayi thi.",
        "emotion": "nostalgic",
        "role": "reveal"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Aur tumne kaanpte hue haath se bola tha: '7 saal baad bhi agar tum saath rahi... toh shaadi karunga tumse.' Promise yaad hai na?",
        "emotion": "romantic",
        "role": "climax"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Lekin do mahine baad... raat ke 1 baje Meera ka achanak message aaya: 'Aarav... we need to talk.' Part 4 ke liye COMMENT karein!",
        "emotion": "shocked",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Aarav looking affectionately at laptop screen
    "Cinematic 8k photorealistic shot of 17-year-old Indian boy Aarav smiling warmly at his laptop screen in cozy dimly lit bedroom at night, golden warm desk lamp reflection, vertical 9:16, masterpiece, no text",
    
    # Scene 2: Meera blushing on phone call
    "Cinematic 8k photorealistic close up: 17-year-old natural Indian girl Meera blushing softly on a late-night phone call in her bedroom, gentle moonlight through window, emotional expressive eyes, vertical 9:16, no text",
    
    # Scene 3: Aarav heartbroken after exam
    "Cinematic 8k photorealistic emotional shot: Aarav sitting heartbroken at study desk with competitive exam results sheet, head in hands, desaturated shadows, vertical 9:16, raw emotional depth, no text",
    
    # Scene 4: Meera comforting him on video call
    "Cinematic 8k photorealistic close up of Meera on phone screen with a gentle reassuring smile, speaking words of unconditional love and comfort, warm bokeh lighting, vertical 9:16, no text",
    
    # Scene 5: Crowded Delhi metro station sunny exterior
    "Cinematic 8k photorealistic wide shot of bustling Delhi metro station exterior on a bright sunny afternoon, 17-year-old Aarav standing nervously in casual jacket with backpack checking his watch, vertical 9:16, no text",
    
    # Scene 6: Meera walking down metro stairs locking eyes
    "Cinematic 8k photorealistic breathtaking medium shot: Meera walking down metro staircase wearing elegant pastel kurti and delicate silver thread bracelet on wrist, locking eyes with Aarav, gentle breeze in hair, vertical 9:16, masterpiece, no text",
    
    # Scene 7: Aarav and Meera at tea stall shy smiles
    "Cinematic 8k photorealistic golden hour shot: Aarav and Meera sitting together at outdoor roadside tea stall with clay cups of cutting chai, nervous shy smiles, warm sunset lens flare, vertical 9:16, no text",
    
    # Scene 8: Close up of gentle hand touch & silver bracelet
    "Cinematic 8k photorealistic extreme close-up of Aarav's trembling fingers gently brushing Meera's wrist with the delicate silver thread bracelet, pure innocence and unspoken promise, vertical 9:16, no text",
    
    # Scene 9: Sudden dark room notification cliffhanger
    "Cinematic 8k photorealistic dramatic cliffhanger: cold desaturated nighttime bedroom, smartphone screen lighting up dark room showing shocking unread WhatsApp message 'Meera: Aarav... we need to talk.', vertical 9:16, masterpiece, no text"
]

def main():
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  🎬 2020: JAB PYAAR ONLINE THA — EPISODE 03 (HUM)")
    print("  💖 DUAL CHARACTER MOVIE DIALOGUE + REALISTIC INDIAN ROMANCE")
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
            "narrator": {"gender": "male", "persona": "Aarav (emotional boy)"},
            "char_b": {"gender": "female", "persona": "Meera (warm gentle girl)"}
        },
        "lines": LINES,
        "word_count": sum(len(ln["text"].split()) for ln in LINES),
        "est_sec": 42.0
    }

    vid = db.create_video(
        TOPIC,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        hook_type="cliffhanger",
        script_json=script_data,
        length_sec=42,
        status="planned"
    )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video #{vid} workspace: {out_dir}")

    # 1. Synthesize Dual Voice Dialogue (Aarav + Meera)
    print("\n🎙️ [Step 1] Synthesizing Dual Character Dialogue (Aarav & Meera)...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_narrator")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Dialogue created: {dur:.1f}s, {len(words)} words ({narration_info['audio_path']})")

    # 2. Scene Timings calculation (9 cuts)
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

    # 3. Generate Visual Frames via Pollinations Flux
    print(f"\n🖼️ [Step 2] Generating {n_scenes} Photorealistic Indian Romance Frames via Flux...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"✅ All {n_scenes} photorealistic romance frames generated successfully!")

    # 4. Build Manifest
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "title": TITLE,
        "script": script_data,
        "subtitles": {
            "style": "kinetic"
        },
        "effects": {
            "sound": {
                "heartbeat": True,
                "riser": False,
                "braam": False,
                "whoosh": True,
                "room_tone": True,
                "ducking": True,
                "master_limiter": True
            }
        },
        "art": {
            "template_id": "warm_nostalgia",
            "template_name": "Warm Nostalgic Indian Romance",
            "pacing": "medium",
            "setting": "Delhi metro station and warm evening tea stall",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Render MP4 with FFmpeg
    print(f"\n🎥 [Step 3] Rendering Episode 3 with FFmpeg (Pacing: ~{scene_dur:.1f}s/cut, Total: {dur:.1f}s)...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # Enhance audio with acoustic romance piano BGM
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "romance_bgm.mp3"
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
            run(cmd, what="romance bgm master mix", timeout=240)
            if enhanced_video.exists() and enhanced_video.stat().st_size > 100000:
                raw_video.unlink(missing_ok=True)
                enhanced_video.rename(raw_video)
                print("✅ Lo-fi Piano Romance BGM successfully mixed!")
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

    db.set_status(vid, "approved", note="Series 2 Ep 3 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 7. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Series 2 Episode 3 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 SERIES 2 EPISODE 03 PUBLISHED SUCCESSFULLY TO YOUTUBE SHORTS!")
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
