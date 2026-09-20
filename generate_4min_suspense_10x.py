#!/usr/bin/env python3
"""
generate_4min_suspense_10x.py — Ultra-Suspenseful 4-Minute Atmospheric AI Psychological Horror Film.

Story: "The 3:17 AM Himalayan Anomaly: Outpost 7 Mimic Incident"
Genre: Psychological Horror / Analog Suspense / True Unsolved Incident
Target Duration: ~4 Minutes (235s - 255s)
Pipeline:
  1. Edge-TTS Narration with Grave Hindi Documentary Profile (hi_m_grave)
  2. 18 AI-Generated Cinematic Psychological Horror Scenes via Pollinations
  3. Dynamic Camera Motions (Ken Burns: zoom_in_dramatic, pan_left, whip_zoom, punch_in)
  4. Cinematic ASS Subtitles (Glowing Crimson / Amber Noir Aesthetic)
  5. Multi-Layer Audio Mix: Real Horror Drone & Ambiance (suspense_bgm.mp3)
  6. YouTube Upload Support with Invariants (Comments 100% ON, MadeForKids=False, Public)

Usage:
  python generate_4min_suspense_10x.py
  python generate_4min_suspense_10x.py --upload
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
from agents.publisher import YouTubePublisher, PublishError

log = Logbook("suspense_4min")

TOPIC = "The 3:17 AM Himalayan Anomaly: Outpost 7 Mimic Incident"
TITLE = "3:17 AM Par Khidki Mat Kholna: Himalayan Post 404 Ka Khaufnak Sach 💀📻 | 10x Suspense (4-Min Mystery)"
CAPTION = (
    "Himalaya ke 14,000 feet unche isolated Outpost 7 par 1994 ki ek kaali raat ko radio band hone ke bawajood achanak ek aisi aawaz gunjne lagi jisne sabke hosh uda diye! "
    "Wo cheez har jawan ki aawaz ki huba-hu copy kar sakti thi... lekin unka chehra insaano jaisa nahi tha! "
    "14 minute ka classified audio log aur khaufnak sach! Dekhiye rooh kampa dene wali sachi ghatna 👇"
)
HASHTAGS = [
    "#SuspenseHorror", "#AnalogHorror", "#HimalayanMystery", "#HorrorStory",
    "#IndianHorror", "#UnsolvedMysteries", "#ParanormalIncident", "#GhostStories",
    "#10xSuspense", "#TrueHorrorStory"
]
HOOK_OVERLAY = "3:17 AM: Khidki Mat Kholna! 💀📻"
COMMENT_BAIT = "Agar raat ke 3:17 baje koi aapke hi gharwale ki aawaz mein darwaza peetne lage, toh kya aap darwaza kholenge ya nahi? Apni raye comment mein zaroor batayein!"

# -----------------------------------------------------------------------------
# 26 LINES OF INTENSE PSYCHOLOGICAL SUSPENSE HINDI SCRIPT (~560 words = ~4m 10s)
# -----------------------------------------------------------------------------
LINES = [
    # --- ACT 1: THE FORBIDDEN WARNING & HOOK (0:00 - 0:38) ---
    {
        "speaker": "narrator",
        "text": "Agar raat ke theek teen bajkar satrah minute par aapke kamre ki khidki par koi dheere se aapka naam pukare... toh chahe kuch bhi ho jaye, khidki ka parda bhool kar bhi mat hatana!",
        "emotion": "dramatic",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Kyunki agar wo aawaz bilkul aapke kisi karibi insaan jaisi lag rahi hai... toh iska matlab yeh nahi ki wo insaan bahar khada hai. Iska matlab yeh hai... ki wo shikaar dhoondh raha hai.",
        "emotion": "whispers",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Yeh koi mann-ghadant kahani nahi hai... yeh Himalaya ke chaudah hazaar feet unche Outpost Seven ki wo sachai hai jise sadiyon se confidential files mein daba kar rakha gaya.",
        "emotion": "cold",
        "role": "hook"
    },

    # --- ACT 2: THE IMPOSSIBLE TRANSMISSION (0:38 - 1:18) ---
    {
        "speaker": "narrator",
        "text": "December unnees sau chauraanve. Charon taraf minus pachchees degree ka jaanleva barafani toofan chal raha tha aur base ka connection poori duniya se toot chuka tha.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Base mein paanch border security ke jawan tainaat the. Raat ke theek teen bajkar satrah minute par, unka heavy military radio transmitter achanak tez static aawaz ke saath on ho gaya.",
        "emotion": "whispers",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Lekin sabse ajeeb baat yeh thi... ki us transmitter ka main power plug pichhle teen din se deewar se nikla hua tha aur antenna baraf ke toofan mein toot chuka tha!",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Radio ke speaker se achanak ek aisi aawaz gunjne lagi jise sunte hi paanchon jawanon ke chehre ka rang ud gaya. Wo aawaz behad dheemi aur robotic thi.",
        "emotion": "dramatic",
        "role": "body"
    },

    # --- ACT 3: THE CLASSIFIED BROADCAST (1:18 - 1:55) ---
    {
        "speaker": "narrator",
        "text": "Wo anjaan aawaz radio par base ke andar baithe ek-ek jawan ka poora naam, unke parivar ki details aur unki heartbeat ki exact speed live bol rahi thi!",
        "emotion": "whispers",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Speaker se aawaz aayi: 'Operator Vikram... tumhare daayein hath ki ungliyan kaanp rahi hain... aur tumhari bandook ka safety lock khula hai.'",
        "emotion": "cold",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Vikram ne chaunk kar apne hath ko dekha... wo sach tha! Lekin bunker ke andar koi camera ya sensor nahi tha... fir unhe andhere mein kaun dekh raha tha?!",
        "emotion": "dramatic",
        "role": "body"
    },

    # --- ACT 4: THE MIMIC AT THE DOOR (1:55 - 2:38) ---
    {
        "speaker": "narrator",
        "text": "Tabhi bunker ke bhari steel door par bahar se teen zordar dastak hui. Thud... thud... thud!",
        "emotion": "whispers",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Bahar baraf ke toofan se unke team leader Captain Joshi ki chikh sunai di: 'Vikram! Jaldi darwaza kholo! Main baraf mein phas gaya hoon, jaldi kholo!'",
        "emotion": "dramatic",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Vikram ne darwaze ki taraf kadam badhaya, lekin tabhi uski nazar theek bagal wale bunk bed par padi... aur uske pairo tale zameen khisak gayi.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Captain Joshi toh pichhle do ghante se bunker ke andar, apne bed par gehri neend mein so rahe the!",
        "emotion": "cold",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Agar Captain Joshi andar the... toh bahar unhi ki aawaz mein gidgida kar darwaza peetne wala kaun tha?!",
        "emotion": "fear",
        "role": "reveal"
    },

    # --- ACT 5: THE NIGHT-VISION REVELATION (2:38 - 3:20) ---
    {
        "speaker": "narrator",
        "text": "Kaanpte hue hathon se Vikram ne night-vision infrared monitor on kiya jo bahar ke main gate ko monitor kar raha tha.",
        "emotion": "whispers",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Screen par jo dikha usne unka khoon thanda kar diya. Bahar koi insaan nahi tha... balki ek lagbhag aath feet lambi, kaali chhaya khadi thi jiska koi chehra nahi tha.",
        "emotion": "dramatic",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Lekin us aakriti ka gala Captain Joshi ke bolne ke bilkul usi rhythm aur pitch par ajeeb tarike se vibrate ho raha tha!",
        "emotion": "fear",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Paranormal aur folklore mein ise 'The Mimic' ya 'Chhalawa' kehte hain... ek aisi rooh jo aapke sabse bharosemand insaan ki aawaz chura kar aapko maut ke daayre mein kheenchti hai.",
        "emotion": "cold",
        "role": "body"
    },

    # --- ACT 6: THE 14-MINUTE BLACKOUT & CHILLING CONCLUSION (3:20 - 4:10) ---
    {
        "speaker": "narrator",
        "text": "Agle hi pal, poore outpost ki lights achanak ek dhamake ke saath phat gayi aur poora bunker ghup andhere mein doob gaya!",
        "emotion": "dramatic",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Classified audio log recorder par record hui aakhri do minute ki tape mein koi goli chalne ki aawaz nahi thi... sirf charon taraf se unhi ke doston ki aawazein hans rahi thi.",
        "emotion": "whispers",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Do hafte baad jab Army ki rescue team wahan pahuchee, toh unhe bunker ka lohe ka darwaza andar se tightly lock mila.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Lekin andar ek bhi jawan maujood nahi tha... sirf deewaron par naakhunon se ek hi cheez saikdon baar khodi gayi thi: Teen bajkar satrah minute!",
        "emotion": "cold",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Wo paanchon jawan kahan gaye, unhe zameen khaa gayi ya koi anjaan taqat nigal gayi... yeh file aaj bhi Army ke unclosed archives mein band hai.",
        "emotion": "whispers",
        "role": "ending"
    },
    {
        "speaker": "narrator",
        "text": "Isliye doston, agar kabhi aadhi raat ko aapke ghar ke bahar se koi aapka apna aapka naam pukare... toh bina dekhe darwaza kholne ki galti kabhi mat karna.",
        "emotion": "dramatic",
        "role": "ending"
    },
    {
        "speaker": "narrator",
        "text": "Kya aapko lagta hai aisi taqatein sach mein hamare beech maujood hain? Apni raye comment mein zaroor batayein aur aisi hi rooh kampa dene wali sachi daastano ke liye channel ko abhi subscribe karein.",
        "emotion": "serious",
        "role": "ending"
    }
]

# -----------------------------------------------------------------------------
# 18 ULTRA-ATMOSPHERIC 9:16 PSYCHOLOGICAL HORROR IMAGE PROMPTS
# -----------------------------------------------------------------------------
IMAGE_PROMPTS = [
    # Scene 1: Snowbound Mountain Outpost at Midnight
    "Snowbound military observation outpost high on a jagged frozen Himalayan cliff peak at pitch black midnight, violent blizzard swirling, glowing red emergency beacon atop the tower, vertical 9:16, 8k cinematic horror, ominous shadows, no text, no watermark",

    # Scene 2: Digital Clock 03:17 AM
    "Extreme macro close-up of an old digital green phosphor LED alarm clock reading 03:17 AM in a dark shadowy room, ice crystals forming on the clock display glass, analog horror atmosphere, vertical 9:16, no text, no watermark",

    # Scene 3: Shadowy Figure at Window
    "Dark mysterious silhouette of a person standing frozen before a fogged frost-covered window pane in a cold concrete room, pale silver moonlight casting long chilling shadow, vertical 9:16, no text, no watermark",

    # Scene 4: Endless Himalayan Blizzard Peaks
    "Vast desolate Himalayan mountain range engulfed in freezing blinding blizzard at dusk, dark towering peaks, barren frozen wasteland, epic cinematic wide shot, vertical 9:16, no text, no watermark",

    # Scene 5: Military Radio Room Interior
    "Interior of an isolated cold military bunker room, vintage green metal radio consoles, blinking indicator dials, dim warm incandescent bulb swaying from ceiling wire, vertical 9:16, no text, no watermark",

    # Scene 6: Severed Wires and Glowing Radio
    "Close-up of vintage military radio receiver console, unplugged severed power cables dangling onto cold concrete floor, glowing eerie faint static light from the analog display dials, vertical 9:16, no text, no watermark",

    # Scene 7: Vibrating Speaker Cone
    "Close-up of a vintage perforated metal radio speaker cone vibrating faintly in the dark, dust motes floating in a thin ray of moonlight, eerie sound transmission feel, vertical 9:16, no text, no watermark",

    # Scene 8: Terrified Radio Operator Soldier
    "Indian military radio operator in heavy olive green winter parka and headset staring at radio dials with eyes wide open in sheer shock and terror, sweating in the freezing cold, vertical 9:16, no text, no watermark",

    # Scene 9: Trembling Hand on Rifle Trigger
    "Trembling gloved hand gripping an army rifle in dim flickering bunker lighting, finger poised over the safety switch, extreme psychological suspense, vertical 9:16, no text, no watermark",

    # Scene 10: Heavy Steel Blast Door
    "Heavy reinforced industrial steel blast door in a concrete military bunker, three massive rusty deadbolts and chains, heavy frost creeping across the iron rivets, vertical 9:16, no text, no watermark",

    # Scene 11: Shocked Soldier Turning Head
    "Terrified soldier slowly turning his head in a dark bunker towards a sleeping officer on an army cot bunk bed, shock and disbelief on his face, dramatic cinematic lighting, vertical 9:16, no text, no watermark",

    # Scene 12: Sleeping Officer on Cot
    "Close-up of senior army officer peacefully sleeping wrapped in olive blankets on a metal bunk bed, completely unaware of the knocking outside, vertical 9:16, no text, no watermark",

    # Scene 13: Grainy Night-Vision Monitor Screen
    "Grainy green monochrome night-vision surveillance monitor screen showing the exterior frozen entrance of the bunker in heavy snowstorm, analog scan lines, vertical 9:16, no text, no watermark",

    # Scene 14: Mimic Silhouette in Blizzard
    "Creepy night-vision thermal camera frame showing a tall unnatural shadowy figure standing motionlessly in the blizzard outside the steel door, elongated limbs, disturbing analog horror, vertical 9:16, no text, no watermark",

    # Scene 15: Red Emergency Strobe Blackout
    "Sudden blackout inside the concrete bunker corridor, single red emergency beacon spinning, casting pulsating blood-red shadows on empty rusted hallway, vertical 9:16, no text, no watermark",

    # Scene 16: Spinning Audio Tape Reel
    "Old magnetic reel-to-reel tape recorder spinning slowly in the dark, illuminated by a faint red LED indicator light, spool of magnetic tape turning, vertical 9:16, no text, no watermark",

    # Scene 17: Frantic Claw Marks Carving 03:17
    "Flashlight beam illuminating a crumbling cold concrete bunker wall covered in frantic claw scratches repeatedly carving '03:17' into the stone, chilling horror evidence, vertical 9:16, no text, no watermark",

    # Scene 18: Creepy Hallway at 3 AM
    "Eerie dark residential apartment hallway at 3 AM, dim doorway cracked open with a faint silhouette standing in shadow, subtle psychological dread, vertical 9:16, no text, no watermark"
]


def render_existing(vid: int, upload: bool = False):
    db = DB()
    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"❌ Manifest not found at: {manifest_path}")
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dur = manifest["narration"]["duration_sec"]
    print(f"\n🎥 Rendering existing Video #{vid} ({dur:.1f}s)...")

    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"
    if bgm_path.exists():
        print(f"\n🎵 Mixing Cinematic Horror Ambiance ({bgm_path.name})...")
        enhanced_video = out_dir / "final_with_horror_bgm.mp4"
        cmd = [
            "-i", str(raw_video),
            "-stream_loop", "-1", "-i", str(bgm_path),
            "-filter_complex",
            f"[1:a]volume=0.18,afade=t=in:st=0:d=2.0,afade=t=out:st={max(0.1, dur-3):.2f}:d=3[bgm];"
            "[0:a][bgm]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(enhanced_video)
        ]
        from core.ffmpeg import run
        try:
            run(cmd, what="horror bgm master mix", timeout=300)
            if enhanced_video.exists() and enhanced_video.stat().st_size > 500000:
                raw_video.unlink(missing_ok=True)
                enhanced_video.rename(raw_video)
                print("✅ Real Cinematic Horror Ambiance mixed successfully!")
        except Exception as e:
            print(f"⚠️ BGM mix fallback note: {e}")

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

    print("\n" + "=" * 75)
    print("  🎉 4-MINUTE 10x SUSPENSE FILM GENERATION COMPLETE!")
    print("=" * 75)
    print(f"  🎬 Video ID    : #{vid}")
    print(f"  📁 Output File : {raw_video}")
    print(f"  ⏱️ Duration    : {final_dur:.1f}s ({final_dur/60:.2f} minutes)")
    print(f"  📦 File Size   : {final_size_mb} MB")
    print(f"  🛡️ Validation  : {'PASS ✅' if rep.ok else 'WARN ⚠️'}")
    print("=" * 75 + "\n")

    if upload:
        _perform_upload(db, vid)

    db.close()


def _perform_upload(db: DB, vid: int):
    print(f"🚀 [Step 6/6] Uploading Video #{vid} to YouTube...")
    db.set_status(vid, "approved", note="Approved for YouTube upload (10x Suspense)")
    pub = YouTubePublisher(db=db)
    try:
        res = pub.publish(vid, privacy="public")
        print(f"✅ Published successfully: {res}")
    except PublishError as pe:
        err_msg = str(pe)
        if "uploadLimitExceeded" in err_msg or "quota" in err_msg.lower():
            print("\n⚠️ YouTube daily upload limit (~7 uploads/day) is active right now.")
            print(f"📌 Video #{vid} has been saved as 'approved' in the database.")
            print("🕒 It will automatically publish tomorrow when YouTube resets via 'python publish_all.py'!")
        else:
            print(f"❌ Upload Error: {pe}")
    except Exception as e:
        err_str = str(e)
        if "uploadLimitExceeded" in err_str:
            print("\n⚠️ YouTube daily upload limit (~7 uploads/day) is active right now.")
            print(f"📌 Video #{vid} has been saved as 'approved' in the database.")
            print("🕒 It will automatically publish tomorrow when YouTube resets via 'python publish_all.py'!")
        else:
            print(f"⚠️ Upload unexpected issue: {e}")


def generate_film(upload: bool = False, preview_only: bool = False):
    print("\n" + "=" * 75)
    print("  🎬 AUTOPILOT: 4-MINUTE 10x SUSPENSE SPECIAL PRODUCTION")
    print(f"  📌 Story : {TOPIC}")
    print(f"  📜 Lines : {len(LINES)} lines (~560 words)")
    print(f"  🖼️ Scenes: {len(IMAGE_PROMPTS)} AI cinematic horror frames")
    print("=" * 75 + "\n")

    t0 = time.time()
    db = DB()

    # 1. Register in SQLite Database
    word_count = sum(len(l["text"].split()) for l in LINES)
    est_duration = round(word_count / 2.2, 1)  # ~245s

    script_data = {
        "topic": TOPIC,
        "title": TITLE,
        "caption": CAPTION,
        "hashtags": HASHTAGS,
        "hook_type": "specific_outcome",
        "hook_line": LINES[0]["text"],
        "hook_text_overlay": HOOK_OVERLAY,
        "comment_bait": COMMENT_BAIT,
        "cast": {
            "narrator": {"gender": "male", "persona": "deep grave mystery narrator"}
        },
        "lines": LINES,
        "word_count": word_count,
        "est_sec": est_duration
    }

    vid = db.create_video(
        TOPIC,
        title=TITLE,
        caption=CAPTION,
        hashtags=HASHTAGS,
        hook_type="specific_outcome",
        script_json=script_data,
        length_sec=int(est_duration),
        status="planned"
    )

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Video Project #{vid} created at: {out_dir}")

    # 2. Narration Audio Generation (Edge-TTS Grave Hindi Profile)
    print(f"\n🎙️ [Step 1/6] Generating ~4-minute narration audio via Edge-TTS (hi_m_grave)...")
    voice_agent = Voice(db=db)
    narration_info = voice_agent.narrate(LINES, out_dir, profile_id="hi_m_grave")
    dur = narration_info["duration_sec"]
    words = narration_info["words"]
    print(f"✅ Narration Audio Generated: {dur:.1f}s ({dur/60:.2f} mins), {len(words)} timed words!")
    print(f"   Audio file: {narration_info['audio_path']}")

    # 3. Scene Timings calculation for 18 Scenes
    n_scenes = len(IMAGE_PROMPTS)
    scene_dur = dur / n_scenes
    scenes = []
    motions = [
        "zoom_in_dramatic", "pan_left", "zoom_in_slow", "pan_right",
        "punch_in", "zoom_out", "whip_zoom", "pan_left", "zoom_in"
    ]

    for i, p in enumerate(IMAGE_PROMPTS):
        st = round(i * scene_dur, 3)
        en = round((i + 1) * scene_dur if i < n_scenes - 1 else dur, 3)
        scenes.append({
            "n": i + 1,
            "beat": f"act_{min(6, (i // 3) + 1)}",
            "image_prompt": p,
            "motion": motions[i % len(motions)],
            "parallax": (i % 2 == 1),
            "file": f"scene_{i+1:02d}.jpg",
            "seed": vid * 250 + i + 1,
            "start": st,
            "end": en,
            "dur": round(en - st, 3)
        })

    # 4. Generate 18 AI Scene Images (ImageGen Pollinations)
    print(f"\n🖼️ [Step 2/6] Generating {n_scenes} atmospheric AI scenes via Pollinations...")
    img_agent = ImageGen(providers=["pollinations", "local_placeholder"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"✅ All {len(scenes_with_paths)} horror scene visuals ready!")

    # 5. Build Complete Production Manifest
    manifest = {
        "video_id": vid,
        "topic": TOPIC,
        "script": script_data,
        "art": {
            "template_id": "crimson_alert",
            "template_name": "Crimson Alert Noir",
            "pacing": "atmospheric_deliberate",
            "setting": "frozen mountain outpost 3:17 AM",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": narration_info,
        "words": words,
        "render_spec": {
            "resolution": "1080x1920",
            "fps": 30,
            "crf": 22
        }
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📄 Manifest written: {manifest_path}")

    if preview_only:
        print("\n✨ Preview mode complete! Assets, audio, and manifest generated.")
        db.close()
        return

    # 6. Render Full 4-Minute MP4 with FFmpeg & Subtitles
    print(f"\n🎥 [Step 3/6] Rendering complete 4-minute video with FFmpeg (Ken Burns + Subtitles)...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    raw_video = Path(render_info["video_path"])

    # 7. Mix Real Cinematic Horror Ambiance BGM
    bgm_path = Path(CONFIG["_root"]) / "assets" / "audio" / "suspense_bgm.mp3"
    if bgm_path.exists():
        print(f"\n🎵 [Step 4/6] Mixing Cinematic Horror Ambiance ({bgm_path.name})...")
        enhanced_video = out_dir / "final_with_horror_bgm.mp4"
        cmd = [
            "-i", str(raw_video),
            "-stream_loop", "-1", "-i", str(bgm_path),
            "-filter_complex",
            f"[1:a]volume=0.18,afade=t=in:st=0:d=2.0,afade=t=out:st={max(0.1, dur-3):.2f}:d=3[bgm];"
            "[0:a][bgm]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(enhanced_video)
        ]
        from core.ffmpeg import run
        try:
            run(cmd, what="horror bgm master mix", timeout=300)
            if enhanced_video.exists() and enhanced_video.stat().st_size > 500000:
                raw_video.unlink(missing_ok=True)
                enhanced_video.rename(raw_video)
                print("✅ Real Cinematic Horror Ambiance mixed successfully!")
        except Exception as e:
            print(f"⚠️ BGM mix fallback note: {e}")

    # 8. Probe & Update Database
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

    print(f"\n🔍 [Step 5/6] Validating final video specifications...")
    rep = validate_dir(out_dir)
    render_info["video_path"] = str(raw_video)
    render_info["duration_sec"] = final_dur
    render_info["size_mb"] = final_size_mb
    manifest["render"] = render_info
    manifest["validation"] = rep.to_dict()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 75)
    print("  🎉 4-MINUTE 10x SUSPENSE FILM GENERATION COMPLETE!")
    print("=" * 75)
    print(f"  🎬 Video ID    : #{vid}")
    print(f"  📁 Output File : {raw_video}")
    print(f"  ⏱️ Duration    : {final_dur:.1f}s ({final_dur/60:.2f} minutes)")
    print(f"  📦 File Size   : {final_size_mb} MB")
    print(f"  🛡️ Validation  : {'PASS ✅' if rep.ok else 'WARN ⚠️'}")
    print("=" * 75 + "\n")

    # 9. Optional Upload to YouTube
    if upload:
        _perform_upload(db, vid)
    else:
        print("💡 To upload this video to YouTube:")
        print(f"   python generate_4min_suspense_10x.py --render-existing {vid} --upload")

    db.close()
    elapsed = round(time.time() - t0, 1)
    print(f"⚡ Total pipeline execution time: {elapsed}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 4-Minute 10x Suspense AI Horror Film")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube directly after render")
    parser.add_argument("--preview-only", action="store_true", help="Generate audio and images only, skip render")
    parser.add_argument("--render-existing", type=int, help="Render an already prepared video ID (e.g. 315)")
    args = parser.parse_args()

    if args.render_existing:
        render_existing(args.render_existing, upload=args.upload)
    else:
        generate_film(upload=args.upload, preview_only=args.preview_only)
