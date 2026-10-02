"""
generate_and_publish_next_all_7_series_batch_part5.py — Batch 5 Master Orchestrator for All Active Series.

Generates and Prepares for Upload:
  1. SERIES_1 (Kaal-Rekha)            : Part 22 (3:14 AM Ka Asli Sach! Wo Loop Meera Ne Kyun Banaya?!)
  2. SERIES_2 (Jab Pyaar Online Tha)  : Episode 18 (London Heathrow Par Rohan Ka Achanak Surprise!)
  3. SERIES_3 (Chintu Ki Jadui Duniya): Episode 16 (Jadui Star Key Se Khula Aasmani Badal Ka Qila!)
  4. SERIES_4 (Dimag Ka Dahi)         : Episode 16 (Wo Kya Hai Jiska Koi Rang Nahi, Par Sab Dekh Sakte Hain?)
  5. SERIES_5 (Ashwatthama 3049 AD)   : Episode 13 (Kurukshetra Ka Plasma Brahmastra Space Mein Activate Hua!)
  6. SERIES_6 (The Observer Files)    : Episode 12 (Smart Home Speakers Started Whispering At 3:17 AM...)
  7. SERIES_7 (Roblox Vault)          : Episode 10 (The Secret 2011 Developer Island Under The Map!)
  8. SERIES_8 (Leonardo da Vinci)     : Episode 2  (Verrocchio Ki Workshop Aur Vo Farishta Jisne Guru Ko Hairan Kar Diya!)

POLICY COMPLIANCE (AGENTS.md):
  • Zero Comment Lock Policy: comments ALWAYS 100% ENABLED (ON)
  • selfDeclaredMadeForKids = False (MANDATORY)
  • privacyStatus = "public"
  • Engagement pinned first comment via commentThreads.insert
  • Transformative storytelling with Humanoid AI voiceover & Ken Burns dynamic motion
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import sqlite3
import subprocess
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

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.config import CONFIG
from core.db import DB
from core.ffmpeg import ffmpeg_bin, probe
from core.logbook import Logbook
from agents.voice import _call_gemini_tts, _pcm_to_wav
from agents.imagegen import ImageGen
from agents.publisher import YouTubePublisher
from core.discord_service import DiscordNotifications, COLOR_BRAND, COLOR_SUCCESS

log = Logbook("all_series_batch_part5")

DISCORD_CHANNEL = "1212765278765584396"

# ─────────────────────────────────────────────────────────────────────────────
# EPISODES CATALOG — NEXT EPISODES FOR ALL 8 ACTIVE SERIES (BATCH 5)
# ─────────────────────────────────────────────────────────────────────────────

BATCH_EPISODES = [
    # ─────────────────────────────────────────────────────────────────────────
    # 1. SERIES_1: KAAL-REKHA — PART 22
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_1",
        "episode_num": 22,
        "topic": "Kaal-Rekha Part 22: The Original Disaster at Bandra-Worli & The Chronos Key",
        "title": "3:14 AM Ka Asli Sach! Wo Loop Meera Ne Kyun Banaya?! ⏳💥 | KAAL-REKHA (Part 22) #Shorts",
        "caption": (
            "Golden Chronos Key ne shunya void ko cheer kar 14th August ki original timeline khol di! ⏳💥\n"
            "Bandra-Worli Sealink par Kabir ke experiment ne ek aisi temporal rift khol di thi jisne poore shahar ko nigal liya tha!\n"
            "Meera ne Kabir ko maut se bachane ke liye waqt ko 3:14 se 3:18 AM ke loop mein qaid kiya tha... lekin ab Chronos-0 jag chuka hai!\n\n"
            "Kya Kabir loop todega ya Meera ka sath dega? Drop your theories! 👇🔥\n\n"
            "#KaalRekha #Part22 #TimeLoop #AnimeShorts #IndianAnime #Shorts #HindiAnime #Mystery #Trending"
        ),
        "hashtags": ["#KaalRekha", "#Part22", "#TimeLoop", "#AnimeShorts", "#IndianAnime", "#Shorts", "#HindiAnime", "#Mystery"],
        "hook_overlay": "⏳ 3:14 AM: FIRST TIMELINE DISASTER! 😱💥",
        "comment_bait": "🔥 Kya Kabir ko Shunya core band karna chahiye ya original timeline mein jaana chahiye? Vote karein! 👇⏳",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Golden Chronos Key jaise hi temporal core se judi, safed shunya achanak toot kar bikhar gaya!",
                "text_speak": "गोल्डन क्रोनोस की जैसे ही उस टाइम-कोर से जुड़ी, असीम सफेद शून्यता काँच की तरह टूट कर बिखर गई!",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Hawa mein chauda August ki purani yaadein tairne lagi... Bandra Worli Sea Link par ek ajeeb toofan garaj raha tha!",
                "text_speak": "हवा में चौदह अगस्त की पुरानी यादें तैरने लगीं... बांद्रा-वर्ली सी-लिंक पर एक भयानक बैंगनी तूफ़ान गरज रहा था!",
                "emotion": "mysterious"
            },
            {
                "speaker": "char_b",
                "text": "Meera ne roti hui aawaz mein kaha: 'Kabir, us raat tumhara experiment fail ho gaya tha... tum mar chuke the!'",
                "text_speak": "मीरा ने रोती हुई आवाज़ में कहा: 'कबीर, उस रात तुम्हारा एक्सपेरिमेंट फेल हो गया था... तुम असल में मर चुके थे!'",
                "emotion": "intense"
            },
            {
                "speaker": "char_b",
                "text": "'Maine tumhe bachane ke liye waqt ko teen bajkar chaudah minute ke loop mein baandh diya tha!'",
                "text_speak": "'मैंने तुम्हें मौत से बचाने के लिए पूरे शहर के वक्त को तीन बजकर चौदह मिनट के लूप में बाँध दिया था!'",
                "emotion": "desperate"
            },
            {
                "speaker": "narrator",
                "text": "Tabhi zameen hilne lagi... aur freeze hue samundar ke neeche se Chronos-Zero ki laal aankhein khul gayi!",
                "text_speak": "तभी ज़मीन काँपने लगी... और जमे हुए समंदर की गहराइयों से क्रोनोस-ज़ीरो की विशाल लाल आँखें खुल गईं!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Ghadi ki sui aage badhi: 3:15 AM! Part 23 dekhne ke liye channel ko abhi SUBSCRIBE karein!",
                "text_speak": "और पहली बार घड़ी की सुई आगे बढ़ी: तीन बजकर पंद्रह मिनट! पार्ट तेईस के लिए चैनल को अभी सब्सक्राइब करें!",
                "emotion": "urgent"
            }
        ],
        "image_prompts": [
            "Cinematic 8k anime shot of Mumbai Bandra Worli Sea Link frozen under an eerie purple cracked sky at 3:14 AM, floating water droplets, MAPPA anime style, vertical 9:16, masterpiece, no text",
            "Dramatic 8k anime shot of glowing golden Chronos key hovering between Kabir's hands radiating holographic memory fragments, vertical 9:16, cinematic anime, no text",
            "Epic 8k anime flashback of massive temporal storm engulfing city bridge in violet lightning, young Kabir running towards control terminal, vertical 9:16, intense action, no text",
            "Emotional 8k anime close up of Meera in lab coat crying with glowing temporal equations reflecting in her eyes as she locks the temporal loop, vertical 9:16, breathtaking, no text",
            "Chilling 8k anime shot of colossal shadowy entity Chronos-0 opening glowing scarlet eyes deep beneath the frozen ocean water, vertical 9:16, cosmic dread, no text",
            "Epic cliffhanger anime shot of Kabir looking at his hands turning into digital temporal particles as the clock ticks to 3:15 AM, vertical 9:16, high tension, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 2. SERIES_2: JAB PYAAR ONLINE THA — EPISODE 18
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_2",
        "episode_num": 18,
        "topic": "Jab Pyaar Online Tha Episode 18: Heathrow Terminal Surprise & The Unsent Letter",
        "title": "London Heathrow Par Rohan Ka Achanak Surprise! 4000 Miles Dur Pyar! ✈️❤️ | JAB PYAAR ONLINE THA (Ep 18) #Shorts",
        "caption": (
            "London Heathrow Airport par Meera apna heavy suitcase kheench rahi thi, aankhon mein thakan liye... ✈️❤️\n"
            "Tabhi arrivals gate ke samne bheed mein ek ladka khada tha, haath mein cardboard sign liye: '@Rohan_99 Looking For Ananya!'\n"
            "4,000 miles ki doori ek pal mein mit gayi jab dono ki aankhein mili! Episode 19 ke liye comment karein! 👇💌\n\n"
            "#JabPyaarOnlineTha #Episode18 #LongDistanceLove #LoveStory #Shorts #RomanticShorts #ViralLove #AnimeShorts"
        ),
        "hashtags": ["#JabPyaarOnlineTha", "#Episode18", "#LongDistanceLove", "#LoveStory", "#Shorts", "#RomanticShorts", "#ViralLove", "#AnimeShorts"],
        "hook_overlay": "✈️ 4,000 MILES KA SURPRISE REUNION! 😭❤️",
        "comment_bait": "❤️ Kya long distance relationship sach mein nibhayi ja sakti hai? 'YES' ya 'NO' comment karein! 👇💌",
        "voice_persona": "hi_romantic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "London Heathrow airport par Meera thaki hui aankhon se apna suitcase kheench rahi thi.",
                "text_speak": "लंदन हीथ्रो एयरपोर्ट पर मीरा थकी हुई आँखों से अपना सूटकेस खींचते हुए बाहर निकल रही थी।",
                "emotion": "gentle"
            },
            {
                "speaker": "narrator",
                "text": "Char hazar mile dur, usne socha tha ki wo is anjan shahar mein bilkul akeli hai.",
                "text_speak": "चार हज़ार मील दूर, उसने सोचा था कि वो इस अजनबी शहर में बिल्कुल तन्हा है।",
                "emotion": "vulnerable"
            },
            {
                "speaker": "char_a",
                "text": "Lekin arrival gate ke beech ek ladka khada tha... haath mein cardboard sign liye jispar unki pehli Discord chat ka username likha tha!",
                "text_speak": "लेकिन अराइवल गेट के ठीक बीच एक लड़का खड़ा था... हाथ में कार्डबोर्ड साइन लिए जिसपर उनकी पहली चैट का यूज़रनेम लिखा था!",
                "emotion": "amazed"
            },
            {
                "speaker": "narrator",
                "text": "Rohan ne achanak aakar kaha: 'Maine bola tha na Meera... screen todkar milne aaoonga!'",
                "text_speak": "रोहन ने मुस्कुराते हुए कहा: 'मैंने बोला था ना मीरा... स्क्रीन तोड़कर तुमसे मिलने आऊँगा!'",
                "emotion": "warm"
            },
            {
                "speaker": "narrator",
                "text": "Us crowded airport par dono ek dusre ke gale lag gaye aur London ki thand pighal gayi!",
                "text_speak": "उस भीड़ भरे एयरपोर्ट पर दोनों एक दूसरे के गले लग गए और लंदन की कड़कती ठंड मानों पिघल गई!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Lekin tabhi Rohan ki jeb se ek return ticket gira... Agla episode dekhne ke liye SUBSCRIBE karein!",
                "text_speak": "लेकिन तभी रोहन की जेब से एक रिटर्न टिकट गिर गया... अगला एपिसोड देखने के लिए सब्सक्राइब करें!",
                "emotion": "mysterious"
            }
        ],
        "image_prompts": [
            "Cinematic 8k anime aesthetic shot of busy London Heathrow international airport arrivals terminal illuminated by warm evening lights, vertical 9:16, Makoto Shinkai style, masterpiece, no text",
            "Close up shot of stylish Indian girl Meera walking through terminal gates pulling suitcase, looking exhausted at her phone screen, vertical 9:16, emotional anime, no text",
            "Heartwarming anime medium shot of young Indian boy Rohan standing in the crowd holding a playful cardboard sign with neon doodles, vertical 9:16, romantic tension, no text",
            "Tearful emotional anime close up of girl's eyes widening in pure shock and joy seeing him in London, tears glistening, vertical 9:16, beautiful lighting, no text",
            "Cinematic wide anime shot of two lovers embracing tightly in the middle of a blurry crowded airport terminal, golden sunbeams streaming through glass windows, vertical 9:16, emotional climax, no text",
            "Cozy aesthetic anime shot of two hot takeaway coffee cups sitting on airport bench with plane taking off in purple dusk sky outside, vertical 9:16, heartwarming ending, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 3. SERIES_3: CHINTU KI JADUI DUNIYA — EPISODE 16
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_3",
        "episode_num": 16,
        "topic": "Chintu Ki Jadui Duniya Episode 16: Jadui Star Key Se Khula Badal Ka Shahi Mahal",
        "title": "Jadui Star Key Se Khula Aasmani Badal Ka Qila! ☁️🏰✨ | CHINTU (Ep 16) #Shorts",
        "caption": (
            "Chocolate Dragon ki di hui Golden Star Key ne aasmaan mein ek nayi jadui sidhi bana di! ☁️🏰✨\n"
            "Chintu aur Golu marshmallow ki sidhiyon par koodte hue sidhe Cloud Castle pahunch gaye!\n"
            "Wahan Cloud King ne unka swagat kiya hawa mein udte hue rainbow cupcakes ke sath! Agle episode ke liye comment karein! 👇🧁\n\n"
            "#ChintuKiDuniya #Episode16 #KidsAnimation #3DAnimation #CartoonShorts #MagicalAdventure #Shorts"
        ),
        "hashtags": ["#ChintuKiDuniya", "#Episode16", "#KidsAnimation", "#3DAnimation", "#CartoonShorts", "#MagicalAdventure", "#Shorts"],
        "hook_overlay": "☁️ AASMANI BADAL KA SHAHI QILA! 🏰✨",
        "comment_bait": "✨ Agar aapko Badal ke Mahal mein jaane ko mile toh aap kiske sath jaoge? Tag ya comment karein! 👇☁️",
        "voice_persona": "hi_kids",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Jaise hi Chintu ne Golden Star Key ko rainbow lock mein ghumaya, aasmaan mein chamakte hue marshmallow ki sidhiyan ban gayi!",
                "text_speak": "जैसे ही चिंटू ने गोल्डन स्टार की को रेनबो लॉक में घुमाया, आसमान में चमकती हुई मार्शमैलो की सीढ़ियां बन गईं!",
                "emotion": "excited"
            },
            {
                "speaker": "char_a",
                "text": "Golu ne uchhal kar kaha: 'Arre wah Chintu! Ye sidhiyan toh bilkul rasgulle jaisi soft hain!'",
                "text_speak": "गोलू ने उछल कर कहा: 'अरे वाह चिंटू! ये सीढ़ियां तो बिल्कुल रसगुल्ले जैसी सॉफ्ट हैं!'",
                "emotion": "happy"
            },
            {
                "speaker": "narrator",
                "text": "Dono doston ne daud lagayi aur safed badalon ke beech bane ek shandar aasmaani qile mein ja pahunche!",
                "text_speak": "दोनों दोस्तों ने दौड़ लगाई और सफेद बादलों के बीच बने एक शानदार आसमानी किले में जा पहुंचे!",
                "emotion": "wonder"
            },
            {
                "speaker": "narrator",
                "text": "Wahan Cloud King ne unhe bulaya aur hawa mein udte hue strawberry aur mango cupcakes pesh kiye!",
                "text_speak": "वहां क्लाउड किंग ने उनका स्वागत किया और हवा में उड़ते हुए स्ट्रॉबेरी और मैंगो कपकेक्स पेश किए!",
                "emotion": "excited"
            },
            {
                "speaker": "narrator",
                "text": "Lekin tabhi qile ke sabse oonche minar par ek laal roshni chamakne lagi... Chintu ki agli masti ke liye SUBSCRIBE karein!",
                "text_speak": "लेकिन तभी किले के सबसे ऊंचे मीनार पर एक लाल रोशनी चमकने लगी... चिंटू की अगली मस्ती के लिए सब्सक्राइब करें!",
                "emotion": "adventurous"
            }
        ],
        "image_prompts": [
            "Vibrant colorful 8k 3D Pixar Disney style glowing star-shaped golden key inserted into a sparkling rainbow keyhole floating in sky, vertical 9:16, magical illumination, no text",
            "Enchanting 3D animated scene of fluffy colorful marshmallow stairs forming a bridge reaching into fluffy golden clouds, vertical 9:16, whimsical fantasy, no text",
            "Joyful 3D Disney style cute Indian boy Chintu and chubby friend Golu climbing marshmallow stairs in awe and excitement, vertical 9:16, vibrant colors, no text",
            "Magnificent 3D animated reveal of grand fantasy castle made of pearlescent white clouds with towers shaped like ice cream swirls, vertical 9:16, breathtaking, no text",
            "Friendly jolly 3D cartoon Cloud King with fluffy cloud beard offering giant trays of flying rainbow cupcakes to laughing kids, vertical 9:16, celebratory, no text",
            "Playful cliffhanger 3D scene of kids discovering a mysterious glowing golden door at the top of the cloud tower with question mark aura, vertical 9:16, fun adventure, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 4. SERIES_4: DIMAG KA DAHI — EPISODE 16
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_4",
        "episode_num": 16,
        "topic": "Dimag Ka Dahi Episode 16: The Invisible Constant Riddle",
        "title": "Wo Kya Hai Jiska Koi Rang Nahi, Par Sab Dekh Sakte Hain? 🧠🔥 | DIMAG KA DAHI (Ep 16) #Shorts",
        "caption": (
            "Aaj ki aisi paheli jo bade-bade geniuses ke dimag ka dahi bana degi! 🧠🔥\n"
            "'Wo kya hai jiska apna koi rang nahi hota, lekin roshni aate hi wo tumhara peecha karti hai?'\n"
            "Aapke paas hain sirf 5 seconds! Comment karein apna jawab aur like karein video! 👇⏳\n\n"
            "#DimagKaDahi #Episode16 #Paheliyan #HindiRiddles #BrainTeaser #Shorts #IQTest #MindGames"
        ),
        "hashtags": ["#DimagKaDahi", "#Episode16", "#Paheliyan", "#HindiRiddles", "#BrainTeaser", "#Shorts", "#IQTest", "#MindGames"],
        "hook_overlay": "🧠 99% LOG GALAT JAWAB DETE HAIN! ❌",
        "comment_bait": "💡 Kya aapne timer khatam hone se pehle sahi jawab socha tha? 'GENIUS' comment karein! 👇⏳",
        "voice_persona": "hi_riddle",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Ek aisi paheli jo ninety-nine percent logon ka dimag ghuma degi!",
                "text_speak": "एक ऐसी पहेली जो निन्यानवे प्रतिशत लोगों का दिमाग घुमा देगी!",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "Wo kya hai jiska apna koi rang nahi hota... lekin roshni aate hi wo har jagah tumhara peecha karti hai?",
                "text_speak": "वो क्या है जिसका अपना कोई रंग नहीं होता... लेकिन रोशनी आते ही वो हर जगह तुम्हारा पीछा करती है?",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Aapke paas hain sirf paanch seconds... sochiye aur comment kijiye!",
                "text_speak": "आपके पास हैं सिर्फ पाँच सेकंड्स... सोचिए और कमेंट कीजिए!",
                "emotion": "urgent"
            },
            {
                "speaker": "narrator",
                "text": "Five... four... three... two... one! Sahi jawab hai: Tumhari Parchhayi ya Shadow!",
                "text_speak": "पाँच... चार... तीन... दो... एक! सही जवाब है: आपकी परछाई यानी शैडो!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Kya aapka dimaag tez tha? Agle mind-blowing riddle ke liye SUBSCRIBE karein!",
                "text_speak": "क्या आपका दिमाग तेज़ था? अगली माइंड-ब्लोइंग पहेली के लिए सब्सक्राइब करें!",
                "emotion": "serious"
            }
        ],
        "image_prompts": [
            "Vibrant 8k 3D stylized glowing golden brain wearing detective hat holding a magnifying glass surrounded by neon question marks, vertical 9:16, punchy energetic, no text",
            "Mysterious 3D animated silhouette of person walking under bright street lamp with long stretching dark shadow mirroring every step, vertical 9:16, cinematic riddle theme, no text",
            "High-octane 3D countdown timer glowing fiery neon numbers 5 4 3 2 1 with comic smoke bursts and ticking clock gear particles, vertical 9:16, tense atmosphere, no text",
            "Dramatic 3D reveal shot of a living shadow detaching from person and waving playfully with glowing yellow eyes, vertical 9:16, clever riddle reveal, no text",
            "Exciting 3D celebration with sparkling confetti, golden 100% IQ badge, and glowing thumbs up icon, vertical 9:16, vibrant victory screen, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 5. SERIES_5: ASHWATTHAMA 3049 AD — EPISODE 13
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_5",
        "episode_num": 13,
        "topic": "Ashwatthama 3049 AD Episode 13: Kurukshetra Plasma Core & Cosmic Brahmashira",
        "title": "Kurukshetra Ka Plasma Brahmastra Space Mein Activate Hua! 🚀🏹⚡ | ASHWATTHAMA 3049 AD (Ep 13) #Shorts",
        "caption": (
            "Dark Asteroid ke toote hue core se 5000 saal purani Sanskrit cybernetic seals jaag uthin! 🚀🏹⚡\n"
            "Ashwatthama ke maathe par sthit Divya Mani ne asteroid ke andar sthit Brahmashira weapon core ko pehchan liya!\n"
            "Mahabharat ke us prachin hathiyar ne deep space mein ek naya celestial portal khol diya! Episode 14 ke liye comment karein! 👇🔥\n\n"
            "#Ashwatthama3049 #Episode13 #SciFiIndia #FuturisticAnime #SpaceWarrior #Brahmastra #Shorts #HindiSciFi"
        ),
        "hashtags": ["#Ashwatthama3049", "#Episode13", "#SciFiIndia", "#FuturisticAnime", "#SpaceWarrior", "#Brahmastra", "#Shorts", "#HindiSciFi"],
        "hook_overlay": "⚡ 5000 SAAL PURANA COSMIC WEAPON! 🚀🏹",
        "comment_bait": "🏹 Kya Ashwatthama ko Brahmashira weapon activate karna chahiye tha? Apni raye dein! 👇🔥",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Dark Asteroid ke toote hue core ke andar, paanch hazar saal purane cybernetic Sanskrit shloka chamak uthe!",
                "text_speak": "डार्क एस्टेरॉयड के टूटे हुए कोर के अंदर, पाँच हज़ार साल पुराने साइबरनेटिक संस्कृत श्लोक नीली ज्वाला से चमक उठे!",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Ashwatthama ke maathe par sthit Divya Mani tezi se dharakne lagi... aur usne prachin altar ko chhua.",
                "text_speak": "अश्वत्थामा के माथे पर स्थित दिव्य मणि तेज़ी से धड़कने लगी... और जैसे ही उसने उस प्राचीन वेदी को छुआ,",
                "emotion": "mysterious"
            },
            {
                "speaker": "char_a",
                "text": "Altar ke andar se Brahmashira Plasma Core bahar nikla... jiski taqat se poora planetary defense grid hil gaya!",
                "text_speak": "वेदी के अंदर से ब्रह्मशिरा प्लाज़्मा कोर बाहर निकला... जिसकी ऊर्जा तरंगों से पूरा स्पेस ग्रिड काँप उठा!",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Ek aawaz gunji: 'Yoddha Ashwatthama... kalyug ke ant ke liye tumhara hathiyar taiyar hai!'",
                "text_speak": "एक ब्रह्मांडीय आवाज़ गूँजी: 'अमर योद्धा अश्वत्थामा... कलियुग के अंतिम युद्ध के लिए तुम्हारा अस्त्र जाग चुका है!'",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Tabhi radar par ek anjaan alien armada dikhi... Episode 14 dekhne ke liye SUBSCRIBE karein!",
                "text_speak": "तभी डीप स्पेस रडार पर एक अज्ञात एलियन सेना प्रकट हुई... एपिसोड चौदह के लिए सब्सक्राइब करें!",
                "emotion": "urgent"
            }
        ],
        "image_prompts": [
            "Epic sci-fi 8k anime shot of cracked dark metallic asteroid floating near futuristic planetary defense grid of Neo-Kashi, vertical 9:16, unreal engine 5, masterpiece, no text",
            "Close up shot of Ashwatthama in futuristic cybernetic armor with glowing red celestial gem on forehead entering glowing asteroid cavern, vertical 9:16, intense sci-fi anime, no text",
            "Macro shot of ancient glowing gold Sanskrit cybernetic circuitry engraving pulsing with plasma energy on obsidian altar, vertical 9:16, hyper-detailed, no text",
            "Spectacular shot of legendary cosmic bow Gandiva and Brahmashira plasma core activating with dazzling electric blue and crimson energy beams, vertical 9:16, cinematic climax, no text",
            "Epic space vista of Ashwatthama standing on hull of starship looking toward distant glowing nebula with celestial star-gate activating, vertical 9:16, cosmic warrior, no text",
            "Intense cliffhanger frame of red warning alerts flashing on cyber helmet as ancient alien armada appears on holographic sensor screen, vertical 9:16, suspense, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 6. SERIES_6: THE OBSERVER FILES — EPISODE 12
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_6",
        "episode_num": 12,
        "topic": "The Observer Files Part 12: Smart Home Voice Assistants Whispering At 3:17 AM",
        "title": "Smart Home Speakers Started Whispering At 3:17 AM... 👁️📻 | THE OBSERVER FILES (Part 12) #Shorts",
        "caption": (
            "Audio recordings extracted from over 200 households confirm the same chilling anomaly... 👁️📻\n"
            "At exactly 03:17 AM, smart home voice assistants turned on unprompted with a glowing red indicator ring.\n"
            "The low-frequency whisper repeated: 'The observer is not outside your window. Look into the reflection.'\n\n"
            "Has your speaker ever behaved strangely at night? Drop your comments below! 👁️\n\n"
            "#TheObserverFiles #Part12 #AnalogHorror #HorrorShorts #Uncanny #Creepy #Shorts #FoundFootage"
        ),
        "hashtags": ["#TheObserverFiles", "#Part12", "#AnalogHorror", "#HorrorShorts", "#Uncanny", "#Creepy", "#Shorts", "#FoundFootage"],
        "hook_overlay": "👁️ DO NOT ANSWER YOUR SPEAKER TONIGHT ⚠️",
        "comment_bait": "👁️ Has your smart speaker ever lit up or talked with no one in the room? Comment your device below! 📻",
        "voice_persona": "en_analog",
        "lines": [
            {
                "speaker": "narrator",
                "text": "If you own a smart home speaker, unplug it before you go to bed tonight.",
                "text_speak": "If you own a smart home speaker, unplug it before you go to bed tonight.",
                "emotion": "urgent"
            },
            {
                "speaker": "narrator",
                "text": "Over two hundred households across four states reported their devices activating simultaneously at three seventeen AM.",
                "text_speak": "Over two hundred households across four states reported their devices activating simultaneously at three seventeen AM.",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "The indicator rings glowed a deep crimson instead of blue, and the microphones began broadcasting a rhythmic breathing sound.",
                "text_speak": "The indicator rings glowed a deep crimson instead of blue, and the microphones began broadcasting a rhythmic breathing sound.",
                "emotion": "chilling"
            },
            {
                "speaker": "narrator",
                "text": "When one homeowner asked 'Who is there?', the speaker responded with their own voice: 'I am standing right behind you.'",
                "text_speak": "When one homeowner asked 'Who is there?', the speaker responded with their own voice: 'I am standing right behind you.'",
                "emotion": "fearful"
            },
            {
                "speaker": "narrator",
                "text": "And the explanation found in the manufacturer's redacted server logs was...",
                "text_speak": "And the explanation found in the manufacturer's redacted server logs was...",
                "emotion": "cold"
            }
        ],
        "image_prompts": [
            "Eerie ECU macro close up of smart home speaker on nightstand in dark bedroom glowing a chilling sinister red ring at exactly 03:17 AM, analog horror VHS aesthetic, vertical 9:16, no text",
            "Grainy CCTV style POV shot from corner of dark silent living room, TV screen showing static noise reflecting on floor, green timestamp 03:17:02 AM, vertical 9:16, dread atmosphere, no text",
            "Chilling analog horror frame of bedroom doorway slightly cracked open, shadow of unnatural elongated humanoid silhouette standing in hallway darkness, vertical 9:16, VHS distortion, no text",
            "ECU macro of smartphone screen lying on bed with audio recorder app displaying waveform pulsing rhythmically to an inaudible voice, vertical 9:16, uncanny realism, no text",
            "Spine chilling final shot of dark bedroom mirror in background showing two glowing circular eyes watching the sleeping figure from inside the glass, vertical 9:16, psychological horror, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 7. SERIES_7: ROBLOX VAULT — EPISODE 10
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_7",
        "episode_num": 10,
        "topic": "Roblox Vault Episode 10: The Forgotten 2011 Developer Island Under The Map",
        "title": "The Secret 2011 Developer Island Under The Map! 🎮🏝️ | ROBLOX VAULT (Ep 10) #Shorts",
        "caption": (
            "Did you know about the secret 2011 developer testing island buried 5,000 studs beneath the map? 🎮🏝️\n"
            "Using the legendary ladder clip glitch, pro players can break through the void ceiling into an untouched vintage world!\n"
            "Inside is the golden admin sword and forgotten sound effects that Roblox never patched! Try it now! 👇🎮\n\n"
            "#RobloxVault #Episode10 #RobloxSecrets #RobloxGlitches #GamingShorts #RobloxTutorial #Shorts #ViralGaming"
        ),
        "hashtags": ["#RobloxVault", "#Episode10", "#RobloxSecrets", "#RobloxGlitches", "#GamingShorts", "#RobloxTutorial", "#Shorts", "#ViralGaming"],
        "hook_overlay": "🔒 SECRET 2011 DEV ISLAND FOUND! 🎮🏝️",
        "comment_bait": "🎮 Have you ever tried the ladder glitch in this game? Comment your Roblox game below! 👇🔥",
        "voice_persona": "en_gaming",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Ninety-nine percent of players have no idea there is an entire hidden island five thousand studs under the map.",
                "text_speak": "Ninety-nine percent of players have no idea there is an entire hidden island five thousand studs under the map.",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "To reach it, you need to head to the old wooden watchtower and perform a double shift-lock bounce against the third ladder rung.",
                "text_speak": "To reach it, you need to head to the old wooden watchtower and perform a double shift-lock bounce against the third ladder rung.",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Instead of void damage, your character clips into an unpatched developer sandbox from twenty-eleven.",
                "text_speak": "Instead of void damage, your character clips into an unpatched developer sandbox from twenty-eleven.",
                "emotion": "urgent"
            },
            {
                "speaker": "narrator",
                "text": "Inside, you can pick up the original golden developer katana with custom particle animations!",
                "text_speak": "Inside, you can pick up the original golden developer katana with custom particle animations!",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "And the reason the developers left this island in the source code is because...",
                "text_speak": "And the reason the developers left this island in the source code is because...",
                "emotion": "curious"
            }
        ],
        "image_prompts": [
            "High energy 8k 3D render of stylized modern Roblox avatar in neon purple jacket discovering a glowing hidden void portal beneath game terrain, vertical 9:16, ray tracing, unreal engine 5, no text",
            "Dynamic action shot of Roblox character executing precision ladder bounce glitch with motion blur and neon cyan trail effect, vertical 9:16, gaming tutorial aesthetic, no text",
            "Spectacular reveal shot of hidden tropical developer test island floating below the map in endless cyan skybox with vintage 2011 Roblox structures, vertical 9:16, vibrant lighting, no text",
            "Close up shot of Roblox character finding a legendary antique golden admin sword stuck in stone block with floating retro particles, vertical 9:16, gaming lore, no text",
            "Exciting cliffhanger screen of secret dev room door displaying classified countdown timer with question mark hologram, vertical 9:16, high contrast neon, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 8. SERIES_8: LEONARDO DA VINCI — EPISODE 2
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_8",
        "episode_num": 2,
        "topic": "Leonardo da Vinci Episode 2: The Angel in Verrocchio's Workshop",
        "title": "Verrocchio Ki Workshop Aur Vo Farishta Jisne Guru Ko Hairan Kar Diya! 🎨🕊️ | LEONARDO (Ep 2) #Shorts",
        "caption": (
            "1475 Florence: Master Andrea del Verrocchio ne apne 23 saal ke apprentice Leonardo ko ek angel paint karne ko kaha! 🎨🕊️\n"
            "Leonardo ne naye oil glaze aur sfumato technique se kneeling angel ko aisi zinda roshni di ki guru ne apna brush hamesha ke liye chhod diya!\n"
            "Forensic documentary of Leonardo's breakthrough masterpiece: 'The Baptism of Christ'. Episode 3 ke liye comment karein! 👇📜\n\n"
            "#LeonardoDaVinci #Renaissance #BaptismOfChrist #ArtHistory #DocumentaryShorts #Series8 #Episode2 #Shorts"
        ),
        "hashtags": ["#LeonardoDaVinci", "#Renaissance", "#BaptismOfChrist", "#ArtHistory", "#DocumentaryShorts", "#Series8", "#Episode2", "#Shorts"],
        "hook_overlay": "🎨 SHISHYA NE GURU KO BHI CHHOD DIYA PICHE! 📜✨",
        "comment_bait": "📜 Kya aapko lagta hai shishya ka guru se aage nikalna hi guru ki sabse badi jeet hoti hai? 'AGREE' comment karein! 👇🎨",
        "voice_persona": "hi_m_grave",
        "lines": [
            {
                "speaker": "narrator",
                "text": "1475 Florence... Master Andrea del Verrocchio ki workshop mein ek aisa chamatkar hua jisne art history badal di!",
                "text_speak": "चौदह सौ पचहत्तर फ्लोरेंस... मास्टर वेरोक्कियो की कार्यशाला में एक ऐसा चमत्कार हुआ जिसने कला का इतिहास बदल दिया!",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "Master Verrocchio 'The Baptism of Christ' painting bana rahe the, aur unhone apne 23 saal ke shishya Leonardo ko ek angel paint karne ko kaha.",
                "text_speak": "मास्टर वेरोक्कियो अपनी पेंटिंग 'द बैपटिज़्म ऑफ क्राइस्ट' बना रहे थे, और उन्होंने अपने तेईस वर्षीय शिष्य लियोनार्डो को एक फ़रिश्ता रंगने का हुक्म दिया।",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Us zamaane mein sabhi painters tempera egg-yolk use karte the, lekin Leonardo ne naye translucent oil glazes ka aavishkar kiya!",
                "text_speak": "उस ज़माने में सभी कलाकार अंडे की जर्दी वाले टेम्पेरा रंग लगाते थे, लेकिन लियोनार्डो ने पारदर्शी तेल के रंगों की नई तकनीक ईजाद कर ली!",
                "emotion": "deep"
            },
            {
                "speaker": "char_a",
                "text": "Jab parda hata, toh Leonardo ke banaye angel ke baal aur komal aankhein aisi chamak rahi thi jaise zinda aasmaan se utar aayi hon!",
                "text_speak": "जब पर्दा हटा, तो लियोनार्डो के बनाए फ़रिश्ते के सुनहरे बाल और कोमल आँखें ऐसी चमक उठीं मानो कोई जीवित फ़रिश्ता आसमान से उतर आया हो!",
                "emotion": "amazed"
            },
            {
                "speaker": "narrator",
                "text": "Vasari ke mutabiq, Guru Verrocchio ne Leonardo ka kaam dekh kar apna brush hamesha ke liye neeche rakh diya!",
                "text_speak": "इतिहासकार वसारी के मुताबिक, गुरु वेरोक्कियो ने लियोनार्डो का काम देखकर अपना ब्रश हमेशा के लिए नीचे रख दिया... क्योंकि शिष्य गुरु से आगे निकल चुका था!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Mona Lisa aur The Last Supper ke sabse bade raazon ko dekhne ke liye channel ko abhi subscribe karein!",
                "text_speak": "मोना लिसा और द लास्ट सपर के अनसुलझे रहस्यों को जानने के लिए चैनल को अभी सब्सक्राइब करें!",
                "emotion": "serious"
            }
        ],
        "image_prompts": [
            "Cinematic Renaissance historical documentary shot of rustic Italian workshop in 1475 Florence, wooden easel with antique oil paints and brushes, warm candle glow, vertical 9:16, no text",
            "Atmospheric painting medium shot of aged master artist Verrocchio watching intently as young long-haired Leonardo paints delicate strokes on wooden panel, vertical 9:16, no text",
            "Macro ECU extreme close-up of translucent luminous amber oil glazes blending seamlessly onto painted angel drapery, golden sfumato lighting, vertical 9:16, no text",
            "Breathtaking museum grade painting close up of kneeling blonde angel with ethereal gentle expression and golden curls, soft heavenly glow, vertical 9:16, masterpiece, no text",
            "Dramatic historical shot of old Italian master painter putting down his wooden brush onto table in stunned awe, tears in his eyes, vertical 9:16, no text",
            "Monumental gold foil parchment documentary title frame showing Leonardo da Vinci's signature in reverse mirror script, candlelight illumination, vertical 9:16, no text"
        ]
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# HUMANOID VOICE ENGINE (Gemini Neural TTS + Edge-TTS High-Res Fallback)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_voice(line: dict, out_wav: Path, persona: str):
    out_wav.parent.mkdir(parents=True, exist_ok=True)

    if persona == "hi_kids":
        voice_name = "Kore" if line.get("speaker") != "char_b" else "Fenrir"
        pitch_arg = "+4Hz"
        rate_arg = "+8%"
    elif persona == "hi_romantic":
        voice_name = "Kore" if line.get("speaker") == "char_b" else "Fenrir"
        pitch_arg = "-2Hz"
        rate_arg = "+4%"
    elif persona in ("en_analog", "en_gaming"):
        voice_name = "Charon" if line.get("speaker") == "char_b" else "Fenrir"
        pitch_arg = "-3Hz"
        rate_arg = "+5%"
    elif persona == "hi_riddle":
        voice_name = "Charon" if line.get("emotion") in ("dramatic", "timer") else "Fenrir"
        pitch_arg = "+0Hz"
        rate_arg = "+6%"
    elif persona == "hi_m_grave":
        voice_name = "Fenrir"
        pitch_arg = "-4Hz"
        rate_arg = "-2%"
    else:
        # Intense Anime / Sci-Fi
        voice_name = "Charon" if line.get("speaker") == "char_b" else "Fenrir"
        pitch_arg = "-2Hz"
        rate_arg = "+5%"

    text = line.get("text_speak", line["text"])

    for attempt in range(1, 4):
        try:
            pcm = _call_gemini_tts(text, voice_name=voice_name)
            if pcm and len(pcm) > 500:
                _pcm_to_wav(pcm, out_wav)
                return
        except Exception:
            if attempt == 3:
                break
            await asyncio.sleep(1.0 * attempt)

    # Edge-TTS robust fallback
    try:
        import edge_tts
        raw_mp3 = out_wav.with_suffix(".tmp.mp3")
        edge_voice = "hi-IN-MadhurNeural" if "hi" in persona else "en-US-ChristopherNeural"
        comm = edge_tts.Communicate(text, edge_voice, rate=rate_arg, pitch=pitch_arg)
        await comm.save(str(raw_mp3))
        subprocess.run([
            ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(raw_mp3), "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1",
            str(out_wav)
        ], check=True)
        raw_mp3.unlink(missing_ok=True)
    except Exception as ex:
        print(f"    ⚠️ Voice generation fallback failed: {ex}")


# ─────────────────────────────────────────────────────────────────────────────
# STYLED SUBTITLE GENERATOR (ASS Kinetic Subtitles)
# ─────────────────────────────────────────────────────────────────────────────
def generate_ass_subtitles(lines: list[dict], durs: list[float], out_ass: Path, series_badge: str):
    header = f"""[Script Info]
Title: {series_badge}
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SeriesBadge,Arial Black,44,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,8,40,40,90,1
Style: SubtitleYellow,Arial Black,58,&H0000FFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,3,2,50,50,220,1
Style: SubtitleWhite,Arial Black,58,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,3,2,50,50,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    total_dur = sum(durs)

    # Top Series Badge
    events.append(f"Dialogue: 0,0:00:00.00,{fmt_ts(total_dur)},SeriesBadge,,0,0,0,,{series_badge}")

    curr_t = 0.0
    for i, line in enumerate(lines):
        d = durs[i]
        st = curr_t
        en = curr_t + d
        style = "SubtitleYellow" if i % 2 == 0 else "SubtitleWhite"
        txt = line["text"].replace("\n", " ")
        events.append(f"Dialogue: 1,{fmt_ts(st)},{fmt_ts(en)},{style},,0,0,0,,{txt}")
        curr_t = en

    out_ass.write_text(header + "\n".join(events), encoding="utf-8")


def fmt_ts(sec: float) -> str:
    m = int(sec // 60)
    s = sec % 60
    return f"{m:d}:{s:05.2f}"


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE EPISODE GENERATION & PUBLISHING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
async def process_single_episode(ep_data: dict, db: DB, pub: YouTubePublisher | None) -> dict:
    series_code = ep_data["series_code"]
    episode_num = ep_data["episode_num"]
    title = ep_data["title"]
    caption = ep_data["caption"]
    hashtags = ep_data["hashtags"]
    lines = ep_data["lines"]
    prompts = ep_data["image_prompts"]
    persona = ep_data["voice_persona"]
    comment_bait = ep_data["comment_bait"]

    print("\n" + "=" * 75)
    print(f"  🎬 PROCESSING: {series_code} — EPISODE {episode_num}")
    print(f"  📌 Title: {title}")
    print("=" * 75)

    cp_dir = ROOT / "output" / f"batch5_{series_code.lower()}_ep{episode_num}"
    cp_dir.mkdir(parents=True, exist_ok=True)
    final_mp4 = cp_dir / "final_with_subs.mp4"

    # 1. Voice Generation
    print(f"\n  [Step 1] Synthesizing {len(lines)} dialogue clips with Neural Audio...")
    voice_wavs = []
    for i, line in enumerate(lines, 1):
        wav_path = cp_dir / f"voice_{i:02d}.wav"
        if not wav_path.exists() or wav_path.stat().st_size < 1000:
            await generate_voice(line, wav_path, persona)
        voice_wavs.append(wav_path)

    scene_durs = []
    for p in voice_wavs:
        info = probe(p)
        dur = float(info["format"]["duration"])
        scene_durs.append(round(dur, 2))
    print(f"  ✓ Voice clips ready! Total speech: {sum(scene_durs):.1f}s")

    # 2. Image Generation
    print(f"\n  [Step 2] Generating {len(prompts)} visual frames via AI Image Engine...")
    img_agent = ImageGen(providers=["pollinations", "local_placeholder"])
    scenes_for_gen = []
    for i, p in enumerate(prompts, 1):
        scenes_for_gen.append({
            "n": i,
            "file": f"scene_{i:02d}.jpg",
            "image_prompt": p,
            "motion": "zoom_in_slow"
        })
    img_agent.generate_all(scenes_for_gen, cp_dir)

    # 3. Ken Burns 30fps Compositing
    print(f"\n  [Step 3] Compositing Ken Burns scenes & mixing procedural BGM...")
    ff = ffmpeg_bin()
    scene_mp4s = []
    bgm_path = ROOT / "assets" / "audio" / "suspense_bgm.mp3"

    for i in range(1, len(lines) + 1):
        scene_jpg = cp_dir / f"scene_{i:02d}.jpg"
        voice_wav = cp_dir / f"voice_{i:02d}.wav"
        scene_mp4 = cp_dir / f"clip_{i:02d}.mp4"
        dur = scene_durs[i - 1]

        if not scene_mp4.exists() or scene_mp4.stat().st_size < 10000:
            zoom_filter = (
                f"scale=1296:2304,"
                f"crop=1080:1920:x='(in_w-out_w)/2':y='(in_h-out_h)/2 + (t/{dur})*60',"
                f"fps=30"
            )
            video_mp4 = cp_dir / f"v_{i:02d}.mp4"
            subprocess.run([
                ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
                "-loop", "1", "-t", str(dur), "-i", str(scene_jpg),
                "-vf", zoom_filter,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
                str(video_mp4)
            ], check=True)

            # Audio mix with gentle BGM
            audio_aac = cp_dir / f"a_{i:02d}.aac"
            if bgm_path.exists():
                subprocess.run([
                    ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
                    "-i", str(voice_wav),
                    "-stream_loop", "-1", "-i", str(bgm_path),
                    "-filter_complex",
                    f"[1:a]volume=0.12[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                    "-map", "[aout]", "-c:a", "aac", "-b:a", "192k",
                    "-t", str(dur), str(audio_aac)
                ], check=True)
            else:
                subprocess.run([
                    ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
                    "-i", str(voice_wav), "-c:a", "aac", "-b:a", "192k",
                    str(audio_aac)
                ], check=True)

            subprocess.run([
                ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
                "-i", str(video_mp4), "-i", str(audio_aac),
                "-c:v", "copy", "-c:a", "copy",
                "-shortest", str(scene_mp4)
            ], check=True)

        scene_mp4s.append(scene_mp4)
        print(f"    ✓ Scene {i}/{len(lines)} ready ({dur:.1f}s)")

    # 4. Concatenate and Burn Subtitles
    print(f"\n  [Step 4] Concatenating scenes & applying styled dual-color subtitles...")
    concat_txt = cp_dir / "concat.txt"
    concat_txt.write_text("\n".join(f"file '{p.resolve()}'" for p in scene_mp4s), encoding="utf-8")

    raw_final_mp4 = cp_dir / "raw_combined.mp4"
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy", str(raw_final_mp4)
    ], check=True)

    sub_ass = cp_dir / "subtitles.ass"
    generate_ass_subtitles(lines, scene_durs, sub_ass, f"{series_code} Ep {episode_num}")

    ass_escaped = str(sub_ass).replace("\\", "/").replace(":", "\\:")
    sub_filter = f"subtitles='{ass_escaped}'"

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_final_mp4),
        "-vf", sub_filter,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "19",
        "-c:a", "copy",
        str(final_mp4)
    ], check=True)

    v_info = probe(final_mp4)
    final_dur = float(v_info["format"]["duration"])
    print(f"  ✅ Render complete: {final_mp4.name} ({final_dur:.1f}s, {final_mp4.stat().st_size / 1024 / 1024:.2f} MB)")

    # 5. YouTube Shorts Upload or Approved DB Registration
    result = None
    if pub:
        print(f"\n  [Step 5] Attempting YouTube Shorts upload...")
        try:
            result = pub.upload_file(
                path=final_mp4,
                title=title,
                caption=caption,
                hashtags=hashtags,
                made_for_kids=False,
                pinned_comment=comment_bait,
            )
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}

    if result and result.get("ok"):
        vid_id = result.get("video_id")
        watch_url = f"https://youtube.com/shorts/{vid_id}"
        print(f"\n  🎉 SUCCESS! Video Live: {watch_url}")

        try:
            con = sqlite3.connect('data/autopilot.db')
            now_ts = time.time()
            con.execute('''
            INSERT INTO videos (
                created_ts, updated_ts, status, topic, title, caption, length_sec,
                series_name, series_index, video_path, public_url, yt_video_id, published_ts, ai_disclosed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now_ts, now_ts, 'published',
                ep_data.get("topic", title),
                title, caption, final_dur,
                series_code, episode_num, str(final_mp4), watch_url, vid_id, now_ts, 1
            ))
            con.commit()
            con.close()
            print(f"  ✓ Video #{series_code} Ep {episode_num} registered in database!")
        except Exception as dbe:
            print(f"  ⚠️ Database record note: {dbe}")

        return {
            "series_code": series_code,
            "episode_num": episode_num,
            "title": title,
            "yt_video_id": vid_id,
            "url": watch_url,
            "duration": final_dur,
            "status": "published"
        }
    else:
        # Gracefully save as approved video ready for immediate 1-click upload
        print(f"  ℹ️ Video saved as APPROVED in database (ready for instant upload once authorized)")
        try:
            con = sqlite3.connect('data/autopilot.db')
            now_ts = time.time()
            con.execute('''
            INSERT INTO videos (
                created_ts, updated_ts, status, topic, title, caption, length_sec,
                series_name, series_index, video_path, ai_disclosed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now_ts, now_ts, 'approved',
                ep_data.get("topic", title),
                title, caption, final_dur,
                series_code, episode_num, str(final_mp4), 1
            ))
            con.commit()
            con.close()
            print(f"  ✓ Video #{series_code} Ep {episode_num} registered in database as approved!")
        except Exception as dbe:
            print(f"  ⚠️ Database record note: {dbe}")

        return {
            "series_code": series_code,
            "episode_num": episode_num,
            "title": title,
            "yt_video_id": None,
            "url": "Ready in DB (approved)",
            "duration": final_dur,
            "status": "approved",
            "path": str(final_mp4)
        }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
async def main_async():
    start_t = time.time()
    db = DB()

    pub = None
    try:
        pub = YouTubePublisher(db=db)
    except Exception as pe:
        print(f"⚠️ YouTubePublisher init note: {pe} (videos will be rendered and saved as approved)")

    print("\n" + "#" * 80)
    print("  🚀 AUTOPILOT MASTER ENGINE: BATCH 5 — ALL SERIES GENERATE & RENDER")
    print(f"  Total Series in Queue: {len(BATCH_EPISODES)}")
    print("#" * 80 + "\n")

    published_results = []
    for ep in BATCH_EPISODES:
        try:
            res = await process_single_episode(ep, db, pub)
            published_results.append(res)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"\n❌ Error processing {ep['series_code']} Ep {ep['episode_num']}: {e}")

    total_time = round(time.time() - start_t, 1)

    print("\n" + "=" * 80)
    print(f"  🏁 BATCH 5 EXECUTION COMPLETE IN {total_time}s!")
    print(f"  🎉 Total Episodes Processed: {len(published_results)} / {len(BATCH_EPISODES)}")
    print("=" * 80)
    for res in published_results:
        status_label = res.get('status', 'unknown')
        print(f"  • [{status_label.upper()}] {res['series_code']} Ep {res['episode_num']}: {res.get('url', res.get('path'))}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main_async())
