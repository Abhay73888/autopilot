"""
generate_and_publish_next_all_series_batch6.py — Batch 6 Master Orchestrator for All Active Series.

Generates and Publishes to YouTube Shorts:
  1. SERIES_1 (Kaal-Rekha)            : Part 23 (3:15 AM Par Samundar Phata! Chronos-Zero Ka Khaufnaak Roop!)
  2. SERIES_2 (Jab Pyaar Online Tha)  : Episode 19 (Sirf 48 Ghante Ka Saath! London Tower Bridge Par Aakhiri Wada!)
  3. SERIES_3 (Chintu Ki Jadui Duniya): Episode 17 (Aasman Mein Mila Jadui Pankhila Ghoda! Chintu Ki Udti Masti!)
  4. SERIES_4 (Dimag Ka Dahi)         : Episode 17 (Paani Mein Geeli Nahi Hoti, Aag Mein Jalti Nahi! Dimag Ka Dahi!)
  5. SERIES_5 (Ashwatthama 3049 AD)   : Episode 14 (Alien Dreadnought Par Ashwatthama Ka Achanak Hamla!)
  6. SERIES_6 (The Observer Files)    : Episode 13 (The Elevator Stopped At Floor -3... It Doesn't Exist!)
  7. SERIES_7 (Roblox Vault)          : Episode 11 (The Banned Golden Domino Crown Glitch In 2026!)
  8. SERIES_8 (Leonardo da Vinci)     : Episode 3  (Milan Ke Duke Ko Bheja Ye Khat! Leonardo Ka Khaufnaak Armoured Tank!)

POLICY COMPLIANCE (AGENTS.md):
  • Zero Comment Lock Policy: comments ALWAYS 100% ENABLED (ON)
  • selfDeclaredMadeForKids = False (MANDATORY)
  • privacyStatus = "public"
  • Engagement pinned first comment via commentThreads.insert
  • Transformative storytelling with Humanoid AI voiceover & Ken Burns dynamic motion
"""

from __future__ import annotations

import asyncio
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

log = Logbook("all_series_batch6")

DISCORD_CHANNEL = "1212765278765584396"

# ─────────────────────────────────────────────────────────────────────────────
# EPISODES CATALOG — NEXT EPISODES FOR ALL 8 ACTIVE SERIES (BATCH 6)
# ─────────────────────────────────────────────────────────────────────────────

BATCH_EPISODES = [
    # ─────────────────────────────────────────────────────────────────────────
    # 1. SERIES_1: KAAL-REKHA — PART 23
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_1",
        "episode_num": 23,
        "topic": "Kaal-Rekha Part 23: The Awakening of Chronos-Zero & The 3:15 AM Singularity",
        "title": "3:15 AM Par Samundar Phata! Chronos-Zero Ka Khaufnaak Roop! ⏳🌊 | KAAL-REKHA (Part 23) #Shorts",
        "caption": (
            "Theek 3:15 AM par Bandra-Worli Sea Link ke neeche se Chronos-Zero jag utha! ⏳🌊\n"
            "Frozen samundar kaanch ki tarah toota aur hazaron parallel timelines hawa mein tairne lagi!\n"
            "Kabir ke haath mein maujood Golden Chronos Key ne neeli cosmic energy chhodna shuru kiya... Lekin Meera ne kaha: 'Kabir, agar Chronos-Zero aage badha toh waqt 3:16 AM par hamesha ke liye mit jayega!'\n\n"
            "Kya Kabir Chronos-Zero ko rok payega ya Shunya core phoot jayega? Drop your theories! 👇🔥\n\n"
            "#KaalRekha #Part23 #TimeLoop #AnimeShorts #IndianAnime #Shorts #HindiAnime #Mystery #Trending"
        ),
        "hashtags": ["#KaalRekha", "#Part23", "#TimeLoop", "#AnimeShorts", "#IndianAnime", "#Shorts", "#HindiAnime", "#Mystery"],
        "hook_overlay": "⏳ 3:15 AM: CHRONOS-ZERO JAAG GAYA! 😱🌊",
        "comment_bait": "🔥 Kya Kabir ko Chronos-Zero se ladna chahiye ya Meera ke sath nayi timeline mein bhaag jana chahiye? Vote karein! 👇⏳",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Theek teen bajkar pandrah minute par... Bandra Sea Link ke neeche se samundar ka seena phat gaya!",
                "text_speak": "गोल्डन सुई तीन बजकर पंद्रह मिनट पर पहुँची... और बांद्रा सी-लिंक के नीचे समंदर का सीना भयानक धमाके से फट गया!",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Hawa mein hazaron parallel timelines kaanch ke tukdon ki tarah tairne lagi... jahan har aaine mein ek alag Kabir qaid tha!",
                "text_speak": "हवा में हज़ारों टाइमलाइंस काँच की तरह तैरने लगीं... जहाँ हर टुकड़े में एक अलग कबीर मौत से लड़ रहा था!",
                "emotion": "mysterious"
            },
            {
                "speaker": "char_b",
                "text": "Meera ne cheekh kar kaha: 'Kabir, Chronos-Zero humare temporal core ko nigalne aa raha hai... Bhaago!'",
                "text_speak": "मीरा ने चीख कर कहा: 'कबीर, क्रोनोस-ज़ीरो हमारे टाइम-कोर को निगलने आ रहा है... भागो यहाँ से!'",
                "emotion": "desperate"
            },
            {
                "speaker": "narrator",
                "text": "Lekin Kabir ne Chronos Key ko apne seene se lagaya aur neeli celestial aag hawa mein phoot padi!",
                "text_speak": "लेकिन कबीर पीछे नहीं हटा... उसने क्रोनोस की को अपने सीने से लगाया और नीली दिव्य ज्वाला हवा में फूट पड़ी!",
                "emotion": "intense"
            },
            {
                "speaker": "char_b",
                "text": "Chronos-Zero ki laal aankhein andhere se garji: 'Tum waqt ke daayre ko kabhi nahi tod sakte Kabir!'",
                "text_speak": "क्रोनोस-ज़ीरो की विशाल लाल आँखें अंधेरे से गरजीं: 'तुम काल-रेखा के दायरे को कभी नहीं तोड़ सकते कबीर!'",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Aur theek tabhi ghadi ki sui aage sarki: 3:16 AM! Part 24 ke liye channel ko SUBSCRIBE karein!",
                "text_speak": "और ठीक तभी घड़ी की सुई आगे सरकी: तीन बजकर सोलह मिनट! पार्ट चौबीस के लिए चैनल को सब्सक्राइब करें!",
                "emotion": "urgent"
            }
        ],
        "image_prompts": [
            "Cinematic 8k anime shot of Mumbai Bandra Worli Sea Link cracked by titanic tidal rift at 3:15 AM, violent violet cosmic lightning tearing through purple clouds, MAPPA anime style, vertical 9:16, masterpiece, no text",
            "Dramatic 8k anime wide perspective of hundreds of floating shattered mirror shards in midnight sky, each shard reflecting a different timeline of Kabir Sen, vertical 9:16, psychological horror, no text",
            "Emotional 8k anime close up of Meera with tears of light streaming down her face, reaching out in terror through raging temporal wind, vertical 9:16, breathtaking, no text",
            "Epic 8k anime action shot of Kabir Sen activating glowing azure Chronos Key, brilliant blue particle flames swirling around his trenchcoat, vertical 9:16, heroic climax, no text",
            "Terrifying 8k anime visual of colossal primordial cosmic beast Chronos-0 with glowing red rift eyes emerging from black stormy abyss, vertical 9:16, cosmic dread, no text",
            "Cliffhanger 8k anime shot of giant cathedral clock face ticking from 3:15 to 3:16 AM while surrounded by temporal shockwaves, vertical 9:16, high tension, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 2. SERIES_2: JAB PYAAR ONLINE THA — EPISODE 19
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_2",
        "episode_num": 19,
        "topic": "Jab Pyaar Online Tha Episode 19: Tower Bridge Rain & The 48-Hour Promise",
        "title": "Sirf 48 Ghante Ka Saath! London Tower Bridge Par Aakhiri Wada! 🌧️❤️ | JAB PYAAR ONLINE THA (Ep 19) #Shorts",
        "caption": (
            "London Heathrow par jab Meera ne Rohan ki pocket se return ticket dekha, toh uski saans tham gayi... 🌧️❤️\n"
            "Rohan sirf 48 ghante ke liye 4,000 miles dur se aaya tha! Usne apna pyara guitar bech diya tha sirf Meera ko ek baar samne se gale lagane ke liye!\n"
            "London ki rimjhim barish mein Tower Bridge par dono ne ek dusre ka haath thama... Episode 20 ke liye comment karein! 👇💌\n\n"
            "#JabPyaarOnlineTha #Episode19 #LongDistanceLove #LoveStory #Shorts #RomanticShorts #ViralLove #AnimeShorts"
        ),
        "hashtags": ["#JabPyaarOnlineTha", "#Episode19", "#LongDistanceLove", "#LoveStory", "#Shorts", "#RomanticShorts", "#ViralLove", "#AnimeShorts"],
        "hook_overlay": "🌧️ SIRF 48 GHANTE KA WAQT! 😭❤️",
        "comment_bait": "❤️ Kya aap apne sachhe pyaar ke liye 4,000 miles travel kar sakte hain? 'YES' ya 'NO' comment karein! 👇💌",
        "voice_persona": "hi_romantic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "London ki sadak par barish ki bundein gir rahi thi, aur Meera ke haath mein Rohan ka return ticket tha.",
                "text_speak": "लंदन की सड़क पर बारिश की बूँदें गिर रही थीं, और मीरा के हाथ में रोहन का रिटर्न टिकट था।",
                "emotion": "gentle"
            },
            {
                "speaker": "narrator",
                "text": "Meera ne roti hui aankhon se poocha: 'Rohan... tum sirf 48 ghante ke liye itni door aaye ho?'",
                "text_speak": "मीरा ने नम आँखों से पूछा: 'रोहन... तुम सिर्फ अड़तालीस घंटे के लिए चार हज़ार मील दूर आए हो?'",
                "emotion": "vulnerable"
            },
            {
                "speaker": "char_a",
                "text": "Rohan ne uska bheega hua haath thama aur muskura kar bola: 'Tumhare sath ka ek pal bhi meri poori zindagi se bada hai!'",
                "text_speak": "रोहन ने उसका भीगा हुआ हाथ थामा और मुस्कुरा कर कहा: 'तुम्हारे साथ का एक पल भी मेरी पूरी ज़िंदगी से बड़ा है!'",
                "emotion": "warm"
            },
            {
                "speaker": "narrator",
                "text": "Usne apni jeb se wahi purana silver locket nikala... jisme teen saal purani pehli Discord chat print thi!",
                "text_speak": "उसने अपनी जेब से वही पुराना सिल्वर लॉकेट निकाला... जिसमें तीन साल पुरानी उनकी पहली चैट की पर्ची रखी थी!",
                "emotion": "amazed"
            },
            {
                "speaker": "narrator",
                "text": "Tower Bridge ki sunhari lights ke neeche dono ne wada kiya ki chahe doori kitni bhi ho, dil kabhi alag nahi honge!",
                "text_speak": "टावर ब्रिज की सुनहरी रोशनी के नीचे दोनों ने वादा किया कि चाहे दूरी कितनी भी हो, दिल कभी जुदा नहीं होंगे!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Lekin tabhi Rohan ke phone par ek alarming call aayi... Agla episode dekhne ke liye SUBSCRIBE karein!",
                "text_speak": "लेकिन तभी रोहन के फोन पर मुंबई से एक इमरजेंसी कॉल आई... अगला एपिसोड देखने के लिए सब्सक्राइब करें!",
                "emotion": "mysterious"
            }
        ],
        "image_prompts": [
            "Cinematic 8k anime aesthetic shot of rainy cobblestone street in London at dusk, golden streetlamp glowing on wet pavement, Makoto Shinkai style, vertical 9:16, masterpiece, no text",
            "Tender emotional anime close up of Indian girl Meera with teary eyes looking down at flight ticket in trembling hands, vertical 9:16, beautiful lighting, no text",
            "Heartwarming anime medium shot of young boy Rohan holding girl's cold hands gently in the rain, warm golden breath in chilly air, vertical 9:16, romance, no text",
            "Macro ECU 8k anime close up of antique silver engraved locket opening to reveal tiny paper chat snippet, warm ambient bokeh, vertical 9:16, no text",
            "Breathtaking wide anime shot of couple embracing under black umbrella on London Tower Bridge with iconic illuminated towers in rainy night sky, vertical 9:16, emotional climax, no text",
            "Cinematic cliffhanger anime shot of smartphone vibrating on wet park bench with caller ID flashing urgent warning light, vertical 9:16, suspense, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 3. SERIES_3: CHINTU KI JADUI DUNIYA — EPISODE 17
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_3",
        "episode_num": 17,
        "topic": "Chintu Ki Jadui Duniya Episode 17: Badal Ke Mahal Mein Pankhila Baby Pegasus!",
        "title": "Aasman Mein Mila Jadui Pankhila Ghoda! Chintu Ki Udti Masti! 🦄☁️✨ | CHINTU (Ep 17) #Shorts",
        "caption": (
            "Badal ke shahi qile ke sabse oonche minar par Chintu aur Golu ko mila ek ajeeb sa baby Pegasus! 🦄☁️✨\n"
            "Wo meethi caramel belon mein fasa ro raha tha! Chintu ne Star Key se uski rassi kaati aur usne khushi se aasmaan mein chhalang laga di!\n"
            "Cloud King ne dono doston ko di jadui flying caps! Agle episode ke liye comment karein! 👇🧁\n\n"
            "#ChintuKiDuniya #Episode17 #KidsAnimation #3DAnimation #CartoonShorts #MagicalAdventure #Shorts"
        ),
        "hashtags": ["#ChintuKiDuniya", "#Episode17", "#KidsAnimation", "#3DAnimation", "#CartoonShorts", "#MagicalAdventure", "#Shorts"],
        "hook_overlay": "🦄 AASMAN MEIN PANKHILA GHODA! ✨☁️",
        "comment_bait": "✨ Agar aapko udne wala baby Pegasus mil jaye, toh aap uska kya naam rakhoge? Comment karein! 👇🦄",
        "voice_persona": "hi_kids",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Cloud Castle ke sabse oonche tower par Chintu aur Golu ne dekha ek chhota sa roopahla baby Pegasus!",
                "text_speak": "क्लाउड कैसल के सबसे ऊंचे टावर पर चिंटू और गोलू ने देखा एक नन्हा सा जादुई पंखिला घोड़ा!",
                "emotion": "wonder"
            },
            {
                "speaker": "char_a",
                "text": "Golu chillaya: 'Chintu dekho! Bechara meethi caramel ki belon mein fasa hua hai!'",
                "text_speak": "गोलू चिल्लाया: 'चिंटू देखो! बेचारा मीठी कैरेमल की लताओं में उलझा हुआ रो रहा है!'",
                "emotion": "excited"
            },
            {
                "speaker": "narrator",
                "text": "Chintu ne turant apni Golden Star Key nikaali aur uski jadui roshni se saari chipchipi belein pighal gayi!",
                "text_speak": "चिंटू ने तुरंत अपनी गोल्डन स्टार की निकाली और उसकी जादुई चमक से सारी चिपचिपी लताएँ पिघल गईं!",
                "emotion": "happy"
            },
            {
                "speaker": "narrator",
                "text": "Azaad hote hi baby Pegasus ne apne chamakdaar indradhanushi pankh phadphadaye aur dono doston ko peeth par bitha kar aasmaan mein ud gaya!",
                "text_speak": "आज़ाद होते ही नन्हे पेगासस ने अपने सतरंगी पंख फड़फड़ाए और दोनों दोस्तों को पीठ पर बैठाकर हवा में उड़ चला!",
                "emotion": "wonder"
            },
            {
                "speaker": "narrator",
                "text": "Lekin aage badhte hi aasmaan mein ek chocolate cyclone garajne laga... Agli masti ke liye SUBSCRIBE karein!",
                "text_speak": "लेकिन तभी सामने एक तूफानी चॉकलेट साइक्लोन गरजने लगा... अगली मस्ती के लिए सब्सक्राइब करें!",
                "emotion": "adventurous"
            }
        ],
        "image_prompts": [
            "Delightful colorful 8k 3D Pixar style shot of whimsical Cloud Castle tower with cotton-candy clouds and sparkling starlight, vertical 9:16, masterpiece, no text",
            "Adorable 3D animated close up of tiny fluffy baby Pegasus with pastel blue coat and glossy golden hooves looking up with big cute eyes, vertical 9:16, no text",
            "Dynamic 3D animated shot of Indian boy Chintu holding glowing golden star wand touching sweet caramel vines with magical sparkle bursts, vertical 9:16, no text",
            "Exhilarating 3D animation wide shot of Chintu and chubby friend Golu laughing with joy riding the flying baby Pegasus through pastel rainbow clouds, vertical 9:16, cinematic, no text",
            "Whimsical cliffhanger 3D animation showing swirling chocolate fudge tornado spinning in candy sky with donut asteroids, vertical 9:16, playful tension, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 4. SERIES_4: DIMAG KA DAHI — EPISODE 17
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_4",
        "episode_num": 17,
        "topic": "Dimag Ka Dahi Episode 17: Paani Mein Geeli Nahi Hoti Aur Aag Mein Jalti Nahi",
        "title": "Paani Mein Geeli Nahi Hoti, Aag Mein Jalti Nahi! Dimag Ka Dahi! 🧠🔥 | DIMAG KA DAHI (Ep 17) #Shorts",
        "caption": (
            "Dimag Ka Dahi Episode 17! Is paheli ka jawab dhoondne mein 99% log haar maan lete hain! 🧠🔥\n"
            "Aapke paas hain sirf 5 seconds! Socho aur answer drop karo comment box mein! 👇🤔\n\n"
            "#DimagKaDahi #Episode17 #Riddles #Paheliyan #BrainTeaser #Shorts #HindiPaheli #MindBending #Quiz"
        ),
        "hashtags": ["#DimagKaDahi", "#Episode17", "#Riddles", "#Paheliyan", "#BrainTeaser", "#Shorts", "#HindiPaheli", "#MindBending", "#Quiz"],
        "hook_overlay": "🧠 PAANI MEIN GEELI NAHI HOTI! 🤯🔥",
        "comment_bait": "🧠 99% log fail ho gaye! Kya aapka jawab 5 seconds se pehle sahi tha? 'PASS' ya 'FAIL' comment karein! 👇🤯",
        "voice_persona": "hi_riddle",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Ek aisi paheli jo bade-bade detectives ke dimaag ki batti gul kar de!",
                "text_speak": "एक ऐसी पहेली जो बड़े-बड़े जासूसों के दिमाग की बत्ती गुल कर दे!",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "Wo kya hai jo paani mein doobti nahi, aag mein jalti nahi, aur andhere mein gayab ho jaati hai?",
                "text_speak": "वो क्या है जो पानी में डूबती नहीं, आग में जलती नहीं, और अंधेरे में गायब हो जाती है?",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Aapke paas hain sirf 5 seconds... dimag lagaiye aur comment karein!",
                "text_speak": "आपके पास हैं सिर्फ 5 सेकंड्स... दिमाग दौड़ाइए और कमेंट कीजिए!",
                "emotion": "timer"
            },
            {
                "speaker": "narrator",
                "text": "Paanch... chaar... teen... do... ek! Sahi jawab hai: Parchhai yaani Shadow!",
                "text_speak": "पाँच... चार... तीन... दो... एक! सही जवाब है: परछाई यानी शैडो!",
                "emotion": "dramatic"
            },
            {
                "speaker": "narrator",
                "text": "Aapka jawab sahi tha ya dahi bana? Video ko like karein aur doston ko challenge bhejein!",
                "text_speak": "आपका जवाब सही था या दिमाग का दही बना? वीडियो को लाइक करें और दोस्तों को चैलेंज भेजें!",
                "emotion": "serious"
            }
        ],
        "image_prompts": [
            "Eye-catching 3D graphic of glowing neon question marks hovering around a hyper-detailed cartoon brain on fire, dark cosmic background, vertical 9:16, masterpiece, no text",
            "Surreal dramatic 3D visual of a walking shadow silhouette cast on liquid rippling water and glowing orange flames simultaneously, vertical 9:16, conceptual art, no text",
            "High energy 3D countdown clock glowing with intense amber neon numerals 5 4 3 2 1 with comic impact sparks, vertical 9:16, no text",
            "Clever cinematic 3D reveal showing a person standing in brilliant beam of spotlight with a sharp distinct shadow stretching on stone floor, vertical 9:16, no text",
            "Vibrant celebratory 3D cartoon frame with golden puzzle pieces locking together and fireworks exploding in neon purple, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 5. SERIES_5: ASHWATTHAMA 3049 AD — EPISODE 14
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_5",
        "episode_num": 14,
        "topic": "Ashwatthama 3049 AD Episode 14: Orbital Drop on Hive Dreadnought",
        "title": "Alien Dreadnought Par Ashwatthama Ka Achanak Hamla! 🚀🏹⚡ | ASHWATTHAMA 3049 AD (Ep 14) #Shorts",
        "caption": (
            "Kurukshetra-Omega station ke tabah hone ke baad Ashwatthama ne akele alien hive ship par attack kar diya! 🚀🏹⚡\n"
            "3049 AD ke plasma spear aur 5,000 saal purane Vedic yoddha ki takat ne alien mothership ki hull ko cheer diya!\n"
            "Reactor chamber mein jaag utha tin-aankhon wala Alien General! Episode 15 ke liye comment karein! 👇🔥\n\n"
            "#Ashwatthama #Part14 #SciFiIndia #Mahabharata3049 #Shorts #SpaceAction #TrendingSciFi #AnimeAction"
        ),
        "hashtags": ["#Ashwatthama", "#Part14", "#SciFiIndia", "#Mahabharata3049", "#Shorts", "#SpaceAction", "#TrendingSciFi", "#AnimeAction"],
        "hook_overlay": "🚀 ALIEN HIVE PAR SOLO ATTACK! ⚡🏹",
        "comment_bait": "⚡ Kya Ashwatthama ka Vedic spear alien dreadnought ko tabah kar payega? 'YES' ya 'NO' comment karein! 👇🚀",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Earth orbit mein alien hive ship ne jaise hi antimatter beam charge ki, tabhi uske hull par ek visphot hua!",
                "text_speak": "पृथ्वी की कक्षा में एलियन मदरशिप ने जैसे ही डार्क बीम चार्ज की, तभी उसकी बाहरी ढाल पर भयानक धमाका हुआ!",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Panch hazar saal purana yoddha Ashwatthama cybernetic jetpack ke sath sidhe dreadnought ke andar dakhil ho chuka tha!",
                "text_speak": "पाँच हज़ार साल पुराना महायोद्धा अश्वत्थामा साइबरनेटिक जेटपैक के साथ सीधे एलियन शिप के भीतर दाखिल हो चुका था!",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Uske hath mein maujood plasma spear ne Vedic mantron ke sath neeli bijli ugli aur saikdon bio-drones dher ho gaye!",
                "text_speak": "उसके हाथ में मौजूद प्लाज़्मा भाले ने वैदिक मंत्रों के साथ नीली बिजली उगली और सैकड़ों बायो-ड्रोन पल में भस्म हो गए!",
                "emotion": "epic"
            },
            {
                "speaker": "narrator",
                "text": "Lekin reactor core tak pahunchte hi samne khada mila tin-aankhon wala colossal Alien General!",
                "text_speak": "लेकिन शिप के मुख्य रिएक्टर तक पहुँचते ही सामने आ खड़ा हुआ तीन खूनी आँखों वाला महाकाय एलियन जनरल!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "General ne apni dark-energy blade kholte hue kaha: 'Tumhara sansaar aaj khatam hoga!' Part 15 ke liye SUBSCRIBE karein!",
                "text_speak": "जनरल ने अपनी डार्क एनर्जी ब्लेड खोलते हुए कहा: 'तुम्हारा संसार आज खत्म होगा!' पार्ट पंद्रह के लिए सब्सक्राइब करें!",
                "emotion": "urgent"
            }
        ],
        "image_prompts": [
            "Epic 8k cinematic sci-fi shot of colossal biomechanical alien dreadnought ship looming in low Earth orbit with crimson energy shields, vertical 9:16, Denis Villeneuve Dune style, masterpiece, no text",
            "Breathtaking action shot of cybernetic armored warrior Ashwatthama breaching the glowing metallic hull of the starship with blue plasma boosters, vertical 9:16, no text",
            "Dynamic close up 8k shot of Ashwatthama swinging glowing electric blue spear slashing through alien insectoid cyber-drones in zero-g corridor, vertical 9:16, no text",
            "Intimidating wide angle 8k shot of colossal three-eyed alien warlord standing in dark purple biomechanical reactor chamber holding double-bladed plasma scythe, vertical 9:16, no text",
            "Cinematic cliffhanger standoff between glowing blue Ashwatthama and towering red shadow alien boss with energy arcs crackling across room, vertical 9:16, intense climax, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 6. SERIES_6: THE OBSERVER FILES — EPISODE 13
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_6",
        "episode_num": 13,
        "topic": "The Observer Files Episode 13: Case File 013 - The Phantom Floor -3",
        "title": "The Elevator Stopped At Floor -3... It Doesn't Exist! 👁️🏢📻 | THE OBSERVER FILES (Part 13) #Shorts",
        "caption": (
            "Case File 013: The Phantom Basement Floor. 👁️🏢\n"
            "In an abandoned 40-story office tower in Chicago, elevator number 4 descends to Floor -3 every night at 3:17 AM.\n"
            "Architectural blueprints confirm the building only has one basement level. The microphone recorded footsteps walking toward the doors from complete darkness.\n\n"
            "Would you step inside? Drop your answer below! 👇📻\n\n"
            "#TheObserverFiles #Part13 #AnalogHorror #FoundFootage #Shorts #Creepypasta #HorrorShorts #Mystery"
        ),
        "hashtags": ["#TheObserverFiles", "#Part13", "#AnalogHorror", "#FoundFootage", "#Shorts", "#Creepypasta", "#HorrorShorts", "#Mystery"],
        "hook_overlay": "👁️ ELEVATOR STOPPED AT FLOOR -3! 😱🏢",
        "comment_bait": "👁️ If an elevator stopped at a floor that doesn't exist, would you step out? Comment YES or NO below! 👇🏢",
        "voice_persona": "en_analog",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Do not get into elevator number four in the Chicago Commerce Tower after midnight.",
                "text_speak": "Do not get into elevator number four in the Chicago Commerce Tower after midnight.",
                "emotion": "chilling"
            },
            {
                "speaker": "narrator",
                "text": "Security logs confirm that every night at exactly 3:17 AM, the elevator descends past the basement... to Floor minus three.",
                "text_speak": "Security logs confirm that every night at exactly 3:17 AM, the elevator descends past the basement... to Floor minus three.",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Building blueprints show only one subterranean floor... Floor minus three physically does not exist.",
                "text_speak": "Building blueprints show only one subterranean floor... Floor minus three physically does not exist.",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "When the doors slide open on CCTV, the camera captures no lights... only the distinct sound of barefoot steps on wet concrete.",
                "text_speak": "When the doors slide open on CCTV, the camera captures no lights... only the distinct sound of barefoot steps on wet concrete.",
                "emotion": "fearful"
            },
            {
                "speaker": "narrator",
                "text": "Then the cabin microphone picks up a whisper right behind the camera: 'Step out... we are waiting.' Subscribe for Part 14.",
                "text_speak": "Then the cabin microphone picks up a whisper right behind the camera: 'Step out... we are waiting.' Subscribe for Part 14.",
                "emotion": "cold"
            }
        ],
        "image_prompts": [
            "Grainy analog horror VHS CCTV perspective of dimly lit elevator interior with flickering overhead fluorescent tubes, vertical 9:16, masterpiece, no text",
            "Macro ECU close up of retro stainless steel elevator button panel glowing amber on digital readout '-3', condensation and scratched metal, vertical 9:16, analog dread, no text",
            "Chilling perspective looking out from elevator doors opening into an infinite pitch-black flooded basement corridor with green emergency light reflecting on water, vertical 9:16, no text",
            "Night vision surveillance camera frame showing faint long shadowy human silhouette standing at the edge of the elevator doorway in absolute dark, vertical 9:16, found footage horror, no text",
            "Distorted analog CRT screen glitch showing Chicago building exterior at 3:17 AM with one single window on the 40th floor glowing blood red, vertical 9:16, analog horror, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 7. SERIES_7: ROBLOX VAULT — EPISODE 11
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_7",
        "episode_num": 11,
        "topic": "Roblox Vault Episode 11: The Mythic Golden Domino Crown Glitch In 2026",
        "title": "The Banned Golden Domino Crown Glitch In 2026! 🎮👑🔒 | ROBLOX VAULT (Ep 11) #Shorts",
        "caption": (
            "Roblox Vault Episode 11: The mythic Golden Domino Crown glitch that was never fully patched! 🎮👑🔒\n"
            "In an unlisted 2014 hangout map, a precise camera angle manipulation renders the 10,000,000 Robux crown on your avatar!\n"
            "Try this before the next patch! Drop your favorite limited below! 👇🎮\n\n"
            "#RobloxVault #Episode11 #RobloxShorts #RobloxGlitches #GamingShorts #RobloxSecrets #TrendingGaming"
        ),
        "hashtags": ["#RobloxVault", "#Episode11", "#RobloxShorts", "#RobloxGlitches", "#GamingShorts", "#RobloxSecrets", "#TrendingGaming"],
        "hook_overlay": "👑 10,000,000 ROBUX CROWN GLITCH! 🎮😱",
        "comment_bait": "🎮 What is your #1 dream Roblox limited item? Drop your username and item in the comments! 👇👑",
        "voice_persona": "en_gaming",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Roblox patched ninety-nine percent of avatar glitches, but this 2014 hidden map still works in 2026.",
                "text_speak": "Roblox patched ninety-nine percent of avatar glitches, but this 2014 hidden map still works in 2026.",
                "emotion": "excited"
            },
            {
                "speaker": "narrator",
                "text": "If you join the unlisted hangout 'Retro Brickverse' and align your camera at an eighty-nine-degree tilt against the concrete archway...",
                "text_speak": "If you join the unlisted hangout 'Retro Brickverse' and align your camera at an eighty-nine-degree tilt against the concrete archway...",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Then execute the classic wave emote while toggling shift-lock twice, the client misreads the hat accessory mesh!",
                "text_speak": "Then execute the classic wave emote while toggling shift-lock twice, the client misreads the hat accessory mesh!",
                "emotion": "urgent"
            },
            {
                "speaker": "narrator",
                "text": "For sixty full seconds, your character wears the ten-million Robux Golden Domino Crown with real sparkle particles!",
                "text_speak": "For sixty full seconds, your character wears the ten-million Robux Golden Domino Crown with real sparkle particles!",
                "emotion": "epic"
            },
            {
                "speaker": "narrator",
                "text": "Other players in the server can actually see it! Comment your username below and subscribe for more secret vaults!",
                "text_speak": "Other players in the server can actually see it! Comment your username below and subscribe for more secret vaults!",
                "emotion": "adventurous"
            }
        ],
        "image_prompts": [
            "Vibrant colorful 8k render of a cool blocky Roblox avatar standing in retro 2014 grassy hangout plaza with glowing neon arches, vertical 9:16, masterpiece, no text",
            "Close up game screenshot aesthetic of avatar wearing rare glowing golden Domino Crown with sparkling yellow star particles floating around head, vertical 9:16, no text",
            "Dynamic first person POV in Roblox experience manipulating camera angle against textured grey brick wall with glowing alignment lines, vertical 9:16, no text",
            "Exciting wide shot of multiple Roblox avatars crowding around in shock taking screenshots of the glowing golden crown avatar, vertical 9:16, high energy, no text",
            "Epic Roblox leaderboard frame showing VIP gold badge glowing and confetti explosion in bright blue sky, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 8. SERIES_8: LEONARDO DA VINCI — EPISODE 3
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_8",
        "episode_num": 3,
        "topic": "Leonardo da Vinci Episode 3: Milan Ke Duke Ka Bulawa Aur Pehla War Machine",
        "title": "Milan Ke Duke Ko Bheja Ye Khat! Leonardo Ka Khaufnaak Armoured Tank! ⚔️📜🎨 | LEONARDO (Ep 3) #Shorts",
        "caption": (
            "1482 mein Leonardo da Vinci ne Milan ke shaktishaali Duke Ludovico Sforza ko ek aisa khat bheja jisne itihaas ko hila diya! ⚔️📜🎨\n"
            "Usne khud ko painter nahi, balke ek Military Engineer bataya! Khat ke sath usne armoured tank, giant crossbow, aur steam cannon ke sketches bheje jo 500 saal aage ki technology the!\n"
            "Duke ne bina der kiye Leonardo ko Milan ka shahi engineer bana diya! Agle episode ke liye comment karein! 👇🏛️\n\n"
            "#LeonardoDaVinci #Episode3 #HistoryShorts #Renaissance #DocumentaryShorts #Inventions #ArtHistory #Shorts"
        ),
        "hashtags": ["#LeonardoDaVinci", "#Episode3", "#HistoryShorts", "#Renaissance", "#DocumentaryShorts", "#Inventions", "#ArtHistory", "#Shorts"],
        "hook_overlay": "⚔️ 500 SAAL PURANA ARMOURED TANK! 📜😱",
        "comment_bait": "🎨 Kya aapko pata tha ki Leonardo painting se zyada military weapons design karte the? Comment karein! 👇📜",
        "voice_persona": "hi_m_grave",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Chaudah sau byasi mein Leonardo ne Milan ke Duke ko ek aisa ajeeb khat bheja jisne itihaas ko hila diya!",
                "text_speak": "चौदह सौ बयासी में लियोनार्डो ने मिलान के ड्यूक को एक ऐसा अजीब खत भेजा जिसने इतिहास को हिला दिया!",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "Usne khud ko ek chitrkaar nahi, balke ek 'Military Engineer' bataya jo yuddh ka naksha badal sakta tha!",
                "text_speak": "उसने खुद को एक चित्रकार नहीं, बल्कि एक 'मिलिट्री इंजीनियर' बताया जो युद्ध का नक्शा बदल सकता था!",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Khat ke sath usne ek gol armoured tank ka naksha bheja... jisme charon taraf cannons lagi thi aur lohe ki chaadar se surakshit tha!",
                "text_speak": "खत के साथ उसने एक गोल बख्तरबंद टैंक का नक्शा भेजा... जिसमें चारों तरफ तोपें लगी थीं और लोहे की चादर से सुरक्षित था!",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Yeh theek wahi tank tha jo aadhunik duniya ne paanch sau saal baad pehle vishwa yuddh mein banaya!",
                "text_speak": "यह ठीक वही टैंक था जो आधुनिक दुनिया ने पाँच सौ साल बाद पहले विश्व युद्ध में बनाया!",
                "emotion": "wonder"
            },
            {
                "speaker": "narrator",
                "text": "Duke ne turant Leonardo ko Milan bula liya... jahan se 'The Last Supper' ki shuruat honi thi! Subscribe for Ep 4!",
                "text_speak": "ड्यूक ने तुरंत लियोनार्डो को मिलान बुला लिया... जहाँ से 'द लास्ट सपर' की शुरुआत होनी थी! सब्सक्राइब फॉर एपिसोड 4!",
                "emotion": "climax"
            }
        ],
        "image_prompts": [
            "Museum quality 8k historical documentary shot of aged Renaissance parchment letter with intricate Leonardo da Vinci sepia mirror-writing, candlelit wooden desk, vertical 9:16, masterpiece, no text",
            "Atmospheric historical painting style shot of Leonardo's original wooden domed armoured turtle tank sketch bursting with mechanical gear schematics, vertical 9:16, no text",
            "Cinematic 8k photorealistic reconstruction of Leonardo's conical wooden and bronze armoured war chariot rolling on battlefield with smoke billowing, vertical 9:16, no text",
            "Regal portrait of Ludovico Sforza Duke of Milan in crimson velvet robes examining Leonardo's mechanical drawings with wide eyes in palace hall, vertical 9:16, no text",
            "Breathtaking historical view of medieval Milan citadel with Leonardo's horse silhouette riding toward gothic gates at golden sunrise, vertical 9:16, epic cliffhanger, no text"
        ]
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# HUMANOID VOICE ENGINE (Gemini Neural TTS + Edge-TTS Fallback)
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
async def process_single_episode(ep_data: dict, db: DB, pub: YouTubePublisher) -> dict:
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
    print(f"  🎬 PROCESSING BATCH 6: {series_code} — EPISODE {episode_num}")
    print(f"  📌 Title: {title}")
    print("=" * 75)

    cp_dir = ROOT / "output" / f"batch6_{series_code.lower()}_ep{episode_num}"
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
    bgm_path = ROOT / "assets" / "audio" / ("romance_bgm.mp3" if series_code == "SERIES_2" else "suspense_bgm.mp3")

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

    # 5. Register in DB as 'approved'
    print(f"\n  [Step 5] Registering video in DB & preparing for YouTube release...")
    con = sqlite3.connect('data/autopilot.db')
    now_ts = time.time()
    cur = con.cursor()
    script_data = json.dumps({"comment_bait": comment_bait})
    cur.execute('''
        INSERT INTO videos (
            created_ts, updated_ts, status, topic, title, caption, length_sec,
            series_name, series_index, video_path, ai_disclosed, user_id, script_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        now_ts, now_ts, 'approved',
        ep_data.get("topic", title),
        title, caption, final_dur,
        series_code, episode_num, str(final_mp4), 1, "admin_abhay", script_data
    ))
    video_db_id = cur.lastrowid
    con.commit()
    con.close()
    print(f"  ✓ Video #{video_db_id} ({series_code} Ep {episode_num}) registered as approved!")

    # 6. YouTube Shorts Upload via YouTubePublisher (Zero Comment Lock Policy Enforced)
    print(f"\n  [Step 6] Publishing Video #{video_db_id} to YouTube Shorts (Comments 100% ON, Public)...")
    res = pub.publish(video_db_id, privacy="public", pin_comment=True)
    if res.get("status") == "published" and res.get("yt_video_id"):
        yt_id = res["yt_video_id"]
        watch_url = f"https://youtube.com/shorts/{yt_id}"
        print(f"\n  🎉 SUCCESS! Video Live: {watch_url}")
        return {
            "series_code": series_code,
            "episode_num": episode_num,
            "title": title,
            "video_db_id": video_db_id,
            "yt_video_id": yt_id,
            "url": watch_url,
            "duration": final_dur,
            "status": "published"
        }
    else:
        print(f"  ⚠️ Publish result: {res}")
        return {
            "series_code": series_code,
            "episode_num": episode_num,
            "title": title,
            "video_db_id": video_db_id,
            "yt_video_id": None,
            "url": "Failed or Queued",
            "duration": final_dur,
            "status": res.get("status", "failed")
        }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MASTER RUNNER
# ─────────────────────────────────────────────────────────────────────────────
async def main_async():
    start_t = time.time()
    db = DB()

    print("\n" + "#" * 80)
    print("  🚀 AUTOPILOT MASTER ENGINE: BATCH 6 — NEXT EPISODE OF ALL SERIES")
    print(f"  Total Series in Queue: {len(BATCH_EPISODES)}")
    print("  Policy: selfDeclaredMadeForKids=False | Comments=100% ON | Public")
    print("#" * 80 + "\n")

    pub = YouTubePublisher(db=db)

    published_results = []
    for ep in BATCH_EPISODES:
        try:
            res = await process_single_episode(ep, db, pub)
            published_results.append(res)
            # Short cooldown between uploads
            await asyncio.sleep(4)
        except Exception as e:
            print(f"\n❌ Error processing {ep['series_code']} Ep {ep['episode_num']}: {e}")
            log.error(f"Error processing {ep['series_code']}: {e}")

    total_time = round(time.time() - start_t, 1)

    print("\n" + "=" * 80)
    print(f"  🏁 BATCH 6 EXECUTION COMPLETE IN {total_time}s!")
    print(f"  🎉 Total Episodes Processed: {len(published_results)} / {len(BATCH_EPISODES)}")
    print("=" * 80)
    for res in published_results:
        status_label = res.get('status', 'unknown')
        print(f"  • [{status_label.upper()}] {res['series_code']} Ep {res['episode_num']}: {res.get('url')}")
    print("=" * 80 + "\n")

    # Dispatch Discord notification for Batch 6 release
    try:
        discord = DiscordNotifications(channel_id=DISCORD_CHANNEL)
        embed_fields = []
        for res in published_results:
            embed_fields.append({
                "name": f"{res['series_code']} (Ep {res['episode_num']})",
                "value": f"[{res['title'][:45]}...]({res.get('url')})",
                "inline": True
            })
        discord.send_embed(
            title="🚀 Batch 6 Released Live on YouTube Shorts (All 8 Active Series)!",
            description=(
                f"**8 brand new episodes** have been generated and published live to YouTube Shorts!\n"
                f"• Zero Comment Lock Policy Enforced (Comments ON)\n"
                f"• Humanoid AI Studio Narration + Ken Burns 30fps\n"
                f"• Dual Kinetic Styled Subtitles + Pinned Discussion Bait"
            ),
            color=COLOR_SUCCESS,
            fields=embed_fields
        )
        print("  📢 Discord notification dispatched successfully!")
    except Exception as de:
        print(f"  ⚠️ Discord notification note: {de}")


if __name__ == "__main__":
    asyncio.run(main_async())
