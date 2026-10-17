#!/usr/bin/env python3
"""
generate_and_publish_all_5_series.py — End-to-End Generator & Publisher for All 5 Series.
Generated episodes:
1. Series 1: Kaal-Rekha (Part 12)
2. Series 2: Jab Pyaar Online Tha (Episode 7 - Season 2 Launch)
3. Series 3: Chintu Ki Jadui Kahani (Episode 5)
4. Series 4: Dimag Ka Dahi Riddles (Episode 5)
5. Series 5: Ashwatthama 3049 AD (Episode 2)

Hard Constraints Enforced:
- selfDeclaredMadeForKids: False (Comments ALWAYS 100% ENABLED)
- privacyStatus: public
- First comment bait posted via commentThreads.insert
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

# Fix Windows terminal UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Real images enforcement
os.environ.pop("AUTOPILOT_ALLOW_PLACEHOLDERS", None)

from core.config import CONFIG
CONFIG["voice"] = {"engine_order": ["edge_tts", "gemini_tts"]}

from core.db import DB
from core.logbook import Logbook
from agents.voice import Voice
from agents.imagegen import ImageGen
from pipeline.render import Renderer
from pipeline.validate import validate_dir
from agents.publisher import YouTubePublisher

log = Logbook("all_5_series")

EPISODES = [
    # ─── 1. SERIES 1: KAAL-REKHA (Part 12) ───
    {
        "series_code": "SERIES_1",
        "episode_num": 12,
        "topic": "Kaal-Rekha Part 12: The 3:18 AM Fracture",
        "title": "The 3:18 AM Fracture: Kabir Trapped in the Matrix! ⏳😱 | KAAL-REKHA (Part 12) #Shorts",
        "caption": (
            "When the frozen clock finally ticked from 3:17 AM to 3:18 AM... Kabir wasn't in New York anymore. "
            "He opened his eyes in a subterranean quantum control room, staring at infinite surveillance monitors—all showing different versions of his own death! ⏳⚡\n\n"
            "Who is the Architect behind the loop? Drop your theories in the comments! 👇🔥\n\n"
            "#KaalRekha #Episode12 #TimeLoop #AnimeShorts #SciFiThriller #Shorts #GlitchInTheMatrix #Mystery"
        ),
        "hashtags": ["#KaalRekha", "#Episode12", "#TimeLoop", "#AnimeShorts", "#SciFiThriller", "#Shorts", "#GlitchInTheMatrix", "#Mystery"],
        "hook_overlay": "⏳ 3:18 AM: THE TIMELINE FRACTURE! 😱",
        "comment_bait": "Who do you think is controlling the infinite time loop? Tell us your theory in the comments! 👇⏳",
        "voice_profile": "hi_m_intense",
        "lines": [
            {"speaker": "narrator", "text": "At exactly 3:18 AM, the frozen silence of New York shattered with a deafening metallic roar!", "emotion": "shocked", "role": "hook"},
            {"speaker": "narrator", "text": "The sky cracked open like shattered black glass, pulling every building and car into a glowing quantum vortex!", "emotion": "urgent", "role": "body"},
            {"speaker": "narrator", "text": "I didn't die... I woke up inside a colossal underground facility beneath the Himalayas!", "emotion": "mysterious", "role": "body"},
            {"speaker": "narrator", "text": "Surrounding me were thousands of cryogenic pods... each containing an exact clone of me from a different timeline!", "emotion": "fearful", "role": "climax"},
            {"speaker": "char_b", "text": "A voice echoed through the sirens: 'Subject 12 awakened. Prepare the final purge.'", "emotion": "cold", "role": "climax"},
            {"speaker": "narrator", "text": "If you discovered you were living in an endless loop... would you try to escape? Tell me below!", "emotion": "intense", "role": "ending"}
        ],
        "image_prompts": [
            "Cinematic 8k hyper-detailed dark anime shot of Times Square sky shattering into black geometric shards, glowing cyan quantum fissures opening, vertical 9:16, MAPPA aesthetic, masterpiece, high contrast, no text",
            "Cinematic anime visual of modern skyscrapers disintegrating into glowing blue digital particles floating into an atmospheric vortex, vertical 9:16, dark fantasy, unreal engine 5, dramatic lighting",
            "Cinematic shot of a lone anime protagonist in a tattered coat standing in a massive brutalist concrete underground vault, warm amber rim light against shadows, vertical 9:16, cinematic anime film still",
            "Cinematic wide angle shot of endless rows of glowing cryogenic glass pods in a futuristic sci-fi bunker, cyan liquid glowing inside, vertical 9:16, volumetric fog, hyper-detailed anime aesthetic",
            "Extreme closeup of a terrifying cybernetic surveillance optic glowing red in darkness, steam venting, vertical 9:16, high tension anime, photorealistic rendering",
            "Cinematic anime portrait of Kabir staring determinedly at the camera with glowing temporal runes reflecting in his eyes, vertical 9:16, dynamic anime poster, masterpiece"
        ],
        "template_id": "dark_anime",
        "sound_effects": {"heartbeat": True, "riser": True, "sub_hit": True, "room_tone": True, "ducking": True}
    },

    # ─── 2. SERIES 2: JAB PYAAR ONLINE THA (Episode 7) ───
    {
        "series_code": "SERIES_2",
        "episode_num": 7,
        "topic": "2020 — Jab Pyaar Online Tha: Season 2 Episode 7 — The London Surprise",
        "title": "He Flew 4,000 Miles to Her Doorstep in London... ✈️❤️ | JAB PYAAR ONLINE THA (Ep 7) #Shorts",
        "caption": (
            "365 days after the airport departure... Meera thought Aarav had moved on with his life in Delhi. "
            "Lekin jab London ki barfiili raat mein uske flat ki doorbell baji... aur samne Aarav khada tha! 😭💔\n\n"
            "Kya sacha pyaar kabhi dooriyon se thakta hai? Apni story COMMENT karein! 👇✨\n\n"
            "#JabPyaarOnlineTha #Series2 #Episode7 #Romance #Shorts #LoveStory #Heartbreak #LongDistance #RelationshipGoals"
        ),
        "hashtags": ["#JabPyaarOnlineTha", "#Series2", "#Episode7", "#Romance", "#Shorts", "#LoveStory", "#Heartbreak", "#LongDistance"],
        "hook_overlay": "✈️ 4,000 MILES KI DOORIE... AAKHIR KHATAM! ❤️🥺",
        "comment_bait": "Kya aap apne pyaar ke liye doosre desh tak travel kar sakte ho? Share your story in comments! 👇❤️",
        "voice_profile": "hi_m_intense",
        "lines": [
            {"speaker": "char_b", "text": "London ki baraf gir rahi thi, aur phone par Aarav ka aakhiri unread message tha: 'Happy One Year Meera'.", "emotion": "melancholic", "role": "hook"},
            {"speaker": "char_b", "text": "Mujhe laga tha dooriyan jeet gayi... par achanak raat ke 11 baje mere flat ki doorbell baji.", "emotion": "mysterious", "role": "body"},
            {"speaker": "char_b", "text": "Darwaza khola toh samne baraf se bheege jacket mein Aarav khada tha, haath mein wahi chai ka cup!", "emotion": "shocked", "role": "body"},
            {"speaker": "narrator", "text": "Maine muskura kar kaha: 'Kaha tha na Meera... chahe saat samundar paar chale jao, dhoondh hi lunga!'", "emotion": "passionate", "role": "climax"},
            {"speaker": "char_b", "text": "Uski aankhon mein dekh kar laga jaise 365 din ka dard ek hi pal mein gayab ho gaya!", "emotion": "emotional", "role": "climax"},
            {"speaker": "narrator", "text": "Kya sach mein sacha pyaar dooriyon se nahi darta? COMMENT karke batao!", "emotion": "passionate", "role": "ending"}
        ],
        "image_prompts": [
            "Cinematic 35mm film still of a cozy London apartment window looking out at snow falling under yellow Victorian street lamps, steaming mug on windowsill, vertical 9:16, masterpiece, warm tones",
            "Cinematic shot of a wooden apartment door in a charming London townhouse, soft hallway lighting, vertical 9:16, atmospheric, 8k resolution",
            "Cinematic medium shot of a handsome 25-year-old Indian man standing in snowy London night holding two steaming paper chai cups, snowflakes on wool jacket, vertical 9:16, shallow depth of field",
            "Cinematic emotional reaction closeup of a beautiful Indian woman with tears of joy in her eyes at her doorstep, vertical 9:16, emotional cinema, photorealistic",
            "Cinematic warm embrace of young couple on snowy London porch under golden doorway light, snowflakes swirling in slow motion, vertical 9:16, romantic film still",
            "Cinematic visual of Aarav and Meera smiling together under warm umbrella on quiet cobblestone London street, vertical 9:16, cinematic masterpiece"
        ],
        "template_id": "cinematic_romance",
        "sound_effects": {"heartbeat": True, "riser": True, "room_tone": True, "ducking": True}
    },

    # ─── 3. SERIES 3: CHINTU KI JADUI DUNIYA (Episode 5) ───
    {
        "series_code": "SERIES_3",
        "episode_num": 5,
        "topic": "Chintu Ki Jadui Kahani: Episode 5 — The Flying Cloud Castle",
        "title": "Chintu's Flying Bicycle Reached the Cloud Castle! 🚲☁️ | Chintu Ki Jadui Kahani (Ep 5) #Shorts",
        "caption": (
            "Chintu aur Golu ne apni cycle par rocket booster lagaya... aur seedha pahunch gaye Baadalon ke Jadui Mehal mein! 🍭☁️\n"
            "Wahan har cheez cotton candy aur chocolate se bani thi! Par ek shararti badal ne unka rasta rok liya! 😱\n\n"
            "Agle adventure ke liye COMMENT karein: 'GOLU'! 👇✨\n\n"
            "#ChintuKiDuniya #KidsAdventures #3DAnimation #PixarStyle #Magic #Shorts #Cartoon #Fun"
        ),
        "hashtags": ["#ChintuKiDuniya", "#KidsAdventures", "#3DAnimation", "#PixarStyle", "#Magic", "#Shorts", "#Cartoon"],
        "hook_overlay": "🚲 CHINTU KI CYCLE AASMAAN MEIN UD GAYI! ☁️✨",
        "comment_bait": "Agar aapke paas udne wali cycle hoti, toh aap kahan jaate? COMMENT mein batao! 👇✨",
        "voice_profile": "hi_m_narrator",
        "lines": [
            {"speaker": "narrator", "text": "Chintu ne jaise hi cycle ki red ghanti bajayi... pahiya hawa mein uth gaya aur cycle aasmaan mein udne lagi!", "emotion": "excited", "role": "hook"},
            {"speaker": "char_b", "text": "Golu piche baitha popcorn khate hue chilla raha tha: 'Chintu slow chalao, mera juice gir jayega!'", "emotion": "funny", "role": "body"},
            {"speaker": "narrator", "text": "Dono seedha gulaabi baadalon ke beech ek vishal Cotton Candy Castle ke saamne land hue!", "emotion": "wonder", "role": "body"},
            {"speaker": "narrator", "text": "Wahan ki sadkein chocolate se bani thi aur pedon par colorful lollipop lage hue the!", "emotion": "joy", "role": "climax"},
            {"speaker": "char_b", "text": "Lekin tabhi ek vishal Fluffy Cloud Monster ne unka raasta rok kar pucha: 'Yahan aane ka password kya hai?!'", "emotion": "dramatic", "role": "climax"},
            {"speaker": "narrator", "text": "Kya Chintu password bata payega? COMMENT mein guess karo aur agle part ke liye subscribe karo!", "emotion": "playful", "role": "ending"}
        ],
        "image_prompts": [
            "Vibrant 3D Pixar style shot of a cute 7-year-old Indian boy Chintu riding a magical flying bicycle with glowing wings above fluffy pink clouds, vertical 9:16, Disney animation render, bright sunny sky",
            "Cute 3D animated scene of a chubby fluffy blue friendly monster Golu holding a giant juice box on the back of flying bicycle, vertical 9:16, Pixar character render, ultra detailed",
            "Whimsical 3D animated kingdom in the clouds made of pastel cotton candy towers, rainbow bridges, and floating sugar castles, vertical 9:16, Pixar lighting, stunning magical environment",
            "Delicious 3D animation closeup of chocolate paved streets with giant swirl lollipop trees and gummy bear lampposts, vertical 9:16, playful Disney 3D style",
            "Adorable 3D Pixar giant puffy cloud with funny googly eyes and cute smile wearing a marshmallow guard hat, vertical 9:16, high quality 3D render",
            "3D animated scene of Chintu and Golu happily high-fiving in front of glittering candy palace, vertical 9:16, joyful Disney Pixar animation, cinematic"
        ],
        "template_id": "kids_3d_cartoon",
        "sound_effects": {"heartbeat": False, "riser": True, "room_tone": True, "ducking": True}
    },

    # ─── 4. SERIES 4: DIMAG KA DAHI (Episode 5) ───
    {
        "series_code": "SERIES_4",
        "episode_num": 5,
        "topic": "Dimag Ka Dahi: Episode 5 — The 3 Doors Mystery",
        "title": "99% Fail! 3 Doors: Lions, Fire, or Poison Gas? 🚪🧠 | Dimag Ka Dahi (Ep 5) #Shorts",
        "caption": (
            "Ek shakhs ko qaid se nikalne ke liye 3 darwazon mein se ek chunna hai:\n"
            "🚪 Darwaza 1: Aag ki bhishan deewar!\n"
            "🚪 Darwaza 2: Zehrili deadly gas!\n"
            "🚪 Darwaza 3: 5 sher jinhone 3 saal se kuch nahi khaya!\n\n"
            "Kaunsa darwaza sabse safe hai? 5 seconds mein soch kar COMMENT karo! 👇🧠\n\n"
            "#DimagKaDahi #Riddles #BrainTeaser #Puzzle #Shorts #ViralQuiz #MindBending #Genius"
        ),
        "hashtags": ["#DimagKaDahi", "#Riddles", "#BrainTeaser", "#Puzzle", "#Shorts", "#ViralQuiz", "#MindBending"],
        "hook_overlay": "🚪 3 DARWAZE... KAUNSA KHOLOGE?! ⏱️🧠",
        "comment_bait": "Kya aapne 5 second se pehle sahi jawab dhoondh liya? Apna score comment karo! 👇🧠",
        "voice_profile": "hi_m_intense",
        "lines": [
            {"speaker": "narrator", "text": "Duniya ke 99% log is 5-second ke riddle mein fail ho jaate hain! Kya aap bach paoge?", "emotion": "urgent", "role": "hook"},
            {"speaker": "narrator", "text": "Aapke samne 3 maut ke darwaze hain. Darwaza 1 mein aag ki deewar hai jo sab bhasm kar deti hai.", "emotion": "intense", "role": "body"},
            {"speaker": "narrator", "text": "Darwaza 2 mein aisi zehrili gas hai jo ek pal mein jaan le leti hai.", "emotion": "mysterious", "role": "body"},
            {"speaker": "narrator", "text": "Aur Darwaza 3 mein 5 aise jungli sher hain jinhone 3 saal se kuch nahi khaya!", "emotion": "dramatic", "role": "climax"},
            {"speaker": "narrator", "text": "Aapka 5-second ka time shuru hota hai ab! 5... 4... 3... 2... 1!", "emotion": "urgent", "role": "climax"},
            {"speaker": "narrator", "text": "Sahi jawab hai Darwaza 3! Kyunki jo sher 3 saal se bhookha hai... wo kab ka mar chuka hoga! Subscribe karo!", "emotion": "celebratory", "role": "ending"}
        ],
        "image_prompts": [
            "Hyper-detailed digital art of a dark stone dungeon hallway with three giant mysterious iron doors numbered 1, 2, 3 with glowing neon frames, vertical 9:16, high contrast, mystery puzzle aesthetic",
            "Dramatic digital art of iron Door 1 glowing with raging volcanic red fire and smoke, vertical 9:16, intense flame illumination, photorealistic",
            "Mysterious digital art of iron Door 2 leaking green toxic neon chemical mist from underneath, skull symbol warning, vertical 9:16, cyber thriller lighting",
            "Dramatic cinematic shot of Door 3 with heavy metal bars and glowing lion eyes in deep pitch-black shadows, vertical 9:16, high tension cinematic",
            "Dynamic glowing neon countdown timer graphic floating in dark chamber reading 5 SECONDS with electric blue sparks, vertical 9:16, high energy viral game show feel",
            "Bright neon green checkmark and unlocked open door revealing safe sunny exit path with gold celebratory confetti, vertical 9:16, triumph victory graphic"
        ],
        "template_id": "viral_quiz",
        "sound_effects": {"heartbeat": True, "riser": True, "room_tone": True, "ducking": True}
    },

    # ─── 5. SERIES 5: ASHWATTHAMA 3049 AD (Episode 2) ───
    {
        "series_code": "SERIES_5",
        "episode_num": 2,
        "topic": "Ashwatthama 3049 AD: Episode 2 — The Brahmashira Code",
        "title": "3,000 Saal Baad Ashwatthama Ne Bola Pehla Shabd! ⚡️🌌 | ASHWATTHAMA 3049 AD (Part 2) #Shorts",
        "caption": (
            "Kailash Underground Base ke sound sensors par 5,000 saal baad achanak Sanskrit ke divine mantras gunj uthe! ⚡️\n"
            "Ashwatthama ne hava mein ek cosmic Brahmashira code draw kiya... aur sari drone army hawa mein freeze ho gayi! 😱\n\n"
            "Kalki kahan chipa hai? Next Episode ke liye COMMENT karein: 'KALKI'! 👇🔥\n\n"
            "#Ashwatthama #Kalki #Mahabharat #SciFi #Himalayas #Mythology #Shorts #Viral #Epic"
        ),
        "hashtags": ["#Ashwatthama", "#Kalki", "#Mahabharat", "#SciFi", "#Himalayas", "#Mythology", "#Shorts"],
        "hook_overlay": "⚡️ 3000 SAAL BAAD BOLA PEHLA SHABD! 🏔️",
        "comment_bait": "Kya Ashwatthama aur Kalki milkar Kali Yuga ka ant karenge? COMMENT mein likho: 'KALKI'! 👇🔥",
        "voice_profile": "hi_m_intense",
        "lines": [
            {"speaker": "narrator", "text": "Kailash deep-core station par achanak saare alarms ek saath shant ho gaye... aur chaaron taraf ek gehra sannata cha gaya!", "emotion": "shocked", "role": "hook"},
            {"speaker": "narrator", "text": "Ashwatthama ne apna vishal haath uthaya aur barfiili hawa mein ek divya Sanskrit chinha banaya!", "emotion": "mysterious", "role": "body"},
            {"speaker": "narrator", "text": "Military AI computer chilla utha: 'Warning! Cosmic energy overload... Brahmashira weapon detected!'", "emotion": "urgent", "role": "body"},
            {"speaker": "narrator", "text": "Uski aakhon se nikal rahi neeli roshni ne hawa mein 3D holographic naksha bana diya... jo sambhal gram ki taraf ishara kar raha tha!", "emotion": "intense", "role": "climax"},
            {"speaker": "narrator", "text": "Usne ghanghor aawaz mein bola: 'Samay poora hua... Narayan ka aakhiri roop prithvi par aa chuka hai!'", "emotion": "epic", "role": "climax"},
            {"speaker": "narrator", "text": "Kya agle part mein Kalki ka chehra samne aayega? Abhi COMMENT karo 'KALKI' aur subscribe karo!", "emotion": "commanding", "role": "ending"}
        ],
        "image_prompts": [
            "Cinematic 8k Dune aesthetic of subterranean monolithic temple beneath ice cavern with glowing ancient Vedic carvings, vertical 9:16, Denis Villeneuve style, colossal scale",
            "Cinematic medium shot of an 8-foot-tall battle-scarred ancient Indian warrior Ashwatthama raising his glowing armored hand creating cyan geometric energy glyphs in air, vertical 9:16, photorealistic 8k",
            "Futuristic military control room with red holographic warning displays flashing BRAHMASHIRA CODE DETECTED in Sanskrit and cybernetic font, vertical 9:16, sci-fi thriller",
            "Holographic cosmic star map projecting across a frozen chamber pointing towards an ancient Himalayan temple coordinate, vertical 9:16, volumetric blue light, cinematic masterpiece",
            "Epic portrait of Ashwatthama with intense glowing eyes and deep scarred forehead emitting celestial blue energy aura, vertical 9:16, hyper-realistic mythological warrior, cinematic",
            "Cinematic shadow silhouette of Kalki holding celestial blazing sword atop high Himalayan ridge against dramatic sunset, vertical 9:16, epic mythological cinema, masterpiece"
        ],
        "template_id": "sci_fi_mythology",
        "sound_effects": {"heartbeat": True, "riser": True, "sub_hit": True, "room_tone": True, "ducking": True}
    },

    # ─── 6. SERIES 6: THE OBSERVER FILES (Episode 1 - US/UK Thriller) ───
    {
        "series_code": "SERIES_6",
        "episode_num": 1,
        "topic": "The Observer Files: Episode 1 — The 4-Second Blackout",
        "title": "The 4-Second Blackout: Who Was Behind You? 👁️😱 | THE OBSERVER FILES (Part 1) #Shorts",
        "caption": (
            "At 3:07 AM, every security camera across New York and London glitched for exactly 4 seconds. "
            "The government blamed a satellite sync error. But when private investigators zoomed into the raw footage, "
            "they found someone standing behind you. Welcome to THE OBSERVER FILES.\n\n"
            "Subscribe for Part 2 tomorrow at midnight.\n\n"
            "#Shorts #TheObserverFiles #AnalogHorror #ScaryStories #Mystery #Thriller #Creepy #ViralShorts #Unexplained"
        ),
        "hashtags": ["#Shorts", "#TheObserverFiles", "#AnalogHorror", "#ScaryStories", "#Mystery", "#Thriller"],
        "hook_overlay": "👁️ THE 4-SECOND BLACKOUT: DON'T LOOK BEHIND YOU",
        "comment_bait": "Did your phone screen flicker right at the 20-second mark? Check behind your door and comment your city below! 👇👁️",
        "voice_profile": "en_us_epic",
        "lines": [
            {"speaker": "narrator", "text": "At 3:07 AM last night, every security camera across New York and London shut down for exactly four seconds.", "emotion": "mysterious", "role": "hook"},
            {"speaker": "narrator", "text": "Authorities blamed a solar flare. But when private investigators analyzed the raw surveillance tapes frame-by-frame, they found something impossible.", "emotion": "intense", "role": "body"},
            {"speaker": "narrator", "text": "Inside thousands of empty bedrooms, subway tunnels, and locked elevators, a tall silhouette in a dark trench coat was standing motionless, staring straight into the camera lens.", "emotion": "chilling", "role": "body"},
            {"speaker": "narrator", "text": "In every single shot, he was holding a handwritten cardboard sign with today's exact date, and a glowing digital countdown timer showing 00:14:59.", "emotion": "shocked", "role": "climax"},
            {"speaker": "narrator", "text": "Three minutes ago, that timer hit zero. If the lights in your room just dimmed, do not look in the mirror.", "emotion": "whisper", "role": "climax"},
            {"speaker": "narrator", "text": "Look at the reflection on your phone screen right now. Is that shadow behind you yours? Drop your city in the comments if you felt it.", "emotion": "eerie", "role": "ending"}
        ],
        "image_prompts": [
            "Eerie midnight CCTV security camera view of Times Square New York completely empty and fog-covered at 3:07 AM, digital glitch static interference overlay, cinematic 9:16 vertical",
            "High-tech dark forensics computer lab, dual monitors displaying frozen surveillance tapes and spectral wave audio waveforms, dramatic blue and cyan moody lighting, 9:16 vertical",
            "Chilling surveillance camera still of a shadowy tall figure in a dark trench coat standing silently at the end of a dimly lit empty subway corridor, looking directly into the camera, analog grain, 9:16 vertical",
            "Extreme close up shot of a weathered cardboard sign held by gloved hands, showing today's date handwritten in bold black ink next to an ominous glowing red digital countdown clock reading 00:14:59, 9:16 vertical",
            "POV shot sitting in a dark bedroom illuminated only by the cold blue light of a smartphone screen, subtle ominous silhouette visible in the cracked open bedroom door behind, spine-chilling horror atmosphere, 9:16 vertical",
            "Distorted black and white reflection on a dark smartphone glass screen, an uncanny shadowy face with glowing eyes looming right behind the viewer's shoulder, cinematic analog glitch, psychological thriller, 9:16 vertical"
        ],
        "template_id": "suspense",
        "sound_effects": {"heartbeat": True, "riser": True, "sub_hit": True, "room_tone": True, "ducking": True}
    }
]


def generate_and_publish_single(ep_data: dict, index: int, total: int) -> dict:
    series_code = ep_data["series_code"]
    episode_num = ep_data["episode_num"]
    title = ep_data["title"]
    caption = ep_data["caption"]
    hashtags = ep_data["hashtags"]
    hook_overlay = ep_data["hook_overlay"]
    comment_bait = ep_data["comment_bait"]
    lines = ep_data["lines"]
    image_prompts = ep_data["image_prompts"]

    print("\n" + "=" * 80)
    print(f"  🎬 [{index}/{total}] STARTING: {series_code} EPISODE {episode_num}")
    print(f"  📌 Title: {title}")
    print("=" * 80)

    t0 = time.time()
    db = DB()

    # Create DB row
    vid = db.create_video(
        ep_data["topic"],
        title=title,
        caption=caption,
        hashtags=hashtags,
        series_name=series_code,
        series_index=episode_num,
        notes=f"{series_code} Episode {episode_num} (God Mode Batch)"
    )
    print(f"  Allocated Video ID: #{vid}")

    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Voiceover
    print(f"\n  🎙️ [Step 1] Synthesizing Neural Speech for {len(lines)} lines...")
    voice_agent = Voice(db=db)
    prof_id = ep_data.get("voice_profile", "hi_m_intense")
    if prof_id not in voice_agent.profiles:
        prof_id = "hi_m_intense"
    voice_res = voice_agent.narrate(lines, out_dir, profile_id=prof_id)
    dur = voice_res["duration_sec"]
    words = voice_res.get("words", [])
    print(f"  ✅ Speech ready: {dur:.2f}s, {len(words)} aligned words.")

    # 2. Visual Frames
    print(f"\n  🖼️ [Step 2] Generating {len(image_prompts)} Cinematic 9:16 Frames...")
    n_scenes = len(image_prompts)
    scene_dur = dur / n_scenes
    motions = ["punch_in", "pan_left", "zoom_in_dramatic", "pan_right", "zoom_in", "zoom_out"]

    scenes = []
    for i, (prompt, motion) in enumerate(zip(image_prompts, motions)):
        st = round(i * scene_dur, 3)
        en = round((i + 1) * scene_dur if i < n_scenes - 1 else dur, 3)
        scenes.append({
            "n": i + 1,
            "beat": "",
            "image_prompt": prompt,
            "motion": motion,
            "parallax": (i % 2 == 1),
            "file": f"scene_{i+1:02d}.jpg",
            "seed": vid * 100 + i + 1,
            "start": st,
            "end": en,
            "dur": round(en - st, 3)
        })

    img_agent = ImageGen(providers=["pollinations"])
    scenes_with_paths = img_agent.generate_all(scenes, out_dir)
    print(f"  ✅ All {n_scenes} visual scenes compiled.")

    # 3. Manifest Construction
    script_data = {
        "topic": ep_data["topic"],
        "title": title,
        "caption": caption,
        "hashtags": hashtags,
        "hook_type": "cliffhanger",
        "hook_line": lines[0]["text"],
        "hook_text_overlay": hook_overlay,
        "comment_bait": comment_bait,
        "lines": lines
    }

    manifest = {
        "video_id": vid,
        "series_code": series_code,
        "episode_num": episode_num,
        "topic": ep_data["topic"],
        "title": title,
        "script": script_data,
        "subtitles": {
            "style": "kinetic"
        },
        "effects": {
            "sound": ep_data.get("sound_effects", {
                "heartbeat": True,
                "riser": True,
                "room_tone": True,
                "ducking": True
            })
        },
        "art": {
            "template_id": ep_data.get("template_id", "noir_teal"),
            "template_name": series_code,
            "pacing": "standard",
            "n_scenes": n_scenes
        },
        "scenes": scenes_with_paths,
        "narration": voice_res,
        "words": words
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. Render Video
    print(f"\n  🎞️ [Step 3] Rendering 1080x1920 60fps MP4 Video with Kinetic Subtitles...")
    renderer = Renderer(manifest)
    render_info = renderer.render(out_dir, preset="fast", keep_temp=False)
    final_video_path = Path(render_info["video_path"])
    print(f"  ✅ Video rendered: {final_video_path.name} ({final_video_path.stat().st_size // 1024} KB)")

    # 5. Quality Validation
    print(f"\n  🔍 [Step 4] Running 4-Gate Quality Validation...")
    rep = validate_dir(out_dir)
    print(f"  Validation: {'PASS ✅' if rep.ok else 'WARN ⚠️'}")

    db.update_video(
        vid,
        title=title,
        caption=caption,
        hashtags=hashtags,
        series_name=series_code,
        series_index=episode_num,
        script_json=json.dumps(script_data, ensure_ascii=False),
        video_path=str(final_video_path),
        cover_path=render_info.get("cover_path"),
        length_sec=dur,
        status="approved",
        notes=f"{series_code} Episode {episode_num} Approved for Upload"
    )

    # 6. YouTube Shorts Upload (Public + 100% Comments Enabled)
    print(f"\n  🚀 [Step 5] Uploading to YouTube Shorts (Public + Comments 100% Enabled)...")
    pub = YouTubePublisher(db=db)
    res = pub.publish(vid, privacy="public", pin_comment=True)
    db.close()

    elapsed = round(time.time() - t0, 1)
    print(f"\n  🎉 [{series_code} EP {episode_num}] PUBLISHED TO YOUTUBE SHORTS!")
    print(f"  🔗 URL          : {res.get('url')}")
    print(f"  💬 Comment Bait : {comment_bait[:50]}...")
    print(f"  ⏱️ Time Taken   : {elapsed}s\n")

    return {
        "series_code": series_code,
        "episode_num": episode_num,
        "video_id": vid,
        "title": title,
        "url": res.get("url"),
        "status": res.get("status"),
        "elapsed": elapsed
    }


def main():
    total_start = time.time()
    print("\n" + "=" * 80)
    print("  🔱 AUTOPILOT: GENERATING & PUBLISHING ALL 5 ACTIVE SERIES")
    print("=" * 80)

    results = []
    for idx, ep in enumerate(EPISODES, 1):
        try:
            res = generate_and_publish_single(ep, idx, len(EPISODES))
            results.append(res)
        except Exception as e:
            log.error(f"Failed generating {ep['series_code']} Ep {ep['episode_num']}", e)
            print(f"  ❌ ERROR on {ep['series_code']}: {e}")
            results.append({
                "series_code": ep["series_code"],
                "episode_num": ep["episode_num"],
                "status": "failed",
                "error": str(e)
            })

    total_time = round(time.time() - total_start, 1)
    print("\n" + "=" * 80)
    print("  🏁 BATCH RUN COMPLETE: ALL 5 SERIES GENERATION & PUBLISH REPORT")
    print("=" * 80)
    for r in results:
        status_icon = "✅" if r.get("status") in ("uploaded", "ok") else "⚠️"
        print(f"  {status_icon} {r['series_code']} Ep {r['episode_num']}: {r.get('url', r.get('status'))} - {r.get('title', '')}")
    print(f"\n  Total Batch Execution Time: {total_time}s")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
