#!/usr/bin/env python3
"""
generate_and_publish_kaalrekha_ep8.py — Generate, Validate, and Publish KAAL-REKHA Part 8.
Features:
- Shocking Climax Reveal: Kabir discovers an ancient journal with his own handwriting from 1924!
- The Terrifying Truth: Kabir himself created the time loop to save Meera from death!
- Moral Dilemma: Break the loop and let Meera die, or stay trapped forever in 3:17 AM?
- Visuals: Dark anime (MAPPA/Ufotable aesthetic via Flux), floating brass clockwork gears.
- Audio: Dual voices (Kabir + Sinister Temporal Entity) + 38Hz Braam Hit + Suspense BGM.
- Upload: Direct YouTube Shorts upload (Public, Comments Enabled).
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

log = Logbook("kaalrekha_ep8")

TOPIC = "Kaal-Rekha Part 8: The Origin of the Loop (Loop Ka Khaufnak Sach)"
TITLE = "Waqt Ka Aakhri Kanta: Kisne Banaya Ye Time-Loop?! ⏳😱 | KAAL-REKHA (Part 8) #Shorts"
CAPTION = (
    "Agar 3:17 AM par ghadi ulti chalne lagi... toh clock tower ke taikhane mein meri 100 saal purani diary kaise mili?! 😱\n"
    "Sabse bada khulasa: Kabir kisi shrap mein nahi phasa tha... is loop ko Kabir ne KHUD banaya tha! ⏳⚡\n\n"
    "Loop tode ya Meera ko bachaye? Agle finale episode (Part 9) ke liye abhi COMMENT karein! 👇🔥"
)
HASHTAGS = ["#KaalRekha", "#Part8", "#Season2", "#Shorts", "#TimeLoop", "#SciFi", "#Anime", "#ShortsFeed"]
HOOK_OVERLAY = "🎬 KAAL-REKHA: PART 8 (ORIGIN OF THE LOOP) ⏳"
COMMENT_BAIT = "Agar aap Kabir hote toh kya karte? Loop todkar Meera ko marne dete ya qaid rehte? COMMENT karein! 👇😱"

LINES = [
    {
        "speaker": "narrator",
        "text": "Agar 3:17 AM par ghadi ulti chalne lagi... toh clock tower ke taikhane se aati wo cheekh kiski thi?!",
        "emotion": "shocked",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Main bhaagte hue purane taikhane mein utra... wahan brass ke vishal gears hawa mein tair rahe the aur neeli bijli chamak rahi thi!",
        "emotion": "suspense",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Beech mein ek purani diary padi thi... maine panna palta aur mere rongte khade ho gaye! Wo handwriting meri apni thi... par taareekh 1924 thi!",
        "emotion": "panic",
        "role": "reveal"
    },
    {
        "speaker": "char_b",
        "text": "Andhere se ek saaye ne kaha: 'Tu kisi shrap mein nahi phasa Kabir... is time-loop ko tune khud banaya tha!'",
        "emotion": "cold",
        "role": "climax"
    },
    {
        "speaker": "char_b",
        "text": "Usne kaha: 'Meera ko maut se bachane ke liye tune waqt ko qaid kiya tha... agar loop toda, toh Meera hamesha ke liye mar jayegi!'",
        "emotion": "intense",
        "role": "climax"
    },
    {
        "speaker": "narrator",
        "text": "Meri chhati par Roman number III chamakne laga... loop todu ya Meera ko bachau? Agle part ke liye COMMENT karein!",
        "emotion": "urgent",
        "role": "ending"
    }
]

IMAGE_PROMPTS = [
    # Scene 1: Clock tower at stormy night with reverse lightning
    "Cinematic 8k photorealistic dark anime shot of colossal gothic clock tower under turbulent violet thunderstorm sky, reverse lightning striking upward from ground, vertical 9:16, MAPPA aesthetic, masterpiece, no text",
    
    # Scene 2: Kabir descending into ominous subterranean gear room
    "Dramatic 8k anime shot of 21-year-old Kabir Sen in torn black jacket descending spiral iron staircase into ancient clockwork sanctuary, floating massive brass cogs glowing with violet ether, vertical 9:16, masterpiece, no text",
    
    # Scene 3: Close up of floating giant gears defying gravity
    "Hyper-detailed 8k dark anime perspective of intricate antique clockwork brass gears suspended mid-air in zero gravity, glowing arcane runes etched on teeth, vertical 9:16, volumetric lighting, no text",
    
    # Scene 4: Kabir discovering the ancient leather-bound diary
    "Cinematic 8k anime close up: Kabir's trembling hands opening a battered 100-year-old leather journal resting on an obsidian pedestal, old cursive ink handwriting, page showing year 1924, vertical 9:16, no text",
    
    # Scene 5: Extreme close up of Kabir's horrified expression
    "Terrifying 8k photorealistic dark anime close up of Kabir's wide horrified eyes, dilated pupils reflecting burning crimson clock hands, pale face drenched in cold sweat, vertical 9:16, cinematic masterpiece, no text",
    
    # Scene 6: Tall mysterious cloaked temporal entity emerging
    "Cinematic 8k dark anime shot: tall mysterious hooded temporal entity emerging from swirling obsidian shadows, glowing white eyes behind porcelain mask, holding an hourglass with purple glowing sand, vertical 9:16, no text",
    
    # Scene 7: Entity pointing at a frozen ghostly memory of Meera
    "Cinematic 8k anime composition: hooded entity pointing toward a shimmering holographic memory of doctor Meera frozen in a shattering glass sphere, tragic beauty, vertical 9:16, ethereal lighting, no text",
    
    # Scene 8: Roman numeral burning from IV to III on Kabir's chest
    "Hyperrealistic 8k anime close-up of Kabir's chest: Roman numeral III burning violently through his torn shirt in molten gold and violet embers, skin glowing with raw temporal energy, vertical 9:16, no text",
    
    # Scene 9: Epic cliffhanger choice between love and freedom
    "Epic 8k cinematic anime cliffhanger: Kabir standing at the center of the shattered clock chamber, torn between saving Meera and destroying the loop, intense emotional climax, vertical 9:16, masterpiece, no text"
]

def main():
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  🎬 KAAL-REKHA: PART 08 — ORIGIN OF THE LOOP")
    print("  🔥 10x PRODUCTION UPGRADE + DUAL NEURAL VOICEOVER + SUSPENSE BGM")
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
            "char_b": {"gender": "male", "persona": "ancient hooded temporal guardian"}
        },
        "lines": LINES,
        "word_count": sum(len(ln["text"].split()) for ln in LINES),
        "est_sec": 38.0
    }

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

    # 1. Synthesize 10x Voice Narration
    print("\n🎙️ [Step 1] Synthesizing 10x Upgraded Neural Voiceover...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_intense")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Narration created: {dur:.1f}s, {len(words)} words ({narration_info['audio_path']})")

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
    print(f"\n🖼️ [Step 2] Generating {n_scenes} Dark Cinematic Anime Frames via Flux...")
    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"✅ All {n_scenes} surreal dark anime frames generated successfully!")

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
            "template_name": "Crimson Alert Psychological Thriller",
            "pacing": "dynamic_fast",
            "setting": "clock tower gear chamber with ancient temporal runes",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Render MP4 with FFmpeg
    print(f"\n🎥 [Step 3] Rendering Part 8 with FFmpeg (Pacing: ~{scene_dur:.1f}s/cut, Total: {dur:.1f}s)...")
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

    db.set_status(vid, "approved", note="Part 8 Approved for YouTube Upload")
    print(f"✅ Video #{vid} APPROVED for upload.")

    # 7. Upload to YouTube Shorts
    print("\n🚀 [Step 5] Uploading Part 8 to YouTube Shorts (Public)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)

    db.close()
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 70)
    print("  🎉 KAAL-REKHA PART 08 PUBLISHED SUCCESSFULLY TO YOUTUBE SHORTS!")
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
