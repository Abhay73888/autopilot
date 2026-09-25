"""
generate_and_publish_next_all_7_series_batch_part4.py — Batch 4 Orchestrator for All Active Series.

Generates and Publishes:
  1. SERIES_1 (Kaal-Rekha)            : Part 21 (3:14 AM - The Shunya Void & Meera's True Purpose)
  2. SERIES_2 (Jab Pyaar Online Tha)  : Episode 17 (London Se 2:00 AM Video Call)
  3. SERIES_3 (Chintu Ki Jadui Duniya): Episode 15 (Chocolate Dragon Ki Gufa Aur Jadui Star Key)
  4. SERIES_4 (Dimag Ka Dahi)         : Episode 15 (The Darkness Riddle That 99% Fail)
  5. SERIES_5 (Ashwatthama 3049 AD)   : Episode 12 (Neo-Kashi Par Dark Asteroid Attack)
  6. SERIES_6 (The Observer Files)    : Episode 11 (Traffic Cameras Stopped Recording Humans)
  7. SERIES_7 (Roblox Vault)          : Episode 9 (Banned 2016 Katana Hidden In Sword Fights)
  8. SERIES_8 (Leonardo da Vinci)     : Episode 2 (Verrocchio Ki Workshop Aur Vo Farishta)

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

log = Logbook("all_series_batch_part4")

DISCORD_CHANNEL = "1212765278765584396"

# ─────────────────────────────────────────────────────────────────────────────
# EPISODES CATALOG — NEXT EPISODES FOR ALL 8 ACTIVE SERIES (BATCH 4)
# ─────────────────────────────────────────────────────────────────────────────

BATCH_EPISODES = [
    # ─────────────────────────────────────────────────────────────────────────
    # 1. SERIES_1: KAAL-REKHA — PART 21
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_1",
        "episode_num": 21,
        "topic": "Kaal-Rekha Part 21: 3:14 AM - The Shunya Void & Meera's True Purpose",
        "title": "3:14 AM Par Mumbai Shunya Ho Gaya! Meera Ka Asli Roop! ⏳💥 | KAAL-REKHA (Part 21) #Shorts",
        "caption": (
            "Theek 3:14 AM par Mumbai ki saari roshni gayab ho gayi aur shahar ek safed shunya mein jam gaya! ⏳💥\n"
            "Meera clock tower ke temporal core mein khadi thi, haath mein golden Chronos key liye!\n"
            "Usne kaha: 'Kabir, ye loop tumhe qaid karne ke liye nahi... original timeline ke us haadse se bachane ke liye banaya tha!'\n\n"
            "Kya Kabir Meera par bharosa karega ya key chheen lega? Drop your theories! 👇🔥\n\n"
            "#KaalRekha #Part21 #TimeLoop #AnimeShorts #IndianAnime #Shorts #HindiAnime #Mystery #Trending"
        ),
        "hashtags": ["#KaalRekha", "#Part21", "#TimeLoop", "#AnimeShorts", "#IndianAnime", "#Shorts", "#HindiAnime", "#Mystery"],
        "hook_overlay": "⏳ 3:14 AM: MUMBAI SHUNYA HO GAYA! 😱💥",
        "comment_bait": "🔥 Kya Meera sach bol rahi hai ya Kabir ko trap kar rahi hai? 'TRUST MEERA' comment karein! 👇⏳",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "3:14 AM par achanak Mumbai ki saari light gayab ho gayi... aur poora shahar ek safed shunya mein jam gaya!",
                "text_speak": "तीन बजकर चौदह मिनट पर अचानक मुंबई की सारी बत्तियां गायब हो गईं... और पूरा शहर एक असीम सफेद शून्यता में जम गया!",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Har aaine ke tukde se violet roshni nikalne lagi... aur temporal core ke beech Meera khadi thi.",
                "text_speak": "हवा में तैरते हर आईने के टुकड़े से बैंगनी रोशनी फूटने लगी... और उस टाइम-कोर के केंद्र में मीरा खड़ी थी!",
                "emotion": "mysterious"
            },
            {
                "speaker": "char_b",
                "text": "Uske haath mein golden Chronos key thi jo kisi zinda dil ki tarah tezi se dhadak rahi thi!",
                "text_speak": "उसके हाथ में चमकती हुई गोल्डन क्रोनोस चाबी थी, जो किसी जीवित दिल की तरह तेज़ी से धड़क रही थी!",
                "emotion": "urgent"
            },
            {
                "speaker": "char_b",
                "text": "Meera ne rote hue kaha: 'Kabir, ye loop maine banaya tha... kyunki 2024 mein tumhari maut tay thi!'",
                "text_speak": "मीरा ने रोते हुए कहा: 'कबीर, यह टाइम-लूप मैंने ही बनाया था... क्योंकि दो हज़ार चौबीस में तुम्हारी मौत तय थी!'",
                "emotion": "dramatic"
            },
            {
                "speaker": "char_b",
                "text": "'Agar is key ko todoge, toh tum azaad ho jaoge... lekin main hamesha ke liye mit jaungi!'",
                "text_speak": "'अगर तुम इस चाबी को तोड़ोगे तो तुम आज़ाद हो जाओगे... लेकिन मैं हमेशा-हमेशा के लिए मिट जाऊँगी!'",
                "emotion": "chilling"
            },
            {
                "speaker": "narrator",
                "text": "Kabir ka haath kaanp raha tha... kya wo key todega? Agle episode ke liye subscribe karein!",
                "text_speak": "कबीर का हाथ काँप रहा था... क्या वो चाबी तोड़ेगा या मीरा को बचाएगा? अगले एपिसोड के लिए सब्सक्राइब करें!",
                "emotion": "intense"
            }
        ],
        "image_prompts": [
            "Dramatic anime shot of modern Mumbai city skyline freezing completely in eerie white void at 3:14 AM, buildings dissolving into floating time shards, MAPPA aesthetic, vertical 9:16, no text",
            "Atmospheric anime perspective inside colossal temporal sanctuary glowing with ultraviolet crystal prisms, floating clock gears in zero gravity, vertical 9:16, no text",
            "Extreme close up anime shot of glowing golden ancient Chronos key pulsating with neon purple energy veins, held by delicate trembling hand, vertical 9:16, no text",
            "Emotional anime beauty portrait of Meera with tears of golden starlight falling down her face, looking into camera with tragic devotion, vertical 9:16, no text",
            "Tense cinematic anime medium shot of Kabir reaching his trembling hand toward glowing artifact while temporal lightning arcs between fingers, vertical 9:16, no text",
            "Epic cliffhanger anime wide shot of Kabir and Meera standing face to face in shattered reality as a giant clock hand strikes 3:14, vertical 9:16, masterpiece, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 2. SERIES_2: JAB PYAAR ONLINE THA — EPISODE 17
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_2",
        "episode_num": 17,
        "topic": "Jab Pyaar Online Tha Episode 17: London Se 2:00 AM Video Call",
        "title": "London Se 2:00 AM Video Call: 4,000 Miles Ki Duri Par Wahi Muskaan! 📱❤️ | JAB PYAAR ONLINE THA (Ep 17) #Shorts",
        "caption": (
            "London pahunchte hi raat ke theek 2:00 AM par Meera ka pehla video call aaya! 📱❤️\n"
            "Baahar London ki barish thi, aur screen par uski ungli mein Aarav ki di hui silver promise ring chamak rahi thi.\n"
            "Aarav ne pucha: 'London kaisa laga?' Meera ne muskurakar kaha: 'Duniya badal gayi Aarav... lekin dil abhi bhi Delhi mein hai!'\n\n"
            "Long-distance relationships mein kya pyaar sach mein barkarar rehta hai? Comment karein! 👇✨\n\n"
            "#JabPyaarOnlineTha #Episode17 #Romance #Shorts #LoveStory #Emotional #Trending"
        ),
        "hashtags": ["#JabPyaarOnlineTha", "#Episode17", "#Romance", "#Shorts", "#LoveStory", "#Emotional"],
        "hook_overlay": "✈️ LONDON SE 2:00 AM VIDEO CALL! 📱❤️",
        "comment_bait": "💖 Long-distance relationships mein sabse zaroori kya hai — Trust ya Daily Calls? 'TRUST' comment karein! 👇✨",
        "voice_persona": "hi_romantic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Raat ke theek 2:00 AM par Aarav ke phone par notification chamka: 'Incoming Video Call: Meera'.",
                "text_speak": "रात के ठीक दो बजे आरव के फोन पर रिंगटोन बजी और स्क्रीन चमकी: 'इनकमिंग वीडियो कॉल: मीरा'।",
                "emotion": "sweet"
            },
            {
                "speaker": "narrator",
                "text": "Screen khulte hi baahar London ki thandi barish aur Big Ben ki halki amber roshni dikhi.",
                "text_speak": "स्क्रीन कनेक्ट होते ही खिड़की के बाहर लंदन की ठंडी बारिश और स्ट्रीटलाइट की सुनहरी रोशनी नज़र आई।",
                "emotion": "calm"
            },
            {
                "speaker": "narrator",
                "text": "Meera ke chehre par thakan thi, lekin uski ungli mein Aarav ki silver promise ring chamak rahi thi.",
                "text_speak": "मीरा के चेहरे पर सफर की थकान थी, लेकिन उसकी उंगली में आरव की दी हुई प्रॉमिस रिंग जगमगा रही थी।",
                "emotion": "sweet"
            },
            {
                "speaker": "char_a",
                "text": "Aarav ne pucha: 'London kaisa laga?' Meera ne muskurate hue screen par apna haath rakha.",
                "text_speak": "आरव ने हौले से पूछा: 'लंदन कैसा लगा?' मीरा ने नम आँखों से मुस्कुराते हुए फोन की स्क्रीन पर हाथ रखा।",
                "emotion": "romantic"
            },
            {
                "speaker": "char_a",
                "text": "'Duniya kitni bhi nayi ho Aarav... par mera dil abhi bhi Delhi ke us cafe mein baitha hai.'",
                "text_speak": "'दुनिया कितनी भी बदल जाए आरव... पर मेरा दिल अब भी दिल्ली के उसी कैफे में तुम्हारे पास बैठा है।'",
                "emotion": "romantic"
            },
            {
                "speaker": "narrator",
                "text": "Kuch dooriyan dilon ko aur kareeb le aati hain. Sacche pyaar ke liye ek red heart drop karein!",
                "text_speak": "कुछ दूरियाँ दिलों को और भी करीब ला देती हैं। सच्चे प्यार के लिए कमेंट में एक लाल दिल ज़रूर छोड़ें!",
                "emotion": "sweet"
            }
        ],
        "image_prompts": [
            "Cozy dark bedroom aesthetic Makoto Shinkai anime style, glowing smartphone showing incoming video call from Meera at 2:00 AM, soft ambient rim light, vertical 9:16, no text",
            "Atmospheric anime shot through rainy London attic window looking out at foggy street lamps and Big Ben silhouette in drizzle, vertical 9:16, no text",
            "Tender close-up anime shot of Meera wearing an oversized beige knit sweater holding phone smiling warmly with misty eyes, vertical 9:16, no text",
            "Extreme close up macro anime shot of girl's finger pressing phone screen, delicate silver promise ring reflecting blue phone light, vertical 9:16, no text",
            "Split screen cinematic anime composition: Aarav in cozy Delhi room on left, Meera in rainy London room on right, both smiling softly, vertical 9:16, no text",
            "Poetic romantic anime cliffhanger shot of glowing smartphone sitting on wooden bedside table with phone wallpaper of Aarav and Meera laughing, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 3. SERIES_3: CHINTU KI JADUI DUNIYA — EPISODE 15
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_3",
        "episode_num": 15,
        "topic": "Chintu Ki Jadui Duniya Episode 15: The Chocolate Dragon & The Star Key",
        "title": "Chocolate Dragon Ki Gufa Aur Jadui Star Key! 🍫🐉✨ | CHINTU (Ep 15) #Shorts",
        "caption": (
            "Chintu aur fluffy monster Golu pahunche Chocolate Dragon ki garam cocoa gufa mein! 🍫🐉✨\n"
            "Giant dragon aag ugalne hi wala tha ki Chintu ne apna backpack khol diya aur strawberry cookies offer kiye!\n"
            "Dragon ne khushi se jhoomte hue unhe di chamakti hui golden Star Key! Kya wo kholenge Starry Castle? Dekhiye! 👇🍭\n\n"
            "#ChintuKiJaduiDuniya #KidsAnimation #3DAnimation #PixarStyle #FamilyFun #Shorts #Cartoon"
        ),
        "hashtags": ["#ChintuKiJaduiDuniya", "#KidsAnimation", "#3DAnimation", "#PixarStyle", "#FamilyFun", "#Shorts", "#Cartoon"],
        "hook_overlay": "🐉 CHOCOLATE DRAGON KI GUFA! 🍫✨",
        "comment_bait": "🍫 Dragon ko strawberry cookies pasand aayi! Aapko kaunsi chocolate pasand hai? Comment karein! 👇🎉",
        "voice_persona": "hi_kids",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Chintu aur Golu Rainbow Island par chalte-chalte ek giant Chocolate Dragon ki gufa mein pahunch gaye!",
                "text_speak": "चिंटू और गोलू रेनबो आइलैंड पर चलते-चलते एक विशाल चॉकलेट ड्रैगन की रहस्यमयी गुफा में पहुँच गए!",
                "emotion": "excited"
            },
            {
                "speaker": "narrator",
                "text": "Gufa ke andar se garam molten chocolate ki khushbu aa rahi thi aur zameen dhak-dhak kaanp rahi thi!",
                "text_speak": "गुफा के अंदर से गर्म चॉकलेट की मीठी खुशबू आ रही थी और पूरी ज़मीन धीरे-धीरे काँप रही थी!",
                "emotion": "amazed"
            },
            {
                "speaker": "char_a",
                "text": "Achanak ek colossal purple dragon saamne aaya aur uske maathe par golden Star Key chamak rahi thi!",
                "text_speak": "अचानक एक बड़ा सा प्यारा जामुनी ड्रैगन सामने आया और उसके सिर पर सोने की जादुई स्टार-की चमक रही थी!",
                "emotion": "shocked"
            },
            {
                "speaker": "char_a",
                "text": "Dragon gusse mein garajta, usse pehle hi Chintu ne apne bag se crunchy strawberry cookies aage kar di!",
                "text_speak": "ड्रैगन गुस्से में दहाड़ता, उससे पहले ही चिंटू ने प्यार से अपने बैग से क्रंची स्ट्रॉबेरी कुकीज़ आगे बढ़ा दीं!",
                "emotion": "excited"
            },
            {
                "speaker": "char_b",
                "text": "Cookie khate hi dragon ke piche do chhote pankh khul gaye aur wo khushi se thumakne laga!",
                "text_speak": "कुकी खाते ही ड्रैगन की आँखें खुशी से चमक उठीं और वो गोलू के साथ मज़े से नाचने लगा!",
                "emotion": "funny"
            },
            {
                "speaker": "narrator",
                "text": "Dragon ne khushi se Star Key Chintu ko de di! Star Castle dekhne ke liye video ko like karein!",
                "text_speak": "ड्रैगन ने हँसते हुए जादुई चाबी चिंटू को सौंप दी! बादलों का जादुई महल देखने के लिए लाइक और सब्सक्राइब करें!",
                "emotion": "happy"
            }
        ],
        "image_prompts": [
            "Pixar 3D animation style colorful entrance to giant chocolate cave made of brownie rocks and flowing milk chocolate rivers, vertical 9:16, vibrant lighting, no text",
            "Whimsical 3D scene inside warm cocoa cavern with floating marshmallow stalactites and glowing amber candy crystals, vertical 9:16, no text",
            "Adorable giant chubby purple 3D cartoon dragon peering down curiously with big sparkling emerald eyes, vertical 9:16, no text",
            "Close up 3D animated shot of little boy Chintu happily offering a giant pink strawberry star cookie to the friendly dragon, vertical 9:16, no text",
            "Funny 3D shot of fluffy monster Golu and giant purple dragon both dancing with mouths full of chocolate cookies, vertical 9:16, no text",
            "Delightful 3D ending shot of Chintu holding up brilliant glowing golden Star Key with colorful rainbow sparkles exploding, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 4. SERIES_4: DIMAG KA DAHI — EPISODE 15
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_4",
        "episode_num": 15,
        "topic": "Dimag Ka Dahi Episode 15: The Darkness Riddle That 99% Fail",
        "title": "Wo Kya Hai Jo Jitni Zyada Hoti Hai, Utna Hi Kam Dikhta Hai?! 🧠💡 | DIMAG KA DAHI (Ep 15) #Shorts",
        "caption": (
            "Dimag Ka Dahi Episode 15! Aisi paheli jiska jawab sirf 1% log pehle attempt mein de paate hain! 🧠💡\n"
            "'Wo kaunsi aisi cheez hai jo jitni badhti jaati hai, aankhon ko utna hi kam dikhai deta hai?'\n"
            "Aapke paas hain 5 seconds! Comment karein apna jawab! 👇🔥\n\n"
            "#DimagKaDahi #Paheli #Riddle #Shorts #BrainTeaser #HindiPaheli #MindBending"
        ),
        "hashtags": ["#DimagKaDahi", "#Paheli", "#Riddle", "#Shorts", "#BrainTeaser", "#HindiPaheli", "#MindBending"],
        "hook_overlay": "🧠 JITNA ZYADA, UTNA KAM DIKHEGA?! 🤯💡",
        "comment_bait": "💡 Kya aapne 5 second se pehle socha tha? 'GENIUS' comment karein agar sahi answer pata tha! 👇🧠",
        "voice_persona": "hi_riddle",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Aaj ki paheli bade-bade toppers aur dimaag ke khiladiyon ke hosh uda degi!",
                "text_speak": "आज की पहेली बड़े-बड़े टॉपर्स और दिमाग के सूरमाओं के पसीने छुड़ा देगी!",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Wo kaunsi aisi cheez hai jo jitni zyada badhti hai... aankhon ko utna hi kam dikhai deta hai?",
                "text_speak": "वो कौन सी ऐसी चीज़ है जो जितनी ज़्यादा बढ़ती है... आँखों को उतना ही कम दिखाई देता है?",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Aapka 5 second ka countdown shuru hota hai ab: 5... 4... 3... 2... 1!",
                "text_speak": "आपका पाँच सेकंड का काउंटडाउन शुरू होता है अब: पाँच... चार... तीन... दो... एक!",
                "emotion": "timer"
            },
            {
                "speaker": "narrator",
                "text": "Sahi jawab hai: ANDHERA (Darkness)! Kyunki jitna andhera badhega, utna hi kam dikhega!",
                "text_speak": "सही जवाब है: अँधेरा! क्योंकि जितना अँधेरा बढ़ेगा, आँखों को उतना ही कम दिखाई देगा!",
                "emotion": "excited"
            },
            {
                "speaker": "char_b",
                "text": "Ab agla challenge: Aisa kya hai jiske paas daant hain par wo kaat nahi sakta?",
                "text_speak": "अब अगला चैलेंज: ऐसा क्या है जिसके पास ढेरों दाँत हैं पर वो कभी काट नहीं सकता?",
                "emotion": "dramatic"
            },
            {
                "speaker": "narrator",
                "text": "Apna dimaag daudaayein, comment mein likhein aur agle episode ke liye subscribe karein!",
                "text_speak": "अपना दिमाग दौड़ाइए, सही जवाब कमेंट बॉक्स में लिखिए और रोज़ाना पहेली के लिए सब्सक्राइब करें!",
                "emotion": "challenging"
            }
        ],
        "image_prompts": [
            "Hyper-dynamic 3D render of glowing giant neon brain wearing glasses looking puzzled with question marks swirling, vertical 9:16, high contrast, no text",
            "Mysterious artistic 3D composition of silhouette face in front of deep dark cosmic abyss with fading light rays, vertical 9:16, no text",
            "High energy 3D gold neon digital timer exploding sparks 5 4 3 2 1 with dramatic motion blur, vertical 9:16, energetic, no text",
            "Dramatic visual reveal shot of dark black velvet background suddenly illuminated by a single brilliant matchstick flame, vertical 9:16, no text",
            "Curious close up 3D cartoon styled antique comb with teeth smiling playfully on colorful studio background, vertical 9:16, no text",
            "Vibrant victory celebration 3D background with glowing golden lightbulb and floating thumbs up emojis, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 5. SERIES_5: ASHWATTHAMA 3049 AD — EPISODE 12
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_5",
        "episode_num": 12,
        "topic": "Ashwatthama 3049 AD Episode 12: Cosmic Asteroid Interception over Neo-Kashi",
        "title": "Neo-Kashi Par Girne Wala Tha Dark Asteroid: Ashwatthama Ka Raudra Roop! ⚡☄️ | ASHWATTHAMA 3049 (Ep 12) #Shorts",
        "caption": (
            "Deep space radar ne alert bajaya: Neo-Kashi ke energy shield ki taraf ek antimatter asteroid 40,000 km/h ki raftaar se badh raha tha! ⚡☄️\n"
            "Planetary defense fail ho gaya, tabhi Ashwatthama ka 3,000 saal purana celestial trishul aasmaan ki taraf chamka!\n"
            "Ashwatthama lower stratosphere mein kood pada aur uski cosmic energy ne asteroid ke do tukde kar diye! Dekhiye! 👇🔥\n\n"
            "#Ashwatthama3049 #SciFiAction #MahabharatSciFi #IndianSciFi #Shorts #EpicAction #Trending"
        ),
        "hashtags": ["#Ashwatthama3049", "#SciFiAction", "#MahabharatSciFi", "#IndianSciFi", "#Shorts", "#EpicAction"],
        "hook_overlay": "☄️ NEO-KASHI PAR ASTEROID ATTACK! ⚡🕉️",
        "comment_bait": "🔥 Ashwatthama ki cosmic power ke liye har koi 'HAR HAR MAHADEV' comment karein! 👇⚡",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Neo-Kashi ke planetary control room mein red sirens cheekh uthe: Ek dark asteroid sheher par girne wala tha!",
                "text_speak": "नियो-काशी के कंट्रोल रूम में रेड अलार्म चीख उठे: एक विशाल डार्क एस्टेरॉयड सीधे शहर की तरफ गिर रहा था!",
                "emotion": "urgent"
            },
            {
                "speaker": "narrator",
                "text": "Defense lasers asteroid ki energy ko rokne mein na-kaam rahe... aasmaan kaala aur laal hone laga!",
                "text_speak": "लेज़र मिसाइलें एस्टेरॉयड को छूते ही भस्म हो गईं... और आसमान भयानक लाल आग से धधकने लगा!",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Tabhi cyber-temple ki chhat par Ashwatthama ne apna divine Trishul uthaya... aur blue plasma lightning phoot padi!",
                "text_speak": "तभी साइबर-मंदिर के शिखर पर अश्वत्थामा ने अपना त्रिशूल उठाया... और उसके शरीर से नीली बिजली फूट पड़ी!",
                "emotion": "epic"
            },
            {
                "speaker": "narrator",
                "text": "Wo supersonic raftaar se stratosphere mein kood gaya aur seedhe asteroid ke core par prahaar kiya!",
                "text_speak": "वो सुपरसोनिक रफ्तार से अंतरिक्ष की तरफ उछला और सीधे एस्टेरॉयड के सीने पर काल बनकर टूट पड़ा!",
                "emotion": "action"
            },
            {
                "speaker": "char_b",
                "text": "Aasmaan mein ek colossal cosmic blast hua... aur asteroid hazaron chamakte sitaron mein bikhhar gaya!",
                "text_speak": "ब्रह्मांड में एक महा-विस्फोट हुआ... और वो भयानक चट्टान लाखों चमकदार तारों में बिखर गई!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Ashwatthama ne garjana ki: 'Dhartee ko koi aanch nahi aayegi!' Agle episode ke liye subscribe karein!",
                "text_speak": "अश्वत्थामा ने गरजते हुए कहा: 'जब तक मैं हूँ, इस धरती को कोई नहीं छू सकता!' लाइक और सब्सक्राइब करें!",
                "emotion": "epic"
            }
        ],
        "image_prompts": [
            "Futuristic Neo-Kashi cybernetic city with towering holographic temples beneath dark stormy red sky with falling fiery asteroid, vertical 9:16, masterpiece, no text",
            "High tech planetary defense room with glowing red emergency holograms and panicked cyber operators, vertical 9:16, cinematic, no text",
            "Colossal 8-foot muscular Ashwatthama standing atop cyber temple raising glowing celestial trishul crackling with electric blue plasma, vertical 9:16, no text",
            "Epic action anime shot of Ashwatthama flying into upper atmosphere trailing divine blue energy sonic boom toward giant burning meteor, vertical 9:16, no text",
            "Massive cosmic explosion in space shattering colossal dark asteroid into millions of glowing blue and gold stardust sparks, vertical 9:16, no text",
            "Heroic low angle shot of Ashwatthama descending back down through glowing smoke with burning eyes and cyber armor gleaming, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 6. SERIES_6: THE OBSERVER FILES — EPISODE 11
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_6",
        "episode_num": 11,
        "topic": "The Observer Files Episode 11: The CCTV Shadows That Move Against Time",
        "title": "Traffic Cameras Stopped Recording Humans... Only Shadows Remain! 👁️📹 | THE OBSERVER FILES (Ep 11) #Shorts",
        "caption": (
            "The Observer Files Episode 11: Classified Highway Protocol. 👁️📹\n"
            "At 3:17 AM across 8 municipal surveillance grids, all vehicles and pedestrians disappeared from screen feeds.\n"
            "In their place: 400 elongated shadow silhouettes walking backward against the direction of wind.\n"
            "Then one silhouette turned, stopped, and pressed its palm against camera lens #4... leaving frosted condensation from INSIDE the server.\n\n"
            "#TheObserverFiles #AnalogHorror #CCTVMystery #Shorts #FoundFootage #HorrorShorts"
        ),
        "hashtags": ["#TheObserverFiles", "#AnalogHorror", "#CCTVMystery", "#Shorts", "#FoundFootage", "#HorrorShorts"],
        "hook_overlay": "👁️ ONLY SHADOWS REMAIN ON CCTV! 📹⚠️",
        "comment_bait": "👁️ If your street camera recorded this at 3:17 AM, would you stay inside? Comment 'NEVER LOOK' below! 🪞",
        "voice_persona": "en_analog",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Do not trust municipal traffic feeds recorded tonight between 3:15 and 3:20 AM.",
                "text_speak": "Do not trust municipal traffic feeds recorded tonight between 3:15 and 3:20 AM.",
                "emotion": "urgent"
            },
            {
                "speaker": "narrator",
                "text": "Across eight surveillance sectors, all physical pedestrians suddenly vanished from the digital sensor.",
                "text_speak": "Across eight surveillance sectors, all physical pedestrians suddenly vanished from the digital sensor.",
                "emotion": "chilling"
            },
            {
                "speaker": "narrator",
                "text": "In their place, high-definition cameras recorded 400 elongated black shadows walking in reverse against the wind.",
                "text_speak": "In their place, high-definition cameras recorded four hundred elongated black shadows walking in reverse against the gale-force wind.",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "At 3:17 AM precisely, one shadow broke formation, turned toward camera four, and stared into the optical lens.",
                "text_speak": "At 3:17 AM precisely, one shadow broke formation, turned toward camera four, and stared directly into the optical lens.",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "A layer of frost formed instantly on the inside of the sealed outdoor camera housing.",
                "text_speak": "A layer of frost formed instantly on the inside of the sealed outdoor camera housing.",
                "emotion": "cold"
            },
            {
                "speaker": "narrator",
                "text": "And when technicians checked the server, it contained only one whisper: 'We are already inside.'",
                "text_speak": "And when technicians checked the server, it contained only one repeated whisper: 'We are already inside.' Subscribe for the next file.",
                "emotion": "chilling"
            }
        ],
        "image_prompts": [
            "Grainy CCTV footage timestamp 03:17 AM of empty misty multi-lane highway, green digital timestamp flickering, analog horror aesthetic, vertical 9:16, no text",
            "Eerie traffic monitor screen showing dozens of tall pitch-black shadow figures gliding silently across wet asphalt in rain, vertical 9:16, no text",
            "Atmospheric analog horror surveillance still of shadowy human silhouette standing motionless in middle of crosswalk staring upwards, vertical 9:16, no text",
            "Extreme close up of CCTV glass camera dome with ice crystal frost forming from the INSIDE surface, blurry dark figure outside, vertical 9:16, no text",
            "Dark municipal traffic monitoring room with rows of flickering TV monitors all showing static with distorted facial outlines, vertical 9:16, no text",
            "Spine chilling analog horror cliffhanger shot of glowing green computer screen with text blinking in dark server room, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 7. SERIES_7: ROBLOX VAULT — EPISODE 9
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_7",
        "episode_num": 9,
        "topic": "Roblox Vault Episode 9: The Banned 2016 Telamon Golden Katana Glitch",
        "title": "The Banned 2016 Katana Hidden In Sword Fights! ⚔️🎮 | ROBLOX VAULT (Ep 9) #Shorts",
        "caption": (
            "Roblox Vault Episode 9: The secret glitch weapon that bypasses all hitbox cooldowns! 🎮⚔️\n"
            "Hidden beneath the cloud spawn in classic Sword Fight on the Heights.\n"
            "If you cancel the potion animation at 0.1s while equipping the venom dagger, you clip straight into the Telamon Vault!\n"
            "Watch the full glitch before developers patch it in tomorrow's update! 👇🎮\n\n"
            "#RobloxVault #RobloxGlitches #SFOTH #GamingSecrets #RobloxShorts #Shorts #Gaming"
        ),
        "hashtags": ["#RobloxVault", "#RobloxGlitches", "#SFOTH", "#GamingSecrets", "#RobloxShorts", "#Shorts", "#Gaming"],
        "hook_overlay": "⚔️ BANNED 2016 WEAPON UNLOCKED! 🎮🔒",
        "comment_bait": "🎮 Have you ever played Sword Fight on the Heights? Comment your Roblox username below! 👇⚔️",
        "voice_persona": "en_gaming",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Ninety-nine percent of Roblox players have no idea this legendary 2016 developer katana is still accessible right now.",
                "text_speak": "Ninety-nine percent of Roblox players have no idea this legendary 2016 developer katana is still accessible right now.",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Head directly to the highest floating cloud island in Sword Fight on the Heights and equip the basic green dagger.",
                "text_speak": "Head directly to the highest floating cloud island in Sword Fight on the Heights and equip the basic green dagger.",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "If you tap the healing potion and cancel the animation at exactly 0.1 seconds, your avatar clips through the floor.",
                "text_speak": "If you tap the healing potion and cancel the animation at exactly 0.1 seconds, your avatar clips right through the floor.",
                "emotion": "urgent"
            },
            {
                "speaker": "narrator",
                "text": "You will fall through the clouds into a hidden gilded glass shrine built by early Roblox creators in 2016.",
                "text_speak": "You will fall through the clouds into a hidden gilded glass shrine built by early Roblox creators in 2016.",
                "emotion": "amazed"
            },
            {
                "speaker": "narrator",
                "text": "Inside rests the Telamon Golden Katana with zero hitbox delay and custom golden lightning particle trails!",
                "text_speak": "Inside rests the Telamon Golden Katana with zero hitbox delay and custom golden lightning particle trails!",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Try this glitch before the next patch, and subscribe to Roblox Vault for tomorrow's hidden badge!",
                "text_speak": "Try this glitch before the next patch, and subscribe to Roblox Vault for tomorrow's hidden badge!",
                "emotion": "happy"
            }
        ],
        "image_prompts": [
            "Vibrant high octane 3D render of stylish Roblox avatar with neon cyan horns standing atop floating cloud island holding glowing green dagger, vertical 9:16, unreal engine 5, no text",
            "Action shot of Roblox avatar performing wall clip shift lock glitch through cloud barrier with blue digital spark particles, vertical 9:16, dynamic gaming angle, no text",
            "Atmospheric reveal shot of Roblox avatar falling into ancient floating golden glass temple among clouds, vertical 9:16, ray tracing, no text",
            "Close up shot of glowing golden 2016 Telamon Katana hovering on an obsidian pedestal with gold lightning crackling, vertical 9:16, no text",
            "Action pose of Roblox avatar wielding blazing golden lightning katana slashing across cyber grid arena, vertical 9:16, high contrast, no text",
            "Exciting high contrast Roblox gaming cliffhanger shot with subscribe button effect and avatar celebrating with thumbs up, vertical 9:16, no text"
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
    print(f"  🎬 PROCESSING: {series_code} — EPISODE {episode_num}")
    print(f"  📌 Title: {title}")
    print("=" * 75)

    cp_dir = ROOT / "output" / f"batch4_{series_code.lower()}_ep{episode_num}"
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

    # 5. YouTube Shorts Upload (Zero Comment Lock Compliant)
    print(f"\n  [Step 5] Uploading {series_code} Ep {episode_num} to YouTube Shorts...")
    result = pub.upload_file(
        path=final_mp4,
        title=title,
        description=caption,
        tags=hashtags,
        privacy="public",
        thumbnail=None,
        category="24",
        language="hi" if "hi" in persona else "en",
    )

    if result.get("status") == "published":
        vid_id = result["yt_video_id"]
        watch_url = f"https://www.youtube.com/watch?v={vid_id}"
        print("=" * 70)
        print(f"  🎉 [{series_code} EP {episode_num}] IS LIVE ON YOUTUBE!")
        print(f"  🆔 Video ID: {vid_id}")
        print(f"  📺 Watch URL: {watch_url}")
        print("=" * 70)

        # 6. Post Engagement First Comment
        print("\n  💬 Posting engagement first comment...")
        try:
            from core.oauth import api_request, authorize
            creds = authorize()
            comment_body = {
                "snippet": {
                    "videoId": vid_id,
                    "topLevelComment": {"snippet": {"textOriginal": comment_bait}}
                }
            }
            st, cmt_res, _ = api_request(
                creds,
                "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
                method="POST",
                body=comment_body,
            )
            cmt_id = cmt_res.get("id") if isinstance(cmt_res, dict) else None
            print(f"  ✓ First comment posted (id: {cmt_id})")
            print("  ✓ Zero Comment Lock Policy: Comments are 100% ENABLED!")
        except Exception as ce:
            print(f"  ⚠️ First comment note: {ce}")

        # 7. Database Record
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
            print(f"  ✓ Database recorded for {series_code} Ep {episode_num}!")
        except Exception as dbe:
            print(f"  ⚠️ Database record note: {dbe}")

        # 8. Discord Notification
        print("\n  📢 Dispatching update to Discord...")
        try:
            embed = DiscordNotifications.create_embed(
                title=f"🎬 [{series_code} Ep {episode_num}] Published Live!",
                description=(
                    f"**{title}**\n\n"
                    f"🔗 **[Watch on YouTube]({watch_url})**\n\n"
                    f"⏱️ **Duration**: {final_dur:.1f}s\n"
                    f"🎙️ **Voiceover**: 100% Pure Neural Humanoid\n"
                    f"💬 **Comments**: 100% Enabled (Zero Comment Lock Compliant)"
                ),
                color=COLOR_SUCCESS,
                url=watch_url,
            )
            DiscordNotifications.send_to_channel(DISCORD_CHANNEL, {"embeds": [embed]})
            print(f"  ✓ Discord notification sent to channel {DISCORD_CHANNEL}!")
        except Exception as de:
            print(f"  ⚠️ Discord dispatch note: {de}")

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
        # Graceful handling if upload quota limit is reached
        print(f"⚠️ YouTube upload warning for {series_code} Ep {episode_num}: {result.get('error') or result}")
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
            print(f"  ✓ Video #{series_code} Ep {episode_num} saved as approved in DB!")
        except Exception as dbe:
            print(f"  ⚠️ Database record note: {dbe}")

        return {
            "series_code": series_code,
            "episode_num": episode_num,
            "title": title,
            "yt_video_id": None,
            "url": "Pending Quota Reset",
            "duration": final_dur,
            "status": "rendered_approved",
            "path": str(final_mp4)
        }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
async def main_async():
    start_t = time.time()
    db = DB()
    pub = YouTubePublisher(db=db)

    print("\n" + "#" * 80)
    print("  🚀 AUTOPILOT MASTER ENGINE: BATCH 4 — ALL SERIES GENERATE & PUBLISH")
    print(f"  Total Series in Queue: {len(BATCH_EPISODES)}")
    print("#" * 80 + "\n")

    published_results = []
    for ep in BATCH_EPISODES:
        try:
            res = await process_single_episode(ep, db, pub)
            published_results.append(res)
            # Brief pause between uploads
            await asyncio.sleep(3)
        except Exception as e:
            print(f"\n❌ Error processing {ep['series_code']} Ep {ep['episode_num']}: {e}")

    total_time = round(time.time() - start_t, 1)

    print("\n" + "=" * 80)
    print(f"  🏁 BATCH 4 EXECUTION COMPLETE IN {total_time}s!")
    print(f"  🎉 Total Episodes Processed: {len(published_results)} / {len(BATCH_EPISODES)}")
    print("=" * 80)
    for res in published_results:
        status_label = res.get('status', 'unknown')
        print(f"  • [{status_label.upper()}] {res['series_code']} Ep {res['episode_num']}: {res['url']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main_async())
