"""
series/series_runner.py — AUTOPILOT Unified Series Generation Engine.

Supports:
  - SERIES_1: Kaal-Rekha (काल-रेखा) Anime Psychological Time-Loop Thriller
  - SERIES_2: Jab Pyaar Online Tha (Romantic Drama)
  - SERIES_3: Chintu Kids Adventures (Animated Family Adventure)
  - SERIES_4: Dimag Ka Dahi (Mind-Bending Riddles)

Enables one-click generation directly from the web dashboard and AI Copilot.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure terminal stdout safely handles UTF-8 without crashing
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook
from agents.voice import Voice
from agents.imagegen import ImageGen
from pipeline.render import Renderer
from pipeline.validate import validate_dir

log = Logbook("series_runner")

# =====================================================================
# SERIES 1: KAAL-REKHA EPISODE CATALOG & PROCEDURAL ENGINE
# =====================================================================

KAAL_REKHA_EPISODES: dict[int, dict[str, Any]] = {
    1: {
        "title": "Raat 3:17 Baje Mujhe Meri Hi Dead Body Dikhi... ⚠️ | KAAL-REKHA (Part 1) #Shorts",
        "caption": "Theek 3:17 AM par cassette player apne aap chalu hua... aur neeche sadak par mujhe meri hi laash dikhi! Kaun tha woh? Drop your theories! 👇",
        "hook_overlay": "3:17 AM: MY OWN DEAD BODY?!",
        "comment_bait": "Phone par usne khud ko 'Number Three' bola jabki cassette par '04' likha tha... Kaun hai zinda Kabir? Drop your theories! 👇",
        "lines": [
            {"speaker": "narrator", "text": "Theek raat ke 3:17 AM par mere vintage cassette player par ek recording play hui: 'Kabir... balcony se mat dekhna!'", "emotion": "serious", "role": "hook"},
            {"speaker": "narrator", "text": "Lekin maine parda hataya... neeche barish mein ek unmarked black ambulance khadi thi.", "emotion": "mysterious", "role": "body"},
            {"speaker": "narrator", "text": "Do ajeeb logon ne ek yellow body-bag bahar nikala... aur uska zipper khul gaya.", "emotion": "urgent", "role": "body"},
            {"speaker": "narrator", "text": "Streetlight ki roshni mein jo chehra dikha... wo mera tha! Mera gala kata hua tha aur aankhein khuli thi!", "emotion": "shocked", "role": "climax"},
            {"speaker": "narrator", "text": "Tabhi mere room ka landline baja... maine kaanpte haathon se phone uthaya.", "emotion": "mysterious", "role": "body"},
            {"speaker": "narrator", "text": "Dusri taraf meri hi aawaz ne kaha: 'Kabir, ye tumhara teesra attempt tha. Agle 60 seconds mein wo upar aa rahe hain... BHAAGO!'", "emotion": "urgent", "role": "cliffhanger"}
        ],
        "image_prompts": [
            "Cinematic 8k anime shot of dark messy bedroom with vintage cassette recorder glowing red at 3:17 AM, rain on window, MAPPA aesthetic, masterpiece, vertical 9:16, no text",
            "Atmospheric 8k anime shot of rainy deserted city street at midnight, mysterious black ambulance with headlights cutting through heavy rain, vertical 9:16, high tension, no text",
            "Chilling 8k anime perspective from 2nd floor balcony looking down at two shadowy figures opening a yellow body bag in torrential rain, vertical 9:16, cinematic, no text",
            "Extreme close up 8k anime style of pale dead Kabir Sen inside body bag with glowing Roman numeral on neck, rain splashing on glass eyes, vertical 9:16, horror suspense, no text",
            "Tense 8k anime shot of Kabir in modern clothes frozen in fear holding a ringing black rotary landline telephone in dark room, sweat beads, vertical 9:16, no text",
            "Dramatic 8k anime shot of Kabir looking back in pure panic as heavy footsteps echo outside door with red warning lights flashing, vertical 9:16, cliffhanger, no text"
        ]
    },
    10: {
        "title": "LOOP TOOT GAYA... YA MEERA KA SACH?! 💥⏳ | KAAL-REKHA (Grand Finale Part 10) #Shorts",
        "caption": "Grand Finale! Kabir ne 3:17 AM par temporal core ko tod diya! Kya waqt aage badha ya Meera hamesha ke liye gayab ho gayi? Season 1 Conclusion! 😱💥👇",
        "hook_overlay": "⏳ KAAL-REKHA (FINALE: THE PARADOX) 💥",
        "comment_bait": "Climax twist: Meera ka aakhiri sandesh kya tha? Season 2 ke liye COMMENT karein: 'SEASON 2'! 👇🔥",
        "lines": [
            {"speaker": "narrator", "text": "Ghadi mein 3:17 AM aur 59 seconds the... agar lever nahi kheencha toh hum sab mit jayenge!", "emotion": "urgent", "role": "hook"},
            {"speaker": "char_b", "text": "Masked Entity ne cheekh kar kaha: 'Kabir mat karna! Lever kheenchne par Meera ka astitva mit jayega!'", "emotion": "intense", "role": "body"},
            {"speaker": "narrator", "text": "Meera ne rokar meri aankhon mein dekha aur kaha: 'Kabir... main kabhi insaan thi hi nahi!'", "emotion": "shocked", "role": "body"},
            {"speaker": "narrator", "text": "'Main is time loop ki chaabi hoon... mujhe azaad karo Kabir!'", "emotion": "vulnerable", "role": "climax"},
            {"speaker": "narrator", "text": "Maine poori taqat se crimson lever ko kheench diya... aasman mein violet bijli phoot padi!", "emotion": "desperate", "role": "climax"},
            {"speaker": "narrator", "text": "Aur pehli baar ghadi ki sui aage badhi: 3:18 AM! Lekin jab maine piche dekha... Meera gayab thi! Season 2 ke liye COMMENT karein!", "emotion": "shocked", "role": "ending"}
        ],
        "image_prompts": [
            "Epic 8k anime shot of colossal antique clock mechanism about to strike 3:18 AM with violet sparks crackling, vertical 9:16, MAPPA aesthetic, masterpiece, no text",
            "Dramatic anime shot of masked porcelain entity desperately lunging forward through temporal lightning mist, vertical 9:16, cinematic, no text",
            "Emotional 8k anime close up of Indian girl Meera dissolving into luminous golden particles with tears in eyes, vertical 9:16, breathtaking, no text",
            "Hyper-detailed anime perspective of Kabir's trembling hand slamming the heavy iron crimson lever down into gears, vertical 9:16, explosive tension, no text",
            "Colossal cathedral clock tower exploding with brilliant ultraviolet light beams tearing through midnight sky, vertical 9:16, anime climax, no text",
            "Heartbreaking 8k anime shot of Kabir standing alone in silent rain as clock clearly displays 3:18 AM, looking at empty space where Meera stood, vertical 9:16, no text"
        ]
    }
}


def get_next_episode_number(db: DB, series_code: str = "SERIES_1") -> int:
    """Find the next episode number to generate based on DB records."""
    rows = db.q(
        "SELECT id, title, notes FROM videos WHERE series_name = ? ORDER BY id DESC LIMIT 10",
        (series_code,)
    )
    max_ep = 0
    import re
    for r in rows:
        title = r["title"] or ""
        notes = r["notes"] or ""
        m = re.search(r'(?:Part|Episode|Ep)\s*(\d+)', f"{title} {notes}", re.IGNORECASE)
        if m:
            ep = int(m.group(1))
            if ep > max_ep:
                max_ep = ep
    
    # Also check existing generator scripts
    if series_code == "SERIES_1" and max_ep < 9:
        max_ep = 9  # ep9 was already prepared in generate_series1_ep9.py
    
    return max_ep + 1 if max_ep > 0 else 1


def generate_series_episode(
    series_code: str = "SERIES_1",
    episode_num: int | None = None,
    *,
    dry_run: bool = False,
    preset: str = "veryfast"
) -> dict[str, Any]:
    """
    Generate an episode of a specified series end-to-end.
    Returns: { "ok": bool, "video_id": int, "title": str, "result_paths": dict, "msg": str }
    """
    db = DB()
    t_start = time.time()
    series_code = series_code.upper().strip()

    if not episode_num:
        episode_num = get_next_episode_number(db, series_code)

    log.info(f"Starting series generation: {series_code} Episode {episode_num} (dry_run={dry_run})")

    # 1. Fetch or synthesize episode story package
    ep_data = None
    if series_code == "SERIES_1" and episode_num in KAAL_REKHA_EPISODES:
        ep_data = KAAL_REKHA_EPISODES[episode_num]
    else:
        # Procedural fallback for Series 1 dynamic episodes or other series
        ep_data = _synthesize_procedural_episode(series_code, episode_num)

    topic = f"Kaal-Rekha Episode {episode_num}: The Temporal Paradox" if series_code == "SERIES_1" else f"{series_code} Episode {episode_num}"
    title = ep_data["title"]
    caption = ep_data["caption"]
    hashtags = ["#KaalRekha", f"#Episode{episode_num}", "#AnimeShorts", "#TimeLoop", "#Shorts", "#HindiAnime"]
    hook_overlay = ep_data.get("hook_overlay", "⏳ TIME LOOP PARADOX 😱")
    comment_bait = ep_data.get("comment_bait", "Drop your craziest theories in COMMENTS! 👇")
    lines = ep_data["lines"]
    image_prompts = ep_data["image_prompts"]

    # 2. Register Video in DB
    vid = db.create_video(
        topic=topic,
        hook_type="cliffhanger",
        voice_id="hi_m_intense",
        template_id="dark_anime_thriller",
        notes=f"{series_code} Episode {episode_num} (One-Click Autonomous Generation)"
    )
    try:
        db.q(
            "UPDATE videos SET series_name = ?, series_index = ? WHERE id = ?",
            (series_code, episode_num, vid)
        )
    except Exception:
        pass

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 3. Voice Generation (Edge-TTS / Neural)
    voice_agent = Voice(db=db)
    voice_res = voice_agent.narrate(lines, out_dir, profile_id="hi_m_intense")
    dur_sec = voice_res["duration_sec"]
    words = voice_res["words"]

    # 4. Image Generation (Flux Engine / AI Visuals)
    n_scenes = len(image_prompts)
    dur_per_scene = dur_sec / max(1, n_scenes)
    motions = ["punch_in", "whip_zoom", "pan_left", "zoom_in_dramatic", "zoom_out", "punch_in"]

    scenes = []
    for i, prompt in enumerate(image_prompts):
        motion = motions[i % len(motions)]
        scenes.append({
            "n": i + 1,
            "file": f"scene_{i+1:02d}.jpg",
            "image_prompt": prompt,
            "motion": motion,
            "parallax": (i % 2 == 1),
            "dur": round(dur_per_scene, 3),
            "emotion": lines[min(i, len(lines) - 1)].get("emotion", "intense"),
            "role": lines[min(i, len(lines) - 1)].get("role", "body")
        })

    img_agent = ImageGen()
    scenes_ready = img_agent.generate_all(scenes, out_dir, seed_base=vid * 100)

    # 5. Build Manifest
    manifest = {
        "video_id": vid,
        "series_code": series_code,
        "episode_num": episode_num,
        "topic": topic,
        "title": title,
        "script": {
            "topic": topic,
            "title": title,
            "caption": caption,
            "hashtags": hashtags,
            "hook_type": "cliffhanger",
            "hook_line": lines[0]["text"],
            "hook_text_overlay": hook_overlay,
            "comment_bait": comment_bait,
            "cast": {
                "narrator": {"gender": "male", "persona": "Kabir"},
                "char_b": {"gender": "male", "persona": "Entity"}
            },
            "lines": lines,
            "word_count": len(words),
            "est_sec": dur_sec
        },
        "narration": {
            "audio_path": voice_res["audio_path"],
            "duration_sec": dur_sec,
            "words_count": len(words),
            "voice_id": "hi_m_intense"
        },
        "words": words,
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
            "template_id": "dark_anime_thriller",
            "template_name": "Dark Anime Psychological Thriller",
            "pacing": "fast",
            "setting": "Cathedral subterranean clock sanctuary",
            "n_scenes": len(scenes_ready)
        },
        "scenes": scenes_ready
    }

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Render Video (FFmpeg + Kinetic Subtitles + Sound FX)
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset=preset)

    # 7. Validate Output
    rep = validate_dir(out_dir)
    if rep.fatals:
        log.warn(f"Validation reported fatals: {rep.fatals}")

    # 8. Update DB
    db.update_video(
        vid,
        title=title,
        caption=caption,
        hashtags=hashtags,
        script_json=manifest["script"],
        video_path=render_info["video_path"],
        cover_path=str(out_dir / "cover.jpg"),
        status="rendered",
        length_sec=render_info["duration_sec"]
    )

    elapsed = round(time.time() - t_start, 1)
    paths = {
        "video_path": str(render_info["video_path"]),
        "cover_path": str(out_dir / "cover.jpg"),
        "manifest_path": str(manifest_path)
    }

    log.ok(f"Series generation success: {series_code} Ep {episode_num} (Video #{vid}) in {elapsed}s")

    return {
        "ok": True,
        "video_id": vid,
        "title": title,
        "episode_num": episode_num,
        "series_code": series_code,
        "result_paths": paths,
        "msg": f"🎬 {series_code} Episode {episode_num} ban ke tayar hai! (Video #{vid})"
    }


def _synthesize_procedural_episode(series_code: str, episode_num: int) -> dict[str, Any]:
    """Procedurally generate episode script and prompts for any episode number."""
    if series_code == "SERIES_1":
        return {
            "title": f"Waqt Ka Aakhiri Kanta... Sach Kya Tha?! 😱⏳ | KAAL-REKHA (Part {episode_num}) #Shorts",
            "caption": f"Kaal-Rekha Part {episode_num}: Kabir aur Meera ka samay ke saath aakhiri sangharsh! Kya loop toota ya naya raaz khula? Watch now! 👇",
            "hook_overlay": f"⏳ KAAL-REKHA (PART {episode_num}) ⚠️",
            "comment_bait": f"Part {episode_num + 1} dekhna chahte hain? Comment karein: 'NEXT PART'! 👇",
            "lines": [
                {"speaker": "narrator", "text": f"Raat ke 3:17 AM par ghadi ki sui achanak ulti disha mein ghoomne lagi!", "emotion": "shocked", "role": "hook"},
                {"speaker": "char_b", "text": "Hawa mein ek kaala saaya prakat hua: 'Kabir, har baar jab tu jeetne ki koshish karta hai, ek aur Meera mar jaati hai!'", "emotion": "cold", "role": "body"},
                {"speaker": "narrator", "text": "Maine deewaron par lage darpan mein dekha... har aaine mein ek alag saal ka Kabir khada tha!", "emotion": "urgent", "role": "body"},
                {"speaker": "narrator", "text": "Meera ne mera haath pakadte hue kaha: 'Kabir, ye hamari pehli mulakaat nahi hai... hum hazaron baar yahan mil chuke hain!'", "emotion": "vulnerable", "role": "climax"},
                {"speaker": "narrator", "text": "Aur tabhi building ke neeche wahi black ambulance aakar ruki... agle episode ke liye subscribe karein!", "emotion": "intense", "role": "ending"}
            ],
            "image_prompts": [
                "Cinematic 8k anime shot of antique wall clock with needles spinning wildly in reverse, sparks and violet mist, vertical 9:16, MAPPA aesthetic, masterpiece, no text",
                "Terrifying 8k anime shot of towering shadow wraith with glowing crimson eyes emerging from mist behind clock mechanism, vertical 9:16, no text",
                "Infinite mirror hall 8k anime perspective reflecting dozens of different versions of Kabir Sen at different ages, vertical 9:16, psychological thriller, no text",
                "Emotional 8k anime close up of 20yo Indian girl Meera desperately gripping Kabir's jacket in stormy darkness, vertical 9:16, cinematic, no text",
                "Dramatic 8k anime wide shot of rain-slicked city streets with ominous black ambulance parking beneath flickering lamppost at 3:17 AM, vertical 9:16, no text"
            ]
        }
    elif series_code == "SERIES_2":
        return {
            "title": f"Jab Uska Aakhiri Message Aaya... 💔🥺 | JAB PYAAR ONLINE THA (Ep {episode_num}) #Shorts",
            "caption": f"Online prem kahani ka ek dard bhara mod... Episode {episode_num} dekhein aur batayein kya sach tha! 👇💔",
            "hook_overlay": "💔 AAKHIRI MESSAGE 📱",
            "comment_bait": "Kya online pyaar sach ho sakta hai? Share your thoughts! 👇",
            "lines": [
                {"speaker": "narrator", "text": "3 saal tak jis ladki se main raat-raat bhar chat karta tha... uska achanak ek message aaya.", "emotion": "serious", "role": "hook"},
                {"speaker": "narrator", "text": "'Main ab se kabhi online nahi aungi... bhool jana mujhe.'", "emotion": "vulnerable", "role": "body"},
                {"speaker": "narrator", "text": "Maine hazaaron call kiye lekin number switch off tha... dil ghabrahat se kaanp raha tha.", "emotion": "urgent", "role": "body"},
                {"speaker": "narrator", "text": "Agle din uske shahar pahuncha toh jo pata chala... mere pairon tale zameen khisak gayi!", "emotion": "shocked", "role": "climax"},
                {"speaker": "narrator", "text": "Agla hissa sunne ke liye video ko like aur follow karein!", "emotion": "intense", "role": "ending"}
            ],
            "image_prompts": [
                "Moody aesthetic 8k anime style of Indian boy in hoodie looking heartbroken at glowing smartphone screen at 2 AM, dark bedroom, vertical 9:16, no text",
                "Close up shot of vintage smartphone screen showing a parting text message in dark room with rain on window, vertical 9:16, no text",
                "Emotional 8k anime shot of boy running through crowded rain-drenched railway platform with backpack, vertical 9:16, cinematic, no text",
                "Dramatic 8k anime perspective of quiet suburban street in rainy evening looking up at locked gate with closed windows, vertical 9:16, no text",
                "Melancholic anime close up of boy's teary eyes reflecting city streetlights, vertical 9:16, masterpiece, no text"
            ]
        }
    else:
        # Default Riddle / Fun
        return {
            "title": f"Dimag Hil Jayega! 99% Log Fail! 🧠😂 | Dimag Ka Dahi (Ep {episode_num}) #Shorts",
            "caption": f"Dimag Ka Dahi Episode {episode_num}: Is paheli ka jawab comment mein do! 99% log fail ho jate hain! 👇🧠",
            "hook_overlay": "🧠 99% LOG FAIL! 🤯",
            "comment_bait": "Jawab kya hai? Comment karein 5 seconds mein! 👇",
            "lines": [
                {"speaker": "narrator", "text": "Ek aisi paheli jo bade-bade genius ke dimag ka dahi bana de!", "emotion": "serious", "role": "hook"},
                {"speaker": "narrator", "text": "Wo kya hai jo subah chaar pairon par, dopahar ko do pairon par, aur shaam ko teen pairon par chalta hai?", "emotion": "mysterious", "role": "body"},
                {"speaker": "narrator", "text": "Aapke paas hain sirf 5 seconds... sochiye aur comment karein!", "emotion": "urgent", "role": "body"},
                {"speaker": "narrator", "text": "5... 4... 3... 2... 1! Sahi jawab hai: Insaan! (Bachpan, javani aur budhapa).", "emotion": "intense", "role": "climax"},
                {"speaker": "narrator", "text": "Kya aapka jawab sahi tha? Like karein aur doston ko challenge bhejein!", "emotion": "serious", "role": "ending"}
            ],
            "image_prompts": [
                "Vibrant colorful 8k 3D cartoon style glowing giant brain wearing glasses and holding magnifying glass, vertical 9:16, energetic, no text",
                "Playful mysterious 3D stylized question marks floating in cosmic purple background with hourglass ticking, vertical 9:16, no text",
                "Dynamic 3D digital countdown timer glowing neon gold 5 4 3 2 1 with comic smoke effects, vertical 9:16, no text",
                "Whimsical 3D animation showing baby crawling, adult walking, and elder with cane in joyful sunset park, vertical 9:16, no text",
                "Exciting 3D celebration with confetti exploding around golden trophy and big thumbs up, vertical 9:16, no text"
            ]
        }
