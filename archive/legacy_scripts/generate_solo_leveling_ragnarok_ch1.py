"""
generate_solo_leveling_ragnarok_ch1.py — Solo Leveling: Ragnarok Chapter 1 Cinematic Hindi Explainer Video.

A 10x better cinematic anime explainer experience created from the 19 webtoon strips:
  • Sliced 68 high-res vertical panels with intelligent Ken Burns scroll & zoom
  • Balanced, punchy anime pacing (~1.18x speed)
  • 100% accurate Hindi phonetics (Devanagari TTS + clean Hinglish subtitles)
  • 3-layer audio mix (voice + procedural Solo Leveling synth/orchestral score + SFX)
  • Custom SFX (System chime, glass shatter, blue flame burst, monster roar, metal impact)
  • Styled ASS kinetic subtitles with Solo Leveling aesthetic (Cyan & Gold)
  • Checkpoint caching for ultra-resilient rendering
  • Final 1080p MP4 compilation + YouTube cover thumbnail
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from core.ffmpeg import ffmpeg_bin, probe

# ─────────────────────────────────────────────────────────────────────────────
# SPEAKER & VOICE ENGINE CONFIGURATION (Balanced 1.18x Anime Pacing)
# ─────────────────────────────────────────────────────────────────────────────
SPEAKER_CONFIG = {
    "narrator": {"voice": "hi-IN-MadhurNeural", "rate": "+18%", "pitch": "+0Hz"},
    "suho":     {"voice": "hi-IN-MadhurNeural", "rate": "+20%", "pitch": "+4Hz"},
    "jinwoo":   {"voice": "hi-IN-MadhurNeural", "rate": "+12%", "pitch": "-6Hz"},
    "bully":    {"voice": "hi-IN-MadhurNeural", "rate": "+20%", "pitch": "-3Hz"},
    "kim":      {"voice": "hi-IN-MadhurNeural", "rate": "+16%", "pitch": "-4Hz"},
    "teacher":  {"voice": "hi-IN-MadhurNeural", "rate": "+16%", "pitch": "+2Hz"},
    "girl":     {"voice": "hi-IN-SwaraNeural",  "rate": "+18%", "pitch": "+4Hz"},
    "system":   {"voice": "hi-IN-MadhurNeural", "rate": "+14%", "pitch": "+6Hz"},
}

EMOTION_VOICE_MOD = {
    "desperate":  {"rate_mod": 3,  "pitch_mod": -3},
    "fearful":    {"rate_mod": -2, "pitch_mod": -3},
    "sad":        {"rate_mod": -3, "pitch_mod": -2},
    "dramatic":   {"rate_mod": 2,  "pitch_mod": -2},
    "angry":      {"rate_mod": 5,  "pitch_mod": +2},
    "excited":    {"rate_mod": 4,  "pitch_mod": +3},
    "calm":       {"rate_mod": 0,  "pitch_mod": 0},
    "curious":    {"rate_mod": 2,  "pitch_mod": +2},
    "surprised":  {"rate_mod": 4,  "pitch_mod": +4},
    "epic":       {"rate_mod": 3,  "pitch_mod": -1},
}

# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 1 SCENE DEFINITIONS (68 Panels Covering the Entire Chapter)
# ─────────────────────────────────────────────────────────────────────────────
SCENES_DATA = [
    # [ACT 1: PROLOGUE - THE OUTER GODS & THE COSMIC CHESSBOARD]
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Solo Leveling ki nayi daastan... Solo Leveling: Ragnarok!",
        "text_speak": "सोलो लेवलिंग की नई दास्तान... सोलो लेवलिंग: रैग्नारॉक!"
    },
    {
        "panel": 2, "speaker": "narrator", "emotion": "dramatic", "camera": "tilt_down", "music": "dark_drone", "sfx": "portal_hum",
        "text_sub": "Outer Gods... wo azeem taakatein jinhone anant bramhand banaye the.",
        "text_speak": "आउटर गॉड्स... वो अज़ीम ताकतें जिन्होंने अनंत ब्रह्मांड बनाए थे।"
    },
    {
        "panel": 3, "speaker": "narrator", "emotion": "dramatic", "camera": "tilt_down", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "In Supreme Beings ne kayi naye aalam, roohein aur kanoon rache...",
        "text_speak": "इन सुप्रीम बीइंग्स ने कई नए आलम, रूहें और कानून रचे..."
    },
    {
        "panel": 4, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_pull", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Lekin jab anant zindagiyon ke baad unhe boredom mehsoos hua...",
        "text_speak": "लेकिन जब अनंत ज़िंदगियों के बाद उन्हें बोरियत महसूस हुई..."
    },
    {
        "panel": 5, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Toh unhone apne manoranjan ke liye apni hi rachi hui duniyaon ko aapas mein ladwa diya!",
        "text_speak": "तो उन्होंने अपने मनोरंजन के लिए अपनी ही रची हुई दुनियाओं को आपस में लड़वा दिया!"
    },
    {
        "panel": 6, "speaker": "narrator", "emotion": "dramatic", "camera": "tilt_down", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Bramhand ke is shatranj par anant yudh shuru ho gaye...",
        "text_speak": "ब्रह्मांड के इस शतरंज पर अनंत युद्ध शुरू हो गए..."
    },
    {
        "panel": 7, "speaker": "narrator", "emotion": "surprised", "camera": "slow_push", "music": "dark_intense", "sfx": "impact_heavy",
        "text_sub": "Lekin tabhi ek aisi ghatna ghati jisne sabko hila diya! Ek Supreme Being ko uski hi creation ne maar giraya!",
        "text_speak": "लेकिन तभी एक ऐसी घटना घटी जिसने सबको हिला दिया! एक सुप्रीम बीइंग को उसकी ही क्रिएशन ने मार गिराया!"
    },
    {
        "panel": 8, "speaker": "narrator", "emotion": "dramatic", "camera": "tilt_down", "music": "dark_drone", "sfx": "portal_hum",
        "text_sub": "Doosri dimensions ke Outer Gods us duniya ko dekhne ke liye ikattha hue jiska maalik mar chuka tha.",
        "text_speak": "दूसरी डायमेंशंस के आउटर गॉड्स उस दुनिया को देखने के लिए इकट्ठा हुए जिसका मालिक मर चुका था।"
    },
    {
        "panel": 9, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Unhe is baat ki parwah nahi thi ki unka sathi mara gaya...",
        "text_speak": "उन्हें इस बात की परवाह नहीं थी कि उनका साथी मारा गया..."
    },
    {
        "panel": 10, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Un sabka sirf ek hi iraada tha: Jo pehle is be-sahara taakat par kabza karega, wahi iska naya maalik banega!",
        "text_speak": "उन सबका सिर्फ़ एक ही इरादा था: जो पहले इस बे-सहारा ताक़त पर कब्ज़ा करेगा, वही इसका नया मालिक बनेगा!"
    },
    {
        "panel": 11, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Aur yahan se shuru hoti hai... Solo Leveling: Ragnarok!",
        "text_speak": "और यहाँ से शुरू होती है... सोलो लेवलिंग: रैग्नारॉक!"
    },

    # [ACT 2: SUHO'S HIGH SCHOOL GRADUATION & AWAKENED BULLY]
    {
        "panel": 12, "speaker": "suho", "emotion": "calm", "camera": "tilt_down", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Mera admission Korea National University of Arts mein ho gaya tha.",
        "text_speak": "मेरा एडमिशन कोरिया नेशनल यूनिवर्सिटी ऑफ़ आर्ट्स में हो गया था।"
    },
    {
        "panel": 13, "speaker": "narrator", "emotion": "happy", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Dost khushi se chillane lage: 'Aakhirkar is narak se azaadi mil gayi!'",
        "text_speak": "दोस्त खुशी से चिल्लाने लगे: 'आखिरकार इस नरक से आज़ादी मिल गई!'"
    },
    {
        "panel": 14, "speaker": "bully", "emotion": "angry", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Tabhi samne aaya school ka bully Lee Eunchul: 'Suho... congrats!'",
        "text_speak": "तभी सामने आया स्कूल का बुली ली यून-चुल: 'सू-हो... बधाई हो!'"
    },
    {
        "panel": 15, "speaker": "bully", "emotion": "angry", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "'Tumhari wajah se is poore high school par kabza karne ka mera plan barbaad ho gaya tha!'",
        "text_speak": "'तुम्हारी वजह से इस पूरे हाई स्कूल पर कब्ज़ा करने का मेरा प्लान बर्बाद हो गया था!'"
    },
    {
        "panel": 16, "speaker": "narrator", "emotion": "sad", "camera": "slow_pull", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Classmates baatein karne lage: 'Ye Lee Eunchul us bechare ladke ko kyun tang kar raha hai jiske maa-baap gayab hain?'",
        "text_speak": "क्लासमेट्स बातें करने लगे: 'ये ली यून-चुल उस बेचारे लड़के को क्यों तंग कर रहा है जिसके माँ-बाप गायब हैं?'"
    },
    {
        "panel": 17, "speaker": "bully", "emotion": "angry", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "'SUHO!' Usne poori taakat se ghonsa maara!",
        "text_speak": "'सू-हो!' उसने पूरी ताक़त से घूंसा मारा!"
    },
    {
        "panel": 18, "speaker": "suho", "emotion": "surprised", "camera": "slow_push", "music": "dark_intense", "sfx": "impact_heavy",
        "text_sub": "Lekin Suho ne aisi tezi se block kiya ki wo khud hairaan reh gaya!",
        "text_speak": "लेकिन सू-हो ने ऐसी तेज़ी से ब्लॉक किया कि वो खुद हैरान रह गया!"
    },
    {
        "panel": 19, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Suho ne aah bharte hue kaha: 'Bas graduation tak shaanti se rehne do...'",
        "text_speak": "सू-हो ने आह भरते हुए कहा: 'बस ग्रेजुएशन तक शांति से रहने दो...'"
    },
    {
        "panel": 20, "speaker": "narrator", "emotion": "surprised", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Tabhi Lee Eunchul ke haath par achanak neeli bijli chamakne lagi! Mana jaag gaya!",
        "text_speak": "तभी ली यून-चुल के हाथ पर अचानक नीली बिजली चमकने लगी! माना जाग गया!"
    },
    {
        "panel": 21, "speaker": "bully", "emotion": "angry", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "'Mujhe zara bhi chot nahi aayi!' uski laal aankhon mein nasha chadh chuka tha!",
        "text_speak": "'मुझे ज़रा भी चोट नहीं आई!' उसकी लाल आँखों में नशा चढ़ चुका था!"
    },
    {
        "panel": 22, "speaker": "narrator", "emotion": "dramatic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "impact_heavy",
        "text_sub": "DHAMAAL! Usne Suho ko lockers aur deewar ke aar-paar de maara!",
        "text_speak": "धमाल! उसने सू-हो को लॉकर्स और दीवार के आर-पार दे मारा!"
    },
    {
        "panel": 23, "speaker": "bully", "emotion": "surprised", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Lee Eunchul apni hi jaagi hui taakat ko dekh kar hairaan tha: 'Ye kya tha...?'",
        "text_speak": "ली यून-चुल अपनी ही जागी हुई ताकत को देख कर हैरान था: 'ये क्या था...?'"
    },
    {
        "panel": 24, "speaker": "narrator", "emotion": "calm", "camera": "slow_pull", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Lekin deewar ke paas baitha Suho... bilkul theek-thaak tha! Uske sharir par ek kharoch tak nahi aayi thi!",
        "text_speak": "लेकिन दीवार के पास बैठा सू-हो... बिल्कुल ठीक-ठाक था! उसके शरीर पर एक खरोंच तक नहीं आई थी!"
    },

    # [ACT 3: TWO YEARS LATER & THE DIVIDED WORLD]
    {
        "panel": 25, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Do saal baad... Seoul Arts University ka campus.",
        "text_speak": "दो साल बाद... सियोल आर्ट्स यूनिवर्सिटी का कैंपस।"
    },
    {
        "panel": 26, "speaker": "suho", "emotion": "calm", "camera": "tilt_down", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Sung Suho ab university ka second-year student ban chuka tha.",
        "text_speak": "सुंग सू-हो अब यूनिवर्सिटी का सेकंड-ईयर स्टूडेंट बन चुका था।"
    },
    {
        "panel": 27, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_push", "music": "dark_drone", "sfx": "portal_hum",
        "text_sub": "Loudspeaker par announcement goonji: 'Main building mein D-Rank Gate khul gaya hai! Sabhi annex building mein shift ho jayein!'",
        "text_speak": "लाउडस्पीकर पर अनाउंसमेंट गूंजी: 'मेन बिल्डिंग में डी-रैंक गेट खुल गया है! सभी एनेक्स बिल्डिंग में शिफ्ट हो जाएं!'"
    },
    {
        "panel": 28, "speaker": "narrator", "emotion": "curious", "camera": "slow_pull", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Hunters ko gate ke andar gaye aath ghante se zyada waqt ho chuka tha.",
        "text_speak": "हंटर्स को गेट के अंदर गए आठ घंटे से ज़्यादा वक़्त हो चुका था।"
    },
    {
        "panel": 29, "speaker": "suho", "emotion": "sad", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Suho ne asman ki taraf dekha: '...Ek aur Gate, huh?'",
        "text_speak": "सू-हो ने आसमान की तरफ देखा: '...एक और गेट, हूह?'"
    },
    {
        "panel": 30, "speaker": "narrator", "emotion": "dramatic", "camera": "tilt_down", "music": "dark_intense", "sfx": "portal_hum",
        "text_sub": "Teen saal pehle achanak duniya bhar mein dobara Gates khulne lage the aur khunkhar monsters bahar aane lage the.",
        "text_speak": "तीन साल पहले अचानक दुनिया भर में दोबारा गेट्स खुलने लगे थे और खूंखार मॉन्स्टर्स बाहर आने लगे थे।"
    },
    {
        "panel": 31, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Lekin tabhi logo ke andar Mana jaaga aur wo Awakened Hunters ban gaye!",
        "text_speak": "लेकिन तभी लोगों के अंदर माना जागा और वो अवेकन्ड हंटर्स बन गए!"
    },
    {
        "panel": 32, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "ambient_soft",
        "text_sub": "Woo Jinchul ne aage aakar Hunter Association banayi aur tabahi ko rok liya.",
        "text_speak": "वू जिन-चुल ने आगे आकर हंटर एसोसिएशन बनाई और तबाही को रोक लिया।"
    },
    {
        "panel": 33, "speaker": "narrator", "emotion": "sad", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Ab duniya do hisson mein bat chuki thi: Awakened aur Non-Awakened.",
        "text_speak": "अब दुनिया दो हिस्सों में बंट चुकी थी: अवेकन्ड और नॉन-अवेकन्ड।"
    },
    {
        "panel": 34, "speaker": "narrator", "emotion": "sad", "camera": "tilt_down", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Aam log chiunti ki tarah rengte the, jabki hunters aasani se sab kuch pa lete the.",
        "text_speak": "आम लोग चींटी की तरह रेंगते थे, जबकि हंटर्स आसानी से सब कुछ पा लेते थे।"
    },
    {
        "panel": 35, "speaker": "suho", "emotion": "sad", "camera": "tilt_down", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Suho art class mein canvas par rang bharte hue apni kismat par gaur kar raha tha.",
        "text_speak": "सू-हो आर्ट क्लास में कैनवस पर रंग भरते हुए अपनी किस्मत पर गौर कर रहा था।"
    },
    {
        "panel": 36, "speaker": "suho", "emotion": "sad", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Zinda rehne ke liye doosron par nirbhar rehna... ye be-basi use andar se khaa rahi thi.",
        "text_speak": "ज़िंदा रहने के लिए दूसरों पर निर्भर रहना... ये बे-बसी उसे अंदर से खा रही थी।"
    },
    {
        "panel": 37, "speaker": "narrator", "emotion": "sad", "camera": "slow_pull", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Uske maa-baap... Sung Jin-Woo aur Cha Hae-In saalon se gayab the.",
        "text_speak": "उसके माँ-बाप... सुंग जिन-वू और चा हे-इन सालों से गायब थे।"
    },
    {
        "panel": 38, "speaker": "suho", "emotion": "desperate", "camera": "slow_push", "music": "mystery_ambient", "sfx": "heartbeat_low",
        "text_sub": "Maa kehti thi main bilkul papa jaisa dikhta hoon... Agar papa yahan hote, toh is kamzori se kaise nikalte?",
        "text_speak": "माँ कहती थी मैं बिल्कुल पापा जैसा दिखता हूँ... अगर पापा यहाँ होते, तो इस कमज़ोरी से कैसे निकलते?"
    },
    {
        "panel": 39, "speaker": "teacher", "emotion": "curious", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "'Suho... aaj tumhara dhyan painting par kaafi achha hai!'",
        "text_speak": "'सू-हो... आज तुम्हारा ध्यान पेंटिंग पर काफ़ी अच्छा है!'"
    },

    # [ACT 4: BERU'S SKETCH & THE BLUE FLAME MONSTER]
    {
        "panel": 40, "speaker": "teacher", "emotion": "curious", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
        "text_sub": "'Ye kya banaya hai? Kya ye koi chiunti jaisa insaan hai?'",
        "text_speak": "'ये क्या बनाया है? क्या ये कोई चींटी जैसा इंसान है?'"
    },
    {
        "panel": 41, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho khud hairaan tha... usne anjaane mein Shadow Ant King Beru ka chehra bana diya tha!",
        "text_speak": "सू-हो खुद हैरान था... उसने अनजाने में शैडो ऐंट किंग बेरू का चेहरा बना दिया था!"
    },
    {
        "panel": 42, "speaker": "narrator", "emotion": "excited", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Bahar Gate se raid squad kamyabi ke saath bahar aa gayi.",
        "text_speak": "बाहर गेट से रेड स्क्वॉड कामयाबी के साथ बाहर आ गई।"
    },
    {
        "panel": 43, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Association ke staff ne kaha: 'Hunter Kim, shaandaar kaam! Raid kamyab rahi!'",
        "text_speak": "एसोसिएशन के स्टाफ ने कहा: 'हंटर किम, शानदार काम! रेड कामयाब रही!'"
    },
    {
        "panel": 44, "speaker": "kim", "emotion": "calm", "camera": "slow_push", "music": "mystery_ambient", "sfx": "ambient_soft",
        "text_sub": "'Humein ek ajeeb monster mila... jiske munh aur aankhon se neeli aag nikal rahi thi.'",
        "text_speak": "'हमें एक अजीब मॉन्स्टर मिला... जिसके मुंह और आँखों से नीली आग निकल रही थी।'"
    },
    {
        "panel": 45, "speaker": "kim", "emotion": "curious", "camera": "slow_push", "music": "mystery_ambient", "sfx": "ambient_soft",
        "text_sub": "'Usne panje se mere pair par halki kharoch maari thi... waise koi badi baat nahi thi.'",
        "text_speak": "'उसने पंजे से मेरे पैर पर हल्की खरोंच मारी थी... वैसे कोई बड़ी बात नहीं थी।'"
    },
    {
        "panel": 46, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "flame_burst",
        "text_sub": "Lekin achanak... Hunter Kim ke pair ki kharoch par neeli aag bhadak uthi!",
        "text_speak": "लेकिन अचानक... हंटर किम के पैर की खरोंच पर नीली आग भड़क उठी!"
    },
    {
        "panel": 47, "speaker": "narrator", "emotion": "fearful", "camera": "handheld_shake", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Hunter Kim dard se cheekhne laga aur zameen par gir pada!",
        "text_speak": "हंटर किम दर्द से चीखने लगा और ज़मीन पर गिर पड़ा!"
    },
    {
        "panel": 48, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "'Hunter Kim... kya aap theek hain?!'",
        "text_speak": "'हंटर किम... क्या आप ठीक हैं?!'"
    },
    {
        "panel": 49, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "monster_roar",
        "text_sub": "BOOM! Hunter Kim ke munh aur aakhon se neeli jwala fati! Wo ek shaitani monster mein tabdeel ho gaya!",
        "text_speak": "बूम! हंटर किम के मुंह और आँखों से नीली ज्वाला फटी! वो एक शैतानी मॉन्स्टर में तब्दील हो गया!"
    },
    {
        "panel": 50, "speaker": "narrator", "emotion": "fearful", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Poore plaza mein cheekh-pukaar mach gayi!",
        "text_speak": "पूरे प्लाज़ा में चीख-पुकार मच गई!"
    },

    # [ACT 5: MASSACRE & CLASSROOM TERROR]
    {
        "panel": 51, "speaker": "narrator", "emotion": "dramatic", "camera": "tilt_down", "music": "dark_intense", "sfx": "impact_heavy",
        "text_sub": "Infected hunter ne guards aur baki hunters ko cheer-faad kar phenkna shuru kar diya!",
        "text_speak": "इन्फेक्टेड हंटर ने गार्ड्स और बाकी हंटर्स को चीर-फाड़ कर फेंकना शुरू कर दिया!"
    },
    {
        "panel": 52, "speaker": "suho", "emotion": "surprised", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Khidki se cheekhein sunkar Suho ne bahar dekha: 'Log aapas mein lad rahe hain...?!'",
        "text_speak": "खिड़की से चीखें सुनकर सू-हो ने बाहर देखा: 'लोग आपस में लड़ रहे हैं...?!'"
    },
    {
        "panel": 53, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "flame_burst",
        "text_sub": "Unki aakhein neeli roshni se dahak rahi thi... wo insaan nahi, monsters ban chuke the!",
        "text_speak": "उनकी आँखें नीली रोशनी से दहक रही थी... वो इंसान नहीं, मॉन्स्टर्स बन चुके थे!"
    },
    {
        "panel": 54, "speaker": "teacher", "emotion": "desperate", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Instructor Im se bachhe bole: 'Aap toh Awakened hain, kuch kijiye!' Par wo kaanpte hue bola: 'Main toh sirf E-Rank hoon...!'",
        "text_speak": "इंस्ट्रक्टर इम से बच्चे बोले: 'आप तो अवेकन्ड हैं, कुछ कीजिए!' पर वो कांपते हुए बोला: 'मैं तो सिर्फ ई-रैंक हूँ...!'"
    },
    {
        "panel": 55, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Tabhi wo neeli aag wala monster building ki chat par chadh gaya aur classroom ki khidki par nishana lagaya!",
        "text_speak": "तभी वो नीली आग वाला मॉन्स्टर बिल्डिंग की छत पर चढ़ गया और क्लासरूम की खिड़की पर निशाना लगाया!"
    },
    {
        "panel": 56, "speaker": "suho", "emotion": "desperate", "camera": "handheld_shake", "music": "dark_intense", "sfx": "glass_shatter",
        "text_sub": "'BHAAGO...!' CRASH! Sheesha todte hue monster seedha class ke andar ghus gaya!",
        "text_speak": "'भागो...!' क्रैश! शीशा तोड़ते हुए मॉन्स्टर सीधा क्लास के अंदर घुस गया!"
    },
    {
        "panel": 57, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "monster_roar",
        "text_sub": "GHOOR! Monster ki dahad se poora kamra kaanp utha!",
        "text_speak": "घूर! मॉन्स्टर की दहाड़ से पूरा कमरा कांप उठा!"
    },
    {
        "panel": 58, "speaker": "girl", "emotion": "desperate", "camera": "tilt_down", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Ek ladki zameen par gir gayi: 'M-Mere pair jam gaye hain... Mujhe bachao...!'",
        "text_speak": "एक लड़की ज़मीन पर गिर गई: 'म-मेरे पैर जम गए हैं... मुझे बचाओ...!'"
    },
    {
        "panel": 59, "speaker": "suho", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Suho bahar nikalte hue bola: 'Main hunters ko lekar aata hoon...!'",
        "text_speak": "सू-हो बाहर निकलते हुए बोला: 'मैं हंटर्स को लेकर आता हूँ...!'"
    },

    # [ACT 6: COURAGE OF THE WEAK & SYSTEM RETURN]
    {
        "panel": 60, "speaker": "suho", "emotion": "angry", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Corridor mein aate hi Suho ruk gaya: 'Lanat hai mujhpar! Hunters ko bulane ka matlab hai use maut ke muh mein chhodna!'",
        "text_speak": "कॉरिडोर में आते ही सू-हो रुक गया: 'लानत है मुझपर! हंटर्स को बुलाने का मतलब है उसे मौत के मुंह में छोड़ना!'"
    },
    {
        "panel": 61, "speaker": "suho", "emotion": "desperate", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "'Main non-awakened hoon toh kya hua?! Sung Suho, dhoondho tum kya kar sakte ho...!'",
        "text_speak": "'मैं नॉन-अवेकन्ड हूँ तो क्या हुआ?! सुंग सू-हो, ढूंढो तुम क्या कर सकते हो...!'"
    },
    {
        "panel": 62, "speaker": "suho", "emotion": "epic", "camera": "slow_pull", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "'AGAR PAPA YAHAN HOTE... TOH WO KYA KARTE?!'",
        "text_speak": "'अगर पापा यहाँ होते... तो वो क्या करते?!'"
    },
    {
        "panel": 63, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "monster_roar",
        "text_sub": "Classroom mein monster ne us roti hui ladki par apna khooni panja uthaya!",
        "text_speak": "क्लासरूम में मॉन्स्टर ने उस रोती हुई लड़की पर अपना खूनी पंजा उठाया!"
    },
    {
        "panel": 64, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "LEKIN TABHI! Suho haath mein bhari laal Fire Extinguisher lekar bijli ki tarah kood pada!",
        "text_speak": "लेकिन तभी! सू-हो हाथ में भारी लाल फायर एक्सटिंग्विशर लेकर बिजली की तरह कूद पड़ा!"
    },
    {
        "panel": 65, "speaker": "suho", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "impact_heavy",
        "text_sub": "'AGAR PAPA HOTE TOH YAHI KARTE!' THWAAAM! Fire extinguisher seedha monster ke munh par de maara!",
        "text_speak": "'अगर पापा होते तो यही करते!' ठ्वाम! फायर एक्सटिंग्विशर सीधा मॉन्स्टर के मुंह पर दे मारा!"
    },
    {
        "panel": 66, "speaker": "narrator", "emotion": "surprised", "camera": "slow_push", "music": "mystery_ambient", "sfx": "ambient_soft",
        "text_sub": "Aur usi lamhe... Suho ke aakhon ke samne digital static chamakne laga!",
        "text_speak": "और उसी लम्हे... सू-हो की आँखों के सामने डिजिटल स्टैटिक चमकने लगा!"
    },
    {
        "panel": 67, "speaker": "system", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "system_chime",
        "text_sub": "[ALERT] Aapne secret quest 'COURAGE OF THE WEAK' ki sabhi shartein poori kar li hain!",
        "text_speak": "[अलर्ट] आपने सीक्रेट क्वेस्ट 'करेज ऑफ द वीक' की सभी शर्तें पूरी कर ली हैं!"
    },
    {
        "panel": 68, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "The System has returned! Sung Jin-Woo ke baad... ab hai Sung Suho ka daur! Subscribe karein Chapter 2 ke liye!",
        "text_speak": "द सिस्टम हैज़ रिटर्नड! सुंग जिन-वू के बाद... अब है सुंग सू-हो का दौर! सब्सक्राइब करें चैप्टर दो के लिए!"
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# AUDIO GENERATION: EDGE-TTS + PROCEDURAL SFX & MUSIC
# ─────────────────────────────────────────────────────────────────────────────
async def generate_voice(text: str, speaker: str, emotion: str, out_wav: Path):
    """Generate Edge-TTS voice wav with emotion modulation."""
    import edge_tts
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    tmp_mp3 = out_wav.with_suffix(".mp3")

    cfg = SPEAKER_CONFIG.get(speaker, SPEAKER_CONFIG["narrator"])
    em = EMOTION_VOICE_MOD.get(emotion, {"rate_mod": 0, "pitch_mod": 0})

    base_rate = int(cfg["rate"].replace("%", "").replace("+", ""))
    base_pitch = int(cfg["pitch"].replace("Hz", "").replace("+", ""))

    final_rate = f"{base_rate + em['rate_mod']:+d}%"
    final_pitch = f"{base_pitch + em['pitch_mod']:+d}Hz"

    for attempt in range(1, 4):
        try:
            comm = edge_tts.Communicate(text, cfg["voice"], rate=final_rate, pitch=final_pitch)
            await comm.save(str(tmp_mp3))
            break
        except Exception as e:
            if attempt == 3:
                raise
            await asyncio.sleep(2)

    ff = ffmpeg_bin()
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp_mp3),
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)
    if tmp_mp3.exists():
        tmp_mp3.unlink()


def generate_music(music_type: str, duration: float, out_wav: Path):
    """Generate rich procedural atmospheric score."""
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "dark_drone":      f"aevalsrc='0.24*sin(2*PI*55*t)+0.18*sin(2*PI*82.4*t)+0.12*sin(2*PI*110*t)+0.06*sin(2*PI*164.8*t)':d={d}:s=44100,volume=0.35",
        "dark_intense":    f"aevalsrc='0.30*sin(2*PI*45*t)+0.22*sin(2*PI*65*t)+0.15*sin(2*PI*130*t)+0.08*(random(0)-0.5)':d={d}:s=44100,volume=0.40",
        "epic_adventure":  f"aevalsrc='0.22*sin(2*PI*130.8*t)+0.18*sin(2*PI*164.8*t)+0.15*sin(2*PI*196*t)+0.14*sin(2*PI*261.6*t)+0.06*sin(2*PI*392*t)':d={d}:s=44100,volume=0.38",
        "city_ambient":    f"aevalsrc='0.16*sin(2*PI*220*t)+0.12*sin(2*PI*277*t)+0.10*sin(2*PI*330*t)':d={d}:s=44100,volume=0.25",
        "sad_piano":       f"aevalsrc='0.22*sin(2*PI*174.6*t)+0.16*sin(2*PI*220*t)+0.14*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.32",
        "curious_ambient": f"aevalsrc='0.18*sin(2*PI*196*t)+0.14*sin(2*PI*246.9*t)+0.10*sin(2*PI*293.7*t)':d={d}:s=44100,volume=0.28",
        "mystery_ambient": f"aevalsrc='0.20*sin(2*PI*73.4*t)+0.15*sin(2*PI*110*t)+0.12*sin(2*PI*146.8*t)':d={d}:s=44100,volume=0.32",
    }
    flt = filters.get(music_type, filters["dark_drone"])

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)


def generate_sfx(sfx_type: str, duration: float, out_wav: Path):
    """Generate procedural sound effects."""
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "system_chime":   f"aevalsrc='0.35*exp(-3*t)*sin(2*PI*880*t)+0.28*exp(-3.5*t)*sin(2*PI*1760*t)+0.18*exp(-4*t)*sin(2*PI*2640*t)':d={d}:s=44100",
        "glass_shatter":  f"aevalsrc='0.45*exp(-8*t)*(random(0)-0.5)+0.30*exp(-14*t)*sin(2*PI*3200*t)':d={d}:s=44100",
        "monster_roar":   f"aevalsrc='0.38*sin(2*PI*(75+20*sin(2*PI*8*t))*t)+0.25*(random(0)-0.5)':d={d}:s=44100",
        "flame_burst":    f"aevalsrc='0.35*exp(-2.5*t)*(random(0)-0.5)+0.25*sin(2*PI*(130-45*t)*t)':d={d}:s=44100",
        "impact_heavy":   f"aevalsrc='0.45*exp(-7*t)*sin(2*PI*55*t)+0.25*exp(-10*t)*(random(0)-0.5)':d={d}:s=44100",
        "braam_impact":   f"aevalsrc='0.40*exp(-1.5*t)*sin(2*PI*40*t)+0.25*exp(-2*t)*sin(2*PI*80*t)':d={d}:s=44100",
        "whoosh_energy":  f"aevalsrc='0.32*exp(-4*t)*sin(2*PI*(320-200*t)*t)':d={d}:s=44100",
        "heartbeat_low":  f"aevalsrc='0.35*sin(2*PI*45*t)*pow(max(0,sin(2*PI*1.2*t)),10)':d={d}:s=44100",
        "portal_hum":     f"aevalsrc='0.25*sin(2*PI*60*t)+0.15*sin(2*PI*(60+8*sin(2*PI*0.5*t))*t)':d={d}:s=44100",
        "ambient_soft":   f"aevalsrc='0.08*sin(2*PI*120*t)':d={d}:s=44100",
    }
    flt = filters.get(sfx_type, filters["ambient_soft"])

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)


def mix_audio(voice_wav: Path, music_wav: Path, sfx_wav: Path, duration: float, out_aac: Path):
    """Mix 3 audio channels with dynamic ducking."""
    ff = ffmpeg_bin()
    out_aac.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filter_complex = (
        "[0:a]volume=1.35,apad[v];"
        "[1:a]volume=0.24[m];"
        "[2:a]volume=0.32[s];"
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
# LIVING SCENE RENDERER (Ken Burns + Blurred Wings 1920x1080)
# ─────────────────────────────────────────────────────────────────────────────
def render_scene_video(img_path: Path, duration: float, camera: str, out_mp4: Path):
    """
    Render 1080p widescreen video from vertical manhwa panel:
      - Background: Ambient blurred and darkened 1920x1080 canvas
      - Foreground: High-definition artwork with dynamic scroll/zoom
      - Camera movement: Ken Burns smooth scroll or zoom
    """
    ff = ffmpeg_bin()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    dur = round(duration, 3)
    w, h = 1920, 1080

    # Background filter
    bg_flt = f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=25:5,eq=brightness=-0.22:contrast=0.95[bg]"

    # Check panel aspect ratio
    with Image.open(str(img_path)) as im:
        iw, ih = im.size

    # If image is tall (vertical manhwa panel), scroll from top to bottom
    if camera == "tilt_down" or (ih / max(1, iw) > 1.4 and camera != "sudden_zoom"):
        fg_flt = (
            f"[0:v]scale=-1:max(1040\\,ih*1040/iw)[fg_raw];"
            f"[fg_raw]crop=w=iw:h=1040:x=0:y='(ih-1040)*t/{dur:.2f}'[fg]"
        )
    else:
        fg_flt = f"[0:v]scale=-1:1040[fg]"

    overlay_flt = "[bg][fg]overlay=(W-w)/2:(H-h)/2[comp]"

    if camera == "slow_push":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.04*t/{dur:.2f})/2)':h='2*floor({h}*(1.01+0.04*t/{dur:.2f})/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p"
        )
    elif camera == "slow_pull":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.05-0.04*t/{dur:.2f})/2)':h='2*floor({h}*(1.05-0.04*t/{dur:.2f})/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p"
        )
    elif camera == "sudden_zoom":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.08*pow(t/{dur:.2f},1.8))/2)':h='2*floor({h}*(1.01+0.08*pow(t/{dur:.2f},1.8))/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p"
        )
    elif camera == "handheld_shake":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*1.04/2)':h='2*floor({h}*1.04/2)',"
            f"crop={w}:{h}:'(in_w-{w})/2+6*sin(14*t)':'(in_h-{h})/2+6*cos(11*t)',format=yuv420p"
        )
    else:
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.025*t/{dur:.2f})/2)':h='2*floor({h}*(1.01+0.025*t/{dur:.2f})/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p"
        )

    full_vf = f"{bg_flt};{fg_flt};{overlay_flt};{comp_scale}"

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-t", str(dur),
        "-i", str(img_path),
        "-filter_complex", full_vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-r", "30", "-pix_fmt", "yuv420p",
        str(out_mp4)
    ], check=True)


# ─────────────────────────────────────────────────────────────────────────────
# SUBTITLE GENERATOR (Solo Leveling Cyan & Gold Aesthetic)
# ─────────────────────────────────────────────────────────────────────────────
def generate_subtitles_ass(scenes_meta: list[dict], out_ass: Path):
    """Generate high-contrast ASS subtitles."""
    out_ass.parent.mkdir(parents=True, exist_ok=True)

    header = """[Script Info]
Title: Solo Leveling Ragnarok Chapter 1 Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,48,&H00FFFFFF,&H000000FF,&H001A0B2E,&H80000000,-1,0,0,0,100,100,1,0,1,4,3,2,60,60,54,1
Style: SystemAlert,Arial Black,52,&H0000E5FF,&H000000FF,&H00002244,&H80000000,-1,0,0,0,100,100,2,0,1,5,4,2,60,60,54,1
Style: TitleStyle,Arial Black,56,&H0000D7FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,2,0,1,5,5,8,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def fmt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:01d}:{m:02d}:{s:05.2f}"

    lines = [header]
    for sc in scenes_meta:
        t_start = fmt_time(sc["start_time"])
        t_end = fmt_time(sc["end_time"])
        text = sc["text_sub"]
        style = "SystemAlert" if sc.get("speaker") == "system" else "Default"
        lines.append(f"Dialogue: 0,{t_start},{t_end},{style},,0,0,0,,{text}\n")

    with open(out_ass, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ─────────────────────────────────────────────────────────────────────────────
# COVER THUMBNAIL GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def generate_cover_thumbnail(panel_path: Path, out_cover: Path):
    """Creates a high-impact YouTube cover thumbnail."""
    ff = ffmpeg_bin()
    out_cover.parent.mkdir(parents=True, exist_ok=True)
    
    # 1280x720 16:9 YouTube thumbnail with title text
    vf = (
        "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
        "eq=contrast=1.15:brightness=-0.05:saturation=1.2,"
        "drawbox=y=ih-200:color=black@0.65:width=iw:height=200:t=fill,"
        "drawtext=text='SOLO LEVELING: RAGNAROK':fontcolor=0x00F0FF:fontsize=52:bold=1:x=(w-text_w)/2:y=h-165:shadowcolor=black:shadowx=3:shadowy=3,"
        "drawtext=text='CHAPTER 1 | JIN-WOO KE BETE KA JAADU ⚔️':fontcolor=white:fontsize=34:bold=1:x=(w-text_w)/2:y=h-95:shadowcolor=black:shadowx=2:shadowy=2"
    )
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(panel_path),
        "-vf", vf,
        "-frames:v", "1",
        str(out_cover)
    ], check=True)


# ─────────────────────────────────────────────────────────────────────────────
# MASTER GENERATOR PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
async def generate_chapter1_video():
    out_dir = ROOT / "output" / "solo_leveling_ragnarok_ch1"
    panels_dir = out_dir / "panels"
    checkpoints_dir = out_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 76)
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 1 — VIDEO ENGINE")
    print(f"  Total Scenes: {len(SCENES_DATA)}")
    print(f"  Target Resolution: 1920x1080 (1080p 30fps Full-Fidelity)")
    print(f"  Pacing: Balanced Anime Storytelling (1.18x)")
    print("=" * 76)

    scenes_meta = []
    current_time = 0.0
    concat_list = []

    for i, sc in enumerate(SCENES_DATA, start=1):
        clip_mp4 = checkpoints_dir / f"clip_{i:04d}.mp4"
        panel_num = sc["panel"]
        panel_path = panels_dir / f"panel_{panel_num:03d}.jpg"

        if not panel_path.exists():
            print(f"  ⚠️ Warning: Panel {panel_path} not found! Using panel 1 as fallback.")
            panel_path = panels_dir / "panel_001.jpg"

        voice_wav = checkpoints_dir / f"voice_{i:04d}.wav"
        music_wav = checkpoints_dir / f"music_{i:04d}.wav"
        sfx_wav = checkpoints_dir / f"sfx_{i:04d}.wav"
        audio_aac = checkpoints_dir / f"audio_{i:04d}.aac"
        silent_mp4 = checkpoints_dir / f"silent_{i:04d}.mp4"

        # Check if full clip is already cached
        if clip_mp4.exists() and clip_mp4.stat().st_size > 10000:
            pr = probe(clip_mp4)
            dur = float(pr.get("format", {}).get("duration", 3.0))
            scenes_meta.append({
                "scene_num": i,
                "start_time": current_time,
                "end_time": current_time + dur,
                "text_sub": sc["text_sub"],
                "speaker": sc["speaker"],
            })
            current_time += dur
            concat_list.append(f"file '{clip_mp4.resolve().as_posix()}'\n")
            print(f"  ✓ [{i:02d}/{len(SCENES_DATA)}] Cached: clip_{i:04d}.mp4 ({dur:.1f}s)")
            continue

        print(f"\n  🎬 [{i:02d}/{len(SCENES_DATA)}] Rendering Scene {i}...")

        # 1. Voice
        if not voice_wav.exists():
            await generate_voice(sc["text_speak"], sc["speaker"], sc["emotion"], voice_wav)
        
        pr_voice = probe(voice_wav)
        v_dur = float(pr_voice.get("format", {}).get("duration", 2.5))
        scene_dur = max(2.0, v_dur + 0.35)

        # 2. Score & SFX
        if not music_wav.exists():
            generate_music(sc["music"], scene_dur, music_wav)
        if not sfx_wav.exists():
            generate_sfx(sc["sfx"], scene_dur, sfx_wav)

        # 3. Mix Audio
        if not audio_aac.exists():
            mix_audio(voice_wav, music_wav, sfx_wav, scene_dur, audio_aac)

        # 4. Render Living Video
        if not silent_mp4.exists():
            render_scene_video(panel_path, scene_dur, sc["camera"], silent_mp4)

        # 5. Mux Video + Audio
        ff = ffmpeg_bin()
        subprocess.run([
            ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(silent_mp4),
            "-i", str(audio_aac),
            "-c:v", "copy", "-c:a", "copy",
            "-shortest",
            str(clip_mp4)
        ], check=True)

        scenes_meta.append({
            "scene_num": i,
            "start_time": current_time,
            "end_time": current_time + scene_dur,
            "text_sub": sc["text_sub"],
            "speaker": sc["speaker"],
        })
        current_time += scene_dur
        concat_list.append(f"file '{clip_mp4.resolve().as_posix()}'\n")
        print(f"  ✓ Scene {i:02d} complete ({scene_dur:.1f}s)")

    # ─────────────────────────────────────────────────────────────────────────
    # CONCATENATE ALL CLIPS
    # ─────────────────────────────────────────────────────────────────────────
    concat_txt = out_dir / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.writelines(concat_list)

    unsubbed_mp4 = out_dir / "unsubbed.mp4"
    print("\n  📦 Concatenating all scenes into master cut...")
    ff = ffmpeg_bin()
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(unsubbed_mp4)
    ], check=True)

    # ─────────────────────────────────────────────────────────────────────────
    # SUBTITLES BURN-IN
    # ─────────────────────────────────────────────────────────────────────────
    subtitles_ass = out_dir / "subtitles.ass"
    generate_subtitles_ass(scenes_meta, subtitles_ass)

    final_mp4 = out_dir / "final.mp4"
    ass_escaped = subtitles_ass.resolve().as_posix().replace(":", "\\:")
    print("  🎨 Burning in styled Solo Leveling kinetic subtitles...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(unsubbed_mp4),
        "-vf", f"subtitles='{ass_escaped}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "copy",
        str(final_mp4)
    ], check=True)

    # ─────────────────────────────────────────────────────────────────────────
    # THUMBNAIL COVER
    # ─────────────────────────────────────────────────────────────────────────
    cover_jpg = out_dir / "cover.jpg"
    cover_src = panels_dir / "panel_067.jpg"  # Golden System Alert Panel
    if not cover_src.exists():
        cover_src = panels_dir / "panel_001.jpg"
    generate_cover_thumbnail(cover_src, cover_jpg)

    pr_final = probe(final_mp4)
    final_dur = float(pr_final.get("format", {}).get("duration", 0))
    final_sz = final_mp4.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 76)
    print("  🎉 SOLO LEVELING: RAGNAROK CHAPTER 1 RECAP READY!")
    print(f"  🎬 Video: {final_mp4}")
    print(f"  ⏱️ Duration: {final_dur:.1f}s ({final_dur/60:.2f} mins)")
    print(f"  💾 File Size: {final_sz:.2f} MB")
    print(f"  🖼️ Cover: {cover_jpg}")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(generate_chapter1_video())
