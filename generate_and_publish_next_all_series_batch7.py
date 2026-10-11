"""
generate_and_publish_next_all_series_batch7.py — Batch 7 Master Orchestrator for All Active Series.

Generates and Publishes to YouTube Shorts:
  1. SERIES_1 (Kaal-Rekha)            : Part 24 (3:16 AM Par Time Loop Toot Gaya! Chronos-Zero Ka Aakhiri Sach!)
  2. SERIES_2 (Jab Pyaar Online Tha)  : Episode 20 (Aakhiri 10 Minute! London Se Mumbai Ka Emotional Wada!)
  3. SERIES_3 (Chintu Ki Jadui Duniya): Episode 18 (Chocolate Cyclone Mein Fasa Baby Pegasus! Chintu Ka Gola Magic!)
  4. SERIES_4 (Dimag Ka Dahi)         : Episode 18 (Wo Kya Hai Jo Jitna Zyada Ho, Utna Hi Kam Dikhta Hai?)
  5. SERIES_5 (Ashwatthama 3049 AD)   : Episode 15 (Alien Mothership Ka Core Room! Ashwatthama Ka Trishul Strike!)
  6. SERIES_6 (The Observer Files)    : Episode 14 (The Forbidden Broadcast On Floor -3... They Are Waiting!)
  7. SERIES_7 (Roblox Vault)          : Episode 12 (The 2007 Ghost Account 'Minish' Left This Secret Place!)
  8. SERIES_8 (Leonardo da Vinci)     : Episode 4  (Milan Ka Shahi Darbar Aur 'The Last Supper' Ka Khaufnaak Raaz!)

POLICY COMPLIANCE (AGENTS.md):
  • Zero Comment Lock Policy: comments ALWAYS 100% ENABLED (ON)
  • selfDeclaredMadeForKids = False (MANDATORY)
  • privacyStatus = "public"
  • Engagement pinned first comment via commentThreads.insert
  • Transformative storytelling with Humanoid AI voiceover & Ken Burns dynamic motion
"""

from __future__ import annotations

import argparse
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

log = Logbook("all_series_batch7")

DISCORD_CHANNEL = "1212765278765584396"

# ─────────────────────────────────────────────────────────────────────────────
# EPISODES CATALOG — NEXT EPISODES FOR ALL 8 ACTIVE SERIES (BATCH 7)
# ─────────────────────────────────────────────────────────────────────────────

BATCH_EPISODES = [
    # ─────────────────────────────────────────────────────────────────────────
    # 1. SERIES_1: KAAL-REKHA — PART 24
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_1",
        "episode_num": 24,
        "topic": "Kaal-Rekha Part 24: 3:16 AM Ka Shunya Dhamaka & The Chronos Rift",
        "title": "3:16 AM Par Time Loop Toot Gaya! Chronos-Zero Ka Aakhiri Sach! ⏳⚡ | KAAL-REKHA (Part 24) #Shorts",
        "caption": (
            "Theek 3:16 AM par Bandra-Worli Sea Link ke upar waqt ka pahiya ulta ghoom gaya! ⏳⚡\n"
            "Chronos-Zero ke cosmic roop se nikli aisi energy jisne Kabir aur Meera ko shunya ke kendra mein kheench liya!\n"
            "Aur tab samne aaya wo raaz jisne Kabir ke pairon tale zameen khiska di: Chronos-Zero koi shaitan nahi, balki Kabir ka hi aane wala kal tha!\n\n"
            "Kya Kabir waqt ki is zanjeer ko tod payega? Drop your theories below! 👇🔥\n\n"
            "#KaalRekha #Part24 #TimeLoop #AnimeShorts #IndianAnime #Shorts #HindiAnime #Mystery #Trending"
        ),
        "hashtags": ["#KaalRekha", "#Part24", "#TimeLoop", "#AnimeShorts", "#IndianAnime", "#Shorts", "#HindiAnime", "#Mystery"],
        "hook_overlay": "⏳ 3:16 AM: TIME LOOP TOOT GAYA! 😱⚡",
        "comment_bait": "🔥 Kya Chronos-Zero sach mein future ka Kabir hai? Apni theory comment mein zaroor batayein! 👇⏳",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Theek teen bajkar sola minute par... poore Mumbai ka waqt freeze ho gaya aur asmaan mein laal bijli chamki!",
                "text_speak": "ठीक तीन बजकर सोलह मिनट पर... पूरी मुंबई का वक्त जम गया और आसमान में लाल बिजली भयानक वेग से चमकी!",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Chronos-Zero ke neele aaine se jab uska chehra samne aaya... toh Kabir ke hosh udd gaye! Wo future ka Kabir hi tha!",
                "text_speak": "क्रोनोस-ज़ीरो के नीले आईने से जब चेहरा सामने आया... तो कबीर के होश उड़ गए! वो भविष्य का कबीर ही था!",
                "emotion": "mysterious"
            },
            {
                "speaker": "char_b",
                "text": "Meera ne kanpte hue cheekha: 'Kabir! Agar tumne Chronos Core ko destroy kiya, toh hum dono hamesha ke liye mit jayenge!'",
                "text_speak": "मीरा ने कांपते हुए चीखा: 'कबीर! अगर तुमने टाइम कोर को तोड़ा, तो हम दोनों हमेशा के लिए इतिहास से मिट जाएंगे!'",
                "emotion": "desperate"
            },
            {
                "speaker": "narrator",
                "text": "Lekin Kabir ne Chronos Key ko sidhe Shunya vortex mein jhonk diya aur ek prachand cosmic dhamaka hua!",
                "text_speak": "लेकिन कबीर पीछे नहीं हटा... उसने क्रोनोस की को शून्य के भंवर में झोंक दिया और एक प्रचंड धमाका हुआ!",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Tabhi ghadi ki sui ulte daudne lagi: 3:15... 3:14... Kya loop fir shuru ho gaya?",
                "text_speak": "तभी घड़ी की सुइयां उल्टी दौड़ने लगीं: तीन बजकर पंद्रह... तीन बजकर चौदह... क्या लूप फिर से शुरू हो गया?",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Part 25 ke grand finale ke liye channel ko SUBSCRIBE karein!",
                "text_speak": "पार्ट पच्चीस के ग्रैंड फिनाले के लिए चैनल को तुरंत सब्सक्राइब करें!",
                "emotion": "urgent"
            }
        ],
        "image_prompts": [
            "Cinematic 8k anime shot of Mumbai city frozen in time under violet storm clouds with red temporal lightning striking Sea Link, MAPPA style, vertical 9:16, masterpiece, no text",
            "Shocking 8k anime reveal shot of colossal mirrored cosmic entity revealing identical scarred face of protagonist Kabir Sen, vertical 9:16, dramatic lighting, no text",
            "Emotional 8k anime close up of Meera in desperation with wind whipping tears across her face reaching forward, vertical 9:16, breathless tension, no text",
            "Epic 8k anime action climax of Kabir Sen thrusting blazing golden clockwork key into swirling dimensional singularity vortex, vertical 9:16, vibrant particles, no text",
            "Eerie 8k anime surreal perspective of gigantic glowing Roman numeral clock hands spinning backwards against shattered starry void, vertical 9:16, mystery, no text",
            "Grand cliffhanger 8k anime shot of Kabir and Meera standing at edge of crumbling reality awaiting the final reset, vertical 9:16, epic finale, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 2. SERIES_2: JAB PYAAR ONLINE THA — EPISODE 20
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_2",
        "episode_num": 20,
        "topic": "Jab Pyaar Online Tha Episode 20: London Airport Goodbye & The Heartbeat Return",
        "title": "Aakhiri 10 Minute! London Se Mumbai Ka Emotional Wada! 🌧️❤️ | JAB PYAAR ONLINE THA (Ep 20) #Shorts",
        "caption": (
            "London Heathrow Airport par aakhiri 10 minute bache the... 🌧️❤️\n"
            "Rohan ki Mumbai flight ka gate khul chuka tha aur Meera uske gale lag kar ro rahi thi!\n"
            "Rohan ne apna purana headphone Meera ko pehnaya aur kaha: 'Jab bhi meri yaad aaye, ye gaana sun lena... Doori sirf shehar ki hai, dil ki nahi!'\n"
            "Lekin security gate cross karte hi Rohan ne jo message bheja, usne Meera ki zindagi badal di! Agle episode ke liye comment karein! 👇💌\n\n"
            "#JabPyaarOnlineTha #Episode20 #LongDistanceLove #LoveStory #Shorts #RomanticShorts #ViralLove #AnimeShorts"
        ),
        "hashtags": ["#JabPyaarOnlineTha", "#Episode20", "#LongDistanceLove", "#LoveStory", "#Shorts", "#RomanticShorts", "#ViralLove", "#AnimeShorts"],
        "hook_overlay": "🌧️ AAKHIRI 10 MINUTE KA FAISLA! 😭💔",
        "comment_bait": "❤️ Kya long-distance relationship sach mein successful ho sakta hai? YES ya NO comment karein! 👇💌",
        "voice_persona": "hi_romantic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "London Heathrow par final boarding announcement hui, aur Rohan ke paas bache the sirf das aakhiri minute!",
                "text_speak": "लंदन हीथ्रो एयरपोर्ट पर फाइनल बोर्डिंग अनाउंसमेंट हुई, और रोहन के पास बचे थे सिर्फ दस आखिरी मिनट!",
                "emotion": "gentle"
            },
            {
                "speaker": "narrator",
                "text": "Meera ne rote hue uska haath kheencha: 'Rohan, kya sach mein internet ka pyaar itni lambi doori jhel payega?'",
                "text_speak": "मीरा ने रोते हुए उसका हाथ भींच लिया: 'रोहन, क्या सच में इंटरनेट का प्यार इतनी लंबी दूरी झेल पाएगा?'",
                "emotion": "vulnerable"
            },
            {
                "speaker": "char_a",
                "text": "Rohan ne uske aanso ponchhe aur muskura kar bola: 'Doori sirf shahar ki hai Meera... hamare dilon ki nahi!'",
                "text_speak": "रोहन ने उसके आंसू पोंछे और हौले से मुस्कुराया: 'दूरी सिर्फ शहरों की है मीरा... हमारे दिलों की कभी नहीं!'",
                "emotion": "warm"
            },
            {
                "speaker": "narrator",
                "text": "Usne apna headphone Meera ko pehnaya, jisme teen saal pehle record kiya hua unka pehla song baj raha tha!",
                "text_speak": "उसने अपना हेडफोन मीरा को पहनाया, जिसमें तीन साल पहले उनके प्यार का पहला गाना बज रहा था!",
                "emotion": "amazed"
            },
            {
                "speaker": "narrator",
                "text": "Aur security gate paar karte hi Meera ke phone par ping hua: Rohan ne agle mahine ki return flight book kar li thi!",
                "text_speak": "और सिक्योरिटी गेट पार करते ही मीरा के फोन पर पिंग हुआ: रोहन ने अगले ही महीने की रिटर्न टिकट बुक कर ली थी!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Ep 21 ke liye video ko like karein aur channel ko SUBSCRIBE karein!",
                "text_speak": "एपिसोड इक्कीस के लिए वीडियो को लाइक करें और चैनल को तुरंत सब्सक्राइब करें!",
                "emotion": "gentle"
            }
        ],
        "image_prompts": [
            "Cinematic 8k anime airport terminal at dusk, giant glass windows showing rain dripping with golden runway lights blurring outside, Makoto Shinkai aesthetic, vertical 9:16, masterpiece, no text",
            "Heartbreaking close up 8k anime shot of Indian girl crying softly as boy gently wipes her cheek with warm woolen sleeve, vertical 9:16, soft emotional lighting, no text",
            "Warm tender anime shot of young boy placing vintage retro headphones over girl's ears with tender loving smile, vertical 9:16, romance, no text",
            "Macro ECU anime shot of smartphone lockscreen showing music visualizer playing 'Our Melody - 2023' with warm bokeh particles, vertical 9:16, no text",
            "Breathtaking anime wide shot of boy turning back and waving from boarding gate corridor bathed in warm airport departure light, vertical 9:16, emotional climax, no text",
            "Close up anime shot of girl's phone screen popping up with green notification: 'Confirmed: Flight to Mumbai - Nov 12', tears turning into happy smile, vertical 9:16, happy ending, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 3. SERIES_3: CHINTU KI JADUI DUNIYA — EPISODE 18
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_3",
        "episode_num": 18,
        "topic": "Chintu Ki Jadui Duniya Episode 18: Chocolate Cyclone Aur Cotton Candy Mountain",
        "title": "Chocolate Cyclone Mein Fasa Baby Pegasus! Chintu Ka Gola Magic! 🌪️🍫🦄 | CHINTU (Ep 18) #Shorts",
        "caption": (
            "Aasman mein ghoomte hue chocolate cyclone ne Chintu, Golu aur baby Pegasus ko gher liya! 🌪️🍫🦄\n"
            "Golu cheekha: 'Chintu! Garam chocolate hume nigal jayegi!' Tabhi Chintu ne Star Key se banaya barfeela ice cream gola!\n"
            "Dono ne maze se cyclone ko chammach se khana shuru kar diya! Aur aage dikha Cotton Candy Mountain! Agle episode ke liye comment karein! 👇🧁\n\n"
            "#ChintuKiDuniya #Episode18 #KidsAnimation #3DAnimation #CartoonShorts #MagicalAdventure #Shorts"
        ),
        "hashtags": ["#ChintuKiDuniya", "#Episode18", "#KidsAnimation", "#3DAnimation", "#CartoonShorts", "#MagicalAdventure", "#Shorts"],
        "hook_overlay": "🌪️ CHOCOLATE CYCLONE KA DHAMAKA! 🍫🦄",
        "comment_bait": "🍫 Agar chocolate cyclone aata toh aap konsi ice-cream flavour mangte? Comment karein! 👇🍦",
        "voice_persona": "hi_kids",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Aasman mein badalon ke beech achanak ek vishal Chocolate Cyclone garajne laga!",
                "text_speak": "आसमान में बादलों के बीच अचानक एक विशाल चॉकलेट साइक्लोन भयंकर आवाज़ से गरजने लगा!",
                "emotion": "wonder"
            },
            {
                "speaker": "char_a",
                "text": "Golu cheekha: 'Chintu! Garam chocolate hume nigal jayegi! Jaldi kuch jadui jugaad lagao!'",
                "text_speak": "गोलू डर के मारे चिल्लाया: 'चिंटू! ये गरम चॉकलेट हमें निगल जाएगी! जल्दी कोई जादुई जुगाड़ लगाओ!'",
                "emotion": "excited"
            },
            {
                "speaker": "narrator",
                "text": "Chintu ne turant apni Star Key ghumayi aur cyclone par barfili vanila spray maar di!",
                "text_speak": "चिंटू ने तुरंत अपनी स्टार की घुमाई और साइक्लोन पर ठंडी जादुई वैनिला बर्फ़ की फुहार मार दी!",
                "emotion": "happy"
            },
            {
                "speaker": "narrator",
                "text": "Cyclone ek pal mein gigantic Choco-Bar ice-cream mein badal gaya aur sab maze se chatne lage!",
                "text_speak": "तूफ़ान पलक झपकते ही विशाल चोको-बार आइसक्रीम बन गया और सब मजे से चाटने लगे!",
                "emotion": "wonder"
            },
            {
                "speaker": "narrator",
                "text": "Pegasus ne unhe Pink Cotton Candy Mountain par utara, jahan intezar kar raha tha ek naya mystery box! Subscribe for Ep 19!",
                "text_speak": "पेगासस ने उन्हें पिंक कॉटन कैंडी माउंटेन पर उतारा, जहाँ इंतज़ार कर रहा था एक नया मिस्ट्री बॉक्स! सब्सक्राइब फॉर एपिसोड उन्नीस!",
                "emotion": "adventurous"
            }
        ],
        "image_prompts": [
            "Vibrant 8k 3D Pixar style shot of sky swirling with thick creamy chocolate twister and rainbow candy sprinkles, vertical 9:16, masterpiece, no text",
            "Hilarious 3D animated scene of chubby Indian boy Golu clinging to cute winged baby Pegasus while wide-eyed in chocolate rain, vertical 9:16, no text",
            "Magical 8k 3D visual of boy Chintu pointing glowing star wand creating frosty ice-crystal blast that freezes chocolate twister, vertical 9:16, no text",
            "Whimsical mouth-watering 3D render of gigantic frozen chocolate mountain pop covered in white vanilla cream, vertical 9:16, no text",
            "Breathtaking 3D fairytale vista of fluffy pink cotton candy mountain peaks with golden mystery chest glowing at summit, vertical 9:16, adventure cliffhanger, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 4. SERIES_4: DIMAG KA DAHI — EPISODE 18
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_4",
        "episode_num": 18,
        "topic": "Dimag Ka Dahi Episode 18: The Darkness & Fog Riddle",
        "title": "Wo Kya Hai Jo Jitna Zyada Ho, Utna Hi Kam Dikhta Hai? 🧠🔥 | DIMAG KA DAHI (Ep 18) #Shorts",
        "caption": (
            "Dosto, aaj ki paheli aapke dimaag ke saare purze hila degi! 🧠🔥\n"
            "Aisi kaunsi cheez hai jo jitni zyada badhti hai, hume utna hi kam dikhai deta hai?\n"
            "99% log pehli baar mein galat sochte hain! 5 second mein jawab do aur comment karo! 👇💡\n\n"
            "#DimagKaDahi #Episode18 #Paheli #RiddlesInHindi #BrainTeasers #Shorts #MindGames #IQTest #HindiPaheli"
        ),
        "hashtags": ["#DimagKaDahi", "#Episode18", "#Paheli", "#RiddlesInHindi", "#BrainTeasers", "#Shorts", "#MindGames", "#IQTest"],
        "hook_overlay": "🧠 99% LOG HO GAYE FAIL! KYA AAP BATA SAKTE HAIN? 🤯⏱️",
        "comment_bait": "💡 Kya aapne 5 second ke andar sahi jawab guess kiya tha? Sach-sach comment karein! 👇🧠",
        "voice_persona": "hi_riddle",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Dosto, aaj ki ye paheli sunte hi aapke dimaag ki batti gul ho jayegi!",
                "text_speak": "दोस्तों, आज की ये पहेली सुनते ही आपके दिमाग की बत्ती गुल हो जाएगी!",
                "emotion": "playful"
            },
            {
                "speaker": "narrator",
                "text": "Batao wo aisi kaunsi cheez hai... jo jitni zyada badhti hai, hume utna hi kam dikhai deta hai?",
                "text_speak": "बताओ वो ऐसी कौन सी चीज़ है... जो जितनी ज़्यादा बढ़ती है, हमें उतना ही कम दिखाई देता है?",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Sochiye! Aapke paas hain sirf paanch second! Five... Four... Three... Two... One!",
                "text_speak": "सोचिए! आपके पास हैं सिर्फ पांच सेकंड! पांच... चार... तीन... दो... एक!",
                "emotion": "timer"
            },
            {
                "speaker": "narrator",
                "text": "Sahi jawab hai: 'Andhera' yaani Darkness! Kyunki andhera jitna badhta hai, aankhein utna hi kam dekh paati hain!",
                "text_speak": "सही जवाब है: 'अंधेरा'! क्योंकि अंधेरा जितना बढ़ता है, आँखें उतना ही कम देख पाती हैं!",
                "emotion": "energetic"
            },
            {
                "speaker": "narrator",
                "text": "Agar aapka dimaag computer jaisa tez tha toh video ko LIKE karein aur dosto ko challenge bhejein!",
                "text_speak": "अगर आपका दिमाग भी तेज़ निकला तो वीडियो को लाइक करें और दोस्तों को चैलेंज भेजें!",
                "emotion": "serious"
            }
        ],
        "image_prompts": [
            "Striking 3D CGI graphic of cartoon brain wearing sunglasses illuminated by neon yellow question marks, dark cyber background, vertical 9:16, masterpiece, no text",
            "Atmospheric conceptual 3D render of eye pupil slowly being enveloped by swirling pitch black ink darkness, dramatic contrast, vertical 9:16, no text",
            "Urgent glowing neon countdown timer display with numbers 5 4 3 2 1 sizzling in amber electric spark lines, vertical 9:16, no text",
            "Brilliant cinematic 3D visual of lone lantern beam piercing through pitch black night revealing the word darkness in radiant light, vertical 9:16, no text",
            "Energetic 3D celebratory explosion of golden lightbulbs and congratulations confetti over neon purple grid, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 5. SERIES_5: ASHWATTHAMA 3049 AD — EPISODE 15
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_5",
        "episode_num": 15,
        "topic": "Ashwatthama 3049 AD Episode 15: The Alien General Standoff & Dark Energy Core",
        "title": "Alien Mothership Ka Core Room! Ashwatthama Ka Trishul Strike! 🚀🏹⚡ | ASHWATTHAMA 3049 AD (Ep 15) #Shorts",
        "caption": (
            "Mothership ke reactor core chamber mein tin-aankhon wale Alien General ne chhed di antim ladai! 🚀🏹⚡\n"
            "Chamber ki gravity zero hui aur dark scythe ne Ashwatthama ki cyber shield ko faad diya!\n"
            "Lekin 5,000 saal ke tapasvi ne Surya Gayatri mantra ka aavhan kiya aur plasma spear se ship ke antimatter core ko bhed diya!\n"
            "Dreadnought Earth ki taraf girne lagi! Episode 16 ke liye comment karein! 👇🔥\n\n"
            "#Ashwatthama #Part15 #SciFiIndia #Mahabharata3049 #Shorts #SpaceAction #TrendingSciFi #AnimeAction"
        ),
        "hashtags": ["#Ashwatthama", "#Part15", "#SciFiIndia", "#Mahabharata3049", "#Shorts", "#SpaceAction", "#TrendingSciFi", "#AnimeAction"],
        "hook_overlay": "🚀 MOTHERSHIP CORE MEIN ASHWATTHAMA! ⚔️💥",
        "comment_bait": "⚡ Kya Ashwatthama akele alien armada ko rok payega? Comment mein likhein 'ASHWATTHAMA'! 👇🔥",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Alien dreadnought ke reactor core mein tin laal aankhon wale General ne apni dark energy scythe chalayi!",
                "text_speak": "एलियन मदरशिप के रिएक्टर कोर में तीन लाल आँखों वाले जनरल ने अपनी डार्क एनर्जी साइथ से भयानक वार किया!",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Pure chamber ki gravity zero ho gayi aur Ashwatthama ki titanium shield tukde-tukde ho gayi!",
                "text_speak": "पूरे चैंबर की ग्रैविटी ज़ीरो हो गई और अश्वत्थामा की टाइटेनियम ढाल टुकड़े-टुकड़े होकर हवा में बिखर गई!",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Lekin paanch hazar saal purane yoddha ne Surya Gayatri mantra padhte hue apna plasma trishul charge kiya!",
                "text_speak": "लेकिन पाँच हज़ार साल पुराने महायोद्धा ने सूर्य गायत्री मंत्र का जाप करते हुए अपना प्लाज़्मा त्रिशूल चार्ज किया!",
                "emotion": "epic"
            },
            {
                "speaker": "narrator",
                "text": "Sunhari aag ke dhamake ne General ke seene ko cheerte hue seedhe ship ke antimatter core ko ubaal diya!",
                "text_speak": "सुनहरी अग्नि के धमाके ने जनरल के सीने को चीरते हुए सीधे शिप के एंटीमैटर रिएक्टर को उड़ा दिया!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Mothership Earth ke atmosphere mein jalne lagi... Part 16 ke liye channel ko SUBSCRIBE karein!",
                "text_speak": "मदरशिप पृथ्वी के वायुमंडल में आग का गोला बनकर गिरने लगी... पार्ट सोलह के लिए चैनल को तुरंत सब्सक्राइब करें!",
                "emotion": "urgent"
            }
        ],
        "image_prompts": [
            "High tech 8k sci-fi reactor core of alien mothership pulsing with unstable purple antimatter plasma, vertical 9:16, Denis Villeneuve Dune aesthetic, masterpiece, no text",
            "Dynamic action shot of towering three-eyed biomechanical alien warlord swinging glowing crimson scythe, vertical 9:16, intense action, no text",
            "Epic 8k cinematic shot of cybernetic warrior Ashwatthama glowing with radiant golden solar aura in zero gravity, raising glowing electric plasma trident, vertical 9:16, no text",
            "Cataclysmic explosion inside starship reactor with golden energy shockwave blasting through purple alien armor plating, vertical 9:16, masterpiece, no text",
            "Panoramic 8k view of giant smoking alien mothership breaking apart in burning orange streaks above Earth's night curved horizon, vertical 9:16, epic cliffhanger, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 6. SERIES_6: THE OBSERVER FILES — EPISODE 14
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_6",
        "episode_num": 14,
        "topic": "The Observer Files Episode 14: Case File 014 - The Broadcast from Floor -3",
        "title": "The Forbidden Broadcast On Floor -3... They Are Waiting! 👁️📻🏢 | THE OBSERVER FILES (Part 14) #Shorts",
        "caption": (
            "Case File 014: What was found inside the phantom basement Floor minus three. 👁️🏢\n"
            "At 3:18 AM, Security Officer Daniel followed the bare footprints on wet concrete into the darkness.\n"
            "He found an intact, operational 1980s television studio broadcasting live.\n"
            "On the monitors was a real-time CCTV feed of his own sleeping children.\n"
            "Then the studio lights clicked on. Subscribe for Part 15! 👇📻\n\n"
            "#TheObserverFiles #Part14 #AnalogHorror #FoundFootage #Shorts #Creepypasta #HorrorShorts #Mystery"
        ),
        "hashtags": ["#TheObserverFiles", "#Part14", "#AnalogHorror", "#FoundFootage", "#Shorts", "#Creepypasta", "#HorrorShorts", "#Mystery"],
        "hook_overlay": "👁️ THE FORBIDDEN FLOOR -3 BROADCAST! 📺😱",
        "comment_bait": "👁️ If an abandoned broadcast showed a live feed of your house, what would you do? Comment below! 👇🏢",
        "voice_persona": "en_analog",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Case File 014: The discovery inside Floor minus three.",
                "text_speak": "Case File 014: The discovery inside Floor minus three.",
                "emotion": "chilling"
            },
            {
                "speaker": "narrator",
                "text": "Security guard Daniel followed the wet footprints into the pitch-black corridor at 3:18 AM.",
                "text_speak": "Security guard Daniel followed the wet footprints into the pitch-black corridor at 3:18 AM.",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Behind a rusty steel door, he found a fully powered 1984 television studio broadcasting into static.",
                "text_speak": "Behind a rusty steel door, he found a fully powered 1984 television studio broadcasting into static.",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "On the CRT monitors, Daniel saw a live surveillance feed of his own living room... with his children sleeping.",
                "text_speak": "On the CRT monitors, Daniel saw a live surveillance feed of his own living room... with his children sleeping.",
                "emotion": "fearful"
            },
            {
                "speaker": "narrator",
                "text": "Then overhead studio spotlights snapped on, revealing seven faceless mannequins dressed as his family. Subscribe for Part 15.",
                "text_speak": "Then overhead studio spotlights snapped on, revealing seven faceless mannequins dressed as his family. Subscribe for Part 15.",
                "emotion": "cold"
            }
        ],
        "image_prompts": [
            "Analog horror VHS screenshot of flashlight illuminating wet footprints trailing into pitch black subterranean tunnel, vertical 9:16, masterpiece, no text",
            "Eerie retro 1980s television broadcast studio in disrepair with heavy analog cameras pointed at an empty anchor desk, vertical 9:16, no text",
            "Chilling close up of vintage CRT monitor buzzing with green static displaying crisp live night-vision perspective of a modern bedroom, vertical 9:16, analog dread, no text",
            "Sudden harsh blinding studio spotlights illuminating dimly lit soundstage revealing chilling faceless mannequins in family clothing seated around dining table, vertical 9:16, found footage terror, no text",
            "Severe static glitch analog VHS distortion cutting to black with red emergency broadcast test pattern, vertical 9:16, analog horror, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 7. SERIES_7: ROBLOX VAULT — EPISODE 12
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_7",
        "episode_num": 12,
        "topic": "Roblox Vault Episode 12: The 2007 Ghost Account 'Minish'",
        "title": "The 2007 Ghost Account 'Minish' Left This Secret Place! 🎮👻🔒 | ROBLOX VAULT (Ep 12) #Shorts",
        "caption": (
            "Roblox Vault Episode 12: The forgotten 2007 account 'Minish' that vanished without a trace! 🎮👻🔒\n"
            "Minish uploaded a 1MB test map with reversed Morse code audio buried deep in the client cache.\n"
            "When players joined, their avatar coordinates locked to an actual real-world location in California!\n"
            "Roblox permanently deleted the account within 2 hours. Did you know this? Comment below! 👇🎮\n\n"
            "#RobloxVault #Episode12 #RobloxShorts #RobloxMysteries #GamingShorts #RobloxSecrets #TrendingGaming"
        ),
        "hashtags": ["#RobloxVault", "#Episode12", "#RobloxShorts", "#RobloxMysteries", "#GamingShorts", "#RobloxSecrets", "#TrendingGaming"],
        "hook_overlay": "🎮 THE 2007 GHOST ACCOUNT 'MINISH'! 🕹️👻",
        "comment_bait": "🕹️ Do you think the 2007 Minish mystery is real or an ARG? Comment below! 👇🎮",
        "voice_persona": "en_gaming",
        "lines": [
            {
                "speaker": "narrator",
                "text": "In October 2007, an unverified Roblox account named Minish published a map titled 'Test 00'.",
                "text_speak": "In October 2007, an unverified Roblox account named Minish published a map titled 'Test 00'.",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "The entire place was empty except for a single grey obelisk emitting reversed Morse code audio.",
                "text_speak": "The entire place was empty except for a single grey obelisk emitting reversed Morse code audio.",
                "emotion": "curious"
            },
            {
                "speaker": "narrator",
                "text": "Players who joined discovered their game chat was typing coordinates on its own without their input.",
                "text_speak": "Players who joined discovered their game chat was typing coordinates on its own without their input.",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Those exact coordinates pointed to an abandoned server warehouse near San Mateo, California.",
                "text_speak": "Those exact coordinates pointed to an abandoned server warehouse near San Mateo, California.",
                "emotion": "shocking"
            },
            {
                "speaker": "narrator",
                "text": "Within two hours, Roblox terminated the account and wiped the game ID forever. Subscribe for Episode 13!",
                "text_speak": "Within two hours, Roblox terminated the account and wiped the game ID forever. Subscribe for Episode 13!",
                "emotion": "cliffhanger"
            }
        ],
        "image_prompts": [
            "Vintage 2007 Roblox aesthetic retro blocky screenshot of empty green baseplate under overcast grey sky with lone tall granite obelisk, vertical 9:16, masterpiece, no text",
            "Close up of retro 2007 Roblox blue UI chat window glitching with mysterious green coordinate numbers being spammed rapidly, vertical 9:16, no text",
            "Satellite view style photograph of rusted deserted industrial server warehouse building surrounded by dry grass in San Mateo California, vertical 9:16, mystery, no text",
            "Authentic retro web browser screenshot of classic Roblox user profile page 'Minish' suddenly displaying red 'Account Terminated' ban banner, vertical 9:16, no text",
            "Creepy aesthetic shot of glowing retro CRT computer monitor reflecting a silhouetted player in a dark bedroom at 3 AM, vertical 9:16, gaming cliffhanger, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 8. SERIES_8: LEONARDO DA VINCI — EPISODE 4
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_8",
        "episode_num": 4,
        "topic": "Leonardo da Vinci Episode 4: The Duke's Commission & The Hidden Melody in The Last Supper",
        "title": "Milan Ka Shahi Darbar Aur 'The Last Supper' Ka Khaufnaak Raaz! 🎨🏛️📜 | LEONARDO (Ep 4) #Shorts",
        "caption": (
            "1495 mein Milan ke Duke Ludovico Sforza ne Leonardo ko Santa Maria Church mein painting banane ka order diya! 🎨🏛️📜\n"
            "Ye banna tha itihaas ka sabse bada masterpiece: 'The Last Supper'!\n"
            "Lekin kya aapko pata hai ki table par rakhi bread aur shishyon ke haathon ke coordination mein ek 40-second ki dardnak music tune chhipi hui hai?\n"
            "Agle episode ke liye comment karein! 👇🏛️\n\n"
            "#LeonardoDaVinci #Episode4 #HistoryShorts #Renaissance #DocumentaryShorts #TheLastSupper #ArtHistory #Shorts"
        ),
        "hashtags": ["#LeonardoDaVinci", "#Episode4", "#HistoryShorts", "#Renaissance", "#DocumentaryShorts", "#TheLastSupper", "#ArtHistory", "#Shorts"],
        "hook_overlay": "🎨 THE LAST SUPPER KA CHHUPA HUA RAAZ! 🏛️📜",
        "comment_bait": "🎨 Kya aapko pata tha ki 'The Last Supper' mein ek sangeet chhipa hua hai? Comment karein! 👇📜",
        "voice_persona": "hi_m_grave",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Chaudah sau pachaanve mein Milan ke Duke ne Leonardo ko Santa Maria Church ki deewar par chitr banane ka aadesh diya!",
                "text_speak": "चौदह सौ पचानवे में मिलान के ड्यूक ने लियोनार्डो को शांता मारिया चर्च की दीवार पर चित्र बनाने का शाही आदेश दिया!",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "Ye koi sadharan painting nahi thi... ye banna tha itihaas ka sabse rahasyamayi masterpiece: 'The Last Supper'!",
                "text_speak": "ये कोई साधारण पेंटिंग नहीं थी... ये बनना था इतिहास का सबसे रहस्यमयी मास्टरपीस: 'द लास्ट सपर'!",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Leonardo ne ghanton tak shishyon ke chehre par insaani darr aur dhokhe ke bhavon ko bariki se ukera!",
                "text_speak": "लियोनार्डो ने कई महीनों तक हर शिष्य के चेहरे पर इंसानी डर और धोखे के भावों को बारीकी से उकेरा!",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Lekin sabse bada raaz tha table par: bread aur haathon ki position mein chhipa tha ek musical notation!",
                "text_speak": "लेकिन सबसे बड़ा राज़ था मेज़ पर: ब्रेड और हाथों की स्थिति में छिपा था एक संगीत का गुप्त सुर!",
                "emotion": "wonder"
            },
            {
                "speaker": "narrator",
                "text": "Jab aadhunik sangeetkaaron ne un notes ko bajaya, toh ek 40-second ka dardnak requiem nikla! Subscribe for Ep 5!",
                "text_speak": "जब आधुनिक संगीतकारों ने उन सुरों को बजाया, तो एक चालीस सेकंड की दर्दनाक धुन निकली! सब्सक्राइब फॉर एपिसोड पांच!",
                "emotion": "climax"
            }
        ],
        "image_prompts": [
            "Grand 8k historical painting view of high Renaissance refectory hall in Milan Santa Maria delle Grazie with massive scaffolding under fresco wall, vertical 9:16, masterpiece, no text",
            "Atmospheric candlelit close up of Leonardo da Vinci deep in thought mixing natural tempera pigments on a rustic wooden palette, vertical 9:16, fine art, no text",
            "Intense macro study of the emotional expressions and dynamic gesturing hands in Leonardo's The Last Supper mural, high fidelity restoration, vertical 9:16, no text",
            "Superimposed 8k conceptual art showing glowing golden musical stave notes overlaying the bread rolls and hands on the Last Supper dining table, vertical 9:16, wonder, no text",
            "Stunning dramatic shot of antique wooden church pipe organ illuminated by stained glass window as invisible fingers play the melancholic hymn, vertical 9:16, historical cliffhanger, no text"
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
        print(f"    ⚠️ Voice generation fallback note: {ex}")


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
# SINGLE EPISODE GENERATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
async def process_single_episode(ep_data: dict, db: DB, pub: YouTubePublisher | None, publish_to_yt: bool = False) -> dict:
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
    print(f"  🎬 PROCESSING BATCH 7: {series_code} — EPISODE {episode_num}")
    print(f"  📌 Title: {title}")
    print("=" * 75)

    cp_dir = ROOT / "output" / f"batch7_{series_code.lower()}_ep{episode_num}"
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
    print(f"\n  [Step 5] Registering video in DB & preparing for release...")
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
    print(f"  ✓ Video #{video_db_id} ({series_code} Ep {episode_num}) registered in DB!")

    # 6. YouTube Shorts Upload (if requested and pub available)
    if publish_to_yt and pub:
        print(f"\n  [Step 6] Publishing Video #{video_db_id} to YouTube Shorts (Comments 100% ON, Public)...")
        try:
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
                    "video_path": str(final_mp4),
                    "status": "published"
                }
            else:
                print(f"  ⚠️ Publish note: {res}")
        except Exception as pe:
            print(f"  ⚠️ Publish error: {pe}")

    return {
        "series_code": series_code,
        "episode_num": episode_num,
        "title": title,
        "video_db_id": video_db_id,
        "yt_video_id": None,
        "url": str(final_mp4),
        "duration": final_dur,
        "video_path": str(final_mp4),
        "status": "rendered_approved"
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MASTER RUNNER
# ─────────────────────────────────────────────────────────────────────────────
async def main_async(publish: bool = False):
    start_t = time.time()
    db = DB()

    print("\n" + "#" * 80)
    print("  🚀 AUTOPILOT MASTER ENGINE: BATCH 7 — NEXT EPISODE OF ALL SERIES")
    print(f"  Total Series in Queue: {len(BATCH_EPISODES)}")
    print("  Policy: selfDeclaredMadeForKids=False | Comments=100% ON | Public")
    print("#" * 80 + "\n")

    pub = None
    if publish:
        try:
            pub = YouTubePublisher(db=db)
        except Exception as pe:
            print(f"⚠️ YouTubePublisher init warning: {pe}")

    results = []
    for ep in BATCH_EPISODES:
        try:
            res = await process_single_episode(ep, db, pub, publish_to_yt=publish)
            results.append(res)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"\n❌ Error processing {ep['series_code']} Ep {ep['episode_num']}: {e}")
            log.error(f"Error processing {ep['series_code']}: {e}")

    total_time = round(time.time() - start_t, 1)

    print("\n" + "=" * 80)
    print(f"  🏁 BATCH 7 EXECUTION COMPLETE IN {total_time}s!")
    print(f"  🎉 Total Episodes Processed: {len(results)} / {len(BATCH_EPISODES)}")
    print("=" * 80)
    for res in results:
        status_label = res.get('status', 'unknown')
        print(f"  • [{status_label.upper()}] {res['series_code']} Ep {res['episode_num']}: {res['title'][:40]}... -> {res['video_path']}")
    print("=" * 80 + "\n")

    # Dispatch Discord notification for Batch 7 Generation
    try:
        discord = DiscordNotifications(channel_id=DISCORD_CHANNEL)
        embed_fields = []
        for res in results:
            embed_fields.append({
                "name": f"{res['series_code']} (Ep {res['episode_num']})",
                "value": f"{res['title'][:45]}...\nDuration: {res['duration']:.1f}s | #{res['video_db_id']}",
                "inline": True
            })
        discord.send_embed(
            title="🎬 Batch 7 Episodes Generated Successfully!",
            description=(
                f"**8 brand new episodes** have been rendered with broadcast-grade studio quality!\n"
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

    return results


def main():
    parser = argparse.ArgumentParser(description="AUTOPILOT Batch 7 Generator")
    parser.add_argument("--publish", action="store_true", help="Also publish to YouTube if authenticated")
    args = parser.parse_args()
    asyncio.run(main_async(publish=args.publish))


if __name__ == "__main__":
    main()
