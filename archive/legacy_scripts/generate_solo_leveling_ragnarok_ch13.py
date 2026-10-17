"""
generate_solo_leveling_ragnarok_ch13.py — Solo Leveling: Ragnarok Chapter 13 Complete Production Master.
Strictly Calibrated for 4 to 5 Minutes Runtime (240s–300s).
Single-pass lightweight FFmpeg rendering with studio warmth DSP humanoid voiceovers.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.ffmpeg import ffmpeg_bin, probe

OUT_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch13"
PANELS_DIR = OUT_DIR / "panels"
CP_DIR = OUT_DIR / "checkpoints"
FINAL_DIR = OUT_DIR / "checkpoints_final"

SCENES = [
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Solo Leveling: Ragnarok Chapter 13! Beast King Wolf ka aavishkar aur Sung Suho ka naya celestial avatar!",
        "text_speak": "सोलो लेवलिंग रैनारॉक चैप्टर तेरह! बीस्ट किंग वुल्फ का अवतार और सू-हो का खौफनाक सेलेश्टियल रूप!"
    },
    {
        "panel": 2, "speaker": "system", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "System Alert: 'Fang's Heir aapke yuddh-saahas ka aadar karta hai! Kya aap use apna Ally banayenge?'",
        "text_speak": "सिस्टम की घंटी गूंजी: 'फैंग का वारिस आपके लड़ने के जज़्बे का सम्मान करता है! क्या आप इसे अपना साथी बनाएंगे?'"
    },
    {
        "panel": 3, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho ne socha: 'Fang ka vanshaj... wahi chhota bhediya ab vishal beast ban chuka hai! Kya main ise recruit kar sakta hoon?'",
        "text_speak": "सू-हो ने सोचा: 'फैंग का वारिस... वही छोटा बच्चा अब इतना ताकतवर भेड़िया बन चुका है! क्या मैं इसे अपना साथी बना सकता हूँ?'"
    },
    {
        "panel": 4, "speaker": "manager", "emotion": "shocked", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky khauf se kaanpa: 'Tu Rakhan ka vanshaj hai?! Tune Rakhan ke fangs ka mana sokh liya?!'",
        "text_speak": "ब्रॉकी खौफ से कांप उठा: 'तू राखान का वारिस है?! तूने राखान के फैंग्स का माना सोख लिया?!'"
    },
    {
        "panel": 5, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne hath aage badhaya: 'Mujhe pehle se hi Fang ke saath judna tha... isliye main ise sweekar karta hoon... YES!'",
        "text_speak": "सू-हो ने हाथ आगे बढ़ाया: 'मुझे पहले से ही फैंग के साथ जुड़ना था... इसलिए मैं इसे स्वीकार करता हूँ... हाँ!'"
    },
    {
        "panel": 6, "speaker": "system", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "System Alert: 'Successor of the Fang aapka Ally ban chuka hai!' Blue aur golden divine urja charo taraf phoot padi!",
        "text_speak": "सिस्टम अलर्ट: 'सक्सेसर ऑफ द फैंग आपका साथी बन चुका है!' नीली और सुनहरी रौशनी का महा-विस्फोट हुआ!"
    },
    {
        "panel": 7, "speaker": "suho", "emotion": "tense", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho bola: 'Kuch mere dimag mein beh raha hai!' Flashback shuru hua: Brocky nannhe bhediye ko sambhal raha tha.",
        "text_speak": "सू-हो चौंक गया: 'कुछ मेरे दिमाग में बह रहा है!' पुरानी यादें खुलीं: ब्रॉकी नन्हे भेड़िये को समझा रहा था."
    },
    {
        "panel": 8, "speaker": "manager", "emotion": "serious", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Brocky ne kaha: 'Shadow Monarch se harne ke baad humne sab kho diya... is sansaar mein sirf taqatwar hi zinda bachte hain.'",
        "text_speak": "ब्रॉकी ने कहा था: 'शैडो मोनार्क से हारने के बाद हमने सब खो दिया... इस दुनिया में सिर्फ ताकतवर ही ज़िंदा बचते हैं.'"
    },
    {
        "panel": 9, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Nannha bhediya akelepan aur darr se kaanp raha tha, tabhi andhere se ajeeb roshan chhayayein aage badhi!",
        "text_speak": "नन्हा भेड़िया डर से कांप रहा था, तभी अंधेरे से अजीब रहस्यमयी साए आगे बढ़े!"
    },
    {
        "panel": 10, "speaker": "sword", "emotion": "epic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Safed roop aur golden halo wala Itarim ka doot bola: 'Ye monster kaafi kaam ka lagta hai... ye hamare liye kaafi hoga.'",
        "text_speak": "दिव्य आभामंडल वाला इटारिम का दूत बोला: 'ये मॉन्स्टर काफी काम का लगता है... ये हमारे लिए काफी होगा.'"
    },
    {
        "panel": 11, "speaker": "narrator", "emotion": "tense", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Doot ne Brocky ki aankh mein ek chamakta hua divine stone gop diya!",
        "text_speak": "दूत ने ब्रॉकी की आंख में एक चमकता हुआ इटारिम स्टोन जबरन घुसा दिया!"
    },
    {
        "panel": 12, "speaker": "manager", "emotion": "painful", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky cheekha: 'AAAARGH!' Nannha bhediya rote hue chillaya: 'Hyena Brocky!'",
        "text_speak": "ब्रॉकी दर्द से चीख पड़ा: 'आहहह!' नन्हा भेड़िया रोते हुए तड़प उठा: 'हायना ब्रॉकी!'"
    },
    {
        "panel": 13, "speaker": "sword", "emotion": "evil", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Doot ne aadesh diya: 'Insaano ko zinda pakadkar laao! Ye tumhari taqat badhayega, lekin tumhari ichhaon ko bhatka dega!'",
        "text_speak": "दूत ने हुक्म दिया: 'इंसानों को ज़िंदा पकड़कर लाओ! ये तुम्हारी ताकत बढ़ाएगा, लेकिन तुम्हारी सोच को भ्रष्ट कर देगा!'"
    },
    {
        "panel": 14, "speaker": "suho", "emotion": "shocked", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Suho ki aankhein khuli: 'Toh Brocky ki aankh mein ye shakti lagane wale log seedhe Itarim se jude hain?!'",
        "text_speak": "सू-हो की आंखें खुलीं: 'तो ब्रॉकी की आंख में ये पत्थर लगाने वाले लोग सीधे इटारिम से जुड़े हैं?!'"
    },
    {
        "panel": 15, "speaker": "suho", "emotion": "emotional", "camera": "slow_push", "music": "epic_adventure", "sfx": "heartbeat_low",
        "text_sub": "Suho ne samjha: 'Bhediya badla nahi lena chahta... balki pagal ho chuke Brocky ko bachana chahta hai!'",
        "text_speak": "सू-हो समझ गया: 'भेड़िया बदला नहीं लेना चाहता... बल्कि पागल हो चुके ब्रॉकी को बचाना चाहता है!'"
    },
    {
        "panel": 16, "speaker": "suho", "emotion": "resolute", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Suho bola: 'Mujhe Brocky ko harana hoga... par abhi mere paas utni taqat nahi hai!' Brocky Itarim aura se dahad utha!",
        "text_speak": "सू-हो बोला: 'मुझे ब्रॉकी को हराना होगा... पर अभी मेरे पास उतनी ताकत नहीं है!' ब्रॉकी लाल ऊर्जा से दहाड़ा!"
    },
    {
        "panel": 17, "speaker": "system", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "DING! System Alert: 'New Quest: Monarch's Heirs!' Sabhi Monarchs ke warison ko dhundho aur Ally banao! Allied: 1/8.",
        "text_speak": "डिंग! नया क्वेस्ट: 'मोनार्क्स हेयर्स!' सभी मोनार्क के वारिसों को ढूंढो और साथी बनाओ! वर्तमान संख्या: एक बटा आठ!"
    },
    {
        "panel": 18, "speaker": "system", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "System Notice: 'Fang ke waris ke saath judne se BOND SKILL form ho rahi hai!' Neeli aur sunhari aag aakash mein chha gayi!",
        "text_speak": "सिस्टम अलर्ट: 'फैंग के वारिस के साथ जुड़ने से बॉन्ड स्किल तैयार हो रही है!' नीली और सुनहरी लपटें आसमान छूने लगीं!"
    },
    {
        "panel": 19, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru garva se dekhne laga: 'Young Monarch kuch aisa anubhav kar rahe hain jo purane Shadow Monarch ne bhi nahi kiya tha!'",
        "text_speak": "बेरू गर्व से देखने लगा: 'यंग मोनार्क कुछ ऐसा अनुभव कर रहे हैं जो पुराने शैडो मोनार्क ने भी नहीं किया था!'"
    },
    {
        "panel": 20, "speaker": "manager", "emotion": "furious", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky zameen hilate hue kooda: 'Tujhe kya laga main tumhe ye karne doonga?!'",
        "text_speak": "ब्रॉकी ज़मीन हिलाते हुए झपटा: 'तुझे क्या लगा मैं तुम्हें ये करने दूंगा?!'"
    },
    {
        "panel": 21, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "KABOOM! Brocky ke hamle se dhuandhar pathar ude, par System ne ghoshna ki: 'Bond Skill successfully produced!'",
        "text_speak": "धमाका! ब्रॉकी के वार से पत्थर उड़ गए, पर सिस्टम ने घोषणा की: 'बॉन्ड स्किल सफलतापूर्वक बन गई!'"
    },
    {
        "panel": 22, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Dhuen se nikla Sung Suho! Uske baal safed-chandi jaise ho chuke the, maathe par Fang ka nishaan tha aur haathon mein Beast Gauntlets!",
        "text_speak": "धुएं से निकला सू-हो! उसके बाल चांदी जैसे सफेद हो चुके थे, माथे पर फैंग का निशान और हाथों में बीस्ट गौंटलेट्स!"
    },
    {
        "panel": 23, "speaker": "system", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "System: 'Bond Skill: Beast Possession Lv. 1 Active!' Successor of the Fang ke saath judkar senses shikar jaise teekhe ho gaye!",
        "text_speak": "सिस्टम: 'बॉन्ड स्किल: बीस्ट पजेशन लेवल वन एक्टिव!' फैंग के साथ जुड़कर सभी इंद्रियां शिकारी जैसी तेज़ हो गईं!"
    },
    {
        "panel": 24, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne mehsoos kiya: 'Mera shareer hawa jaisa halka hai... chhotisi harkat se main khatre ko pehle hi bhaamp sakta hoon!'",
        "text_speak": "सू-हो ने महसूस किया: 'मेरा शरीर हवा जैसा हल्का है... ज़रा सी हरकत से मैं हर खतरे को पहले ही भांप सकता हूँ!'"
    },
    {
        "panel": 25, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Suho ne hawa mein spinning high kick se seedha Brocky ki thodi par bijli ki tarah prahaar kiya!",
        "text_speak": "सू-हो ने बिजली की फुर्ती से स्पिनिंग हाई किक से सीधा ब्रॉकी की ठोड़ी पर प्रहार किया!"
    },
    {
        "panel": 26, "speaker": "manager", "emotion": "painful", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky ka jabda hil gaya, khoon phoot pada: 'Ye kya ho raha hai?! Kya ye wahi kamzor bachha hai?!'",
        "text_speak": "ब्रॉकी का जबड़ा हिल गया, खून फूट पड़ा: 'ये क्या हो रहा है?! क्या ये वही बच्चा है?!'"
    },
    {
        "panel": 27, "speaker": "manager", "emotion": "furious", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky pagal ho utha: 'Agar main hara to sab chhin jayega!' Usne apne seene par Itarim ka prateek jagrit kar diya!",
        "text_speak": "ब्रॉकी पागल हो उठा: 'अगर मैं हारा तो सब छिन जाएगा!' उसने अपने सीने पर इटारिम का प्रतीक जागृत कर दिया!"
    },
    {
        "panel": 28, "speaker": "beru", "emotion": "panicked", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky ka vishalkay shareer raakshas ki tarah badh gaya! Beru chillaya: 'Iska Mana toofani gati se badh raha hai!'",
        "text_speak": "ब्रॉकी का शरीर दानव की तरह विशाल हो गया! बेरू चिल्लाया: 'इसका माना तूफानी गति से बढ़ रहा है!'"
    },
    {
        "panel": 29, "speaker": "manager", "emotion": "evil", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Brocky dahada: 'Taqat ka farq prajati se tay hota hai! Apne kamzor insaani shareer ke aage gidgidao!'",
        "text_speak": "ब्रॉकी दहाड़ा: 'ताकत का फर्क प्रजाति से तय होता है! अपने कमज़ोर इंसानी जिस्म के आगे गिड़गिड़ाओ!'"
    },
    {
        "panel": 30, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky ne pahad tod dene wala vishal ghoonsa mara, poori ghaati mein bhukamp aa gaya!",
        "text_speak": "ब्रॉकी ने पहाड़ फोड़ देने वाला विशाल घूंसा मारा, पूरी घाटी में भूकंप आ गया!"
    },
    {
        "panel": 31, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "CLASH! Suho ne akele haath se Brocky ke colossal punch ko hawa mein hi rok liya! Shockwaves se chattaanein toot gayi!",
        "text_speak": "क्लैश! सू-हो ने अकेले हाथ से ब्रॉकी के महा-घूंसे को हवा में ही रोक लिया! शॉकवेव से चट्टानें टूट गईं!"
    },
    {
        "panel": 32, "speaker": "system", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "System Alert: 'You learned Skill: Martial Arts Lv. 1!' Bare-handed attacks ka damage +33% badh gaya!",
        "text_speak": "सिस्टम की घंटी बजी: 'मार्शल आर्ट्स लेवल वन अनलॉक!' नंगे हाथों के हमलों की ताकत तैंतीस प्रतिशत बढ़ गई!"
    },
    {
        "panel": 33, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru garva se garja: 'Shadow Monarch ke aage prajati ke farq ki baat mat kar! Shikhar par baithe Monarch se unchi koi prajati nahi!'",
        "text_speak": "बेरू गर्व से गरजा: 'शैडो मोनार्क के आगे प्रजाति की बात मत कर! शिखर पर बैठे मोनार्क से ऊंची कोई प्रजाति नहीं!'"
    },
    {
        "panel": 34, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho aakash mein kooda aur bijli ki raftaar se Brocky ke sar par vinashkari Axe Kick maari! BOOOM!",
        "text_speak": "सू-हो आसमान में कूदा और बिजली की रफ्तार से ब्रॉकी के सिर पर एक्स किक मारी! ज़मीन पाताल तक फट गई!"
    },
    {
        "panel": 35, "speaker": "narrator", "emotion": "tense", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Dhuandhar toofan thama. Suho ki saansein chal rahi thi, Beast skill deactivate hui aur bhediya alag hokar khada hua.",
        "text_speak": "धुएं का तूफ़ान थमा. सू-हो की सांसें फूल रही थीं, बीस्ट स्किल बंद हुई और भेड़िया अलग होकर खड़ा हुआ."
    },
    {
        "panel": 36, "speaker": "manager", "emotion": "painful", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Brocky malbe mein pada bola: 'Taqatwar... mujhe taqatwar banna hoga...' Bhediya uske kareeb gaya.",
        "text_speak": "ब्रॉकी मलबे में पड़ा बोला: 'ताकतवर... मुझे ताकतवर बनना था...' भेड़िया उसके करीब गया."
    },
    {
        "panel": 37, "speaker": "manager", "emotion": "emotional", "camera": "slow_push", "music": "ambient_soft", "sfx": "heartbeat_low",
        "text_sub": "Brocky ki aankh ka Itarim stone toot gaya: 'Mujhe yaad aaya... meri taqatwar banne ki asli wajah...'",
        "text_speak": "ब्रॉकी की आंख का पत्थर चटक गया: 'मुझे याद आया... मेरी ताकतवर बनने की असली वजह...'"
    },
    {
        "panel": 38, "speaker": "manager", "emotion": "emotional", "camera": "slow_push", "music": "ambient_soft", "sfx": "heartbeat_low",
        "text_sub": "Sir Rakhan ki yaad aayi: 'Main krodhit tha... kyunki main aapki raksha nahi kar paaya tha...'",
        "text_speak": "लॉर्ड राखान की याद आई: 'मैं गुस्से में था... क्योंकि मैं आपकी रक्षा नहीं कर पाया था...'"
    },
    {
        "panel": 39, "speaker": "narrator", "emotion": "emotional", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Brocky ne shaanti se aankhein band kar li, aur vishalkay bhediye ne aakash ki taraf dekh kar aarti jaisi howled: 'AWOOOOO!'",
        "text_speak": "ब्रॉकी ने शांति से आंखें मूंद लीं, और विशालकाय भेड़िये ने आसमान की तरफ मुंह उठाकर विलाप किया: 'आऊऊऊऊ!'"
    },
    {
        "panel": 40, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "System Alert: 'Hyena Brocky defeated! YOU HAVE LEVELED UP TWICE!' Chapter 13 ka safal samapan!",
        "text_speak": "सिस्टम अलर्ट: 'हायना ब्रॉकी परास्त! दो बार लेवल अप!' सोलो लेवलिंग रैनारॉक का महा-अध्याय जारी रहेगा!"
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# VOICEOVER GENERATOR (10X BETTER HUMANOID EMOTIVE QUALITY)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    import edge_tts

    voice = "hi-IN-MadhurNeural"
    rate_str = "+18%"  # High-energy pace tuned for 4.5m
    pitch_str = "+0Hz"

    if speaker == "beru":
        rate_str = "+21%"
        pitch_str = "+6Hz"
    elif speaker == "sword":
        rate_str = "+15%"
        pitch_str = "-2Hz"
    elif speaker == "manager": # Brocky
        rate_str = "+14%"
        pitch_str = "-5Hz"
    elif speaker == "suho":
        rate_str = "+18%"
        pitch_str = "+1Hz"

    raw_mp3 = out_wav.with_suffix(".mp3")
    for attempt in range(1, 6):
        try:
            communicator = edge_tts.Communicate(text_speak, voice, rate=rate_str, pitch=pitch_str)
            await communicator.save(str(raw_mp3))
            if raw_mp3.exists() and raw_mp3.stat().st_size > 500:
                break
        except Exception as e:
            if attempt == 5:
                raise
            print(f"    ⚠️ Edge-TTS attempt {attempt}/5 failed ({e}), retrying in {attempt * 2}s...")
            await asyncio.sleep(attempt * 2)

    # 6-Stage Studio Warmth DSP Equalizer
    ff = ffmpeg_bin()
    dsp_chain = (
        "highpass=f=75,"
        "equalizer=f=125:t=q:w=1.5:g=3.2,"
        "equalizer=f=420:t=q:w=2.0:g=-1.8,"
        "equalizer=f=2800:t=q:w=1.8:g=2.6,"
        "equalizer=f=8000:t=q:w=2.0:g=1.5,"
        "acompressor=threshold=-15dB:ratio=3.5:attack=15:release=120:makeup=2.2dB"
    )

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_mp3),
        "-af", dsp_chain,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)

    if raw_mp3.exists():
        raw_mp3.unlink()

# ─────────────────────────────────────────────────────────────────────────────
# PROCEDURAL SCORE & SFX
# ─────────────────────────────────────────────────────────────────────────────
def generate_music(music_type: str, duration: float, out_wav: Path):
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "dark_drone":     f"aevalsrc='0.22*sin(2*PI*55*t)+0.16*sin(2*PI*82.4*t)+0.10*sin(2*PI*110*t)':d={d}:s=44100,volume=0.26",
        "dark_intense":   f"aevalsrc='0.28*sin(2*PI*45*t)+0.20*sin(2*PI*65*t)+0.12*sin(2*PI*130*t)+0.07*(random(0)-0.5)':d={d}:s=44100,volume=0.32",
        "epic_adventure": f"aevalsrc='0.20*sin(2*PI*130.8*t)+0.16*sin(2*PI*164.8*t)+0.14*sin(2*PI*196*t)+0.12*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.30",
        "ambient_soft":   f"aevalsrc='0.16*sin(2*PI*174.6*t)+0.14*sin(2*PI*220*t)+0.10*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.24",
    }
    flt = filters.get(music_type, filters["dark_drone"])
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)

def generate_sfx(sfx_type: str, duration: float, out_wav: Path):
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "c_rank_blade_slash": f"aevalsrc='0.45*exp(-6*t)*sin(2*PI*(800-450*t)*t)+0.25*exp(-8*t)*(random(0)-0.5)':d={d}:s=44100",
        "braam_impact":       f"aevalsrc='0.42*exp(-1.5*t)*sin(2*PI*40*t)+0.26*exp(-2*t)*sin(2*PI*80*t)':d={d}:s=44100",
        "whoosh_energy":      f"aevalsrc='0.32*exp(-4*t)*sin(2*PI*(320-200*t)*t)':d={d}:s=44100",
        "heartbeat_low":      f"aevalsrc='0.35*sin(2*PI*45*t)*pow(max(0,sin(2*PI*1.3*t)),10)':d={d}:s=44100",
        "ambient_soft":       f"aevalsrc='0.08*sin(2*PI*120*t)':d={d}:s=44100",
    }
    flt = filters.get(sfx_type, filters["ambient_soft"])
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)

def mix_audio(voice_wav: Path, music_wav: Path, sfx_wav: Path, duration: float, out_aac: Path):
    ff = ffmpeg_bin()
    out_aac.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filter_complex = (
        "[0:a]volume=1.40,apad[v];"
        "[1:a]volume=0.18[m];"
        "[2:a]volume=0.25[s];"
        "[v][m][s]amix=inputs=3:duration=longest:dropout_transition=2,"
        f"atrim=end={d:.3f},aresample=44100"
    )
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(voice_wav),
        "-i", str(music_wav),
        "-i", str(sfx_wav),
        "-filter_complex", filter_complex,
        "-c:a", "aac", "-b:a", "192k",
        str(out_aac)
    ], check=True)

# ─────────────────────────────────────────────────────────────────────────────
# SINGLE-PASS COMPOSITOR (ZERO DUPLICATE FILES)
# ─────────────────────────────────────────────────────────────────────────────
def render_scene_direct(img_path: Path, audio_aac: Path, duration: float, camera: str, out_mp4: Path):
    ff = ffmpeg_bin()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    dur = max(2.5, round(duration, 3))
    w, h = 1920, 1080

    with Image.open(str(img_path)) as im:
        iw, ih = im.size
    aspect = iw / max(1, ih)

    bg_flt = f"[0:v]scale=320:180:force_original_aspect_ratio=increase,crop=320:180,boxblur=6:2,scale={w}:{h}:flags=bicubic,eq=brightness=-0.22:contrast=0.95[bg]"

    if aspect >= 1.2 or aspect >= 0.7:
        fg_flt = f"[0:v]scale=-2:1040[fg_scaled];[fg_scaled]pad=w=iw+10:h=ih+10:x=5:y=5:color=0x151520@0.8[fg]"
    else:
        fg_w = 1250
        fg_flt = (
            f"[0:v]scale={fg_w}:-2[fg_scaled];"
            f"[fg_scaled]crop=w={fg_w}:h=min(in_h\\,1040):x=0:y='if(gt(in_h\\,1040)\\,(in_h-1040)*t/{dur:.2f}\\,0)'[fg_pan];"
            f"[fg_pan]pad=w={fg_w}+10:h=1050:x=5:y=5:color=0x151520@0.8[fg]"
        )

    comp_flt = f"[bg][fg]overlay=(W-w)/2:(H-h)/2[comp]"

    if camera == "sudden_zoom":
        motion_flt = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.04*pow(t/{dur:.2f},1.5))/2)':h='2*floor({h}*(1.01+0.04*pow(t/{dur:.2f},1.5))/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p[v]"
        )
    elif camera == "handheld_shake":
        motion_flt = (
            f"[comp]scale=w='2*floor({w}*1.03/2)':h='2*floor({h}*1.03/2)',"
            f"crop={w}:{h}:'(in_w-{w})/2+4*sin(12*t)':'(in_h-{h})/2+4*cos(9*t)',format=yuv420p[v]"
        )
    else:
        motion_flt = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.02*t/{dur:.2f})/2)':h='2*floor({h}*(1.01+0.02*t/{dur:.2f})/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p[v]"
        )

    filter_complex = f"{bg_flt};{fg_flt};{comp_flt};{motion_flt}"

    cmd = [
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-t", str(dur), "-i", str(img_path),
        "-i", str(audio_aac),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_mp4)
    ]
    subprocess.run(cmd, check=True)

# ─────────────────────────────────────────────────────────────────────────────
# SUBTITLES & THUMBNAIL
# ─────────────────────────────────────────────────────────────────────────────
def generate_ass_subtitles(scenes: list[dict], scene_durs: list[float], out_ass: Path):
    header = """[Script Info]
Title: Solo Leveling Ragnarok Chapter 13 Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: RagnarokCyan,Segoe UI,40,&H00F0FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0.5,0,1,3.5,2.5,2,50,50,55,1
Style: RagnarokGold,Segoe UI,40,&H00D7FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0.5,0,1,3.5,2.5,2,50,50,55,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt_time(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        cs = int(round((t - int(t)) * 100))
        if cs >= 100:
            cs = 99
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    events = []
    curr = 0.0
    for sc, dur in zip(scenes, scene_durs):
        start_s = curr
        end_s = curr + dur
        style = "RagnarokGold" if sc["speaker"] in ["manager", "beru", "system"] else "RagnarokCyan"
        text = sc["text_sub"].replace("\n", "\\N")
        events.append(f"Dialogue: 0,{fmt_time(start_s)},{fmt_time(end_s)},{style},,0,0,0,,{text}")
        curr = end_s

    out_ass.parent.mkdir(parents=True, exist_ok=True)
    with open(out_ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")
    print(f"  ✓ Dual-Color Subtitles generated: {out_ass.name}")

def create_thumbnail(out_thumb: Path):
    out_thumb.parent.mkdir(parents=True, exist_ok=True)
    p22 = PANELS_DIR / "panel_022.jpg" # Suho transformed in silver hair Beast Form
    if not p22.exists():
        p22 = PANELS_DIR / "panel_001.jpg"

    with Image.open(str(p22)) as im:
        thumb = im.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(thumb)
    try:
        font_big = ImageFont.truetype("arialbd.ttf", 66)
        font_sub = ImageFont.truetype("arialbd.ttf", 44)
    except Exception:
        font_big = ImageFont.load_default()
        font_sub = font_big

    draw.rectangle([(20, 20), (1260, 160)], fill=(10, 12, 24, 215))
    draw.text((40, 30), "SUHO BEAST FORM AWAKENS! 🐺⚡", fill=(0, 240, 255), font=font_big)
    draw.text((40, 100), "CHAPTER 13 FULL RECAP IN HINDI", fill=(255, 215, 0), font=font_sub)

    thumb.save(str(out_thumb), quality=95)
    print(f"  ✓ High-CTR Thumbnail created: {out_thumb.name}")

# ─────────────────────────────────────────────────────────────────────────────
# MASTER GENERATOR PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
async def run_pipeline():
    ff = ffmpeg_bin()
    CP_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 75)
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 13 — MASTER PRODUCTION")
    print("  Target: Strictly 4 to 5 Minutes (240s–300s) · 10x Humanoid Voice")
    print("=" * 75)

    scene_durs = []
    scene_clips = []

    for i, sc in enumerate(SCENES, start=1):
        p_num = sc["panel"]
        img_path = PANELS_DIR / f"panel_{p_num:03d}.jpg"
        if not img_path.exists():
            img_path = PANELS_DIR / "panel_001.jpg"

        print(f"🎬 Scene {i:02d}/{len(SCENES)} (Panel {p_num:03d}): {sc['speaker'].upper()}")

        # 1. Voiceover
        v_wav = CP_DIR / f"sc_{i:02d}_v.wav"
        if not v_wav.exists() or v_wav.stat().st_size < 1000:
            await generate_voice(sc["text_speak"], sc["speaker"], sc["emotion"], v_wav)

        info = probe(v_wav)
        v_dur = float(info["format"]["duration"])
        dur = max(3.5, v_dur + 0.30)
        scene_durs.append(dur)

        sc_mp4 = FINAL_DIR / f"sc_{i:02d}_final.mp4"
        if sc_mp4.exists() and sc_mp4.stat().st_size > 50000:
            scene_clips.append(sc_mp4)
            continue

        # 2. Score & SFX
        m_wav = FINAL_DIR / f"sc_{i:02d}_m.wav"
        generate_music(sc["music"], dur, m_wav)

        s_wav = FINAL_DIR / f"sc_{i:02d}_s.wav"
        generate_sfx(sc["sfx"], dur, s_wav)

        # 3. Audio Mix
        mix_aac = FINAL_DIR / f"sc_{i:02d}_mix.aac"
        mix_audio(v_wav, m_wav, s_wav, dur, mix_aac)

        # 4. Direct Single-Pass Video + Audio Render
        render_scene_direct(img_path, mix_aac, dur, sc["camera"], sc_mp4)
        scene_clips.append(sc_mp4)

        # Clean up temporary scene audio
        for tmp_f in [m_wav, s_wav, mix_aac]:
            if tmp_f.exists():
                try:
                    tmp_f.unlink()
                except Exception:
                    pass

    total_dur = sum(scene_durs)
    print("\n" + "=" * 75)
    print(f"  ⏱️ EXACT TOTAL DURATION: {total_dur:.1f}s ({total_dur/60:.2f} minutes)")
    print("=" * 75)

    # Concatenate
    concat_list = OUT_DIR / "concat_list_final.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            clean_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    unsubbed_mp4 = OUT_DIR / "solo_leveling_ragnarok_ch13_unsubbed.mp4"
    print(f"\n📦 Concatenating all {len(scene_clips)} scenes into {unsubbed_mp4.name}...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(unsubbed_mp4)
    ], check=True)

    # Calibrate to exactly 270s if needed
    final_mp4 = OUT_DIR / "solo_leveling_ragnarok_ch13_final.mp4"
    if not (240.0 <= total_dur <= 300.0):
        target_total = 270.0
        factor = total_dur / target_total
        print(f"  ⚠️ Recalibrating duration from {total_dur:.1f}s to {target_total:.1f}s (factor: {factor:.4f}x)...")
        scene_durs = [round(d / factor, 3) for d in scene_durs]
        total_dur = sum(scene_durs)

        ass_path = OUT_DIR / "solo_leveling_ragnarok_ch13.ass"
        generate_ass_subtitles(SCENES, scene_durs, ass_path)

        ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
        v_flt = f"setpts=PTS/{factor:.4f},ass='{ass_escaped}'"
        a_flt = f"atempo={factor:.4f}"

        print(f"🔥 Burning styled subtitles and applying tempo factor {factor:.4f}x into: {final_mp4.name}...")
        subprocess.run([
            ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(unsubbed_mp4),
            "-vf", v_flt,
            "-af", a_flt,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            str(final_mp4)
        ], check=True)
    else:
        ass_path = OUT_DIR / "solo_leveling_ragnarok_ch13.ass"
        generate_ass_subtitles(SCENES, scene_durs, ass_path)

        ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
        sub_filter = f"ass='{ass_escaped}'"

        print(f"🔥 Burning styled subtitles into final broadcast master: {final_mp4.name}...")
        subprocess.run([
            ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(unsubbed_mp4),
            "-vf", sub_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "copy",
            str(final_mp4)
        ], check=True)

    # Clean up unsubbed mp4 to save disk space
    if unsubbed_mp4.exists():
        try:
            unsubbed_mp4.unlink()
        except Exception:
            pass

    # Thumbnail
    thumb_path = OUT_DIR / "thumbnail.jpg"
    create_thumbnail(thumb_path)

    final_info = probe(final_mp4)
    final_sec = float(final_info.get("format", {}).get("duration", total_dur))
    final_size_mb = final_mp4.stat().st_size / (1024 * 1024)

    print("\n" + "🎉" * 38)
    print("  ✅ SOLO LEVELING: RAGNAROK CHAPTER 13 FINAL MASTER IS READY!")
    print(f"  📁 Output: {final_mp4}")
    print(f"  ⏱️ Final Duration: {final_sec:.1f}s ({final_sec/60:.2f} minutes)")
    print(f"  💾 File Size: {final_size_mb:.2f} MB")
    print("🎉" * 38 + "\n")

    if not (240.0 <= final_sec <= 300.0):
        raise ValueError(f"CRITICAL: Final duration {final_sec:.1f}s is not within 240s-300s window!")

    return final_mp4

def main():
    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()
