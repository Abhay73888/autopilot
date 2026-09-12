#!/usr/bin/env python3
"""
generate_series2_ep2_movie_dialogue.py — Series 2 Episode 2: "HI SE HUM TAK"
PROTOTYPE: Two-Character Cinematic Movie Dialogue (No 3rd person narration).
Features:
- Character 1 (Aarav): Male emotional teenage voice
- Character 2 (Meera): Female sweet/vulnerable teenage voice
- Alternating speaker close-ups with cinematic push-ins & reaction shots
- Photorealistic Indian visual aesthetic via Flux
- Kinetic Center-Pop Subtitles with Rose Pink & Gold romance highlights
- Emotional lo-fi piano BGM + transition whooshes + heartbeat swell on confession
- STRICT: LOCAL PREVIEW ONLY (DO NOT UPLOAD).
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

log = Logbook("series2_ep2_dialogue")

TOPIC = "2020 — Jab Pyaar Online Tha: Episode 2 (Hi Se Hum Tak) — Movie Dialogue Cut"
TITLE = "Raat Ke 2 Baje Meera Ka Phone Aaya... 💬❤️ | JAB PYAAR ONLINE THA (Ep 2) #Shorts"
CAPTION = "Jab Aarav aur Meera ne pehli baar dil ki baat boli... 2020 lockdown ki sabse emotional online love story. JAB PYAAR ONLINE THA (Episode 2). Part 3 ke liye COMMENT karein! 👇"
HASHTAGS = ["#JabPyaarOnlineTha", "#Series2", "#Episode2", "#Shorts", "#Romance", "#LoveStory", "#MovieDialogue"]
HOOK_OVERLAY = "✨ JAB PYAAR ONLINE THA (EPISODE 2) 🎧"
COMMENT_BAIT = "Kya aapne bhi kabhi kisi se aisi late-night call ki hai? Episode 3 ke liye COMMENT karein! 👇"

# 100% Real 2-Person Movie Dialogue between Aarav (narrator/male) and Meera (char_b/female)
LINES = [
    {
        "speaker": "narrator",  # Aarav
        "text": "Meera... soyi nahi abhi tak? Raat ke 2 baj rahe hain.",
        "emotion": "tender",
        "role": "hook"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Tum online the na Aarav... toh mujhe neend kaise aati?",
        "emotion": "sweet",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Kabhi darr lagta hai ki agar ye lockdown khatam ho gaya... toh tum mujhe bhool jaogi?",
        "emotion": "vulnerable",
        "role": "body"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Tumhe sach mein lagta hai main bhool sakti hoon? Tumhe bhoolna itna aasaan hai kya?",
        "emotion": "romantic",
        "role": "body"
    },
    {
        "speaker": "narrator",  # Aarav
        "text": "Kal class mein tumhara camera band tha Meera... main andar se darr gaya tha.",
        "emotion": "nervous",
        "role": "reveal"
    },
    {
        "speaker": "char_b",    # Meera
        "text": "Bas ghar mein thoda pareshan thi... par jab tum kehte ho na 'main yahin hoon', toh sab theek lagta hai.",
        "emotion": "emotional",
        "role": "climax"
    },
    {
        "speaker": "char_b",    # Meera (confession whisper)
        "text": "Aarav... I think I'm falling for you.",
        "emotion": "whisper",
        "role": "ending"
    },
    {
        "speaker": "narrator",  # Aarav (breath hitch / shock)
        "text": "Meera... kya yeh sach hai?",
        "emotion": "shocked",
        "role": "ending"
    }
]

# Alternating cinematic close-ups and over-the-shoulder shots
IMAGE_PROMPTS = [
    # Scene 1: Aarav speaking (Line 1)
    "Cinematic 8k photorealistic close-up portrait of 16-year-old Indian boy Aarav speaking emotionally on video call, lips slightly parted talking, dark bedroom at 2 AM illuminated by soft cool blue smartphone screen light, wheatish skin, deep brown emotional eyes, vertical 9:16, masterpiece, 24fps film aesthetic, no text, no watermark",
    
    # Scene 2: Meera listening with a shy blush (Line 1 -> Line 2 bridge)
    "Cinematic 8k photorealistic over-the-shoulder reaction shot of 16-year-old Indian girl Meera listening intently to mobile screen, tender soft smile, nodding gently with genuine affection, warm golden bedside lamp lighting, dark wavy hair in messy bun, delicate silver bracelet, vertical 9:16, photorealistic, no text",
    
    # Scene 3: Meera speaking (Line 2)
    "Cinematic 8k photorealistic close-up portrait of 16-year-old Indian girl Meera talking softly with shy romantic smile, lips moving gently in speech, expressive sparkling brown eyes, warm cozy bedroom atmosphere, vertical 9:16, hyperrealistic, masterpiece, no text",
    
    # Scene 4: Aarav listening with butterflies (Line 2 -> Line 3 bridge)
    "Cinematic 8k photorealistic close-up of Aarav listening with breathless wonder and butterflies in his eyes, smiling softly in dark room, faint blue screen reflection dancing in his pupils, vertical 9:16, photorealistic, no text",
    
    # Scene 5: Aarav speaking vulnerable line about lockdown ending (Line 3)
    "Cinematic 8k photorealistic dramatic close-up of Aarav speaking with deep emotional vulnerability and pain, eyes glistening with unspoken fear, rain droplets streaking on bedroom window behind him, cinematic moody lighting, vertical 9:16, photorealistic, no text",
    
    # Scene 6: Meera speaking emotional reassurance (Line 4)
    "Cinematic 8k photorealistic close-up portrait of Meera speaking earnestly with deep emotional eye contact, tears glistening in her eyes, soft trembling lips smiling with pure love, warm volumetric lighting, vertical 9:16, masterpiece, hyperrealistic, no text",
    
    # Scene 7: Aarav speaking worried about missing in class (Line 5)
    "Cinematic 8k photorealistic close-up of Aarav leaning into camera speaking with anxious tenderness, concerned eyebrows, intense genuine care, vertical 9:16, photorealistic, no text",
    
    # Scene 8: Meera touching silver bracelet & opening up (Line 6)
    "Cinematic 8k photorealistic medium close-up of Meera holding delicate silver thread bracelet on her wrist while speaking emotionally, teary eyes filled with gratitude and warmth, vertical 9:16, hyperrealistic, no text",
    
    # Scene 9: Meera close-up whisper confession (Line 7)
    "Cinematic 8k photorealistic extreme close-up on Meera's face in soft golden shadows, whispering a secret confession with shy blushing cheeks and breathtaking emotional intimacy, vertical 9:16, masterpiece, 24fps film look, no text",
    
    # Scene 10: Aarav stunned emotional reaction (Line 8 -> Climax)
    "Cinematic 8k photorealistic dramatic close-up on Aarav's face completely frozen in stunned disbelief and pure awe, phone screen glow illuminating his wide emotional eyes, breath hitched in throat, cinematic cut to black, vertical 9:16, masterpiece, no text"
]


def main():
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  🎬 GENERATING SERIES 2 — EPISODE 02: CINEMATIC MOVIE DIALOGUE CUT")
    print("  🎭 DUAL CASTING: Aarav (Male) & Meera (Female) Direct Conversation")
    print("  ⚠️ MODE: LOCAL PREVIEW ONLY (UPLOAD DISABLED)")
    print("=" * 70)

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
            "narrator": {"name": "Aarav", "gender": "male", "persona": "emotional teenage boy"},
            "char_b": {"name": "Meera", "gender": "female", "persona": "warm, gentle teenage girl"}
        },
        "lines": LINES,
        "word_count": sum(len(ln["text"].split()) for ln in LINES),
        "est_sec": 35.0
    }

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

    # 2. Voice Generation with Dual Casting (Aarav: Male, Meera: Female)
    print("\n🎙️ [Step 1] Synthesizing Dual Character Dialogue (Aarav ➔ Meera)...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_narrator")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Dialogue Narration created: {dur:.1f}s, {len(words)} words ({narration_info['audio_path']})")
    print(f"   Engines used: {narration_info.get('engines_used')}")

    # 3. Scene Timings calculation (10 alternating shots)
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    scenes = []
    # Dynamic camera motions for movie feel: push-ins, subtle pans
    motions = ["zoom_in", "pan_left", "zoom_in", "zoom_in_slow", "zoom_in", "zoom_in_slow", "pan_right", "pan_left", "zoom_in_slow", "zoom_in"]
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

    # 4. Generate Visual Frames via Flux (Photorealistic Movie Close-ups)
    print(f"\n🖼️ [Step 2] Generating {n_scenes} Photorealistic Movie Dialogue Frames via Flux...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"✅ All {n_scenes} dialogue close-up frames generated successfully!")

    # 5. Build Manifest with Option A Viral Kinetic Edit Engine
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
            "template_name": "Cinematic Movie Dialogue",
            "pacing": "dynamic_fast",
            "setting": "2020 lockdown late night video call confession",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render MP4 with FFmpeg & on-screen SERIES 2 badge
    print(f"\n🎥 [Step 3] Rendering Movie Dialogue Cut with FFmpeg (Pacing: ~{scene_dur:.1f}s/cut, Total: {dur:.1f}s)...")
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
            f"[1:a]volume=0.13,afade=t=in:st=0:d=1.0,afade=t=out:st={max(0.1, dur-2):.2f}:d=2[bgm];"
            "[0:a][bgm]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(enhanced_video)
        ]
        from core.ffmpeg import run
        try:
            run(cmd, what="movie dialogue bgm mix", timeout=240)
            if enhanced_video.exists() and enhanced_video.stat().st_size > 100000:
                raw_video.unlink(missing_ok=True)
                enhanced_video.rename(raw_video)
                print("✅ Romantic Movie Dialogue BGM successfully mixed!")
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

    db.set_status(vid, "approved", note="Series 2 Ep 2 Movie Dialogue Cut Approved (Local Preview — Not Uploaded)")

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 SERIES 2 — EPISODE 02 (MOVIE DIALOGUE CUT) GENERATED & RENDERED!")
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
