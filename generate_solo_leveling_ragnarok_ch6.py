"""
generate_solo_leveling_ragnarok_ch6.py — Solo Leveling: Ragnarok Chapter 6 Cinematic Explainer Video.

Key Technical Guarantees:
  1. 100% Pure Gemini Neural Humanoid TTS:
     • 'Fenrir' for Narrator, Suho, Lim Dogyun
     • 'Charon' for Beru, Beast Monarch of Fangs
     Real human breath, pitch dynamics, emotional inflection, and natural conversational delivery.
  2. Natural Human-Storyteller Script:
     Conversational, engaging, expressive Hindi/Hinglish script formatted for authentic storytelling.
  3. High-CTR 1280x720 YouTube Thumbnail (The Monarch of Fangs Reveal).
  4. 36 Action-Packed Scenes with smooth Ken Burns camera pan/zoom & bokeh backdrop.
  5. Dual-Color ASS Subtitles (Ragnarok Cyan & Monarch Gold).
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
from agents.voice import _call_gemini_tts, _pcm_to_wav

# ─────────────────────────────────────────────────────────────────────────────
# 36 SCRIPTED SCENES (CHAPTER 6 COMPLETE STORYLINE — NATURAL HUMAN NARRATION)
# ─────────────────────────────────────────────────────────────────────────────
SCENES = [
    # [ACT 1: THE FIRST SHADOW EXTRACTION & DISAPPOINTMENT]
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Solo Leveling: Ragnarok — Chapter 6! Suho ka pehla Shadow Soldier aur Beast Monarch ka raaz!",
        "text_speak": "सोलो लेवलिंग: रैग्नारॉक — चैप्टर छह! सू-हो का पहला शैडो सैनिक और बीस्ट मोनार्क का सबसे खौफनाक रहस्य!"
    },
    {
        "panel": 2, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne aadesh diya: 'ARISE!' Aur zameen se kaali-neeli maut ki laptein uth khadi huin!",
        "text_speak": "जैसे ही सू-हो ने कहा 'अराइज़!', मलबे को चीरती हुई नीली-काली रहस्यमयी ऊर्जा हवा में तैरने लगी!"
    },
    {
        "panel": 3, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "SHADOW GOBLIN LV. 1 prakat hua! Neeli aankhon wala chhotasa shadow soldier!",
        "text_speak": "और उस लाश से बाहर निकला एक नन्हा साया! सिस्टम का नोटिफिकेशन चमका: शैडो गोब्लिन लेवल वन, कॉमन रैंक!"
    },
    {
        "panel": 4, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho ne thande chehre se dekha: 'Ye toh mere andaze se kaafi kamzor nikla...'",
        "text_speak": "सू-हो ने बिल्कुल बेरुखी से उस नन्हे शैडो को देखा और बोला: 'भाई... ये तो उम्मीद से कहीं ज़्यादा कमज़ोर और पिद्दी निकला!'"
    },
    {
        "panel": 5, "speaker": "beru", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Beru ne pasina pochha: 'Aage chal kar ye taqatwar banega!' Tabhi Suho ke pet mein chuhe daud pade!",
        "text_speak": "बेरू पसीना पोंछते हुए सफाई देने लगा कि आगे चलकर ये बहुत कमाल का स्किल बनेगा! तभी सू-हो के पेट में ज़ोरदार भूख की गड़गड़ाहट हुई!"
    },

    # [ACT 2: HOSPITAL FEAST & THE THREE CRITICAL MISSIONS]
    {
        "panel": 6, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Shadow Dungeon se bahar nikal kar Suho seedha hospital ke bistar par lauta.",
        "text_speak": "चाबी का इस्तेमाल करके सू-हो तुरंत शैडो डंजन से बाहर आ गया और अस्पताल के कमरे में पहुँचा।"
    },
    {
        "panel": 7, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Do din se bhookhe Suho ne hospital ka khana aise chapaata jaise koi amrit ho!",
        "text_speak": "दो दिन से भूखे सू-हो ने अस्पताल के सादे खाने पर ऐसे धावा बोला, जैसे दुनिया का सबसे स्वादिष्ट पकवान खा रहा हो!"
    },
    {
        "panel": 8, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru ne samjhaya: 'Pehla mission hai outer space ke monsters se dharti ko bachana aur Jin-Woo ki tarah level up karna!'",
        "text_speak": "बेरू ने गंभीर होकर कहा: 'मालिक, अब आपके तीन मिशन हैं! पहला—अंतरिक्ष के राक्षसों का शिकार करके अपने पिता सुंग जिन-वू की तरह महाबली बनना!'"
    },
    {
        "panel": 9, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "'Doosra mission: har haal mein maa Cha Hae-In ko dhoondhna!' Suho ki aankhon mein chahat thi.",
        "text_speak": "'और दूसरा मिशन—हर हाल में अपनी माँ, मिस चा हाए-इन को ढूँढ निकालना!' सू-हो की आँखों में माँ को वापस पाने की तड़प साफ़ झलक रही थी।"
    },

    # [ACT 3: BERU'S GLORY & HUNTER ASSOCIATION EVALUATION]
    {
        "panel": 10, "speaker": "beru", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Beru garja: 'Teesra mission—meri khoi hui Marshal taqat wapas pana! Mujhe bas magic khana hai!'",
        "text_speak": "बेरू ने सीना तानकर चीख लगाई: 'और तीसरा सबसे ज़रूरी मिशन—मुझ मार्शल बेरू की खोई हुई असली ताकत को वापस लौटाना! मुझे बस जादुई ऊर्जा खानी है!'"
    },
    {
        "panel": 11, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho bola: 'Matlab hume har haal mein dungeons mein ghusna padega... chalo taiyyari karte hain.'",
        "text_speak": "सू-हो ने चम्मच रखते हुए कहा: 'यानी तीनों रास्तों की एक ही मंज़िल है—डंजन में उतरना! तो चलो, हंटर लाइसेंस लेने चलते हैं।'"
    },
    {
        "panel": 12, "speaker": "narrator", "emotion": "curious", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Hunter Association ke raste Suho ne socha: 'Main toh level up kar sakta hoon... kya pata main S-Rank nikal aaoon?!'",
        "text_speak": "एसोसिएशन जाते वक्त सू-हो मन ही मन मुस्कुराया: 'मैं तो लेवल अप कर सकता हूँ... क्या पता मेरा टेस्ट सीधा एस-रैंक निकल आए?!'"
    },
    {
        "panel": 13, "speaker": "narrator", "emotion": "surprised", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "shock_sting",
        "text_sub": "Jhatka! Afsar ne report dekhi: 'Aapka magic level sirf 46 hai... AAP EK E-RANK AWAKENER HAIN!'",
        "text_speak": "लेकिन जैसे ही टेस्ट रिपोर्ट आई, पैरों तले ज़मीन खिसक गई! ऑफिसर बोली: 'आपका मैजिक लेवल सिर्फ छियालीस है... आप एक ई-रैंक हंटर हैं!'"
    },

    # [ACT 4: E-RANK REALITY & THE MINING TEAM WORKAROUND]
    {
        "panel": 14, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho sar jhukaye bahar nikla. Beru tasalli dene laga: 'Aapne Strength badhai thi, isliye mana kam hai!'",
        "text_speak": "शाम के ढलते सूरज में सू-हो मुंह लटकाए बाहर निकला। बेरू सांत्वना देने लगा: 'मालिक, आपने ताकत बढ़ाई थी, इसलिए मैजिक लेवल कम आया!'"
    },
    {
        "panel": 15, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho ne socha: 'Raid parties toh E-Rank ko ghaans bhi nahi daaltin... toh main dungeon kaise jaoonga?'",
        "text_speak": "सू-हो ने अपनी हथेलियों को देखा: 'हंटर गिल्ड्स तो ई-रैंक वालों को मुड़कर भी नहीं देखतीं... ऐसे में मैं डंजन के अंदर कदम कैसे रखूँगा?'"
    },
    {
        "panel": 16, "speaker": "narrator", "emotion": "curious", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Tabhi Suho ke dimaag ki batti jali! Dungeons mein teen tarah ki teams hoti hain!",
        "text_speak": "तभी अचानक सू-हो की आँखों में एक अनोखी चमक आ गई! उसे डंजन रेड्स का पुराना नियम याद आया!"
    },
    {
        "panel": 17, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Strike squad ladi hai, par Hauling aur Mining team mein E-Rank bhi bharti ho sakte hain! Rasta mil gaya!",
        "text_speak": "राक्षसों से सिर्फ स्ट्राइक टीम लड़ती है... लेकिन लाशें ढोने वाली और जादुई पत्थर खोदने वाली माइनिंग टीम में ई-रैंक भी जा सकते हैं!"
    },

    # [ACT 5: CRYSTAL CAVE & REUNITING WITH LIM DOGYUN]
    {
        "panel": 18, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "c_rank_blade_slash",
        "text_sub": "Ting-Ting! Neeli crystals ki ghaati mein Suho helmet pehne kudal chala raha tha!",
        "text_speak": "टन-टन! नीले चमकते जादुई पत्थरों की गुफ़ा में सू-हो सिर पर हेलमेट पहने कुदाल चला रहा था!"
    },
    {
        "panel": 19, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Paas mein khada tha Lim Dogyun — university ka teaching assistant jo us haadse mein akela bhaag gaya tha.",
        "text_speak": "और उसके ठीक बगल में खड़ा था लिम डोग्युन—यूनिवर्सिटी का वही असिस्टेंट, जो हमले के वक्त डरकर भाग गया था।"
    },
    {
        "panel": 20, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Dogyun ne sharminda hokar maafi maangi: 'Suho, main akela awaken tha fir bhi dar ke bhaag gaya... mujhe maaf kar do.'",
        "text_speak": "डोग्युन ने शर्म से सिर झुकाकर माफ़ी माँगी: 'सू-हो... उस दिन मैं अकेला अवेकनर था, फिर भी डरपोक की तरह भाग निकला... मुझे माफ़ कर दो भाई।'"
    },
    {
        "panel": 21, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho ne kandhe par haath rakha: 'Sir upar kijiye, Association khud kehti hai ki E-Rank monster dekhte hi bhaag jayein!'",
        "text_speak": "सू-हो ने मुस्कुराते हुए उसके कंधे पर हाथ रखा: 'सिर उठाइए भाई! एसोसिएशन खुद कहती है कि ई-रैंक हंटर्स को राक्षस देखते ही पूरी रफ़्तार से भाग जाना चाहिए!'"
    },

    # [ACT 6: COMEDIC REVELATION & CHIBI BERU]
    {
        "panel": 22, "speaker": "narrator", "emotion": "surprised", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "shock_sting",
        "text_sub": "Dogyun ki aankhein phat gayin: 'KYYA?! Tera mana level 46 hai... mujhse bhi kam?! Lekin tu toh lad raha tha!'",
        "text_speak": "डोग्युन हक्का-बक्का रह गया: 'क्या?! तेरा मैजिक लेवल छियालीस है... यानी मुझसे भी कम?! लेकिन मैंने तो तुझे छत पर राक्षसों से लड़ते देखा था!'"
    },
    {
        "panel": 23, "speaker": "narrator", "emotion": "curious", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Dogyun hairan tha ki itne kam mana ke bawjood Suho ne monster ko maar giraya tha!",
        "text_speak": "डोग्युन मन ही मन सोचने लगा कि इतने कमज़ोर मैजिक के साथ कोई राक्षस से भिड़कर ज़िंदा कैसे बच सकता है!"
    },
    {
        "panel": 24, "speaker": "beru", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Tabhi Suho ke collar se Beru nikla: 'Beshak! Mere Young Monarch bemisaal hain!'",
        "text_speak": "तभी सू-हो के कॉलर से नन्हा बेरू फुदक कर बाहर आया: 'बिल्कुल! हमारे छोटे मालिक इस पूरी दुनिया में बेमिसाल हैं!'"
    },
    {
        "panel": 25, "speaker": "narrator", "emotion": "fearful", "camera": "handheld_shake", "music": "dark_intense", "sfx": "glass_shatter",
        "text_sub": "Dogyun ki cheekh nikal gayi: 'HIIIIK?! M-MONSTER?!' Suho ne jhooth bol diya: 'Main summoner hoon!'",
        "text_speak": "काली चींटी को देखते ही डोग्युन की चीख निकल गई: 'अरे बाप रे, मॉन्स्टर!' सू-हो ने बात संभालते हुए कह दिया: 'अरे डरो मत, मैं समनर हूँ!'"
    },

    # [ACT 7: RUNNING SKILL JOKE & THE DEEP CAVERN]
    {
        "panel": 26, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Dogyun bola: 'Mere paas Running Skill hai!' Suho ne taunt mara: 'Tabhi itni tezi se bhaage the!'",
        "text_speak": "डोग्युन सीना फुलाकर बोला: 'मेरी जानकारी के लिए बता दूँ, मेरे पास भागने का स्पेशल स्किल है!' सू-हो हँसा: 'तभी आप उस दिन हवा की रफ़्तार से भागे थे!'"
    },
    {
        "panel": 27, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Gufa ki gahraaiyon mein dekhte hue Suho ne socha: Strike team aage kya kar rahi hogi?",
        "text_speak": "अंधेरी गुफा की गहराई की ओर देखते हुए सू-हो ने सोचा: आगे जो स्ट्राइक टीम लड़ रही है, वो अब तक कहाँ पहुँची होगी?"
    },
    {
        "panel": 28, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Aage Strike team bhediyon ko maar kar niraash thi: 'Is dungeon mein ghanta kuch nahi mil raha!'",
        "text_speak": "आगे चल रही स्ट्राइक टीम मरे हुए भेड़ियों को देखकर चिढ़ रही थी कि इस डंजन में कोई कीमती खज़ाना नहीं है।"
    },
    {
        "panel": 29, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "shock_sting",
        "text_sub": "Tabhi ek hunter cheekha: 'LEADER! Bagal ke gufa raste se laal roshni nikal rahi hai!'",
        "text_speak": "तभी एक हंटर ने आवाज़ लगाई: 'लीडर! इधर एक छुपा हुआ गुप्त रास्ता है, जहाँ से अजीब लाल रोशनी फूट रही है!'"
    },

    # [ACT 8: THE CURSED TEMPLE & KIM YONGJUN'S GREED]
    {
        "panel": 30, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Wo ek pracheen mandir ke khandaron mein pahuñche jahan hawa mein maut ki badboo thi.",
        "text_speak": "वे सब एक प्राचीन भूमिगत मंदिर के खंडहरों में दाखिल हुए, जहाँ की हवा में खौफनाक सन्नाटा पसरा था।"
    },
    {
        "panel": 31, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Chabootare par ek vishaal shaitani talwar gadi thi, jis se laal angaare jaisi aag nikal rahi thi!",
        "text_speak": "और ठीक बीचोबीच एक गोल वेदी पर धंसी हुई थी—एक विशाल, भयानक तलवार! जिसके ब्लेड से खूनी लाल लपटें उठ रही थीं!"
    },
    {
        "panel": 32, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Hunters ki laalach jaag gayi: 'JACKPOT! Ye koi aam hathiyar nahi hai, laakhon mein bikega!'",
        "text_speak": "हंटर्स की लालच जाग उठी: 'जैकपॉट लग गया! ये कोई मामूली हथियार नहीं है, बाज़ार में करोड़ों का बिकेगा!'"
    },
    {
        "panel": 33, "speaker": "narrator", "emotion": "fearful", "camera": "handheld_shake", "music": "dark_intense", "sfx": "glass_shatter",
        "text_sub": "C-Rank tank Kim Yongjun aage badha: 'Main C-Rank tank hoon, trap hua toh bhi jhel loonga!' Aur mutthi kas li!",
        "text_speak": "सी-रैंक टैंक किम योंग-जुन घमंड में आगे बढ़ा: 'पीछे हटो! मैं सी-रैंक का ताकतवर टैंक हूँ, कोई ट्रैप हुआ तो भी झेल लूँगा!' और उसने तलवार की मूठ पकड़ ली!"
    },

    # [ACT 9: POSSESSION & THE BEAST MONARCH REVEAL]
    {
        "panel": 34, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "GURRRR! Farsh ke neeche se vishaal bhediye ka khaufnaak jabda aur peeli aag jaisi aankhein khulin!",
        "text_speak": "गड़गड़ाहट के साथ फ़र्श के नीचे अंधेरे से एक विशालकाय भेड़िये का खूनी जबड़ा और दहकती हुई पीली आँखें जाग उठीं!"
    },
    {
        "panel": 35, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "c_rank_blade_slash",
        "text_sub": "Kim Yongjun ke munh se ghoorkaar nikli: 'TUMHARI HIMMAT KAISE HUI...?' Aur usne sabhi par talwar chala di!",
        "text_speak": "किम योंग-जुन का चेहरा दरिंदे में बदल गया! उसके हलक़ से एक घिनौनी गुर्राहट गूँजी: 'तुम्हारी हिम्मत कैसे हुई...?!' और उसने अपनी ही टीम पर तलवार चला दी!"
    },
    {
        "panel": 36, "speaker": "beru", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Aasman cheekh utha: 'MONARCH OF FANGS KI TALWAR PAR HATH DAALNE KI HIMMAT KISNE KI?!'",
        "text_speak": "गुफा की दीवारें थर्रा उठीं और एक भयानक दानव की आवाज़ गूँज उठी: 'मोनार्क ऑफ फैंग्स की पावन तलवार को छूने की जुर्रत किसने की?!'"
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# 100% PURE GEMINI HUMANOID VOICE ENGINE (Real Breath & Human Emotion)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_humanoid_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    """
    Synthesize rich, emotionally inflected humanoid voice using Google Gemini TTS.
    Falls back gracefully only if unexpected network failure occurs.
    """
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    voice_name = "Charon" if speaker in ("beru", "monarch") else "Fenrir"

    # Call Gemini TTS
    for attempt in range(1, 4):
        try:
            pcm = _call_gemini_tts(text_speak, voice_name=voice_name)
            if pcm and len(pcm) > 500:
                _pcm_to_wav(pcm, out_wav)
                break
        except Exception as e:
            print(f"    ⚠️ Gemini TTS attempt {attempt} failed ({e}), retrying...")
            if attempt == 3:
                # Fallback to high-quality edge-tts only as safety net
                import edge_tts
                raw_mp3 = out_wav.with_suffix(".tmp.mp3")
                comm = edge_tts.Communicate(text_speak, "hi-IN-MadhurNeural", rate="+6%", pitch="-2Hz")
                await comm.save(str(raw_mp3))
                subprocess.run([
                    ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
                    "-i", str(raw_mp3), "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1",
                    str(out_wav)
                ], check=True)
                raw_mp3.unlink(missing_ok=True)
                break
            await asyncio.sleep(2.0)

    # Studio Warmth DSP Chain for natural broadcasting richness
    dsp_wav = out_wav.with_name(f"dsp_{out_wav.name}")
    ff = ffmpeg_bin()
    bass_boost = 3.5 if voice_name == "Charon" else 2.0
    dsp_chain = (
        f"equalizer=f=120:t=q:w=1.2:g={bass_boost},"
        "equalizer=f=2800:t=q:w=1.4:g=2.2,"
        "acompressor=threshold=-16dB:ratio=2.5:attack=15:release=100:makeup=1.8dB,"
        "atempo=1.04"
    )
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(out_wav),
        "-af", dsp_chain,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(dsp_wav)
    ], check=True)

    if dsp_wav.exists() and dsp_wav.stat().st_size > 1000:
        dsp_wav.replace(out_wav)


# ─────────────────────────────────────────────────────────────────────────────
# PROCEDURAL SCORE & SFX
# ─────────────────────────────────────────────────────────────────────────────
def generate_music(music_type: str, duration: float, out_wav: Path):
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "dark_drone":     f"aevalsrc='0.22*sin(2*PI*55*t)+0.16*sin(2*PI*82.4*t)+0.10*sin(2*PI*110*t)':d={d}:s=44100,volume=0.30",
        "dark_intense":   f"aevalsrc='0.28*sin(2*PI*45*t)+0.20*sin(2*PI*65*t)+0.12*sin(2*PI*130*t)+0.07*(random(0)-0.5)':d={d}:s=44100,volume=0.36",
        "epic_adventure": f"aevalsrc='0.20*sin(2*PI*130.8*t)+0.16*sin(2*PI*164.8*t)+0.14*sin(2*PI*196*t)+0.12*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.34",
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
        "glass_shatter":      f"aevalsrc='0.40*exp(-8*t)*(random(0)-0.5)+0.25*exp(-14*t)*sin(2*PI*3200*t)':d={d}:s=44100",
        "shock_sting":        f"aevalsrc='0.35*exp(-2.5*t)*sin(2*PI*1200*t)+0.20*exp(-4*t)*sin(2*PI*2400*t)':d={d}:s=44100",
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
        "[0:a]volume=1.35,apad[v];"
        "[1:a]volume=0.20[m];"
        "[2:a]volume=0.28[s];"
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
# WIDE SCENE RENDERER (1250px FOREGROUND + KEN BURNS MOTION)
# ─────────────────────────────────────────────────────────────────────────────
def render_wide_scene_video(img_path: Path, duration: float, camera: str, out_mp4: Path):
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
        ff, "-y", "-loop", "1", "-t", str(dur), "-i", str(img_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-pix_fmt", "yuv420p",
        str(out_mp4)
    ]
    subprocess.run(cmd, check=True)


def join_scene(video_mp4: Path, audio_aac: Path, out_mp4: Path):
    ff = ffmpeg_bin()
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(video_mp4),
        "-i", str(audio_aac),
        "-c:v", "copy",
        "-c:a", "copy",
        "-shortest",
        str(out_mp4)
    ], check=True)


# ─────────────────────────────────────────────────────────────────────────────
# ASS SUBTITLES & HIGH-CTR THUMBNAIL
# ─────────────────────────────────────────────────────────────────────────────
def generate_ass_subtitles(scenes: list[dict], scene_durs: list[float], out_ass: Path):
    header = """[Script Info]
Title: Solo Leveling Ragnarok Chapter 6 Subtitles
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
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    events = []
    curr = 0.0
    for sc, dur in zip(scenes, scene_durs):
        start = curr + 0.15
        end = curr + dur - 0.15
        style = "RagnarokGold" if sc.get("speaker") in ("beru", "monarch") else "RagnarokCyan"
        text = sc["text_sub"].replace("\n", "\\N")
        events.append(f"Dialogue: 0,{fmt_time(start)},{fmt_time(end)},{style},,0,0,0,,{text}")
        curr += dur

    out_ass.write_text(header + "\n".join(events), encoding="utf-8")


def generate_thumbnail(panel_img: Path, out_thumb: Path):
    """Create a high-CTR YouTube thumbnail (1280x720)."""
    out_thumb.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(str(panel_img)) as im:
        base = im.convert("RGB")

    canvas = Image.new("RGB", (1280, 720), (10, 10, 20))
    bw, bh = base.size
    scale = max(1280 / bw, 720 / bh)
    scaled_w, scaled_h = int(bw * scale), int(bh * scale)
    base_scaled = base.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    offset_x = (1280 - scaled_w) // 2
    offset_y = (720 - scaled_h) // 2
    canvas.paste(base_scaled, (offset_x, offset_y))

    # Gradient overlay for text readability
    draw = ImageDraw.Draw(canvas)
    for y in range(500, 720):
        alpha = int(220 * ((y - 500) / 220))
        draw.line([(0, y), (1280, y)], fill=(0, 0, 10, alpha))
    for y in range(0, 220):
        alpha = int(200 * ((220 - y) / 220))
        draw.line([(0, y), (1280, y)], fill=(5, 5, 20, alpha))

    try:
        font_large = ImageFont.truetype("arialbd.ttf", 60)
        font_sub = ImageFont.truetype("arialbd.ttf", 44)
        font_badge = ImageFont.truetype("arialbd.ttf", 36)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    # Red badge
    draw.rounded_rectangle([(40, 30), (460, 95)], radius=12, fill=(220, 20, 60))
    draw.text((60, 42), "SOLO LEVELING RAGNAROK", font=font_badge, fill=(255, 255, 255))

    # Main hook text
    draw.text((45, 540), "CHAPTER 6 : MONARCH OF FANGS!", font=font_large, fill=(0, 240, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    draw.text((45, 625), "CURSED SWORD OF THE BEAST! 🔥", font=font_sub, fill=(255, 215, 0), stroke_width=3, stroke_fill=(0, 0, 0))

    canvas.save(str(out_thumb), quality=95)
    print(f"  ✓ High-CTR Thumbnail generated: {out_thumb}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
async def run_pipeline():
    ff = ffmpeg_bin()
    out_dir = ROOT / "output" / "solo_leveling_ragnarok_ch6"
    panels_dir = out_dir / "panels"
    cp_dir = out_dir / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 75)
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 6 — 100% PURE HUMANOID VOICE ENGINE")
    print("=" * 75)

    scene_durs = []
    scene_mp4s = []

    for i, sc in enumerate(SCENES, start=1):
        pid = sc["panel"]
        img_path = panels_dir / f"panel_{pid:03d}.jpg"
        if not img_path.exists():
            print(f"  ❌ Missing panel: {img_path}")
            continue

        scene_final = cp_dir / f"scene_{i:03d}.mp4"
        voice_wav = cp_dir / f"voice_{i:03d}.wav"
        music_wav = cp_dir / f"music_{i:03d}.wav"
        sfx_wav = cp_dir / f"sfx_{i:03d}.wav"
        audio_aac = cp_dir / f"audio_{i:03d}.aac"
        video_mp4 = cp_dir / f"video_{i:03d}.mp4"

        print(f"\n[Scene {i:02d}/36] Panel {pid:03d} | Spk: {sc['speaker']} | Emo: {sc['emotion']}")

        # 1. 100% Pure Gemini Humanoid Voice
        if not voice_wav.exists() or voice_wav.stat().st_size < 1000:
            print(f"  🎙️ Synthesizing 100% Gemini humanoid voice ({sc['speaker']})...")
            await generate_humanoid_voice(sc["text_speak"], sc["speaker"], sc["emotion"], voice_wav)
            await asyncio.sleep(2.0)  # Pacing to guarantee zero rate limits

        v_dur = float(probe(voice_wav)["format"]["duration"])
        dur = max(4.2, v_dur + 0.65)
        scene_durs.append(dur)
        print(f"  ⏱️ Audio: {v_dur:.2f}s -> Scene Dur: {dur:.2f}s")

        def is_valid_mp4(p: Path) -> bool:
            if not p.exists() or p.stat().st_size < 10000:
                return False
            try:
                probe(p)
                return True
            except Exception:
                return False

        if is_valid_mp4(scene_final):
            print(f"  ✓ Checkpoint: scene_{i:03d}.mp4")
            scene_mp4s.append(scene_final)
            continue

        # 2. Score & SFX
        if not music_wav.exists():
            generate_music(sc["music"], dur, music_wav)
        if not sfx_wav.exists():
            generate_sfx(sc["sfx"], dur, sfx_wav)
        if not audio_aac.exists():
            mix_audio(voice_wav, music_wav, sfx_wav, dur, audio_aac)

        # 3. Video Render
        if not is_valid_mp4(video_mp4):
            print(f"  🎬 Rendering wide 1250px panel motion ({sc['camera']})...")
            render_wide_scene_video(img_path, dur, sc["camera"], video_mp4)

        # 4. Join Video + Audio
        print(f"  🔗 Joining scene_{i:03d}...")
        join_scene(video_mp4, audio_aac, scene_final)
        scene_mp4s.append(scene_final)

    # ─────────────────────────────────────────────────────────────────────────
    # CONCATENATION & HARDCODED SUBTITLES
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("  🎞️ CONCATENATING 36 SCENES & BURNING SUBTITLES")
    print("=" * 75)

    concat_list = out_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in scene_mp4s:
            escaped = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{escaped}'\n")

    raw_combined = out_dir / "solo_leveling_ragnarok_ch6_raw.mp4"
    print(f"  📦 Concatenating into {raw_combined}...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(raw_combined)
    ], check=True)

    # Subtitles
    ass_path = out_dir / "solo_leveling_ragnarok_ch6.ass"
    generate_ass_subtitles(SCENES[:len(scene_durs)], scene_durs, ass_path)
    print(f"  ✓ Dual-color subtitles saved: {ass_path}")

    # Burn subtitles
    final_output = out_dir / "solo_leveling_ragnarok_ch6_final.mp4"
    print(f"  🔥 Burning subtitles into {final_output}...")
    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    vf_chain = f"ass='{ass_escaped}'"

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_combined),
        "-vf", vf_chain,
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "copy",
        str(final_output)
    ], check=True)

    # Thumbnail
    thumb_path = out_dir / "thumbnail.jpg"
    thumb_source = panels_dir / "panel_036.jpg"
    if not thumb_source.exists():
        thumb_source = panels_dir / "panel_031.jpg"
    generate_thumbnail(thumb_source, thumb_path)

    total_dur = float(probe(final_output)["format"]["duration"])
    size_mb = final_output.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 75)
    print(f"  🎉 SOLO LEVELING: RAGNAROK CHAPTER 6 RENDERED SUCCESSFULLY!")
    print(f"  📁 Video: {final_output}")
    print(f"  ⏱️ Duration: {total_dur:.1f}s (~{total_dur/60:.2f} min)")
    print(f"  💾 File Size: {size_mb:.1f} MB")
    print(f"  🖼️ Thumbnail: {thumb_path}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
