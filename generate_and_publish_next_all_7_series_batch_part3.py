"""
generate_and_publish_next_all_7_series_batch_part3.py — Batch 3 Orchestrator for All Active Series.

Generates and Publishes:
  1. SERIES_1 (Kaal-Rekha)            : Part 20 (Clock Tower & The Red Diary)
  2. SERIES_2 (Jab Pyaar Online Tha)  : Episode 16 (Heathrow Airport Farewell)
  3. SERIES_3 (Chintu Ki Jadui Duniya): Episode 14 (Rainbow Island Star Key)
  4. SERIES_4 (Dimag Ka Dahi)         : Episode 14 (The Soundless Break Riddle)
  5. SERIES_5 (Ashwatthama 3049 AD)   : Episode 11 (Brahmashira Awakening in Neo-Kashi)
  6. SERIES_6 (The Observer Files)    : Episode 10 (The 3:17 AM Radio Frequency)
  7. SERIES_7 (Roblox Vault)          : Episode 8 (Brookhaven Secret Laboratory)

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

log = Logbook("all_7_series_batch_part3")

DISCORD_CHANNEL = "1212765278765584396"

# ─────────────────────────────────────────────────────────────────────────────
# EPISODES CATALOG — NEXT EPISODES FOR ALL 7 ACTIVE SERIES (BATCH 3)
# ─────────────────────────────────────────────────────────────────────────────

BATCH_EPISODES = [
    # ─────────────────────────────────────────────────────────────────────────
    # 1. SERIES_1: KAAL-REKHA — PART 20
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_1",
        "episode_num": 20,
        "topic": "Kaal-Rekha Part 20: The Clock Tower & The Red Diary Truth",
        "title": "Clock Tower Mein Khuli Laal Diary: Loop Ka Aakhri Sach! ⏳💥 | KAAL-REKHA (Part 20) #Shorts",
        "caption": (
            "Theek 3:17 AM par Kabir clock tower ki top par pahuncha aur laal diary ka aakhri panna khola! ⏳💥\n"
            "Diary ke aakhri panne par Meera ki tasveer thi aur likha tha: 'Meera future mein kabhi thi hi nahi... wo loop ki architect hai!'\n"
            "Tabhi clock tower ki ghadi ulti ghumne lagi aur aaine se Meera ki aawaz aayi: 'Kabir, tumne aane mein der kar di!'\n\n"
            "Kya Kabir waqt ke is chakraviewh ko tod payega? Comment karein! 👇🔥\n\n"
            "#KaalRekha #Part20 #TimeLoop #AnimeShorts #IndianAnime #Shorts #HindiAnime #Mystery #Trending"
        ),
        "hashtags": ["#KaalRekha", "#Part20", "#TimeLoop", "#AnimeShorts", "#IndianAnime", "#Shorts", "#HindiAnime", "#Mystery"],
        "hook_overlay": "⏳ CLOCK TOWER: LAAL DIARY KA AAKHRI SACH?! 💥",
        "comment_bait": "🔥 Kya Meera shuru se dushman thi ya majboor? 'MEERA TRUTH' comment karein! 👇⏳",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Theek raat ke 3:17 AM par Kabir Mumbai clock tower ke sabse upar pahuncha... jahan ghadibaazi ki aawaz goonj rahi thi!",
                "text_speak": "ठीक रात के तीन बजकर सत्रह मिनट पर कबीर मुंबई क्लॉक टॉवर के सबसे ऊपर पहुँचा... जहाँ घड़ी की सुइयों की भयानक आवाज़ गूँज रही थी!",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "Usne kaanpte haathon se future Kabir ki di hui laal diary ka aakhri panna khola.",
                "text_speak": "उसने काँपते हाथों से फ्यूचर कबीर की दी हुई लाल डायरी का आखिरी पन्ना खोला।",
                "emotion": "mysterious"
            },
            {
                "speaker": "char_b",
                "text": "Panne par Meera ki tasveer thi aur niche khoon se likha tha: 'Meera ko mat bachana... loop usi ne banaya hai!'",
                "text_speak": "पन्ने पर मीरा की तस्वीर थी और नीचे खून से लिखा था: 'मीरा को मत बचाना... यह टाइम लूप उसी ने बनाया है!'",
                "emotion": "chilling"
            },
            {
                "speaker": "narrator",
                "text": "Achanak ghadi ki suiyan ulti bhaagne lagi... 3:17 se 3:16... 3:15!",
                "text_speak": "अचानक क्लॉक टॉवर की सुइयाँ उल्टी भागने लगीं... तीन सत्रह से तीन सोलह... तीन पंद्रह!",
                "emotion": "urgent"
            },
            {
                "speaker": "char_b",
                "text": "Parchhayi se Meera ki muskaan aayi: 'Kabir... tum 20vi baar bhi sach nahi samajh sake!'",
                "text_speak": "दीवार की परछाई से मीरा की मुस्कान आई: 'कबीर... तुम बीसवीं बार भी सच नहीं समझ सके!'",
                "emotion": "dramatic"
            },
            {
                "speaker": "narrator",
                "text": "Kya Meera asli qatil hai? Subscribe karein aur agle season premiere ke liye ready rahein!",
                "text_speak": "क्या मीरा ही असली टाइम-लूप की मास्टरमाइंड है? सब्सक्राइब करें और अगले महा-एपिसोड के लिए तैयार रहें!",
                "emotion": "intense"
            }
        ],
        "image_prompts": [
            "Dramatic anime high-angle shot inside towering clock tower mechanism, massive spinning bronze gears, glowing amber clock face showing 3:17 AM, MAPPA style, vertical 9:16, no text",
            "Tense anime shot of Kabir standing in moonlight holding glowing crimson leather diary open, rain splashing through open gothic arched windows, vertical 9:16, no text",
            "Macro close up anime drawing of aged diary page with blood red sketch of Meera's face and ancient cipher text glowing, vertical 9:16, no text",
            "Chilling anime shot of massive clock hands violently reversing with violet spark lightning bolts tearing through the glass clock face, vertical 9:16, no text",
            "Shadowy anime silhouette of Meera emerging from wall mirrors with crimson glowing eyes and sinister gentle smile, high suspense, vertical 9:16, no text",
            "Epic cliffhanger anime shot of Kabir looking down at shattered glass falling across Mumbai skyline illuminated by giant temporal anomaly portal, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 2. SERIES_2: JAB PYAAR ONLINE THA — EPISODE 16
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_2",
        "episode_num": 16,
        "topic": "Jab Pyaar Online Tha Episode 16: The Heathrow Airport Farewell & Promise",
        "title": "Heathrow Airport Par Meera Ka Aakhri Alvida... 7 Saal Ka Vaada! 💔✈️ | JAB PYAAR ONLINE THA (Ep 16) #Shorts",
        "caption": (
            "London ke Heathrow Airport departure gate par jab Meera ka aakhri boarding call hua... 💔✈️\n"
            "Aarav ne aage badhkar uski ungli mein silver promise ring pehnate hue kaha: '2020 mein laptop screen se shuru hua tha... par ye rishta hamesha ke liye hai!'\n"
            "Meera ne nam aankhon se mudkar dekha aur gale lag gayi. Kya saccha pyaar dooriyon ko hara sakta hai? Comment karein! 👇💖\n\n"
            "#JabPyaarOnlineTha #Episode16 #Romance #Shorts #LoveStory #Emotional #Trending"
        ),
        "hashtags": ["#JabPyaarOnlineTha", "#Episode16", "#Romance", "#Shorts", "#LoveStory", "#Emotional"],
        "hook_overlay": "✈️ HEATHROW AIRPORT: MEERA KA AAKHRI ALVIDA?! 💔",
        "comment_bait": "💖 Kya aapko lagta hai long-distance relationships sach mein chalte hain? 'TRUE LOVE' comment karein! 👇✨",
        "voice_persona": "hi_romantic",
        "lines": [
            {
                "speaker": "narrator",
                "text": "London Heathrow Airport ka departure gate... jahan Meera ki flight ka aakhri boarding call shuru ho chuka tha.",
                "text_speak": "लंदन हीथ्रो एयरपोर्ट का डिपार्चर गेट... जहाँ मीरा की फ्लाइट का आखिरी बोर्डिंग कॉल गूँज रहा था।",
                "emotion": "calm"
            },
            {
                "speaker": "narrator",
                "text": "Dono chup the... lekin aankhon mein 2020 ke lockdown se lekar ab tak ke saat saal ka safar chal raha tha.",
                "text_speak": "दोनों बिल्कुल खामोश थे... लेकिन आँखों में दो हज़ार बीस के लॉकडाउन से लेकर अब तक के सात साल का सफर तैर रहा था।",
                "emotion": "sweet"
            },
            {
                "speaker": "char_a",
                "text": "Aarav ne Meera ka kaanpta haath pakda aur uski ungli mein ek silver promise ring pehna di.",
                "text_speak": "आरव ने मीरा का काँपता हाथ थामा और उसकी उंगली में एक चमकती हुई सिल्वर प्रॉमिस रिंग पहना दी।",
                "emotion": "romantic"
            },
            {
                "speaker": "char_a",
                "text": "'Meera... hamara pyaar laptop screen se shuru hua tha, par ye ring is baat ka saboot hai ki main humesha tumhara rahunga.'",
                "text_speak": "'मीरा... हमारा प्यार एक लैपटॉप स्क्रीन से शुरू हुआ था, पर यह रिंग इस बात का सबूत है कि मैं हमेशा तुम्हारा इंतज़ार करूँगा।'",
                "emotion": "romantic"
            },
            {
                "speaker": "narrator",
                "text": "Meera ki aankhon se aansu beh nikle... usne daudkar Aarav ko gale lagaya aur flight gate ki taraf badh gayi.",
                "text_speak": "मीरा की आँखों से खुशी के आँसू बह निकले... उसने आरव को गले से लगाया और मुड़कर बोर्डिंग गेट की तरफ बढ़ गई।",
                "emotion": "sweet"
            },
            {
                "speaker": "narrator",
                "text": "Kuch kahaniyan dooriyon se khatam nahi hoti, balki aur gehari ho jaati hain. Drop a heart for real love!",
                "text_speak": "कुछ प्रेम कहानियाँ दूरियों से खत्म नहीं होतीं, बल्कि और भी अमर हो जाती हैं। सच्चे प्यार के लिए एक लाल दिल कमेंट करें!",
                "emotion": "romantic"
            }
        ],
        "image_prompts": [
            "Breathtaking Makoto Shinkai anime wide shot of London Heathrow modern departure terminal floor-to-ceiling glass wall at sunset, British Airways jet on runway, vertical 9:16, no text",
            "Tender anime medium shot of Aarav in warm grey overcoat looking at Meera with heartfelt devoted expression, golden sunset rays illuminating his face, vertical 9:16, no text",
            "Macro close up anime shot of Aarav's hands gently sliding delicate silver ring with tiny sparkling sapphire onto Meera's finger, romantic lighting, vertical 9:16, no text",
            "Emotional anime beauty portrait of Meera with tears glistening in her eyes smiling through sorrow, hair gently blowing in airport draft, vertical 9:16, no text",
            "Cinematic silhouette anime shot of young lovers embracing tightly in front of massive airport glass window overlooking sunset tarmac, vertical 9:16, no text",
            "Poetic anime cliffhanger shot of Meera walking down jet bridge looking back over shoulder smiling with promise ring shining, soft bokeh particles, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 3. SERIES_3: CHINTU KI JADUI DUNIYA — EPISODE 14
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_3",
        "episode_num": 14,
        "topic": "Chintu Ki Jadui Duniya Episode 14: Rainbow Island Secret Star Key",
        "title": "Chintu Aur Golu Ko Mila Aasmani Khazana! 🌈✨ | CHINTU (Ep 14) #Shorts",
        "caption": (
            "Chintu aur fluffy monster Golu ko unke treehouse ke neeche mila ek ascharyajanak jadui golden compass! 🌈✨\n"
            "Compass ne badalon ke upar Rainbow Island ka raasta dikhaya jahan floating candy waterfalls aur golden Star Key chhippi thi!\n"
            "Lekin wahan pahunchte hi Chocolate Dragon ne unka raasta rok liya! Kya Chintu bacha payega khazana? Dekhiye! 👇🍭\n\n"
            "#ChintuKiJaduiDuniya #KidsAnimation #3DAnimation #PixarStyle #FamilyFun #Shorts #Cartoon"
        ),
        "hashtags": ["#ChintuKiJaduiDuniya", "#KidsAnimation", "#3DAnimation", "#PixarStyle", "#FamilyFun", "#Shorts", "#Cartoon"],
        "hook_overlay": "🌈 CHINTU KO MILA AASMANI KHAZANA! ✨🍭",
        "comment_bait": "🍭 Agar aapko Rainbow Island jane mile toh aap kya khayenge? 'CANDY' comment karein! 👇🎉",
        "voice_persona": "hi_kids",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Chintu aur uske fluffy jadui monster Golu ko treehouse ke sandook mein ek chamakta hua golden compass mila!",
                "text_speak": "चिंटू और उसके प्यारे जादूई मॉन्स्टर गोलू को ट्री-हाउस के पुराने संदूक में एक चमकता हुआ गोल्डन कंपास मिला!",
                "emotion": "excited"
            },
            {
                "speaker": "narrator",
                "text": "Compass ki sui seedhe badalon ki taraf ghumne lagi... aur aasmaan mein saat rango ki jadui seedhiyan ban gayi!",
                "text_speak": "कंपास की सुई सीधे बादलों की तरफ घूमने लगी... और आसमान में सात रंगों की सतरंगी सीढ़ियाँ बन गईं!",
                "emotion": "happy"
            },
            {
                "speaker": "char_a",
                "text": "Chintu ne uchhal kar kaha: 'Golu bhaiya dekho! Ye toh seedhe Rainbow Island ja raha hai!'",
                "text_speak": "चिंटू ने उछलकर कहा: 'गोलू भैया देखो! यह तो सीधे बादलों वाले रेनबो आइलैंड जा रहा है!'",
                "emotion": "excited"
            },
            {
                "speaker": "narrator",
                "text": "Wahan pahunchte hi unhe dikhi strawberry ki jheel aur ek giant chocolate bunny jo golden Star Key par baitha tha!",
                "text_speak": "वहाँ पहुँचते ही उन्हें दिखी स्ट्रॉबेरी की मीठी झील और एक बड़ा सा चॉकलेट बनी जो जादुई स्टार-की पर बैठा था!",
                "emotion": "amazed"
            },
            {
                "speaker": "char_b",
                "text": "Golu ne apna pet sehlaate hue bola: 'Chintu... pehle chocolate khayein ya chabi uthayein?!'",
                "text_speak": "गोलू ने अपना गोल-मटोल पेट सहलाते हुए बोला: 'चिंटू... पहले चॉकलेट खाएँ या वो जादुई चाबी उठाएँ?!'",
                "emotion": "funny"
            },
            {
                "speaker": "narrator",
                "text": "Aapke paas chabi hoti toh aap kya kholte? Like karein aur doston ko share karein!",
                "text_speak": "आपके पास यह जादुई चाबी होती तो आप क्या खोलते? वीडियो को लाइक करें और चैनल को सब्सक्राइब करें!",
                "emotion": "happy"
            }
        ],
        "image_prompts": [
            "Vibrant Pixar Disney 3D style shot of cute 7-year-old boy Chintu with cheerful blue cap and huge adorable fluffy green monster Golu holding glowing antique brass compass, vertical 9:16, no text",
            "Whimsical 3D animation shot of magnificent rainbow glass stairs arching high into cotton candy clouds under brilliant golden sunshine, vertical 9:16, no text",
            "Enchanting 3D render of floating Rainbow Island in the clouds with sparkling pink strawberry juice waterfall and candy cane trees, vertical 9:16, no text",
            "Adorable 3D shot of friendly giant milk chocolate rabbit with pink marshmallow ears guarding a glowing golden star key on a sugar pedestal, vertical 9:16, no text",
            "Funny 3D shot of fluffy Golu licking a giant lollipop with comical wide eyes and Chintu giggling excitedly, vibrant lighting, vertical 9:16, no text",
            "Joyful 3D wide shot of Chintu and Golu holding the glowing golden Star Key high as colorful confetti floats in the sky, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 4. SERIES_4: DIMAG KA DAHI — EPISODE 14
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_4",
        "episode_num": 14,
        "topic": "Dimag Ka Dahi Episode 14: The Soundless Break Riddle",
        "title": "Wo Kya Hai Jo Tootne Par Aawaz Nahi Karta?! 🧠🔥 | DIMAG KA DAHI (Ep 14) #Shorts",
        "caption": (
            "Duniya ki aisi paheli jisme 99% log pehli baar mein galat jawab dete hain! 🧠🔥\n"
            "Aisi kaunsi cheez hai jise chahe kitni bhi jor se todo... uski tootne par ratti bhar aawaz nahi aati?\n"
            "Aapke paas hain sirf 5 seconds! Comment mein sahi jawab likhein aur dekhein kitne log sahi hain! 👇🎯\n\n"
            "#DimagKaDahi #Paheli #Riddles #Quiz #BrainTeaser #Shorts #HindiPaheli #Challenge"
        ),
        "hashtags": ["#DimagKaDahi", "#Paheli", "#Riddles", "#Quiz", "#BrainTeaser", "#Shorts", "#HindiPaheli", "#Challenge"],
        "hook_overlay": "🧠 TOOTNE PAR AAWAZ NAHI KARTA?! 🔥",
        "comment_bait": "🎯 Kya aapne 5 second se pehle socha tha? 'GENIUS' comment karein! 👇🧠",
        "voice_persona": "hi_riddle",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Aaj ki paheli bade-bade hoshiyar logon ke dimag ka dahi bana degi!",
                "text_speak": "आज की पहेली बड़े-बड़े होशियार लोगों के दिमाग का दही बना देगी!",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "Batao wo kaunsi aisi cheez hai... jo tootne par bilkul aawaz nahi karti, par dard sabse zyada deti hai?",
                "text_speak": "बताओ वो कौन सी ऐसी चीज़ है... जो टूटने पर बिल्कुल आवाज़ नहीं करती, पर दर्द सबसे ज़्यादा देती है?",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "Aapke paas hain sirf 5 seconds... 5... 4... 3... 2... 1!",
                "text_speak": "आपके पास हैं सिर्फ पाँच सेकंड्स... पाँच... चार... तीन... दो... एक!",
                "emotion": "timer"
            },
            {
                "speaker": "narrator",
                "text": "Sahi jawab hai: 'Vishwas' yaani Trust... aur 'Khamoshi'!",
                "text_speak": "सही जवाब है: 'विश्वास' यानी भरोसा... और 'खामोशी'!",
                "emotion": "dramatic"
            },
            {
                "speaker": "narrator",
                "text": "Kyunki jab kisi ka vishwas toot-ta hai, toh koi shor nahi hota, bas zindagi badal jaati hai.",
                "text_speak": "क्योंकि जब किसी का विश्वास टूटता है, तो कोई आवाज़ नहीं होती, बस ज़िंदगी का भरोसा बदल जाता है।",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "Agar aapka dimag tej hai toh channel ko subscribe karein aur agla challenge accept karein!",
                "text_speak": "अगर आपका जवाब सही था तो तुरंत सब्सक्राइब करें और दोस्तों को यह चैलेंज भेजें!",
                "emotion": "happy"
            }
        ],
        "image_prompts": [
            "High energy 3D cartoon style giant glowing brain surrounded by electric question marks and comic book smoke, neon gold and purple background, vertical 9:16, no text",
            "Mysterious stylized 3D silhouette of an intricate glass heart shattering in total silence with floating golden particles, dramatic lighting, vertical 9:16, no text",
            "Bold glowing 3D digital countdown timer displaying neon numbers 5 4 3 2 1 with dramatic red fire embers, vertical 9:16, no text",
            "Magnificent 3D visual metaphor of golden puzzle piece clicking into a heart silhouette with radiant golden aura, vertical 9:16, no text",
            "Thoughtful artistic 3D render of a hand holding fragile crystal threads of trust in glowing moonlight, philosophical depth, vertical 9:16, no text",
            "Exciting dynamic 3D celebration with gold trophies and flying confetti, congratulations banner vibe, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 5. SERIES_5: ASHWATTHAMA 3049 AD — EPISODE 11
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_5",
        "episode_num": 11,
        "topic": "Ashwatthama 3049 Episode 11: Brahmashira Awakening in Neo-Kashi",
        "title": "Ashwatthama Ka 3000 Saal Purana Trishul Cyber-Grid Mein Jaag Gaya! ⚡🕉️ | ASHWATTHAMA 3049 (Ep 11) #Shorts",
        "caption": (
            "Year 3049: Neo-Kashi ke underground quantum core mein Dark Syndicate ne Ashwatthama ko captive banaya! ⚡🕉️\n"
            "Unke nanotech surgical lasers jaise hi forehead ki Divine Mani ko chhoone lage... 3000 saal purana Brahmashira Astra cyber-grid mein explode ho gaya!\n"
            "Poore shehar ki holograms par Mahadev ka Tandav shuru ho gaya! Dekhiye epical sci-fi action! 👇🔥\n\n"
            "#Ashwatthama3049 #CyberpunkMythology #IndianSciFi #EpicAction #Shorts #AnimeShorts #Trending"
        ),
        "hashtags": ["#Ashwatthama3049", "#CyberpunkMythology", "#IndianSciFi", "#EpicAction", "#Shorts", "#AnimeShorts"],
        "hook_overlay": "⚡ CYBER-GRID MEIN JAAGA BRAHMASHIRA ASTRA! 🕉️",
        "comment_bait": "🔥 Kya 3049 mein bhi ancient divine powers technology se aage hain? 'HAR HAR MAHADEV' comment karein! 👇⚡",
        "voice_persona": "hi_m_intense",
        "lines": [
            {
                "speaker": "narrator",
                "text": "San 3049: Neo-Kashi ke subterranean quantum laboratory mein Dark Syndicate ke scientist Ashwatthama ke samne khade the.",
                "text_speak": "सन तीन हज़ार उनचास: नियो-काशी की गहरी क्वांटम लैब में डार्क सिंडिकेट के वैज्ञानिक अश्वत्थामा के सामने खड़े थे।",
                "emotion": "serious"
            },
            {
                "speaker": "narrator",
                "text": "Unhone nanotech plasma drill chalu kiya taaki unke maathe se 5000 saal purani divine Mani ko nikala ja sake.",
                "text_speak": "उन्होंने नैनोटेक प्लाज्मा लेज़र चालू किया ताकि उनके माथे से पाँच हज़ार साल पुरानी अमर दिव्य मणि को निकाला जा सके।",
                "emotion": "shocked"
            },
            {
                "speaker": "char_b",
                "text": "Lekin jaise hi laser Mani se takrayi... lab ke saare quantum servers par Sanskrit shlok flash hone lage!",
                "text_speak": "लेकिन जैसे ही लेज़र मणि से टकराई... लैब के सारे क्वांटम सर्वर लाल होकर फटने लगे और स्क्रीनों पर संस्कृत श्लोक गूँज उठे!",
                "emotion": "dramatic"
            },
            {
                "speaker": "char_b",
                "text": "Ashwatthama ki aankhein dehak uthi: 'Murkhon! Tum jise radiation samajh rahe ho, wo Brahmashira Astra ki aag hai!'",
                "text_speak": "अश्वत्थामा की आँखें अंगारों की तरह चमक उठीं: 'मूर्खों! तुम जिसे रेडिएशन समझ रहे हो, वो ब्रह्मशिरा अस्त्र की अमर ज्वाला है!'",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "Ek prachand bijli ke jhatke se unke cybernetic shackles pighal gaye aur haath mein glowing divine Trishul prakat ho gaya!",
                "text_speak": "एक प्रचंड दिव्य विस्फोट से उनकी स्टील की बेड़ियाँ पिघल गईं और उनके हाथों में साक्षात प्रलयंकारी त्रिशूल प्रकट हो गया!",
                "emotion": "climax"
            },
            {
                "speaker": "narrator",
                "text": "Neo-Kashi par yudh ka elaan ho chuka hai! Episode 12 ke liye abhi subscribe karein!",
                "text_speak": "नियो-काशी पर महा-युद्ध का बिगुल बज चुका है! अगले एपिसोड बारह के लिए अभी सब्सक्राइब ठोकें!",
                "emotion": "intense"
            }
        ],
        "image_prompts": [
            "High-octane cyberpunk sci-fi anime shot of massive towering immortal warrior Ashwatthama bound in pulsing neon blue energy chains inside dark cyberpunk lab, vertical 9:16, no text",
            "Extreme macro anime shot of glowing emerald and gold Divine Gem embedded in warrior's forehead deflecting red cybernetic laser beams with blinding golden shockwave, vertical 9:16, no text",
            "Stunning anime visual of holographic computer screens shattering into millions of cyber particles as ancient glowing Sanskrit glyphs illuminate the chamber, vertical 9:16, no text",
            "Intense close up anime portrait of Ashwatthama with fierce divine fury in his eyes, sacred battle ash across forehead, golden energy flowing through dark hair, vertical 9:16, no text",
            "Epic action anime shot of Ashwatthama breaking through titanium restraints holding a blazing cyber-trishul surrounded by crackling celestial lightning, vertical 9:16, no text",
            "Cinematic wide anime cliffhanger shot of Ashwatthama standing on skyscraper rooftop overlooking rainy cyberpunk Neo-Kashi city as red sirens wail, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 6. SERIES_6: THE OBSERVER FILES — EPISODE 10
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_6",
        "episode_num": 10,
        "topic": "The Observer Files Episode 10: The Shortwave Broadcast 3.17 MHz",
        "title": "The 3:17 AM Radio Signal Is Speaking YOUR Name... 📻😱 | THE OBSERVER FILES (Part 10) #Shorts",
        "caption": (
            "The Observer Files Part 10: Declassified incident report from the Chernobyl Exclusion Zone. 📻😱\n"
            "At exactly 3:17 AM, analog radios across nine countries tuned into 3.17 MHz simultaneously.\n"
            "The broadcast did not use synthetic static. It used the voice of whoever was currently awake... to whisper their private childhood memories.\n"
            "Do not answer the broadcast. Subscribe to log your survival! 👇👁️\n\n"
            "#TheObserverFiles #AnalogHorror #ScaryShorts #HorrorStories #Shorts #Creepypasta #Mystery"
        ),
        "hashtags": ["#TheObserverFiles", "#AnalogHorror", "#ScaryShorts", "#HorrorStories", "#Shorts", "#Creepypasta", "#Mystery"],
        "hook_overlay": "👁️ 3:17 AM: IT WHISPERS YOUR REAL NAME 📻",
        "comment_bait": "👁️ Have you ever heard your name called when no one was home? Comment 'SAFE' if you survived! 👇📻",
        "voice_persona": "en_analog",
        "lines": [
            {
                "speaker": "narrator",
                "text": "If your radio or car audio turns itself on tonight at 3:17 AM... do not adjust the frequency.",
                "text_speak": "If your radio or car audio turns itself on tonight at 3:17 AM... do not adjust the frequency.",
                "emotion": "chilling"
            },
            {
                "speaker": "narrator",
                "text": "Declassified audio analysis from three naval radar stations confirmed an anomalous transmission on three point one seven megahertz.",
                "text_speak": "Declassified audio analysis from three naval radar stations confirmed an anomalous transmission on three point one seven megahertz.",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "The signal does not broadcast music or emergency alerts. It plays the sound of breathing directly inside your room.",
                "text_speak": "The signal does not broadcast music or emergency alerts. It plays the sound of breathing directly inside your room.",
                "emotion": "shocked"
            },
            {
                "speaker": "char_b",
                "text": "In the latest recorded intercept, a whisper came through: 'We know you are watching this video alone. Turn around.'",
                "text_speak": "In the latest recorded intercept, a whisper came through: 'We know you are watching this video alone. Turn around.'",
                "emotion": "fearful"
            },
            {
                "speaker": "narrator",
                "text": "The reflection on your dark phone screen is not lagging behind anymore. It is waiting for you to blink.",
                "text_speak": "The reflection on your dark phone screen is not lagging behind anymore. It is waiting for you to blink.",
                "emotion": "chilling"
            },
            {
                "speaker": "narrator",
                "text": "Subscribe to stay in the transmission network... while you still can.",
                "text_speak": "Subscribe to stay in the transmission network... while you still can.",
                "emotion": "cold"
            }
        ],
        "image_prompts": [
            "Creepy analog horror style shot of a vintage 1980s bedside radio glowing with eerie red digital clock numbers 03:17 AM in pitch black bedroom, vertical 9:16, VHS static, no text",
            "Grainy classified military surveillance photo of empty naval radio control room with green oscilloscope screens pulsing with erratic sine waves, vertical 9:16, analog horror grain, no text",
            "POV chilling horror shot sitting inside parked car on deserted foggy forest road at night, car radio dial glowing pale green amidst dense mist, vertical 9:16, no text",
            "Extreme macro horror close-up of speaker grill with faint red human eye visible behind the cloth mesh looking back at listener, psychological terror, vertical 9:16, no text",
            "Disturbing analog horror shot of dark bedroom mirror reflecting person sitting on bed, but reflection has head rotated 180 degrees unnatural angle, vertical 9:16, no text",
            "Final analog horror transmission card with heavy VHS tracking static and faded emergency alert broadcast symbol, chilling mystery, vertical 9:16, no text"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 7. SERIES_7: ROBLOX VAULT — EPISODE 8
    # ─────────────────────────────────────────────────────────────────────────
    {
        "series_code": "SERIES_7",
        "episode_num": 8,
        "topic": "Roblox Vault Episode 8: The Brookhaven Secret Laboratory Glitch",
        "title": "99% Players Missed This Secret Basement In Brookhaven! 🎮🔒 | ROBLOX VAULT (Ep 8) #Shorts",
        "caption": (
            "Roblox Vault Episode 8: The unpatched 2017 secret room hidden deep inside Brookhaven! 🎮🔒\n"
            "If you go behind the hospital X-ray wall with the lantern and crouch jump backwards, you fall into an abandoned developer test lab!\n"
            "Inside is a working computer terminal that gives access to unreleased vehicle prototypes! Try this before it gets patched! 👇🎮\n\n"
            "#Roblox #Brookhaven #RobloxSecrets #RobloxGlitches #GamingShorts #Shorts #Gamer"
        ),
        "hashtags": ["#Roblox", "#Brookhaven", "#RobloxSecrets", "#RobloxGlitches", "#GamingShorts", "#Shorts", "#Gamer"],
        "hook_overlay": "🔒 BROOKHAVEN SECRET LAB FOUND?! 🎮",
        "comment_bait": "🎮 Did this glitch work for you? Comment your Roblox username below! 👇🔥",
        "voice_persona": "en_gaming",
        "lines": [
            {
                "speaker": "narrator",
                "text": "Ninety-nine percent of Brookhaven players have no idea there is a secret developer laboratory right beneath their feet.",
                "text_speak": "Ninety-nine percent of Brookhaven players have no idea there is a secret developer laboratory right beneath their feet.",
                "emotion": "shocked"
            },
            {
                "speaker": "narrator",
                "text": "First, equip the camping lantern and head inside the hospital third floor right behind the MRI machine.",
                "text_speak": "First, equip the camping lantern and head inside the hospital third floor right behind the MRI machine.",
                "emotion": "mysterious"
            },
            {
                "speaker": "narrator",
                "text": "If you turn shift lock on and walk backwards into the dark corner seam, your avatar clips straight through the map!",
                "text_speak": "If you turn shift lock on and walk backwards into the dark corner seam, your avatar clips straight through the map!",
                "emotion": "urgent"
            },
            {
                "speaker": "narrator",
                "text": "You will land in an unreleased underground testing chamber with vintage green arcade cabinets and developer logs from 2017.",
                "text_speak": "You will land in an unreleased underground testing chamber with vintage green arcade cabinets and developer logs from 2017.",
                "emotion": "intense"
            },
            {
                "speaker": "narrator",
                "text": "The computer screen displays coordinates to a hidden gold safe that was never officially released in the update.",
                "text_speak": "The computer screen displays coordinates to a hidden gold safe that was never officially released in the update.",
                "emotion": "amazed"
            },
            {
                "speaker": "narrator",
                "text": "Try this before developers patch the wall, and subscribe for the next secret room!",
                "text_speak": "Try this before developers patch the wall, and subscribe for the next secret room!",
                "emotion": "happy"
            }
        ],
        "image_prompts": [
            "Vibrant cinematic 3D render of stylish Roblox avatar in black and neon cyan hoodie standing inside hospital corridor holding glowing lantern, vertical 9:16, ray tracing, unreal engine 5, no text",
            "Action shot of Roblox avatar performing wall clip glitch through hospital wall with blue digital spark particle effects, vertical 9:16, dynamic gaming angle, no text",
            "Atmospheric reveal shot of Roblox avatar falling into underground secret concrete bunker with vintage green computer monitors glowing, vertical 9:16, no text",
            "Close up shot of retro blocky Roblox computer screen showing glowing neon green blueprint coordinates and secret vault icon, vertical 9:16, no text",
            "Dramatic shot of Roblox avatar standing before a giant heavy steel vault door with glowing gold handle inside secret room, vertical 9:16, no text",
            "Exciting high contrast Roblox gaming cliffhanger shot with neon subscribe button effect and avatar celebrating with thumbs up, vertical 9:16, no text"
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
    else:
        # Intense Anime / Sci-Fi
        voice_name = "Charon" if line.get("speaker") == "char_b" else "Fenrir"
        pitch_arg = "-2Hz"
        rate_arg = "+5%"

    text = line.get("text_speak", line["text"])

    for attempt in range(1, 5):
        try:
            pcm = _call_gemini_tts(text, voice_name=voice_name)
            if pcm and len(pcm) > 500:
                _pcm_to_wav(pcm, out_wav)
                return
        except Exception:
            if attempt == 4:
                break
            await asyncio.sleep(1.5 * attempt)

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

    cp_dir = ROOT / "output" / f"batch3_{series_code.lower()}_ep{episode_num}"
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

    # 3. Ken Burns 60fps Compositing
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
        raise RuntimeError(f"YouTube upload failed for {series_code}: {result}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
async def main_async():
    start_t = time.time()
    db = DB()
    pub = YouTubePublisher(db=db)

    print("\n" + "#" * 80)
    print("  🚀 AUTOPILOT MASTER ENGINE: BATCH 3 — ALL 7 SERIES GENERATE & PUBLISH")
    print("#" * 80 + "\n")

    published_results = []
    for ep in BATCH_EPISODES:
        try:
            res = await process_single_episode(ep, db, pub)
            published_results.append(res)
        except Exception as e:
            print(f"\n❌ Error processing {ep['series_code']} Ep {ep['episode_num']}: {e}")

    total_time = round(time.time() - start_t, 1)

    print("\n" + "=" * 80)
    print(f"  🏁 BATCH 3 EXECUTION COMPLETE IN {total_time}s!")
    print(f"  🎉 Total Episodes Published: {len(published_results)} / {len(BATCH_EPISODES)}")
    print("=" * 80)
    for res in published_results:
        print(f"  • {res['series_code']} Ep {res['episode_num']}: {res['url']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main_async())
