"""
generate_solo_leveling_ragnarok_ch10_tight.py — Solo Leveling: Ragnarok Chapter 10 Cinematic Explainer.
Strictly Calibrated for 4 to 5 Minutes Runtime (~255s / 4.25 mins).
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

# ─────────────────────────────────────────────────────────────────────────────
# 37 SYNCHRONIZED SCENES (CALIBRATED FOR EXACTLY 4 TO 5 MINUTES RUNTIME)
# ─────────────────────────────────────────────────────────────────────────────
SCENES = [
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Solo Leveling: Ragnarok — Chapter 10! Sung Jinwoo ke bete Suho ka naya toofani safar shuru!",
        "text_speak": "सोलो लेवलिंग: रैग्नारॉक — चैप्टर दस! जिन-वू के बेटे सुंग सू-हो का नया तूफानी सफर शुरू!"
    },
    {
        "panel": 2, "speaker": "manager", "emotion": "shocked", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Black Tortoise Guild mein khabar aayi ki naye E-Rank hunter Suho ne unka bada scout offer thukra diya!",
        "text_speak": "ब्लैक टॉर्टॉयज़ गिल्ड में खबर आई कि नए ई-रैंक हंटर सू-हो ने उनका बड़ा ऑफर ठुकरा दिया!"
    },
    {
        "panel": 3, "speaker": "manager", "emotion": "furious", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Recruiter aag-baboola ho utha: 'Ek mamooli E-Rank hunter hamari itni badi guild ko reject kar raha hai?!'",
        "text_speak": "रिक्रूटर आगबबूला हो उठा: 'एक मामूली ई-रैंक हंटर हमारी इतनी बड़ी गिल्ड को लात मार रहा है?!'"
    },
    {
        "panel": 4, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Recruiter bola: 'Ise jald samajh aayega ki guild ke bina hunter banna kitna khaufnaak hota hai!'",
        "text_speak": "रिक्रूटर गुर्राया: 'इसे जल्द समझ आएगा कि गिल्ड के बिना हंटर बनना कितना खौफनाक है!'"
    },
    {
        "panel": 5, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho bola: 'Ye sab mujhe porter banana chahte hain... kisi guild mein phasne se mera level-up ruk jayega!'",
        "text_speak": "सू-हो ने कहा: 'ये सब मुझे कुली बनाना चाहते हैं... किसी गिल्ड में फँसने से मेरा लेवल-अप रुक जाएगा!'"
    },
    {
        "panel": 6, "speaker": "suho", "emotion": "curious", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Farsh par let kar Suho ne Beast Monarch ki talwar se pucha: 'Kyun Fang of Rakan, kya aage baat karein?'",
        "text_speak": "फर्श पर लेटकर सू-हो ने बीस्ट मोनार्क की तलवार से पूछा: 'क्यों फैंग ऑफ राखान, क्या आगे बात करें?'"
    },
    {
        "panel": 7, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho ne elaan kiya tha: 'Shadow Monarch ki parchhai aur Beast Monarch ka khanjar, dono milkar ladenge!'",
        "text_speak": "सू-हो ने ऐलान किया था: 'शैडो मोनार्क की परछाई और बीस्ट मोनार्क का खंजर, दोनों मिलकर लड़ेंगे!'"
    },
    {
        "panel": 8, "speaker": "sword", "emotion": "evil", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Talwar sann reh gayi: 'Ye itni badi baat itni asaani se kaise keh sakta hai? Par Shadow humara sathi ban sakta hai!'",
        "text_speak": "तलवार सन्न रह गई: 'ये इतनी बड़ी बात इतनी बेफिक्री से कैसे कह सकता है? पर शैडो हमारा साथी बन सकता है!'"
    },
    {
        "panel": 9, "speaker": "sword", "emotion": "calm", "camera": "sudden_zoom", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Talwar ne shart rakhi: 'Mujhe Beast Monarch ke kisi doosre pavitra dham par lekar chalo!'",
        "text_speak": "तलवार ने अपनी शर्त रखी: 'मुझे बीस्ट मोनार्क के किसी दूसरे पवित्र धाम पर लेकर चलो!'"
    },
    {
        "panel": 10, "speaker": "sword", "emotion": "curious", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Talwar ne rasta bataya: 'Par us dham ka gate toot chuka hai... yaani wahan Dungeon Break ho chuka hai!'",
        "text_speak": "तलवार ने रास्ता बताया: 'पर उस धाम का गेट टूट चुका है... यानी वहाँ डंजन ब्रेक हो चुका है!'"
    },
    {
        "panel": 11, "speaker": "narrator", "emotion": "urgent", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Suho foran samajh gaya: 'Field-Type Dungeon! Jahan khule gate ke darinde poori dharti ko barbad kar dete hain!'",
        "text_speak": "सू-हो फौरन समझ गया: 'फील्ड-टाइप डंजन! जहाँ खुले गेट के खूंखार दरिंदे पूरी धरती को बर्बाद कर देते हैं!'"
    },
    {
        "panel": 12, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne chacha ke liye sandesh chhoda aur nanhe Beru ke saath pavitra dham ki talash mein nikal pada!",
        "text_speak": "सू-हो ने चाचा के लिए संदेश छोड़ा और नन्हे बेरू के साथ पवित्र धाम की तलाश में निकल पड़ा!"
    },
    {
        "panel": 13, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Gwanak parvat ki sarhad par chetavani board laga tha: 'Yahan sirf Hyena Guild ka pravesh manya hai!'",
        "text_speak": "ग्वानाक पर्वत की सरहद पर चेतावनी बोर्ड लगा था: 'यहाँ सिर्फ खूंखार हायना गिल्ड का प्रवेश मान्य है!'"
    },
    {
        "panel": 14, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho ne dekha: 'Ye Hyena Guild purane khatarnaak apradhiyon ki jamaat hai... yahan aana gair-kanooni hai!'",
        "text_speak": "सू-हो ने देखा: 'ये हायना गिल्ड पुराने खतरनाक अपराधियों की जमात है... यहाँ आना गैर-कानूनी है!'"
    },
    {
        "panel": 15, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ki aankhon mein neeli jyoti jal uthi aur mutthi mein urja garajne lagi: 'Taiyyar ho jao, hum andar jaa rahe hain!'",
        "text_speak": "सू-हो की आँखों में नीली ज्योति जल उठी और मुट्ठी में ऊर्जा गरजने लगी: 'तैयार हो जाओ, हम अंदर जा रहे हैं!'"
    },
    {
        "panel": 16, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Tadaak! Ruler's Authority ki telekinesis se Suho ne suraksha camera ko hawa mein hi kachra bana diya!",
        "text_speak": "तड़ाक! रूलर्स अथॉरिटी की टेलीकिनेसिस से सू-हो ने सुरक्षा कैमरे को हवा में ही लोहे का कचरा बना दिया!"
    },
    {
        "panel": 17, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Nanha Beru garv se bola: 'Young Monarch, musibaton ko mitane ka aapka ye andaaz hubahu Raja Jinwoo jaisa hai!'",
        "text_speak": "नन्हा बेरू गर्व से बोला: 'युवराज, मुसीबतों को मिटाने का आपका ये बेखौफ अंदाज हूबहू राजा जिन-वू जैसा है!'"
    },
    {
        "panel": 18, "speaker": "suho", "emotion": "curious", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Jungle mein neela kohra chhaya tha... Beru ne bataya: 'Ye antariksh ka alien mana hai jo duniya ki deewaron ko cheerta hai!'",
        "text_speak": "जंगल में नीला कोहरा छाया था... बेरू ने बताया: 'ये अंतरिक्ष का एलियन माना है जो दुनिया की दीवारों को चीरता है!'"
    },
    {
        "panel": 19, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Beru ne raaz khola: 'Gahre antariksh ke Itarim devta is aayam ko tod kar rakshasi fauj Dharti par bhejna chahte hain!'",
        "text_speak": "बेरू ने राज़ खोला: 'गहरे अंतरिक्ष के इतारिम देवता इस आयाम को तोड़कर राक्षसी सेना धरती पर भेजना चाहते हैं!'"
    },
    {
        "panel": 20, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Beru bola: 'Shaktishaali asuron ko aane mein waqt lagega!' Suho ne thaan liya: 'Mujhe tezi se level-up karna hoga!'",
        "text_speak": "बेरू बोला: 'शक्तिशाली असुरों को आने में वक्त लगेगा!' सू-हो ने ठान लिया: 'मुझे तेजी से लेवल-अप करना होगा!'"
    },
    {
        "panel": 21, "speaker": "narrator", "emotion": "urgent", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Gurrrr! Andhere junglon se do darinde lapke: Daggerclaw Vriga aur laal aankhon wala Black Shadow Rajan!",
        "text_speak": "गुर्र्र्र! अंधेरे जंगलों से दो खूंखार दरिंदे लपके: डैगरक्लॉ व्रीगा और लाल आँखों वाला ब्लैक शैडो राजन!"
    },
    {
        "panel": 22, "speaker": "sword", "emotion": "evil", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Talwar chillayi: 'Mujhe mukhya hathiyar banao!' Par Suho muskuraya: 'Nahi, main apne haathon se ladunga!'",
        "text_speak": "तलवार चिल्लाई: 'मुझे मुख्य हथियार बनाओ!' पर सू-हो मुस्कुराया: 'नहीं, मैं अपने हाथों से लड़ूँगा!'"
    },
    {
        "panel": 23, "speaker": "suho", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Dhadak! Suho ne martial arts ke zordaar mukkho se vishaal darinde ke jabde par bijli jaisa vaar kiya!",
        "text_speak": "धड़ाक! सू-हो ने मार्शल आर्ट्स के जोरदार मुक्कों से उस विशाल दरिंदे के जबड़े पर बिजली जैसा वार किया!"
    },
    {
        "panel": 24, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Ruler's Authority ke saath Suho ne naya kaushal daaga: STORM SLASH! Toofani bawandar ne darindon ko cheer daala!",
        "text_speak": "रूलर्स अथॉरिटी के साथ सू-हो ने अपना नया कौशल दागा: स्टॉर्म स्लैश! तूफानी बवंडर ने दरिंदों को चीर डाला!"
    },
    {
        "panel": 25, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Zameen par dher laashon ki taraf Suho ne haath badhaya aur aadesh diya: 'SHADOW EXTRACTION!'",
        "text_speak": "ज़मीन पर ढेर लाशों की तरफ सू-हो ने बायाँ हाथ बढ़ाया और आदेश दिया: 'शैडो एक्सट्रैक्शन!'"
    },
    {
        "panel": 26, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Neele shadow kavach ne Suho ko dhank liya: 'Mare hue dushmano se hathiyar aur sena banana... yahi hai naya tareeqa!'",
        "text_speak": "नीले शैडो कवच ने सू-हो को ढँक लिया: 'मरे हुए दुश्मनों से हथियार और सेना बनाना... यही है मेरा नया तरीका!'"
    },
    {
        "panel": 27, "speaker": "sword", "emotion": "shocked", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Talwar kaanpne lagi: 'Jitne dushman marenge, ye utna ajey hoga... isiliye hum pichle yuddh mein haar gaye the!'",
        "text_speak": "तलवार थर-थर काँपने लगी: 'जितने दुश्मन मरेंगे, ये उतना अजेय होगा... इसीलिए हम युद्ध में हार गए थे!'"
    },
    {
        "panel": 28, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Buddhi badhte hi 5-5 shadow darinde khade ho gaye! Beru kuch kehne laga toh Suho ne daant diya: 'Chup raho!'",
        "text_speak": "बुद्धि बढ़ते ही 5-5 शैडो दरिंदे खड़े हो गए! बेरू कुछ कहने लगा तो सू-हो ने डांट दिया: 'चुप रहो!'"
    },
    {
        "panel": 29, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho pavitra dham ke paas pahuncha, jahan raat ke sannate mein truckon aur headlighton ki chamak dikhayi di!",
        "text_speak": "सू-हो पवित्र धाम के पास पहुँचा, जहाँ रात के सन्नाटे में ट्रकों और हेडलाइटों की चमक दिखाई दी!"
    },
    {
        "panel": 30, "speaker": "suho", "emotion": "curious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho ne jhadiyon se dekha: 'Itni der raat ko ye shikari yahan kya saazish rach rahe hain?'",
        "text_speak": "सू-हो ने झाड़ियों से देखा: 'इतनी देर रात को ये शिकारी यहाँ क्या साजिश रच रहे हैं?'"
    },
    {
        "panel": 31, "speaker": "narrator", "emotion": "shocked", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Suho ke hosh udd gaye! Aag ke paas ek bebas ladki rassiyon se jakdi thi aur munh par patti bandhi thi!",
        "text_speak": "सू-हो के होश उड़ गए! आग के पास एक बेबस लड़की रस्सियों से जकड़ी थी और मुँह पर पट्टी बंधी थी!"
    },
    {
        "panel": 32, "speaker": "suho", "emotion": "furious", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Ek darinde hunter ne ladki ke baal kheench kar neech hasi hasi! Suho ne daant peese: 'Beru, kya ye apharan ho raha hai?'",
        "text_speak": "एक वहशी शिकारी ने लड़की के बाल खींचकर नीच हँसी हँसी! सू-हो ने दाँत पीसे: 'बेरू, क्या ये अपहरण हो रहा है?'"
    },
    {
        "panel": 33, "speaker": "beru", "emotion": "urgent", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Beru ne licence ki duhai dekar rokna chaha, par jab usne dekha... toh Suho apni jagah se gayab tha!",
        "text_speak": "बेरू ने लाइसेंस की दुहाई देकर रोकना चाहा, पर जब उसने देखा... तो सू-हो अपनी जगह से गायब था!"
    },
    {
        "panel": 34, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "ambient_soft",
        "text_sub": "Kyunki Suho ke pita Jinwoo apradhiyon ko dafnane wale police the, aur dada ek veer firefighter!",
        "text_speak": "क्योंकि सू-हो के पिता जिन-वू अपराधियों को दफनाने वाले पुलिस थे, और दादा एक वीर फायरफाइटर!"
    },
    {
        "panel": 35, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "In do nayakon ke saaye mein pale Suho ki fitrat thi: INSAF KE MAAMLE MEIN SOCHNE SE PEHLE ACTION LENA!",
        "text_speak": "इन दो नायकों के साए में पले सू-हो की फितरत थी: इंसाफ के मामले में सोचने से पहले तुरंत एक्शन लेना!"
    },
    {
        "panel": 36, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Kadaak! Aasman ko cheerti neeli bijli ki tarah Suho us darinde hunter ki theek peeth ke peeche kaal bankar utra!",
        "text_speak": "कड़ाक! आसमान को चीरती नीली बिजली की तरह सू-हो उस हैवान शिकारी की ठीक पीठ के पीछे काल बनकर उतरा!"
    },
    {
        "panel": 37, "speaker": "suho", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Hunter ne chauk kar pucha: 'Are... kaun?!' Aur saamne Suho ki aankhon mein nyay ka khooni angaar tha! CLIFFHANGER!",
        "text_speak": "शिकारी ने चौंक कर पीछे देखा: 'अरे... कौन?!' और सामने सू-हो की आँखों में न्याय का खूनी अंगार था! क्लिफहैंगर!"
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# 10x BETTER HUMANOID NEURAL VOICE ENGINE (Character Specific Tuning & DSP)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_humanoid_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    
    rate_map = {
        "narrator": "+18%",
        "suho": "+18%",
        "beru": "+22%",
        "sword": "+14%",
        "manager": "+18%"
    }
    pitch_map = {
        "narrator": "-1Hz",
        "suho": "+1Hz",
        "beru": "+4Hz",
        "sword": "-5Hz",
        "manager": "-2Hz"
    }
    voice_name = "hi-IN-SwaraNeural" if speaker == "beru" else "hi-IN-MadhurNeural"
    
    r = rate_map.get(speaker, "+18%")
    p = pitch_map.get(speaker, "-1Hz")
    
    import edge_tts
    raw_mp3 = out_wav.with_suffix(".tmp.mp3")
    saved = False
    for attempt in range(1, 9):
        try:
            comm = edge_tts.Communicate(text_speak, voice_name, rate=r, pitch=p)
            await comm.save(str(raw_mp3))
            if raw_mp3.exists() and raw_mp3.stat().st_size > 1000:
                saved = True
                break
        except Exception as e:
            print(f"    ⚠️ edge_tts attempt {attempt}/8 failed ({e}), retrying in {attempt * 2}s...")
            await asyncio.sleep(attempt * 2.0)
            
    if not saved or not raw_mp3.exists():
        raise RuntimeError(f"Failed to generate voice for: {text_speak[:30]}")
    
    subprocess.run([
        ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_mp3), "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1",
        str(out_wav)
    ], check=True)
    raw_mp3.unlink(missing_ok=True)

    # 10x Better Studio Warmth DSP Chain
    dsp_wav = out_wav.with_name(f"dsp_{out_wav.name}")
    ff = ffmpeg_bin()
    
    bass_boost = 3.6 if speaker in ("sword", "narrator") else (1.5 if speaker == "beru" else 2.4)
    treble_boost = 3.0 if speaker == "beru" else 2.2
    
    dsp_chain = (
        "highpass=f=75,"
        f"equalizer=f=125:t=q:w=1.4:g={bass_boost},"
        f"equalizer=f=3200:t=q:w=1.5:g={treble_boost},"
        "equalizer=f=7200:t=q:w=2.0:g=-1.5,"
        "acompressor=threshold=-17dB:ratio=2.8:attack=12:release=120:makeup=2.2dB,"
        "aecho=0.8:0.88:20:0.10"
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
# WIDE SCENE RENDERER (PERFECT FOCUS ON DISPLAYED ART)
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
Title: Solo Leveling Ragnarok Chapter 10 Subtitles
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
        start_str = fmt_time(curr + 0.1)
        end_str = fmt_time(curr + dur - 0.1)
        style = "RagnarokGold" if sc["speaker"] in ("beru", "suho", "sword") else "RagnarokCyan"
        text = sc["text_sub"].replace("\n", " ")
        events.append(f"Dialogue: 0,{start_str},{end_str},{style},,0,0,0,,{text}")
        curr += dur

    out_ass.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    print(f"  ✓ Dual-Color Subtitles generated: {out_ass.name}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
async def run_pipeline():
    ff = ffmpeg_bin()
    out_dir = ROOT / "output" / "solo_leveling_ragnarok_ch10"
    panels_dir = out_dir / "panels"
    cp_dir = out_dir / "checkpoints_tight"
    cp_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 75)
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 10 — EXACT 4-5 MINUTE CINEMATIC ENGINE")
    print("  10x Humanoid Voice Quality · 100% 1:1 Voice-to-Image Matching")
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

        print(f"\n[Scene {i:02d}/37] Panel {pid:03d} | Spk: {sc['speaker'].upper()} ({sc['emotion']})")

        # 1. Humanoid Voice
        if not voice_wav.exists() or voice_wav.stat().st_size < 1000:
            print(f"  🎙️ Synthesizing 10x humanoid voice for {sc['speaker'].upper()}...")
            await generate_humanoid_voice(sc["text_speak"], sc["speaker"], sc["emotion"], voice_wav)
            await asyncio.sleep(0.2)

        probe_data = probe(voice_wav)
        v_dur = float(probe_data["format"]["duration"]) if (probe_data and "format" in probe_data and "duration" in probe_data["format"]) else 6.5
        dur = max(6.2, v_dur + 0.35)
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
            print(f"  ✓ Checkpoint hit: scene_{i:03d}.mp4")
            scene_mp4s.append(scene_final)
            continue

        # 2. Score & SFX
        if not music_wav.exists():
            generate_music(sc["music"], dur, music_wav)
        if not sfx_wav.exists():
            generate_sfx(sc["sfx"], dur, sfx_wav)

        if not audio_aac.exists():
            mix_audio(voice_wav, music_wav, sfx_wav, dur, audio_aac)

        # 3. Video Render with 1:1 matching panel
        if not is_valid_mp4(video_mp4):
            print(f"  🎬 Rendering wide panel motion ({sc['camera']}) on panel_{pid:03d}.jpg...")
            render_wide_scene_video(img_path, dur, sc["camera"], video_mp4)

        # 4. Join Video + Audio
        print(f"  🔗 Joining scene_{i:03d}...")
        join_scene(video_mp4, audio_aac, scene_final)
        scene_mp4s.append(scene_final)

    # Concat & Burn Subtitles
    print("\n" + "=" * 75)
    print("  🎞️ CONCATENATING 37 SCENES & BURNING SUBTITLES")
    print("=" * 75)

    concat_list = out_dir / "concat_list_tight.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in scene_mp4s:
            escaped = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{escaped}'\n")

    raw_final = out_dir / "raw_combined_tight.mp4"
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(raw_final)
    ], check=True)

    # Subtitles
    sub_ass = out_dir / "subtitles_tight.ass"
    generate_ass_subtitles(SCENES, scene_durs, sub_ass)

    final_mp4 = out_dir / "solo_leveling_ragnarok_ch10_final.mp4"
    ass_escaped = str(sub_ass).replace("\\", "/").replace(":", "\\:")
    sub_filter = f"subtitles='{ass_escaped}'"

    print("  🔥 Burning subtitles...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_final),
        "-vf", sub_filter,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "19",
        "-c:a", "copy",
        str(final_mp4)
    ], check=True)

    v_info = probe(final_mp4)
    total_dur = float(v_info["format"]["duration"])
    size_mb = final_mp4.stat().st_size / 1024 / 1024
    print("\n" + "#" * 75)
    print(f"  🎉 SOLO LEVELING RAGNAROK CHAPTER 10 COMPLETE!")
    print(f"  📁 Video: {final_mp4.name} ({size_mb:.2f} MB)")
    print(f"  ⏱️ Total Duration: {total_dur:.1f}s ({total_dur/60:.2f} mins)")
    print("#" * 75 + "\n")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
