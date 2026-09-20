"""
generate_solo_leveling_ch2_video.py — Solo Leveling Chapter 2: Cinematic Hindi Explainer Video.

Story:
  • Hunters Association guards discuss Jin-Woo ("The Weakest E-Rank") entering a D-Rank dungeon.
  • Ju-Hee heals Jin-Woo during the fierce raid and scolds him out of concern.
  • Jin-Woo jokes that he hunts for fun, hiding his true pain.
  • Hunters collect valuable magic cores, while Jin-Woo only gets a tiny, worthless E-Rank core.
  • Discovery of the DOUBLE LAIR inside the cave!
  • Mr. Song illuminates the dark tunnel, revealing a colossal ancient gate.
  • The 17 hunters hold a vote: 8 vote TO ENTER, 8 vote TO LEAVE — a DEAD TIE!
  • The entire fate rests on Sung Jin-Woo's final vote.
  • Remembering his sick mother and his sister's college fees, Jin-Woo votes YES: "I'M GOING!"
  • They step into the jaws of death — The Double Dungeon!

Optimizations:
  • Speed: 1.5x fast-paced narration (Edge-TTS rate +45% to +50%)
  • Fast scene transitions (no dead pauses)
  • Pronunciation perfected via phonetic Hindi/Devanagari text mapping
  • Clean styled English/Hinglish subtitles
  • Procedural mood score + SFX (fireball, healing chime, braam, sword slash)
  • Full 1080p Ken Burns widescreen presentation
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.ffmpeg import ffmpeg_bin, probe

# ─────────────────────────────────────────────────────────────────────────────
# PRONUNCIATION & VOICE ENGINE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
SPEAKER_CONFIG = {
    "narrator": {"voice": "hi-IN-MadhurNeural", "rate": "+45%", "pitch": "+0Hz"},
    "jinwoo":   {"voice": "hi-IN-MadhurNeural", "rate": "+48%", "pitch": "+3Hz"},
    "juhee":    {"voice": "hi-IN-SwaraNeural",  "rate": "+45%", "pitch": "+4Hz"},
    "kim":      {"voice": "hi-IN-MadhurNeural", "rate": "+44%", "pitch": "-6Hz"},
    "bak":      {"voice": "hi-IN-MadhurNeural", "rate": "+44%", "pitch": "-4Hz"},
    "song":     {"voice": "hi-IN-MadhurNeural", "rate": "+42%", "pitch": "-10Hz"},
    "guard":    {"voice": "hi-IN-MadhurNeural", "rate": "+44%", "pitch": "-3Hz"},
    "hunter":   {"voice": "hi-IN-MadhurNeural", "rate": "+46%", "pitch": "-2Hz"},
}

EMOTION_VOICE_MOD = {
    "desperate":  {"rate_mod": 4,  "pitch_mod": -4},
    "fearful":    {"rate_mod": -2, "pitch_mod": -4},
    "sad":        {"rate_mod": -4, "pitch_mod": -3},
    "dramatic":   {"rate_mod": 2,  "pitch_mod": -2},
    "angry":      {"rate_mod": 6,  "pitch_mod": +2},
    "excited":    {"rate_mod": 5,  "pitch_mod": +4},
    "calm":       {"rate_mod": 0,  "pitch_mod": 0},
    "happy":      {"rate_mod": 3,  "pitch_mod": +2},
    "curious":    {"rate_mod": 2,  "pitch_mod": +2},
    "nervous":    {"rate_mod": 0,  "pitch_mod": +2},
    "surprised":  {"rate_mod": 5,  "pitch_mod": +6},
    "hopeful":    {"rate_mod": 3,  "pitch_mod": +2},
    "serious":    {"rate_mod": 2,  "pitch_mod": -3},
}

# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 2 SCENES DATA (All 54 Pages)
# Each scene has:
#   - text_sub: Displayed in subtitles (clean readable Hinglish/English)
#   - text_speak: Spoken by TTS (phonetically perfected in Devanagari to avoid mispronunciation)
# ─────────────────────────────────────────────────────────────────────────────
SCENES_DATA = [
    # [ACT 1: THE GUARDS & THE GATE]
    {
        "page": 1, "speaker": "guard", "emotion": "calm", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Raid team andar chali gayi hai... rasta bilkul saaf hai!",
        "text_speak": "रेड टीम अंदर चली गई है... रास्ता बिल्कुल साफ़ है!"
    },
    {
        "page": 2, "speaker": "guard", "emotion": "curious", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Kya soch rahe ho bhai? Chehra utra hua kyun hai?",
        "text_speak": "क्या सोच रहे हो भाई? चेहरा उतरा हुआ क्यों है?"
    },
    {
        "page": 3, "speaker": "guard", "emotion": "sad", "camera": "slow_pull", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Yaar mujhe Hunter Sung Jin-Woo ki chinta ho rahi hai... hum usse coffee bhi nahi de paaye.",
        "text_speak": "यार मुझे हंटर सुंग जिन-वू की चिंता हो रही है... हम उसे कॉफ़ी भी नहीं दे पाए।"
    },
    {
        "page": 4, "speaker": "guard", "emotion": "curious", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Wahi E-Rank Hunter na? Waise ye Dungeon kaunse rank ka hai? D-Rank ka bataya tha!",
        "text_speak": "वही ई-रैंक हंटर ना? वैसे ये डंजन कौन से रैंक का है? डी-रैंक का बताया था!"
    },
    {
        "page": 5, "speaker": "guard", "emotion": "nervous", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
        "text_sub": "Maine aaj tak Jin-Woo ko bina chot khaye nahi dekha! Khair, D-Rank hai toh kuch bura nahi hoga... chalo chalte hain!",
        "text_speak": "मैंने आज तक जिन-वू को बिना चोट खाए नहीं देखा! ख़ैर, डी-रैंक है तो कुछ बुरा नहीं होगा... चलो चलते हैं!"
    },
    {
        "page": 6, "speaker": "narrator", "emotion": "excited", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Solo Leveling Chapter 2! Jahan kismat lene wali hai ek bhayanak mod!",
        "text_speak": "सोलो लेवलिंग चैप्टर दो! जहाँ क़िस्मत लेने वाली है एक भयानक मोड़!"
    },

    # [ACT 2: JU-HEE HEALING & JIN-WOO'S PAIN]
    {
        "page": 7, "speaker": "juhee", "emotion": "sad", "camera": "slow_push", "music": "soft_strings", "sfx": "magic_heal",
        "text_sub": "Jin-Woo... tum itni zidd kyun karte ho hunter banne ki? Is tarah ladna tumhare liye bohot khatarnak hai!",
        "text_speak": "जिन-वू... तुम इतनी ज़िद्द क्यों करते हो हंटर बनने की? इस तरह लड़ना तुम्हारे लिए बहुत ख़तरनाक है!"
    },
    {
        "page": 8, "speaker": "juhee", "emotion": "angry", "camera": "slow_push", "music": "soft_strings", "sfx": "ambient_soft",
        "text_sub": "Har baar nayi museebat mol lete ho! Aur Jin-Woo sar jhuka kar kehta hai... Maaf karna Ju-Hee.",
        "text_speak": "हर बार नई मुसीबत मोल लेते हो! और जिन-वू सर झुका कर कहता है... माफ़ करना जू-ही।"
    },
    {
        "page": 9, "speaker": "juhee", "emotion": "sad", "camera": "slow_pull", "music": "soft_strings", "sfx": "ambient_soft",
        "text_sub": "Mujhe maafi nahi chahiye Jin-Woo! Mujhe sirf tumhari chinta hoti hai...",
        "text_speak": "मुझे माफ़ी नहीं चाहिए जिन-वू! मुझे सिर्फ़ तुम्हारी चिंता होती है..."
    },

    # [ACT 3: THE BATTLE RAGES]
    {
        "page": 10, "speaker": "narrator", "emotion": "excited", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "fireball_whoosh",
        "text_sub": "Aur wahan doosri taraf... hunters aag ke sholon se bhediyon ko raakh kar rahe the!",
        "text_speak": "और वहाँ दूसरी तरफ़... हंटर्स आग के शोलों से भेड़ियों को राख कर रहे थे!"
    },
    {
        "page": 11, "speaker": "narrator", "emotion": "excited", "camera": "handheld_shake", "music": "dark_intense", "sfx": "sword_slash",
        "text_sub": "Tez dhaar talwaron se monsters ke tukde kiye ja rahe the! Khoon ki bauchar ho rahi thi!",
        "text_speak": "तेज़ धार तलवारों से मॉन्स्टर्स के टुकड़े किए जा रहे थे! ख़ून की बौछार हो रही थी!"
    },
    {
        "page": 12, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Dungeon ke vishaal khambhon ke beech jadugaron aur yoddhaon ne poore maidan ko saaf kar diya!",
        "text_speak": "डंजन के विशाल खंभों के बीच जादूगरों और योद्धाओं ने पूरे मैदान को साफ़ कर दिया!"
    },
    {
        "page": 13, "speaker": "juhee", "emotion": "calm", "camera": "slow_push", "music": "soft_strings", "sfx": "ambient_soft", "use_crop": "page_013_clean.png",
        "text_sub": "Shukr hai... kam se kam ye raid ab khatam hone wali hai.",
        "text_speak": "शुक्र है... कम से कम ये रेड अब ख़त्म होने वाली है।"
    },
    {
        "page": 14, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "soft_strings", "sfx": "ambient_soft",
        "text_sub": "Ju-Hee ki jaadui roshni se Jin-Woo ke zakhm dheere dheere bharne lage the.",
        "text_speak": "जू-ही की जादुई रोशनी से जिन-वू के ज़ख़्म धीरे-धीरे भरने लगे थे।"
    },
    {
        "page": 15, "speaker": "hunter", "emotion": "happy", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
        "text_sub": "Lo bhai sab saaf! Bak bhai, tum abhi tak zinda ho matlab!",
        "text_speak": "लो भाई सब साफ़! बाक भाई, तुम अभी तक ज़िंदा हो मतलब!"
    },
    {
        "page": 16, "speaker": "bak", "emotion": "happy", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
        "text_sub": "Haha! Ye raid toh bilkul bacchon ka khel nikli! Koi dam hi nahi tha!",
        "text_speak": "हाहा! ये रेड तो बिल्कुल बच्चों का खेल निकली! कोई दम ही नहीं था!"
    },

    # [ACT 4: JIN-WOO'S SECRET REASON]
    {
        "page": 17, "speaker": "juhee", "emotion": "curious", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Jin-Woo... kya tumhare paas koi aisi wajah hai jisse tum hunting nahi chhodte?",
        "text_speak": "जिन-वू... क्या तुम्हारे पास कोई ऐसी वजह है जिससे तुम हंटिंग नहीं छोड़ते?"
    },
    {
        "page": 18, "speaker": "juhee", "emotion": "sad", "camera": "slow_pull", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Apni jaan ko har roz daav par lagane ki aakhir kya wajah hai?",
        "text_speak": "अपनी जान को हर रोज़ दाव पर लगाने की आख़िर क्या वजह है?"
    },
    {
        "page": 19, "speaker": "jinwoo", "emotion": "happy", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
        "text_sub": "Arrey main toh bas shauk ke liye hunter hoon! Agar ye nahi karunga toh boriyat se mar jaunga!",
        "text_speak": "अरे मैं तो बस शौक़ के लिए हंटर हूँ! अगर ये नहीं करूँगा तो बोरियत से मर जाऊँगा!"
    },
    {
        "page": 20, "speaker": "jinwoo", "emotion": "nervous", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
        "text_sub": "(Asli majboori bataunga toh sharmindagi hogi...) Aur Ju-Hee boli: Aise shauk rahe toh agla raid seedha narak mein hoga!",
        "text_speak": "असली मजबूरी बताऊंगा तो शर्मिंदगी होगी... और जू-ही बोली: ऐसे शौक़ रहे तो अगला रेड सीधा नर्क में होगा!"
    },
    {
        "page": 21, "speaker": "juhee", "emotion": "angry", "camera": "handheld_shake", "music": "light_warm", "sfx": "shock_sting",
        "text_sub": "Hanso mat pagal! Tanka toot jayega aur zakhm dobara khul jayega!",
        "text_speak": "हँसो मत पागल! टांका टूट जाएगा और ज़ख़्म दोबारा खुल जाएगा!"
    },

    # [ACT 5: THE MAGICAL CORES & THE DISCOVERY]
    {
        "page": 22, "speaker": "hunter", "emotion": "calm", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
        "text_sub": "Ye dekho... monster ko maarne ke baad milta hai ye chamakta hua Magical Core!",
        "text_speak": "ये देखो... मॉन्स्टर को मारने के बाद मिलता है ये चमकता हुआ मैजिकल कोर!"
    },
    {
        "page": 23, "speaker": "hunter", "emotion": "excited", "camera": "sudden_zoom", "music": "curious_ambient", "sfx": "ambient_soft",
        "text_sub": "Ek shandar chamakta sitara jaisa pathar... jiski keemat lakhon mein hoti hai!",
        "text_speak": "एक शानदार चमकता सितारा जैसा पत्थर... जिसकी क़ीमत लाखों में होती है!"
    },
    {
        "page": 24, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
        "text_sub": "Ek C-Rank monster ka magic core hazaron-lakhon rupaye deta hai...",
        "text_speak": "एक सी-रैंक मॉन्स्टर का मैजिक कोर हज़ारों-लाखों रुपये देता है..."
    },
    {
        "page": 25, "speaker": "narrator", "emotion": "sad", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Lekin Jin-Woo ek E-Rank Hunter tha... C-Rank monsters ko haath lagana bhi uske bas ki baat nahi thi.",
        "text_speak": "लेकिन जिन-वू एक ई-रैंक हंटर था... सी-रैंक मॉन्स्टर्स को हाथ लगाना भी उसके बस की बात नहीं थी।"
    },
    {
        "page": 26, "speaker": "jinwoo", "emotion": "sad", "camera": "slow_pull", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Itni chotein khane aur marte-marte bachne ke baad... mujhe mila sirf ek chhota sa E-Rank core.",
        "text_speak": "इतनी चोटें खाने और मरते-मरते बचने के बाद... मुझे मिला सिर्फ़ एक छोटा सा ई-रैंक कोर।"
    },
    {
        "page": 27, "speaker": "jinwoo", "emotion": "desperate", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
        "text_sub": "Apni jaan dav par laga kar itni kamayi? Aise main ghar kaise chalaunga...",
        "text_speak": "अपनी जान दाव पर लगा कर इतनी कमाई? ऐसे मैं घर कैसे चलाऊँगा..."
    },
    {
        "page": 28, "speaker": "hunter", "emotion": "excited", "camera": "sudden_zoom", "music": "mystery_ambient", "sfx": "shock_sting",
        "text_sub": "Achanak pichhe se ek hunter chillaya: Suno sab log! Yahan ek aur raasta hai!",
        "text_speak": "अचानक पीछे से एक हंटर चिल्लाया: सुनो सब लोग! यहाँ एक और रास्ता है!"
    },

    # [ACT 6: THE DOUBLE LAIR]
    {
        "page": 29, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_push", "music": "mystery_ambient", "sfx": "portal_hum",
        "text_sub": "Sabhi hunters daud kar wahan pahunche... samne tha ek vishaal gufa ka kaala darwaza — The Double Lair!",
        "text_speak": "सभी हंटर्स दौड़ कर वहाँ पहुँचे... सामने था एक विशाल गुफ़ा का काला दरवाज़ा — द डबल लेयर!"
    },
    {
        "page": 30, "speaker": "song", "emotion": "serious", "camera": "slow_push", "music": "mystery_ambient", "sfx": "ambient_soft",
        "text_sub": "Veteran Leader Mr. Song ne dekha aur bole: Double Dungeon ki afwaah sach nikli... ye waqai asli hai!",
        "text_speak": "वेटरन लीडर मिस्टर सोंग ने देखा और बोले: डबल डंजन की अफ़वाह सच निकली... ये वाक़ई असली है!"
    },
    {
        "page": 31, "speaker": "narrator", "emotion": "excited", "camera": "sudden_zoom", "music": "mystery_ambient", "sfx": "fireball_whoosh",
        "text_sub": "Mr. Song ne apni hatheli par ek dhum-dhamaka aag ka gola jala liya!",
        "text_speak": "मिस्टर सोंग ने अपनी हथेली पर एक धू-धू जलता आग का गोला बना लिया!"
    },
    {
        "page": 32, "speaker": "song", "emotion": "serious", "camera": "slow_push", "music": "mystery_ambient", "sfx": "fireball_whoosh",
        "text_sub": "Unhone us aag ke gole ko seedha gufa ke andhere mein phenk diya!",
        "text_speak": "उन्होंने उस आग के गोले को सीधा गुफ़ा के अंधेरे में फेंक दिया!"
    },
    {
        "page": 33, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Aag ki lapat taaron ki tarah andheri surang mein aage daudti chali gayi!",
        "text_speak": "आग की लपट तारों की तरह अंधेरी सुरंग में आगे दौड़ती चली गई!"
    },
    {
        "page": 34, "speaker": "narrator", "emotion": "fearful", "camera": "slow_pull", "music": "dark_drone", "sfx": "braam_impact",
        "text_sub": "Aur roshni padte hi samne dikha... ek prachin, khaufnak mandir ka vishaal darwaza!",
        "text_speak": "और रोशनी पड़ते ही सामने दिखा... एक प्राचीन, ख़ौफ़नाक मंदिर का विशाल दरवाज़ा!"
    },
    {
        "page": 35, "speaker": "song", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Mr. Song bole: Sabhi dhyan se meri baat suno...",
        "text_speak": "मिस्टर सोंग बोले: सभी ध्यान से मेरी बात सुनो..."
    },
    {
        "page": 36, "speaker": "song", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Dungeon tab tak band nahi hota jab tak Boss zinda ho. Iska matlab Dungeon Boss isi gufa ke andar hai!",
        "text_speak": "डंजन तब तक बंद नहीं होता जब तक बॉस ज़िंदा हो। इसका मतलब डंजन बॉस इसी गुफ़ा के अंदर है!"
    },
    {
        "page": 37, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft", "use_crop": "page_037_clean.png",
        "text_sub": "Sabhi 17 hunters us andhere ke kinare khade hokar lalach aur darr mein doob gaye.",
        "text_speak": "सभी सत्रह हंटर्स उस अंधेरे के किनारे खड़े होकर लालच और डर में डूब गए।"
    },
    {
        "page": 38, "speaker": "song", "emotion": "serious", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
        "text_sub": "Gate abhi bhi khula hai, matlab Boss andar intezaar kar raha hai.",
        "text_speak": "गेट अभी भी खुला है, मतलब बॉस अंदर इंतज़ार कर रहा है।"
    },
    {
        "page": 39, "speaker": "song", "emotion": "serious", "camera": "slow_pull", "music": "curious_ambient", "sfx": "ambient_soft",
        "text_sub": "Niyam ke mutabiq hume Guild ko khabar karni chahiye thi, lekin...",
        "text_speak": "नियम के मुताबिक़ हमें गिल्ड को ख़बर करनी चाहिए थी, लेकिन..."
    },
    {
        "page": 40, "speaker": "song", "emotion": "serious", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
        "text_sub": "Agar doosre high-rank hunters pehle aa gaye, toh hamara saara munafa chhin jayega!",
        "text_speak": "अगर दूसरे हाई-रैंक हंटर्स पहले आ गए, तो हमारा सारा मुनाफ़ा छिन जाएगा!"
    },
    {
        "page": 41, "speaker": "song", "emotion": "dramatic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "ambient_soft",
        "text_sub": "Isliye main chahta hoon... ki hum sab milkar is Boss ko khatam karein aur saari daulat le lein!",
        "text_speak": "इसलिए मैं चाहता हूँ... कि हम सब मिलकर इस बॉस को ख़त्म करें और सारी दौलत ले लें!"
    },

    # [ACT 7: THE TIE-BREAK VOTE]
    {
        "page": 42, "speaker": "song", "emotion": "serious", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
        "text_sub": "Chunki ye khatarnak ho sakta hai... hum 17 log aapas mein vote karenge!",
        "text_speak": "चूंकि ये ख़तरनाक हो सकता है... हम सत्रह लोग आपस में वोट करेंगे!"
    },
    {
        "page": 43, "speaker": "song", "emotion": "serious", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
        "text_sub": "Aur vote ke natije ke baad koi shikayat nahi karega!",
        "text_speak": "और वोट के नतीजे के बाद कोई शिकायत नहीं करेगा!"
    },
    {
        "page": 44, "speaker": "hunter", "emotion": "excited", "camera": "sudden_zoom", "music": "light_warm", "sfx": "ambient_soft",
        "text_sub": "Lalach mein hunters chillaye: Hum ladenge! Hum andar jayenge!",
        "text_speak": "लालच में हंटर्स चिल्लाए: हम लड़ेंगे! हम अंदर जाएँगे!"
    },
    {
        "page": 45, "speaker": "juhee", "emotion": "fearful", "camera": "slow_pull", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Lekin kuch dare hue hunters bole: Nahi... aur Ju-Hee ne haath utha kar kaha: Mujhe nahi jana!",
        "text_speak": "लेकिन कुछ डरे हुए हंटर्स बोले: नहीं... और जू-ही ने हाथ उठा कर कहा: मुझे नहीं जाना!"
    },
    {
        "page": 46, "speaker": "song", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "shock_sting",
        "text_sub": "Mr. Song ne gina... 8 log bol rahe hain JAO, aur 8 log bol rahe hain MAT JAO! 8 aur 8 ka barabar tie!",
        "text_speak": "मिस्टर सोंग ने गिना... आठ लोग बोल रहे हैं जाओ, और आठ लोग बोल रहे हैं मत जाओ! आठ और आठ का बराबर टाई!"
    },
    {
        "page": 47, "speaker": "song", "emotion": "dramatic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Mr. Song mud gaye: Sung Jin-Woo... tumhara kya kehna hai?",
        "text_speak": "मिस्टर सोंग मुड़ गए: सुंग जिन-वू... तुम्हारा क्या कहना है?"
    },
    {
        "page": 48, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "17 logon ki zindagi aur maut ka aakhri faisla... Sung Jin-Woo ke ek akele vote par aa ruka tha!",
        "text_speak": "सत्रह लोगों की ज़िंदगी और मौत का आख़िरी फ़ैसला... सुंग जिन-वू के एक अकेले वोट पर आ रुका था!"
    },

    # [ACT 8: JIN-WOO'S DECISION & CLIFFHANGER]
    {
        "page": 49, "speaker": "jinwoo", "emotion": "desperate", "camera": "slow_push", "music": "sad_piano", "sfx": "heartbeat_low",
        "text_sub": "Jin-Woo ne mutthi kas li: Mere paas bilkul paise nahi hain... behen ko college bhejna hai...",
        "text_speak": "जिन-वू ने मुट्ठी कस ली: मेरे पास बिल्कुल पैसे नहीं हैं... बहन को कॉलेज भेजना है..."
    },
    {
        "page": 50, "speaker": "jinwoo", "emotion": "sad", "camera": "slow_pull", "music": "sad_piano", "sfx": "heartbeat_low",
        "text_sub": "Aur meri beemar maa... jo salon se aspatal mein behosh padi hain...",
        "text_speak": "और मेरी बीमार माँ... जो सालों से हॉस्पिटल में बेहोश पड़ी हैं..."
    },
    {
        "page": 51, "speaker": "jinwoo", "emotion": "desperate", "camera": "slow_push", "music": "sad_piano", "sfx": "heartbeat_low",
        "text_sub": "Mujhe apne parivaar ke liye jeena hoga... chahe mujhe maut ke muh mein hi kyun na koodna pade!",
        "text_speak": "मुझे अपने परिवार के लिए जीना होगा... चाहे मुझे मौत के मुंह में ही क्यों ना कूदना पड़े!"
    },
    {
        "page": 52, "speaker": "jinwoo", "emotion": "angry", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Jin-Woo dahaada: Main jaa raha hoon! Main vote deta hoon andar jaane ka!",
        "text_speak": "जिन-वू दहाड़ा: मैं जा रहा हूँ! मैं वोट देता हूँ अंदर जाने का!"
    },
    {
        "page": 53, "speaker": "jinwoo", "emotion": "hopeful", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Bas ek aakhri baar... chalte hain aur is Boss ko khatam karte hain!",
        "text_speak": "बस एक आख़िरी बार... चलते हैं और इस बॉस को ख़त्म करते हैं!"
    },
    {
        "page": 54, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_pull", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Lekin Jin-Woo nahi jaanta tha... ki uska ye ek vote sabhi ko Cartenon Temple ki maut ke pinjre mein band karne wala hai! Agle Chapter 3 ke liye LIKE aur SUBSCRIBE zaroor karein!",
        "text_speak": "लेकिन जिन-वू नहीं जानता था... कि उसका ये एक वोट सभी को कार्टेनन टेम्पल की मौत के पिंजरे में बंद करने वाला है! अगले चैप्टर तीन के लिए लाइक और सब्सक्राइब ज़रूर करें!"
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# CORE GENERATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

async def generate_speech(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    """Generate human-like speech via Edge-TTS at 1.5x speed with correct pronunciation."""
    import edge_tts

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    tmp_mp3 = out_wav.with_suffix(".mp3")

    cfg = SPEAKER_CONFIG.get(speaker, SPEAKER_CONFIG["narrator"])
    base_voice = cfg["voice"]
    base_rate = int(cfg["rate"].replace("%", "").replace("+", ""))
    base_pitch = int(cfg["pitch"].replace("Hz", "").replace("+", ""))

    em = EMOTION_VOICE_MOD.get(emotion, {"rate_mod": 0, "pitch_mod": 0})
    final_rate = f"{base_rate + em['rate_mod']:+d}%"
    final_pitch = f"{base_pitch + em['pitch_mod']:+d}Hz"

    for attempt in range(1, 4):
        try:
            comm = edge_tts.Communicate(text_speak, base_voice, rate=final_rate, pitch=final_pitch)
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
    """Procedural music score tailored to scene mood."""
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "dark_drone":      f"aevalsrc='0.22*sin(2*PI*55*t)+0.15*sin(2*PI*82.4*t)+0.10*sin(2*PI*110*t)+0.05*sin(2*PI*164.8*t)':d={d}:s=44100,volume=0.35",
        "dark_intense":    f"aevalsrc='0.28*sin(2*PI*45*t)+0.20*sin(2*PI*65*t)+0.12*sin(2*PI*130*t)+0.08*(random(0)-0.5)':d={d}:s=44100,volume=0.38",
        "epic_adventure":  f"aevalsrc='0.20*sin(2*PI*130.8*t)+0.18*sin(2*PI*164.8*t)+0.15*sin(2*PI*196*t)+0.12*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.35",
        "city_ambient":    f"aevalsrc='0.15*sin(2*PI*220*t)+0.12*sin(2*PI*277*t)+0.10*sin(2*PI*330*t)':d={d}:s=44100,volume=0.25",
        "sad_piano":       f"aevalsrc='0.20*sin(2*PI*174.6*t)+0.15*sin(2*PI*220*t)+0.12*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.30",
        "light_warm":      f"aevalsrc='0.18*sin(2*PI*261.6*t)+0.14*sin(2*PI*329.6*t)+0.10*sin(2*PI*392*t)':d={d}:s=44100,volume=0.28",
        "curious_ambient": f"aevalsrc='0.16*sin(2*PI*196*t)+0.12*sin(2*PI*246.9*t)+0.10*sin(2*PI*293.7*t)':d={d}:s=44100,volume=0.28",
        "soft_strings":    f"aevalsrc='0.18*sin(2*PI*220*t)+0.15*sin(2*PI*261.6*t)+0.12*sin(2*PI*329.6*t)':d={d}:s=44100,volume=0.30",
        "mystery_ambient": f"aevalsrc='0.18*sin(2*PI*73.4*t)+0.14*sin(2*PI*110*t)+0.10*sin(2*PI*146.8*t)':d={d}:s=44100,volume=0.32",
    }
    flt = filters.get(music_type, filters["city_ambient"])

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)


def generate_sfx(sfx_type: str, duration: float, out_wav: Path):
    """Procedural sound effect synthesis."""
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "heartbeat_low":   f"aevalsrc='0.35*sin(2*PI*45*t)*pow(max(0,sin(2*PI*1.4*t)),10)':d={d}:s=44100",
        "portal_hum":      f"aevalsrc='0.25*sin(2*PI*60*t)+0.15*sin(2*PI*(60+8*sin(2*PI*0.5*t))*t)':d={d}:s=44100",
        "whoosh_energy":   f"aevalsrc='0.3*exp(-4*t)*sin(2*PI*(320-220*t)*t)':d={d}:s=44100",
        "fireball_whoosh": f"aevalsrc='0.35*exp(-3*t)*sin(2*PI*(180+60*sin(2*PI*10*t))*t)+0.15*(random(0)-0.5)':d={d}:s=44100",
        "sword_slash":     f"aevalsrc='0.38*exp(-7*t)*sin(2*PI*(800-600*t)*t)+0.2*exp(-9*t)*(random(0)-0.5)':d={d}:s=44100",
        "magic_heal":      f"aevalsrc='0.25*exp(-2*t)*sin(2*PI*523.25*t)+0.20*exp(-2.5*t)*sin(2*PI*659.25*t)+0.15*exp(-3*t)*sin(2*PI*783.99*t)':d={d}:s=44100",
        "shock_sting":     f"aevalsrc='0.35*exp(-3*t)*sin(2*PI*520*t)+0.25*exp(-3*t)*sin(2*PI*554*t)':d={d}:s=44100",
        "braam_impact":    f"aevalsrc='0.4*exp(-1.5*t)*sin(2*PI*40*t)+0.25*exp(-2*t)*sin(2*PI*80*t)':d={d}:s=44100",
        "ambient_soft":    f"aevalsrc='0.06*sin(2*PI*120*t)':d={d}:s=44100",
    }
    flt = filters.get(sfx_type, filters["ambient_soft"])

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)


def mix_audio(voice_wav: Path, music_wav: Path, sfx_wav: Path, duration: float, out_aac: Path):
    """Mix 3 audio channels with voice priority ducking."""
    ff = ffmpeg_bin()
    out_aac.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filter_complex = (
        "[0:a]volume=1.40,apad[v];"
        "[1:a]volume=0.20[m];"
        "[2:a]volume=0.28[s];"
        "[v][m][s]amix=inputs=3:duration=longest:dropout_transition=1,"
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


def render_scene_video(img_path: Path, duration: float, camera: str, out_mp4: Path):
    """
    Render 1080p widescreen video from vertical manga page:
      - Background: blurred, darkened, zoomed 1920x1080 canvas
      - Foreground: crisp centered manga page
      - Fast Ken Burns dynamic movement (matched to 1.5x pace)
    """
    ff = ffmpeg_bin()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    dur = round(duration, 3)
    w, h = 1920, 1080

    bg_flt = f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=25:5,eq=brightness=-0.18:contrast=0.95[bg]"

    if camera == "tilt_down":
        fg_flt = (
            f"[0:v]scale=w=-1:h='max(1040, 2337*0.6)':eval=init[fg_raw];"
            f"[fg_raw]crop=w=iw:h=1040:x=0:y='(ih-1040)*t/{dur:.2f}'[fg]"
        )
    else:
        fg_flt = f"[0:v]scale=-1:1040[fg]"

    overlay_flt = "[bg][fg]overlay=(W-w)/2:(H-h)/2[comp]"

    if camera == "slow_push":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.06*t/{dur:.2f})/2)':h='2*floor({h}*(1.01+0.06*t/{dur:.2f})/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p"
        )
    elif camera == "slow_pull":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.07-0.06*t/{dur:.2f})/2)':h='2*floor({h}*(1.07-0.06*t/{dur:.2f})/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p"
        )
    elif camera == "sudden_zoom":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.10*pow(t/{dur:.2f},1.8))/2)':h='2*floor({h}*(1.01+0.10*pow(t/{dur:.2f},1.8))/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p"
        )
    elif camera == "handheld_shake":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*1.04/2)':h='2*floor({h}*1.04/2)',"
            f"crop={w}:{h}:'(in_w-{w})/2+7*sin(16*t)':'(in_h-{h})/2+7*cos(13*t)',format=yuv420p"
        )
    else:
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.04*t/{dur:.2f})/2)':h='2*floor({h}*(1.01+0.04*t/{dur:.2f})/2)':eval=frame,"
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


def generate_subtitles_ass(scenes_meta: list[dict], out_ass: Path):
    """Generate high-contrast, styled ASS subtitles with character highlights."""
    out_ass.parent.mkdir(parents=True, exist_ok=True)

    header = """[Script Info]
Title: Solo Leveling Ch 2 Hindi Recap
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,50,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3.5,1.5,2,40,40,65,1
Style: JinWoo,Arial,50,&H0080FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3.5,1.5,2,40,40,65,1
Style: JuHee,Arial,50,&H00FFB0FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3.5,1.5,2,40,40,65,1
Style: Song,Arial,50,&H00FFAA00,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3.5,1.5,2,40,40,65,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def to_ass_time(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        cs = int((sec - int(sec)) * 100)
        return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

    lines = [header]
    current_time = 0.0
    for sm in scenes_meta:
        dur = sm["duration"]
        speaker = sm.get("speaker", "narrator")
        if speaker == "jinwoo":
            style = "JinWoo"
        elif speaker == "juhee":
            style = "JuHee"
        elif speaker == "song":
            style = "Song"
        else:
            style = "Default"

        t_start = to_ass_time(current_time + 0.05)
        t_end = to_ass_time(current_time + dur - 0.05)
        text = sm["text_sub"]
        lines.append(f"Dialogue: 0,{t_start},{t_end},{style},,0,0,0,,{text}\n")
        current_time += dur

    with open(out_ass, "w", encoding="utf-8") as f:
        f.writelines(lines)


async def main():
    out_dir = ROOT / "output" / "solo_leveling_ch2"
    pages_dir = out_dir / "pages"
    cp_dir = out_dir / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("⚔️ SOLO LEVELING CHAPTER 2 — FAST 1.5x CINEMATIC HINDI RECAP")
    print(f"📁 Output Directory: {out_dir}")
    print("⚡ Pacing: 1.5x Speed + Perfected English/Hindi Pronunciation")
    print("=" * 70)

    # Ensure cropped ad images exist
    p13_clean = pages_dir / "page_013_clean.png"
    if not p13_clean.exists():
        im = Image.open(pages_dir / "page_013.png")
        w, h = im.size
        im.crop((0, 0, w, int(h * 0.58))).save(str(p13_clean))

    p37_clean = pages_dir / "page_037_clean.png"
    if not p37_clean.exists():
        im = Image.open(pages_dir / "page_037.png")
        w, h = im.size
        im.crop((0, 0, w, int(h * 0.52))).save(str(p37_clean))

    scenes_meta = []
    total_scenes = len(SCENES_DATA)

    for i, item in enumerate(SCENES_DATA, start=1):
        pid = item["page"]
        speaker = item["speaker"]
        emotion = item["emotion"]
        camera = item["camera"]
        music = item["music"]
        sfx = item["sfx"]
        text_sub = item["text_sub"]
        text_speak = item["text_speak"]
        crop_override = item.get("use_crop", None)

        if crop_override:
            img_file = pages_dir / crop_override
        else:
            img_file = pages_dir / f"page_{pid:03d}.png"

        scene_mp4 = cp_dir / f"scene_{i:03d}_p{pid:03d}.mp4"

        # Checkpoint check
        if scene_mp4.exists() and scene_mp4.stat().st_size > 50000:
            info = probe(scene_mp4)
            dur = float(info["format"]["duration"])
            print(f"[{i:02d}/{total_scenes}] ✓ Cached scene {i:02d} (page {pid:03d}, {dur:.1f}s)")
            scenes_meta.append({
                "index": i, "page": pid, "duration": dur,
                "text_sub": text_sub, "speaker": speaker, "mp4": scene_mp4
            })
            continue

        print(f"\n[{i:02d}/{total_scenes}] 🎬 Processing Scene #{i:02d} (Page {pid:03d}, Speaker={speaker}, Emotion={emotion})...")

        # 1. Voice (1.5x speed with perfected pronunciation)
        voice_wav = cp_dir / f"voice_{i:03d}.wav"
        if not voice_wav.exists() or voice_wav.stat().st_size < 1000:
            await generate_speech(text_speak, speaker, emotion, voice_wav)

        vinfo = probe(voice_wav)
        vdur = float(vinfo["format"]["duration"])
        # Fast pacing: voice duration + 0.25s breathing room (snappy YouTube anime recap cut)
        scene_dur = max(1.8, round(vdur + 0.25, 2))

        # 2. Music
        music_wav = cp_dir / f"music_{i:03d}.wav"
        if not music_wav.exists():
            generate_music(music, scene_dur, music_wav)

        # 3. SFX
        sfx_wav = cp_dir / f"sfx_{i:03d}.wav"
        if not sfx_wav.exists():
            generate_sfx(sfx, scene_dur, sfx_wav)

        # 4. Mix Audio
        mixed_aac = cp_dir / f"mixed_{i:03d}.aac"
        if not mixed_aac.exists():
            mix_audio(voice_wav, music_wav, sfx_wav, scene_dur, mixed_aac)

        # 5. Render Video
        raw_vid = cp_dir / f"raw_{i:03d}.mp4"
        if not raw_vid.exists():
            render_scene_video(img_file, scene_dur, camera, raw_vid)

        # 6. Join audio and video
        ff = ffmpeg_bin()
        subprocess.run([
            ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(raw_vid),
            "-i", str(mixed_aac),
            "-c:v", "copy", "-c:a", "copy", "-shortest",
            str(scene_mp4)
        ], check=True)

        if raw_vid.exists():
            raw_vid.unlink()

        print(f"  ✅ Scene {i:02d} rendered ({scene_dur:.1f}s)")
        scenes_meta.append({
            "index": i, "page": pid, "duration": scene_dur,
            "text_sub": text_sub, "speaker": speaker, "mp4": scene_mp4
        })

    # Subtitles
    print("\n📝 Generating ASS Subtitles...")
    sub_ass = out_dir / "subtitles.ass"
    generate_subtitles_ass(scenes_meta, sub_ass)

    # Concat
    print("\n🔗 Concatenating scenes into feature video...")
    unsubbed_mp4 = out_dir / "unsubbed.mp4"
    lst_file = out_dir / "concat_list.txt"
    with open(lst_file, "w", encoding="utf-8") as f:
        for sm in scenes_meta:
            f.write(f"file '{sm['mp4'].resolve().as_posix()}'\n")

    ff = ffmpeg_bin()
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(lst_file),
        "-c", "copy",
        str(unsubbed_mp4)
    ], check=True)

    # Subtitle burn
    print("\n🔤 Burning Subtitles into Final 1080p MP4...")
    final_mp4 = out_dir / "final.mp4"
    ass_escaped = str(sub_ass).replace("\\", "/").replace(":", "\\:")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(unsubbed_mp4),
        "-vf", f"ass='{ass_escaped}'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "copy",
        str(final_mp4)
    ], check=True)

    # Dramatic YouTube Thumbnail
    print("\n🖼️ Creating YouTube Cover Thumbnail from Page 34 (Colossal Temple Entrance)...")
    cover_jpg = out_dir / "cover.jpg"
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(pages_dir / "page_034.png"),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=contrast=1.20:saturation=1.25:brightness=-0.05",
        str(cover_jpg)
    ], check=True)

    info = probe(final_mp4)
    dur = float(info["format"]["duration"])
    size_mb = final_mp4.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 70)
    print("🎉 SOLO LEVELING CHAPTER 2 VIDEO GENERATION COMPLETE!")
    print(f"🎬 Video: {final_mp4}")
    print(f"⏱️ Duration: {dur:.1f}s ({dur/60:.2f} minutes)")
    print(f"📦 Size: {size_mb:.2f} MB")
    print(f"🖼️ Thumbnail: {cover_jpg}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
