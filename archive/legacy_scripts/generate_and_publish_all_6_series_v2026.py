#!/usr/bin/env python3
"""
generate_and_publish_all_6_series_v2026.py — End-to-End Generator & Publisher for All 6 Series.
Incorporating 2026 YouTube Shorts Algorithm Viral Shortcuts:
  1. Cold-Open Hook (< 1.5s, 0% fluff, massive curiosity gap)
  2. Seamless Infinity Loop (Ending sentence connects seamlessly into Opening sentence)
  3. High-CTR Dual Captions & Dynamic Visual Movement
  4. Pinned Comment Bait (Engagement multiplier)
  5. Mandatory Policy Constraints: selfDeclaredMadeForKids=False, comments ALWAYS 100% enabled.

Episodes:
  1. Series 1: Kaal-Rekha (Part 13) — "The Clone Protocol"
  2. Series 2: Jab Pyaar Online Tha (Season 2 Episode 8) — "The 24-Hour London Promise"
  3. Series 3: Chintu Ki Jadui Kahani (Episode 6) — "The Crystal Rainbow Bridge"
  4. Series 4: Dimag Ka Dahi Riddles (Episode 6) — "The Reverse Clock Paradox"
  5. Series 5: Ashwatthama 3049 AD (Episode 3) — "The Celestial Wrath of the Astra"
  6. Series 6: The Observer Files (Episode 2) — "The Red Mirror Lag"
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

log = Logbook("all_6_series_v2026")

EPISODES = [
    # ─── 1. SERIES 1: KAAL-REKHA (Part 13) ───
    {
        "series_code": "SERIES_1",
        "episode_num": 13,
        "topic": "Kaal-Rekha Part 13: The Clone Protocol (Pod Zero)",
        "title": "I Found Myself Trapped in Pod Zero! ⏳😱 | KAAL-REKHA (Part 13) #Shorts",
        "caption": (
            "Inside the subterranean Himalayan facility, Kabir discovered thousands of cryo-pods with his own clones. "
            "Lekin jab usne Pod Zero ka frosted glass saaf kiya... uske hosh udd gaye! ⏳⚡\n\n"
            "Kya Kabir hi is loop ka creator hai? Drop your theories in the comments! 👇🔥\n\n"
            "#KaalRekha #Episode13 #TimeLoop #AnimeShorts #SciFiThriller #Shorts #GlitchInTheMatrix #Mystery"
        ),
        "hashtags": ["#KaalRekha", "#Episode13", "#TimeLoop", "#AnimeShorts", "#SciFiThriller", "#Shorts", "#GlitchInTheMatrix", "#Mystery"],
        "hook_overlay": "⏳ 3:18 AM: CLONE POD ZERO OPENED! 😱",
        "comment_bait": "Agar aapko pata chale ki aap kisi infinite loop ka clone number 13 hain, to aap pehla kadam kya uthayenge? Drop your answer! 👇⏳",
        "voice_profile": "hi_m_intense",
        "lines": [
            {"speaker": "narrator", "text": "Himalaya ke neeche bani secret lab mein hazaron cryo-pods ke beech, mera dimaag sunn ho gaya!", "emotion": "shocked", "role": "hook"},
            {"speaker": "narrator", "text": "Har ek pod par mera chehra tha, par sabse aage ek black glass pod tha jisme likha tha Pod Zero!", "emotion": "urgent", "role": "body"},
            {"speaker": "narrator", "text": "Maine jaise hi us glass ko haath lagaya, pod ka door khula aur andar se nikla ek diary jisme meri hi handwriting thi!", "emotion": "mysterious", "role": "body"},
            {"speaker": "narrator", "text": "Pehle page par likha tha: Agar tum ye padh rahe ho, to tum teetarve clone ho aur pichle baarah mar chuke hain!", "emotion": "fearful", "role": "climax"},
            {"speaker": "char_b", "text": "Tabbhi poori lab mein red emergency siren goonj utha: 'Protocol Thirteen activated. Eliminate all evidence!'", "emotion": "cold", "role": "climax"},
            {"speaker": "narrator", "text": "Aur is poore loop ko khatam karne ka sirf ek raasta tha jo shuru hota hai...", "emotion": "intense", "role": "ending"}
        ],
        "image_prompts": [
            "Cinematic 8k hyper-detailed dark anime shot of Kabir walking through a subterranean brutalist concrete chamber filled with endless glowing cyan cryogenic pods, vertical 9:16, high contrast, MAPPA aesthetic, no text",
            "Cinematic anime visual of a massive obsidian black cryogenic chamber glowing with ominous crimson runes, Pod Zero marked on plate, dramatic volumetric fog, vertical 9:16",
            "Close-up anime shot of Kabir's trembling hand wiping frost off glass, glowing biometric interface illuminating his shocked eyes, vertical 9:16, cinematic anime lighting",
            "Cinematic dramatic shot of a weathered leather diary glowing with temporal blue dust, pages filled with handwritten temporal equations and countdown timers, vertical 9:16",
            "Terrifying anime scene of red emergency warning lights spinning in massive industrial ceiling, armed cybernetic sentries mobilizing in shadows, vertical 9:16",
            "Dynamic cinematic anime portrait of Kabir clutching the diary with glowing temporal aura igniting around his body, determined fierce gaze, vertical 9:16, masterpiece"
        ],
        "template_id": "dark_anime",
        "sound_effects": {"heartbeat": True, "riser": True, "sub_hit": True, "room_tone": True, "ducking": True}
    },

    # ─── 2. SERIES 2: JAB PYAAR ONLINE THA (Season 2 Episode 8) ───
    {
        "series_code": "SERIES_2",
        "episode_num": 8,
        "topic": "2020 — Jab Pyaar Online Tha: Season 2 Episode 8 — The 24-Hour London Promise",
        "title": "24 Hours in London to Save 3 Years of Love... ✈️❤️ | JAB PYAAR ONLINE THA (S2 Ep 8) #Shorts",
        "caption": (
            "Aarav London pahunch to gaya, lekin uske paas sirf 24 ghante the. "
            "London ki barf aur thand mein do toote hue dilon ki aakhiri koshish! 😭💔\n\n"
            "Kya saccha pyaar waqt aur doori dono ko hara sakta hai? Comment mein dil drop karein! ❤️👇\n\n"
            "#JabPyaarOnlineTha #Episode8 #RomanticDrama #LoveStory #EmotionalShorts #Shorts #Heartbreak #CoupleGoals"
        ),
        "hashtags": ["#JabPyaarOnlineTha", "#Episode8", "#RomanticDrama", "#LoveStory", "#EmotionalShorts", "#Shorts", "#Heartbreak", "#CoupleGoals"],
        "hook_overlay": "✈️ 24 HOURS LEFT IN LONDON! 💔",
        "comment_bait": "Kya aap apne pyaar ke liye bina bataye 4,000 miles travel kar sakte hain? Dil se 'Yes' ya 'No' comment karein! ❤️👇",
        "voice_profile": "hi_m_narrator",
        "lines": [
            {"speaker": "narrator", "text": "Meera ki aankhon mein aansu the jab usne London ki barf mein Aarav ko samne khada dekha!", "emotion": "emotional", "role": "hook"},
            {"speaker": "narrator", "text": "Aarav ne muskurate hue kaha: 'Mujhe pata hai mera visa sirf chaubees ghante ka hai, par main bina gale lagaye nahi ja sakta tha!'", "emotion": "warm", "role": "body"},
            {"speaker": "narrator", "text": "Woh poori raat dono London Bridge par haath pakad kar chale, jaise teen saal ki doori ek pal mein mit gayi ho!", "emotion": "romantic", "role": "body"},
            {"speaker": "narrator", "text": "Subah ke paanch baje, Heathrow airport ki announcement ne unka sapna tod diya: 'Final boarding call for Delhi!'", "emotion": "sorrow", "role": "climax"},
            {"speaker": "char_a", "text": "Meera ne uska haath kas ke pakadte hue kaha: 'Agar tum is baar wapas gaye... to main hamesha ke liye akele reh jaungi.'", "emotion": "crying", "role": "climax"},
            {"speaker": "narrator", "text": "Aur us aakhiri alvida ki shuruat hoti hai usi pehli mulaqat se...", "emotion": "deep", "role": "ending"}
        ],
        "image_prompts": [
            "Emotional cinematic shot of young Indian boy standing in falling snow outside cozy London brick townhouse, warm yellow porch light, vertical 9:16, shallow depth of field, 8k romance movie still",
            "Close up of Indian girl's teary emotional eyes reflecting soft London winter streetlights, breath condensing in cold air, cinematic color grading, vertical 9:16",
            "Romantic wide angle cinematic silhouette of young couple walking hand in hand across snow-dusted Tower Bridge at night, glowing city lights, vertical 9:16",
            "Cinematic airport departure terminal at dawn, rainy window overlooking aircraft tarmac, vintage moody romantic tone, vertical 9:16",
            "Tender close-up of two hands gently holding fingers together at airport security gate, blurred travelers in background, photorealistic emotional realism, vertical 9:16",
            "Cinematic parting glance of Aarav looking back with a determined loving smile through airport departure gate, warm amber rim lighting, vertical 9:16"
        ],
        "template_id": "warm_editorial",
        "sound_effects": {"heartbeat": True, "riser": True, "room_tone": True, "ducking": True}
    },

    # ─── 3. SERIES 3: CHINTU KI JADUI KAHANI (Episode 6) ───
    {
        "series_code": "SERIES_3",
        "episode_num": 6,
        "topic": "Chintu Ki Jadui Kahani: Episode 6 — The Crystal Rainbow Bridge",
        "title": "Chintu Aur Sunehra Dragon! 🌈🐉 | CHINTU KI JADUI DUNIYA (Ep 6) #Shorts",
        "caption": (
            "Chintu aur Golu jaise hi badalon ke aage badhe, unhe mila chamakta hua Crystal Rainbow Bridge! "
            "Lekin us bridge ko paar karne ke liye ek sunehre dragon ne pucha ek mazedaar jadui sawal! ☁️✨\n\n"
            "Kya aapko pata hai dragon ka password? Comment mein batao! 👇🎉\n\n"
            "#ChintuKiJaduiDuniya #KidsStories #AnimationShorts #MagicalAdventures #CartoonKids #Shorts #FunRiddles"
        ),
        "hashtags": ["#ChintuKiJaduiDuniya", "#KidsStories", "#AnimationShorts", "#MagicalAdventures", "#CartoonKids", "#Shorts", "#FunRiddles"],
        "hook_overlay": "🌈 SUNEHRA DRAGON AUR JADUI PUL! 🐉✨",
        "comment_bait": "Agar aapko badalon par udne wala ek chhota dragon mile, to aap uska kya naam rakhenge? Comment karo! 🐉✨",
        "voice_profile": "hi_f_calm",
        "lines": [
            {"speaker": "narrator", "text": "Chintu aur Golu ne jaise hi badal par kadam rakha, aasmaan se ek chamakta hua indradhanushi pul nikal aaya!", "emotion": "excited", "role": "hook"},
            {"speaker": "narrator", "text": "Pul ke beech mein khada tha ek nanha sunehra dragon jiske pankh heere jaise chamak rahe the!", "emotion": "playful", "role": "body"},
            {"speaker": "char_b", "text": "Dragon ne meethi aawaz mein kaha: 'Is pul ko wahi paar karega jo aisi cheez bataye jo baantne se hamesha badhti hai!'", "emotion": "mysterious", "role": "body"},
            {"speaker": "narrator", "text": "Golu ne socha pizza... par Chintu ne jhat se bola: 'Khushi aur Muskaan!'", "emotion": "happy", "role": "climax"},
            {"speaker": "narrator", "text": "Dragon khush hokar aasmaan mein udne laga aur poore badal par rang-birangi toffees ki baarish ho gayi!", "emotion": "cheerful", "role": "climax"},
            {"speaker": "narrator", "text": "Aur dosto, aisi hi jadui kahaniyan tab shuru hoti hain jab...", "emotion": "warm", "role": "ending"}
        ],
        "image_prompts": [
            "Pixar 3D style cute animated shot of young Indian boy Chintu and chubby friend Golu walking onto glowing soft cloud bridge, magical sparkle dust, vibrant saturated colors, 9:16 vertical",
            "Adorable 3D Pixar animated golden baby dragon with sparkling diamond wings sitting on a crystal rainbow slide, big expressive friendly eyes, vertical 9:16",
            "Whimsical fantasy sky kingdom with floating cotton candy clouds, candy castles, pastel rainbow bridge stretching into horizon, ultra high detail 3D render, vertical 9:16",
            "Close up of Chintu smiling brightly pointing his finger with a glowing lightbulb idea above his head, Pixar animation style, vertical 9:16",
            "Spectacular colorful animated shower of sparkling rainbow candies and glowing stars falling through fluffy pink clouds, vibrant joyful celebration, vertical 9:16",
            "Chintu, Golu, and the baby golden dragon cheering together flying over dreamland clouds, warm sunny golden hour, 3D animated movie still, vertical 9:16"
        ],
        "template_id": "kids_adventure",
        "sound_effects": {"riser": True, "room_tone": True, "ducking": True}
    },

    # ─── 4. SERIES 4: DIMAG KA DAHI RIDDLES (Episode 6) ───
    {
        "series_code": "SERIES_4",
        "episode_num": 6,
        "topic": "Dimag Ka Dahi: Episode 6 — The Reverse Clock Paradox",
        "title": "Sirf 1% Genius Is Ghadi Ka Jawab De Payenge! 🧠⏱️ | DIMAG KA DAHI (Ep 6) #Shorts",
        "caption": (
            "Ek aisi purani jadui ghadi jo sirf tab ulti chalti hai jab koi jhoot bolta hai! "
            "Aapke paas hain sirf 5 second is dhasu riddle ka jawab dene ke liye! 🧠🔥\n\n"
            "Apna jawab comment mein likhein aur dekhein kiska IQ 140+ hai! 👇\n\n"
            "#DimagKaDahi #Paheliyan #BrainTeaser #Riddles #HindiPaheliyan #IQTest #Shorts #MindGames #ViralQuiz"
        ),
        "hashtags": ["#DimagKaDahi", "#Paheliyan", "#BrainTeaser", "#Riddles", "#HindiPaheliyan", "#IQTest", "#Shorts", "#MindGames", "#ViralQuiz"],
        "hook_overlay": "🧠 99% FAIL: REVERSE CLOCK RIDDLE! ⏱️",
        "comment_bait": "Kya aapne 5 second khatam hone se pehle sahi jawab dhoond liya tha? Apna answer comment mein likhein! 🧠💡",
        "voice_profile": "hi_m_narrator",
        "lines": [
            {"speaker": "narrator", "text": "Ek aisi ajeeb ghadi jo sirf tab ulti chalti hai jab koi jhoot bolta hai—aur 99% log is paheli mein haar gaye!", "emotion": "challenging", "role": "hook"},
            {"speaker": "narrator", "text": "Ek kamre mein teen ghadiyan thi: ek 10 baje par, doosri 12 par aur teesri 3 par!", "emotion": "urgent", "role": "body"},
            {"speaker": "narrator", "text": "Jab chor ne kaha 'Maine chori nahi ki', to pehli ghadi do ghante peeche chali gayi!", "emotion": "mysterious", "role": "body"},
            {"speaker": "narrator", "text": "Aapke paas hain paanch second: Agar chor ne teen baar jhoot bola, to ghadi mein kya baje honge?", "emotion": "curious", "role": "climax"},
            {"speaker": "narrator", "text": "Time over! Har jhoot par do ghante peeche, to 10 mein se 6 ghante ghate—sahi jawab hai char baje!", "emotion": "triumphant", "role": "climax"},
            {"speaker": "narrator", "text": "Aur aise dimag hila dene wale sawal wapas aate hain jab...", "emotion": "playful", "role": "ending"}
        ],
        "image_prompts": [
            "Hyper-detailed dark mystery detective study with antique brass grandfather clock whose hands are spinning backwards with blue ethereal light, cinematic 9:16 vertical",
            "Dramatic close-up of three antique pocket watches resting on dark mahogany table showing different glowing times, warm candle lighting, vertical 9:16",
            "Mysterious shadowed silhouette of a suspect in an interrogation room holding a glowing silver antique clock, cinematic high contrast film noir, vertical 9:16",
            "High impact glowing neon 5-second digital countdown hologram pulsing in center of screen with question marks, high tension quiz graphic, vertical 9:16",
            "Vibrant glowing green checkmark reveal over the antique clock face striking exactly 4 o clock with golden sparks, dynamic satisfying reveal, vertical 9:16",
            "Dramatic mystery concept art with human brain made of glowing clockwork brass gears and neon neurons, masterpiece vertical 9:16"
        ],
        "template_id": "quiz_pop",
        "sound_effects": {"heartbeat": True, "riser": True, "sub_hit": True, "ducking": True}
    },

    # ─── 5. SERIES 5: ASHWATTHAMA 3049 AD (Episode 3) ───
    {
        "series_code": "SERIES_5",
        "episode_num": 3,
        "topic": "Ashwatthama 3049 AD: Episode 3 — The Celestial Wrath of the Astra",
        "title": "Immortal Warrior Destroys 31st Century AI Fleet! 🔱⚡ | ASHWATTHAMA 3049 (Ep 3) #Shorts",
        "caption": (
            "Jab 31st century ke rogue AI federation ne Ashwatthama ko orbital lasers se ghera... "
            "unhe laga ki ek 5000 saal purana yoddha mar jayega. Lekin unhone Divya Mani ki asli shakti nahi dekhi thi! 🔱🔥\n\n"
            "Har Har Mahadev! Comment mein apni shradha likhein! 👇🔱\n\n"
            "#Ashwatthama3049 #Episode3 #CyberpunkMythology #IndianSciFi #MahabharatFuturistic #AnimeAction #Shorts #Kalki2898AD"
        ),
        "hashtags": ["#Ashwatthama3049", "#Episode3", "#CyberpunkMythology", "#IndianSciFi", "#MahabharatFuturistic", "#AnimeAction", "#Shorts", "#Kalki2898AD"],
        "hook_overlay": "🔱 5000 YR OLD IMMORTAL VS AI FLEET! ⚡",
        "comment_bait": "Kya prachin divya astra 31st century ke futuristic sci-fi weapons se hazaar guna powerful hain? 'Har Har Mahadev' comment karein! 🔱⚡",
        "voice_profile": "hi_m_intense",
        "lines": [
            {"speaker": "narrator", "text": "Himalaya ke aakash mein jab sau se zyada orbital dreadnoughts ne Ashwatthama ko lock kiya, to prithvi kaanp uthi!", "emotion": "epic", "role": "hook"},
            {"speaker": "narrator", "text": "AI armada ke command centre se aawaz aayi: 'Surrender immortal entity, or face total atomization!'", "emotion": "cold", "role": "body"},
            {"speaker": "narrator", "text": "Lekin Ashwatthama ne bas apni aankhein band ki... aur unke maathe ki Divya Mani surya ki tarah dahak uthi!", "emotion": "mystical", "role": "body"},
            {"speaker": "narrator", "text": "Ek prachin Sanskrit mantra goonjte hi aakash mein neeli bijliyon ka Brahmashira chakra ban gaya!", "emotion": "intense", "role": "climax"},
            {"speaker": "narrator", "text": "Sirf ek second mein saare futuristic dreadnoughts bina aawaz ke cosmic dhool mein badal gaye!", "emotion": "shocked", "role": "climax"},
            {"speaker": "narrator", "text": "Kyunki jab Mahakaal ka aashirwaad activate hota hai...", "emotion": "deep", "role": "ending"}
        ],
        "image_prompts": [
            "Epic cinematic anime shot of a massive fleet of dark cybernetic sci-fi warships hovering menacingly in Himalayan storm clouds, glowing red targeting beams, 9:16 vertical",
            "Low angle imposing anime shot of eight-foot tall Ashwatthama standing on snowy mountain peak, tattered robes blowing in blizzard, glowing crimson gem in forehead, vertical 9:16",
            "Extreme close up of Ashwatthama's forehead divine gem radiating blinding cosmic solar flares and celestial Sanskrit runes, hyper detailed anime masterpiece, vertical 9:16",
            "Breathtaking celestial anime spectacle of gigantic rotating blue lightning Brahmashira mandala chakra ripping through the sky, epic cosmic energy, vertical 9:16",
            "Cataclysmic sci-fi explosion as colossal orbital dreadnought battleships disintegrate into shimmering blue particles and electrical storms across the clouds, vertical 9:16",
            "Majestic anime still of immortal warrior Ashwatthama wielding a celestial trident glowing with ancient divine fire against a starry cosmic void, vertical 9:16"
        ],
        "template_id": "dark_anime",
        "sound_effects": {"heartbeat": True, "riser": True, "sub_hit": True, "room_tone": True, "ducking": True}
    },

    # ─── 6. SERIES 6: THE OBSERVER FILES (Episode 2) ───
    {
        "series_code": "SERIES_6",
        "episode_num": 2,
        "topic": "The Observer Files: Episode 2 — The Red Mirror Lag",
        "title": "Your Mirror Lagged by 2 Seconds at 3:00 AM... 👁️🪞 | THE OBSERVER FILES (Part 2) #Shorts",
        "caption": (
            "At 3:00 AM across Tokyo and London subway restrooms, maintenance workers noticed something chilling. "
            "The mirror reflections weren't syncing with real life—they were moving 2 seconds before the human moved. Welcome to Part 2 of THE OBSERVER FILES.\n\n"
            "Look into your mirror right now. Is it blinking when you blink? Comment your country below! 👇👁️\n\n"
            "#Shorts #TheObserverFiles #AnalogHorror #ScaryStories #Mystery #Thriller #Creepy #ViralShorts #Unexplained"
        ),
        "hashtags": ["#Shorts", "#TheObserverFiles", "#AnalogHorror", "#ScaryStories", "#Mystery", "#Thriller", "#Creepy", "#ViralShorts", "#Unexplained"],
        "hook_overlay": "👁️ 3:00 AM: THE MIRROR LAG PHENOMENON! 🪞",
        "comment_bait": "Have you ever felt your reflection took a microsecond too long to blink? Comment your city below if you've experienced this! 👁️😱",
        "voice_profile": "en_us_epic",
        "lines": [
            {"speaker": "narrator", "text": "If you wake up at 3:00 AM tonight, do not look into your bathroom mirror under any circumstance!", "emotion": "urgent", "role": "hook"},
            {"speaker": "narrator", "text": "At 3:00 AM last night, security cameras inside three international airports recorded a glitch that physics cannot explain.", "emotion": "mysterious", "role": "body"},
            {"speaker": "narrator", "text": "When travelers washed their hands, their mirror reflections were moving two full seconds ahead of them.", "emotion": "fearful", "role": "body"},
            {"speaker": "narrator", "text": "In frame forty-two, a man walked away from the sink, but his reflection remained standing still, smiling directly into the glass.", "emotion": "chilling", "role": "climax"},
            {"speaker": "narrator", "text": "Forensic audio extracted a faint whisper from the microphone: 'We are done waiting on this side.'", "emotion": "whisper", "role": "climax"},
            {"speaker": "narrator", "text": "And the chilling truth about what lives on the other side begins when...", "emotion": "cold", "role": "ending"}
        ],
        "image_prompts": [
            "Chilling cinematic analog horror shot looking at a dimly lit bathroom mirror at 3:00 AM, cold fluorescent flickering lights, uncanny atmosphere, vertical 9:16",
            "Grainy surveillance CCTV camera timestamped 03:00:02 AM showing an empty modern airport restroom with fogged mirrors and green emergency signs, vertical 9:16",
            "Spine-tingling psychological thriller shot of a person with back to camera, but their reflection in mirror is unnervingly out of sync with a sinister stare, vertical 9:16",
            "Extreme close up of the reflection's face pressing against the inside of the mirror glass with unnatural subtle grin, distorted analog VHS grain, vertical 9:16",
            "Terrifying visual of subtle crack spreading across bathroom mirror glass with glowing red mist leaking from the seam, cinematic horror still, vertical 9:16",
            "POV looking at dark smartphone screen reflection in pitch black bedroom, subtle shadowy duplicate figure standing right behind head, vertical 9:16"
        ],
        "template_id": "suspense",
        "sound_effects": {"heartbeat": True, "riser": True, "room_tone": True, "ducking": True}
    }
]


def process_episode(ep_data: dict, idx: int, total: int) -> dict:
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
    print(f"  🎬 [{idx}/{total}] GENERATING & PUBLISHING: {series_code} (Episode {episode_num})")
    print(f"  📌 Title : {title}")
    print(f"  🎯 Hook  : {hook_overlay}")
    print(f"  🔁 Loop  : Infinity Loop Ready")
    print("=" * 80)

    t0 = time.time()
    db = DB()
    vid = db.create_video(
        topic=ep_data["topic"],
        title=title,
        caption=caption,
        hashtags=hashtags,
        series_name=series_code,
        series_index=episode_num,
        notes=f"{series_code} Episode {episode_num} (2026 Viral Algorithm Batch)"
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
            "template_id": ep_data.get("template_id", "dark_anime"),
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
    print("  🔱 AUTOPILOT: GENERATING & PUBLISHING ALL 6 SERIES (2026 VIRAL ALGORITHM)")
    print("=" * 80)

    results = []
    for idx, ep in enumerate(EPISODES, 1):
        try:
            r = process_episode(ep, idx, len(EPISODES))
            results.append(r)
        except Exception as e:
            log.error(f"Failed processing {ep.get('series_code')}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "series_code": ep.get("series_code"),
                "episode_num": ep.get("episode_num"),
                "error": str(e)
            })

    total_time = round(time.time() - total_start, 1)
    print("\n" + "=" * 80)
    print("  🏆 ALL 6 SERIES BATCH PUBLISH COMPLETE REPORT")
    print(f"  ⏱️ Total Batch Duration: {total_time}s")
    print("=" * 80)
    for res in results:
        code = res.get("series_code")
        ep = res.get("episode_num")
        if "url" in res and res["url"]:
            print(f"  ✅ {code} (Ep {ep}) -> {res['url']} ({res.get('elapsed')}s)")
        else:
            print(f"  ❌ {code} (Ep {ep}) -> FAILED: {res.get('error')}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
