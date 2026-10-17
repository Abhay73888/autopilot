#!/usr/bin/env python3
"""
generate_4min_horror_special.py — Complete 4-Minute Atmospheric AI Horror Film Generator.

Story: "Kuldhara: Ek Hi Raat Mein Gayab Hue 84 Gaon Ka Khaufnak Shraap"
Genre: Supernatural Horror / Real Unexplained Mystery (Rajasthan, India)
Target Duration: ~4 Minutes (230s - 250s)
Pipeline:
  1. Edge-TTS Narration with Deep Atmospheric Voice (hi-IN-MadhurNeural)
  2. 18 AI-Generated Cinematic Horror Scenes via Pollinations
  3. Dynamic Camera Motions (Ken Burns: zoom_in_dramatic, pan_left, whip_zoom, etc.)
  4. Cinematic ASS Subtitles (Glowing Amber/Crimson Dark Aesthetic)
  5. Multi-Layer Audio Mix: Real Horror Drone & Ambiance (suspense_bgm.mp3)
  6. YouTube Upload Support with Invariants (Comments 100% ON, MadeForKids=False)

Usage:
  python generate_4min_horror_special.py
  python generate_4min_horror_special.py --upload
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

log = Logbook("horror_4min")

TOPIC = "Kuldhara Ghost Village: Ek Hi Raat Mein Gayab Hue 84 Gaon Ka Khaufnak Shraap"
TITLE = "Kuldhara Ka Khaufnak Sach: 1 Raat Mein Gayab Hue 84 Gaon Ka Shraap 💀⏳ (4-Min Mystery)"
CAPTION = (
    "Jaisalmer ke tapte hue registan mein 200 saal pehle ek hi raat mein 84 gaon ke 1500 parivar achanak gayab ho gaye! "
    "Na koi laash mili, na ret par pahiye ke nishaan... sirf ek maut ka shraap! "
    "2013 mein jab Paranormal Society ne yahan raat bitayi to gaadiyon par nanhe bachhon ke geele haath chhap gaye! "
    "Dekhiye Kuldhara ka khaufnak sach 👇"
)
HASHTAGS = [
    "#KuldharaMystery", "#GhostVillage", "#HorrorStory", "#IndianHorror",
    "#SupernaturalMystery", "#ParanormalActivity", "#RajasthanMystery", "#BhootiaGaon",
    "#MysteryDocu", "#DarkTales"
]
HOOK_OVERLAY = "Kuldhara: 84 Gaon Gayab 💀"
COMMENT_BAIT = "Kya aap kisi aisi shraapit jagah par akele raat guzarne ki himmat karenge? Ya ye shraap sirf ek vehem hai? Comment mein batayein!"

# -----------------------------------------------------------------------------
# 26 LINES OF ATMOSPHERIC HINDI SCRIPT (~530 words = ~4 minutes narration)
# -----------------------------------------------------------------------------
LINES = [
    # --- ACT 1: THE OPENING HOOK (0:00 - 0:35) ---
    {
        "speaker": "narrator",
        "text": "Jaisalmer ke tapte hue registan ke beech ek aisi jagah hai, jahan pichhle do sau saal se koi bhi insaan ek raat bhi zinda nahi guzar saka.",
        "emotion": "serious",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Yeh hai Kuldhara... ek aisi shraapit zameen, jahan san atharah sau pachchees ki ek kaali raat ko chaurasi gaon ke pandrah sau parivar achanak gayab ho gaye!",
        "emotion": "whispers",
        "role": "hook"
    },
    {
        "speaker": "narrator",
        "text": "Na koi laash mili, na kisi bailgaadi ke pahiye ke nishaan, aur na hi registan ki ret par kisi insaan ke kadmo ke nishaan.",
        "emotion": "serious",
        "role": "hook"
    },

    # --- ACT 2: THE EVIL DIWAN & THE FORBIDDEN DESIRE (0:35 - 1:15) ---
    {
        "speaker": "narrator",
        "text": "Sadiyon pehle yeh gaon behad khush-haal tha. Yahan Paliwal Brahman rehte the, jo sookhi zameen se sona ugana jaante the.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Lekin is khushi par achanak Jaisalmer ke sabse krur aur aiyash diwan Salim Singh ki gandi nazar pad gayi.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Salim Singh ki nazar gaon ke pradhan ki solah saal ki masoom beti par padi. Usne elaan kiya: agle purnima ki raat tak ladki uski haveli mein honi chahiye!",
        "emotion": "dramatic",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Usne dhamki di: agar kisi ne inkaar kiya, toh uske sipahi har ek gaon ko zinda aag ke hawale kar denge aur ek-ek bache ko talwar se kaat denge.",
        "emotion": "cold",
        "role": "body"
    },

    # --- ACT 3: THE MIDNIGHT COUNCIL & THE DEADLY CURSE (1:15 - 2:00) ---
    {
        "speaker": "narrator",
        "text": "Purnima ki aakhri raat aayi. Charon taraf ghana andhera tha. Sabhi chaurasi gaon ke mukhiya Kuldhara ke mandir mein chupchap ikattha hue.",
        "emotion": "whispers",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Yeh aatmasamman aur beti ki izzat ka sawal tha. Unhone faisla kiya ki woh apna sadiyon purana aashiyana hamesha ke liye chhod denge, lekin us darinde ke aage nahi jhukenge.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Lekin gaon chhodne se theek pehle, sabhi buzurgon ne mandir ke aangan mein ret ko mutthi mein lekar ek khaufnak shraap diya.",
        "emotion": "dramatic",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Unhone shraap diya: Aaj ke baad is zameen par koi doosra insaan kabhi aabad nahi ho payega... jo bhi yahan aayega, uski aatma yahin dafan hokar bhatakti reh jayegi!",
        "emotion": "cold",
        "role": "reveal"
    },

    # --- ACT 4: THE SILENT EMPTY DAWN (2:00 - 2:40) ---
    {
        "speaker": "narrator",
        "text": "Agli subah jab Salim Singh apni fauj ke saath Kuldhara pahuche, toh unke pairo tale zameen khisak gayi.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Haveliyon ke bhari lakdi ke darwaze khule the. Chulhon par adhpaki rotiyan thandi pad chuki thi. Aangan mein paani ke ghade waise hi rakhe the.",
        "emotion": "whispers",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Lekin pandrah sau parivar, unke lakho janwar aur unka saaman sab kuch ek hi raat mein hawa mein gayab ho chuka tha!",
        "emotion": "dramatic",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Door-door tak faile registan mein unka ek bhi nishaan nahi mila. Itne log kahan gaye, unhe zameen nigal gayi ya aasmaan khaa gaya, yeh sadiyon se an-suljha rahasya hai.",
        "emotion": "cold",
        "role": "body"
    },

    # --- ACT 5: THE PARANORMAL SOCIETY MIDNIGHT EXPEDITION (2:40 - 3:25) ---
    {
        "speaker": "narrator",
        "text": "Kai saal baad, saal do hazaar terah mein, Indian Paranormal Society ki ek tees sadasyon ki team high-tech equipments ke saath Kuldhara aayi.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Woh yeh saabit karna chahte the ki bhoot-pret sirf ek afwah hai. Unhone laser grids, EMF radiation meters aur thermal infrared cameras lagaye.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Raat ke theek do bajkar tees minute par, registan ka taapmaan achanak chaalees degree se girkar seedha zero degree tak pahunch gaya!",
        "emotion": "dramatic",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Laser grid ki deewaron par achanak aisi aakritiyan guzarti dikhi jinka koi shareer nahi tha. EMF meters ke kaante achanak pagal ho gaye!",
        "emotion": "whispers",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Aur sabse khaufnak ghatna tab ghati jab investigators ki band gaadiyon ke sheesho par nanhe bachhon ke geele haatho ke nishaan ubhar aaye!",
        "emotion": "fear",
        "role": "reveal"
    },

    # --- ACT 6: THE ACTIVE GOVERNMENT BAN & CHILLING CONCLUSION (3:25 - 4:10) ---
    {
        "speaker": "narrator",
        "text": "Aaj bhi Archaeological Survey of India ne Kuldhara ke mukhya dwar par ek lohe ka bada warning board laga rakha hai.",
        "emotion": "serious",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Board par saaf likha hai: Suraj dhalne ke baad aur suraj nikalne se pehle is bhootia khandahar mein pravesh karna sakht qanoonan apradh hai.",
        "emotion": "cold",
        "role": "body"
    },
    {
        "speaker": "narrator",
        "text": "Aas-paas ke gaon wale batate hain ki andheri raato mein Kuldhara ki sunsaan galiyon se auraton ke rone ki aawazein aur payal ki jhankar saaf sunai deti hai.",
        "emotion": "whispers",
        "role": "reveal"
    },
    {
        "speaker": "narrator",
        "text": "Jo koi bhi raat mein is shraapit seher ke andar ruka, woh subah kabhi theek dimaag ke saath wapas nahi laut saka.",
        "emotion": "cold",
        "role": "ending"
    },
    {
        "speaker": "narrator",
        "text": "Ab sawal yeh hai: Kya aap kisi aisi jagah par akele ek raat bitane ki himmat kar sakte hain? Ya aapke hisaab se shraap sirf ek vehem hai?",
        "emotion": "dramatic",
        "role": "ending"
    },
    {
        "speaker": "narrator",
        "text": "Apni raye comment box mein zaroor likhein, aur aisi hi an-suljhi khaufnak sachi ghatnaon ke liye channel ko abhi subscribe karein.",
        "emotion": "serious",
        "role": "ending"
    }
]

# -----------------------------------------------------------------------------
# 18 ULTRA-CINEMATIC HORROR IMAGE PROMPTS (Vertical 9:16, Noir Dark Atmosphere)
# -----------------------------------------------------------------------------
IMAGE_PROMPTS = [
    # Scene 1: Opening Thar Desert & Distant Ghost Town
    "Vast empty golden Thar desert at dusky twilight, crumbling sandstone ruins of an abandoned ghost village in the distance, ominous storm clouds, cinematic lighting, 8k, moody horror atmosphere, vertical 9:16, no text, no watermark",

    # Scene 2: Ancient Stone Gateway of Kuldhara
    "Ancient weathered stone gateway arch of cursed Kuldhara village, dark midnight sky with eerie glowing pale moon, mist creeping across cracked earth, haunting shadows, vertical 9:16, no text, no watermark",

    # Scene 3: Empty Abandoned Courtyards with Moonlight
    "Row of desolate abandoned sandstone havelis with shattered windows, moonlight casting long eerie shadows on empty sand-covered streets, cinematic noir, vertical 9:16, no text, no watermark",

    # Scene 4: Golden Prosperity of Historic Ancient Village
    "Historical depiction of wealthy ancient Rajasthani village in 1800s, traditional stone houses, prosperous marketplace, warm golden hour sun, vintage cinematic realism, vertical 9:16, no text, no watermark",

    # Scene 5: Diwan Salim Singh Menacing Silhouette
    "Silhouette of an evil arrogant Indian royal diwan minister dressed in ornate Mughal-Rajasthani robes holding a curved talwar sword, dark palace terrace, glowing sinister red torches, vertical 9:16, no text, no watermark",

    # Scene 6: Tearful Innocent Village Maiden
    "Close-up of a beautiful traditional Rajasthani young woman wearing an ornate yellow and red veil, tear dripping down her cheek in candle-lit darkness, expressions of fear, cinematic portrait, vertical 9:16, no text, no watermark",

    # Scene 7: Burning Torches and Ruthless Soldiers
    "Fierce royal guards on horseback holding blazing fire torches at night outside ancient stone town gates, smoke rising, high suspense drama, vertical 9:16, no text, no watermark",

    # Scene 8: Secret Midnight Council inside Ancient Temple
    "Group of elder Rajasthani village leaders with white turbans and beards gathered secretly inside a dark sandstone temple around a single flame, grim solemn faces, dramatic Rembrandt shadows, vertical 9:16, no text, no watermark",

    # Scene 9: Chanting the Ancient Curse
    "Elder village leader holding a fistful of sacred desert dust raising both arms toward the dark storm clouds in deep sorrow and fury, mystical glowing embers, dark fantasy realism, vertical 9:16, no text, no watermark",

    # Scene 10: Desert Dust Storm Sweeping Over Ancient Town
    "Massive supernatural black dust storm swallowing the sandstone ruins of Kuldhara under blood red crescent moon, whirlwind of sand, apocalyptic horror, vertical 9:16, no text, no watermark",

    # Scene 11: Empty Kitchen with Untouched Hearth
    "Interior of an ancient abandoned stone mud kitchen, unfinished bread dough resting on cold clay tawa, abandoned brass water vessel on dusty floor, cobwebs, morning rays through cracked roof, vertical 9:16, no text, no watermark",

    # Scene 12: Endless Desert Dunes with Vanishing Footprints
    "High-angle shot of vast rolling sand dunes of the Thar desert, single trail of footprints abruptly ending in the middle of nowhere, desolate infinity, vertical 9:16, no text, no watermark",

    # Scene 13: Paranormal Investigators in the Darkness
    "Modern paranormal researchers wearing dark jackets holding glowing green laser grid projectors and digital EMF radiation meters inside a pitch-black ruined corridor, high suspense, vertical 9:16, no text, no watermark",

    # Scene 14: Thermal Imaging Anomaly
    "Green thermal imaging night-vision camera display revealing a glowing blue cold silhouette of an ethereal human figure standing in the center of an empty ruined courtyard, sci-fi horror, vertical 9:16, no text, no watermark",

    # Scene 15: Ghostly Handprints on Car Glass
    "Macro close-up of a dusty SUV window glass in pitch black night, small translucent child handprints appearing mysteriously on the foggy exterior glass from outside, terrifying chilling horror, vertical 9:16, no text, no watermark",

    # Scene 16: Weathered Official Warning Sign Board
    "Rusty iron official government warning sign board at the barricaded iron entrance of a ghost village at dusk, overgrown desert thorn bushes, haunting silence, cinematic photography, vertical 9:16, no text, no watermark",

    # Scene 17: Spectral Woman in Ethereal Veil
    "Translucent misty ghostly apparition of a woman in traditional floating red Rajasthani lehenga gliding through ruined crumbling archways under moonlight, eerie beauty, supernatural mystery, vertical 9:16, no text, no watermark",

    # Scene 18: Wide Aerial View of the Cursed Desert Ruins
    "Panoramic aerial drone view of the entire cursed ghost village of Kuldhara at midnight, cracked ruins illuminated by a faint mystical silver moonlight, surrounded by pitch-black endless desert, vertical 9:16, no text, no watermark"
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
    print("  🎉 4-MINUTE HORROR FILM GENERATION COMPLETE!")
    print("=" * 75)
    print(f"  🎬 Video ID    : #{vid}")
    print(f"  📁 Output File : {raw_video}")
    print(f"  ⏱️ Duration    : {final_dur:.1f}s ({final_dur/60:.2f} minutes)")
    print(f"  📦 File Size   : {final_size_mb} MB")
    print(f"  🛡️ Validation  : {'PASS ✅' if rep.ok else 'WARN ⚠️'}")
    print("=" * 75 + "\n")

    if upload:
        print(f"🚀 Uploading Video #{vid} to YouTube...")
        db.set_status(vid, "approved", note="Approved for YouTube upload")
        pub = YouTubePublisher(db=db)
        res = pub.publish(vid, privacy="public")
        print(f"✅ Published: {res}")

    db.close()


def generate_film(upload: bool = False, preview_only: bool = False):
    print("\n" + "=" * 75)
    print("  🎬 AUTOPILOT: 4-MINUTE HORROR SPECIAL PRODUCTION")
    print(f"  📌 Story : {TOPIC}")
    print(f"  📜 Lines : {len(LINES)} lines (~530 words)")
    print(f"  🖼️ Scenes: {len(IMAGE_PROMPTS)} AI cinematic horror frames")
    print("=" * 75 + "\n")

    t0 = time.time()
    db = DB()

    # 1. Register in SQLite Database
    word_count = sum(len(l["text"].split()) for l in LINES)
    est_duration = round(word_count / 2.2, 1)  # ~240s

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
            "narrator": {"gender": "male", "persona": "deep dark mystery documentary host"}
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
            "seed": vid * 200 + i + 1,
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
            "template_id": "noir_teal",
            "template_name": "Horror Noir",
            "pacing": "atmospheric_deliberate",
            "setting": "cursed desert ghost village",
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
    print("  🎉 4-MINUTE HORROR FILM GENERATION COMPLETE!")
    print("=" * 75)
    print(f"  🎬 Video ID    : #{vid}")
    print(f"  📁 Output File : {raw_video}")
    print(f"  ⏱️ Duration    : {final_dur:.1f}s ({final_dur/60:.2f} minutes)")
    print(f"  📦 File Size   : {final_size_mb} MB")
    print(f"  🛡️ Validation  : {'PASS ✅' if rep.ok else 'WARN ⚠️'}")
    print("=" * 75 + "\n")

    # 9. Optional Upload to YouTube
    if upload:
        print(f"🚀 [Step 6/6] Uploading Video #{vid} to YouTube...")
        # Invariants: Zero comment lock, selfDeclaredMadeForKids=False, comment_bait posted
        db.set_status(vid, "approved", note="Approved for YouTube upload")
        pub = YouTubePublisher(db=db)
        res = pub.publish(vid, privacy="public")
        print(f"✅ Published: {res}")
    else:
        print("💡 To upload this video to YouTube with comments 100% ON:")
        print(f"   python generate_4min_horror_special.py --upload")

    db.close()
    elapsed = round(time.time() - t0, 1)
    print(f"⚡ Total pipeline execution time: {elapsed}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 4-Minute Atmospheric AI Horror Film")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube directly after render")
    parser.add_argument("--preview-only", action="store_true", help="Generate audio and images only, skip render")
    parser.add_argument("--render-existing", type=int, help="Render an already prepared video ID (e.g. 301)")
    args = parser.parse_args()

    if args.render_existing:
        render_existing(args.render_existing, upload=args.upload)
    else:
        generate_film(upload=args.upload, preview_only=args.preview_only)
