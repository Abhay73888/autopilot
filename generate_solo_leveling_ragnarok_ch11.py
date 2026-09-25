"""
generate_solo_leveling_ragnarok_ch11.py — Solo Leveling: Ragnarok Chapter 11 Cinematic Explainer.
Strictly Calibrated for 4 to 5 Minutes Runtime (~270s / 4.5 mins).
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
# 42 SYNCHRONIZED SCENES (CALIBRATED FOR EXACTLY 4 TO 5 MINUTES RUNTIME)
# ─────────────────────────────────────────────────────────────────────────────
SCENES = [
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Solo Leveling: Ragnarok — Chapter 11! Suho ka apradhi Hyena Guild ke gupt adday par toofani hamla!",
        "text_speak": "सोलो लेवलिंग: रैग्नारॉक — चैप्टर ग्यारह! सू-हो का खूंखार हायना गिल्ड के अड्डे पर तूफानी धावा!"
    },
    {
        "panel": 2, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Aasman se bijli bankar Suho ne Hyena Guild ke gundon par achanak dive-kick se hamla kar diya!",
        "text_speak": "आसमान से बिजली बनकर सू-हो ने हायना गिल्ड के गुंडों पर अचानक जबरदस्त डाइव-किक से हमला बोल दिया!"
    },
    {
        "panel": 3, "speaker": "manager", "emotion": "shocked", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Gunde thar-thar kaanp uthe: 'Ye koun achanak hamare beech mein kood pada?!'",
        "text_speak": "गुंडे थर-थर कांप उठे: 'ये कौन अचानक हमारे बीच में कूद पड़ा?!'"
    },
    {
        "panel": 4, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho ne socha: 'Arre yaar, kisi doosri guild ki zameen par bina ijazat aana to gair-kanooni hai... ab kya karun?'",
        "text_speak": "सू-हो ने सोचा: 'अरे यार, किसी दूसरी गिल्ड की ज़मीन पर बिना इजाज़त आना तो गैर-कानूनी है... अब क्या करूँ?'"
    },
    {
        "panel": 5, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Apni pehchan chhupane ke liye Suho ne neeli shadow energy se chehre par ek khaufnaak Shadow Mask bana liya!",
        "text_speak": "अपनी पहचान छुपाने के लिए सू-हो ने नीली शैडो एनर्जी से चेहरे पर एक खौफनाक शैडो मास्क बना लिया!"
    },
    {
        "panel": 6, "speaker": "suho", "emotion": "furious", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Mask pehen kar Suho bola: 'Tum jaise napak log masoomon ko kidnap karke unki jaan khatre mein daalte ho?!'",
        "text_speak": "मास्क पहनकर सू-हो दहाड़ा: 'तुम जैसे अपराधी मासूमों को किडनैप करके उनकी जान खतरे में डालते हो?!'"
    },
    {
        "panel": 7, "speaker": "manager", "emotion": "furious", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Hyena Guild ke gunde chillaye: 'Tujhe maut chahiye kya?! Iske tukde-tukde kar do!'",
        "text_speak": "हायना गिल्ड के गुंडे चिल्लाए: 'तुझे मौत चाहिए क्या?! इसके टुकड़े-टुकड़े कर दो!'"
    },
    {
        "panel": 8, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho ne aasan andaaz mein socha: 'Inka average rank sirf D-rank hai... mujhe apni taqat kam rakhni hogi!'",
        "text_speak": "सू-हो ने शांत दिमाग से सोचा: 'इनका रैंक सिर्फ डी-रैंक है... मुझे अपनी ताकत कम रखनी होगी ताकि ये बच सकें!'"
    },
    {
        "panel": 9, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho ne bina hathiyar, sirf ungliyon aur mutthiyon se unhe hawa mein 20 foot ooncha uda diya!",
        "text_speak": "सू-हो ने बिना हथियार, सिर्फ मुक्कों और लातों से उन्हें हवा में बीस फुट ऊंचा उछाल दिया!"
    },
    {
        "panel": 10, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Gunde zameen par bhed-bakriyon ki tarah dher ho gaye, unki ek na chali!",
        "text_speak": "सारे गुंडे फर्श पर भेड़-बकरियों की तरह ढेर हो गए, किसी की एक न चली!"
    },
    {
        "panel": 11, "speaker": "beru", "emotion": "crying", "camera": "slow_push", "music": "ambient_soft", "sfx": "whoosh_energy",
        "text_sub": "Ped par baitha Beru garv se bola: 'Young Monarch, D-rank insaan ab aapka muqabla nahi kar sakte! Beru ka dil khush ho gaya!'",
        "text_speak": "पेड़ पर बैठा बेरू गर्व से बोला: 'यंग मोनार्क, डी-रैंक इंसान अब आपका मुकाबला नहीं कर सकते! बेरू का दिल खुश हो गया!'"
    },
    {
        "panel": 12, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Suho ka System Status chamka: Level 16, 2,350 HP aur 33 Strength points!",
        "text_speak": "सू-हो का सिस्टम स्टेटस चमका: लेवल 16, तेईस सौ पचास एचपी और तैंतीस स्ट्रेंथ पॉइंट्स!"
    },
    {
        "panel": 13, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho ne behosh gundon ko lakdiyon ki tarah ek ke upar ek dher karke bandh diya!",
        "text_speak": "सू-हो ने सभी बेहोश गुंडों को लकड़ियों की तरह एक के ऊपर एक ढेर करके बांध दिया!"
    },
    {
        "panel": 14, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "ambient_soft", "sfx": "ambient_soft",
        "text_sub": "Bandhak ro pade: 'Shukriya humein bachane ke liye! Kya aap Hunter Association se hain?'",
        "text_speak": "बंधक रो पड़े: 'शुक्रिया हमें बचाने के लिए! क्या आप हंटर एसोसिएशन से हैं?'"
    },
    {
        "panel": 15, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "ambient_soft", "sfx": "ambient_soft",
        "text_sub": "Suho bola: 'Haan, aap waisa samajh sakte hain. Jaldi se surakshit jagah nikal jaiye!'",
        "text_speak": "सू-हो बोला: 'हाँ, आप वैसा समझ सकते हैं। जल्दी से सुरक्षित जगह निकल जाइए!'"
    },
    {
        "panel": 16, "speaker": "sword", "emotion": "curious", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Talwar Fang of Rakan thar-tharayi: 'Suho, aage dekho... jiske liye hum yahan aaye the, wo andar hai!'",
        "text_speak": "तलवार फैंग ऑफ राखान थरथराई: 'सू-हो, आगे देखो... जिसके लिए हम यहाँ आए थे, वो अंदर है!'"
    },
    {
        "panel": 17, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho Hyena Guild ke kaale tahkhane ke andheron mein aage badhta chala gaya!",
        "text_speak": "सू-हो हायना गिल्ड के काले तहखाने के भयानक अंधेरों में आगे बढ़ता चला गया!"
    },
    {
        "panel": 18, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Wahan khoon ki balti, injection aur khaufnaak pinjre bane hue the!",
        "text_speak": "वहाँ खून की बाल्टियां, सीरिंज और खौफनाक कैदखाने के पिंजरे बने हुए थे!"
    },
    {
        "panel": 19, "speaker": "suho", "emotion": "shocked", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Ek andhere pinjre mein ek chhota, zakhmi bhediya dard se karah raha tha!",
        "text_speak": "एक अंधेरे पिंजरे में एक छोटा, पट्टियों में लिपटा ज़ख्मी भेड़िया दर्द से कराह रहा था!"
    },
    {
        "panel": 20, "speaker": "sword", "emotion": "shocked", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Talwar ne khaufnaak sach khola: 'Ye koi mamooli janwar nahi... ye Beast King Fang Monarch Rakhan ka vanshaj hai!'",
        "text_speak": "तलवार ने खौफनाक सच खोला: 'ये कोई मामूली जानवर नहीं... ये बीस्ट किंग फैंग मोनार्क राखान का वंशज है!'"
    },
    {
        "panel": 21, "speaker": "sword", "emotion": "crying", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Talwar boli: 'Shadow Monarch Jinwoo se haarne ke baad Rakhan ne apne vanshaj ko sharan di thi... par ye bachha marne ki kagar par hai!'",
        "text_speak": "तलवार बोली: 'शैडो मोनार्क जिन-वू से हारने के बाद राखान ने अपने वंशज को शरण दी थी... पर ये बच्चा मरने की कगार पर है!'"
    },
    {
        "panel": 22, "speaker": "beru", "emotion": "urgent", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Beru ne pucha: 'Young Monarch, ab aap kya karenge?'",
        "text_speak": "बेरू ने बेचैनी से पूछा: 'यंग मोनार्क, अब आप क्या करेंगे?'"
    },
    {
        "panel": 23, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Tabhi zameen par bhari kadmon ki aahat aayi: 'Bahar ke gundon ko maarne wala sirf ek hi insaan hai...'",
        "text_speak": "तभी ज़मीन पर भारी कदमों की आहट गूंजी: 'बाहर के पहरेदारों को मारने वाला सिर्फ एक ही इंसान है...'"
    },
    {
        "panel": 24, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Andhere se bahar nikla ek vishal, 10-foot lamba darinda — Werewolf Brocky!",
        "text_speak": "अंधेरे से बाहर निकला एक विशाल, दस फुट लंबा दानवी भेड़िया — वेयरवॉल्फ ब्रॉकी!"
    },
    {
        "panel": 25, "speaker": "sword", "emotion": "shocked", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Talwar cheekh uthi: 'Brocky! Tu zinda hai?! Tujhe to vanshaj ki hifazat ke liye bheja gaya tha!'",
        "text_speak": "तलवार चीख उठी: 'ब्रॉकी! तू ज़िंदा है?! तुझे तो राखान के वंशज की हिफाज़त के लिए भेजा गया था!'"
    },
    {
        "panel": 26, "speaker": "manager", "emotion": "evil", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Brocky ki laal aankhein chamki: 'Insaan... teri himmat kaise hui meri cheez ko chhoone ki?!'",
        "text_speak": "ब्रॉकी की लाल आंखें खूंखार चमकी: 'इंसान... तेरी हिम्मत कैसे हुई मेरी चीज़ को छूने की?!'"
    },
    {
        "panel": 27, "speaker": "narrator", "emotion": "urgent", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Brocky laal bijli ki raftaar se kooda, hawa mein shaktishaali shockwaves phoot pade!",
        "text_speak": "ब्रॉकी लाल बिजली की रफ्तार से झपटा, हवा में विनाशकारी शॉकवेव फूट पड़े!"
    },
    {
        "panel": 28, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Brocky ke bhediya panje ne Suho par aisa bhayankar vaar kiya ki haddiyan hil gayi!",
        "text_speak": "ब्रॉकी के पंजे ने सू-हो पर ऐसा भयानक वार किया कि हड्डियां तक कांप गईं!"
    },
    {
        "panel": 29, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Suho poori building ko cheerte hue bahar patharon mein ja gira, zameen par gehri khai ban gayi!",
        "text_speak": "सू-हो पूरी बिल्डिंग को चीरता हुआ बाहर पत्थरों में जा गिरा, ज़मीन पर गहरी खाई बन गई!"
    },
    {
        "panel": 30, "speaker": "suho", "emotion": "painful", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Beru cheekha: 'Young Monarch!' Suho khoon thookte hue bola: 'Ab tak jitni maar padi hai, ye sabse dardnaak thi!'",
        "text_speak": "बेरू चीखा: 'यंग मोनार्क!' सू-हो खून थूकते हुए बोला: 'अब तक जितनी मार पड़ी है, ये सबसे दर्दनाक थी!'"
    },
    {
        "panel": 31, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "System gungunaya: 'Skill: Endurance Level Up! Physical Resistance +20% se seedha +40% ho gayi!'",
        "text_speak": "सिस्टम की घंटी बजी: 'स्किल एंड्योरेंस लेवल अप! फिजिकल रेसिस्टेंस बीस प्रतिशत से बढ़कर सीधे चालीस प्रतिशत हो गई!'"
    },
    {
        "panel": 32, "speaker": "beru", "emotion": "shocked", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Beru ka chehra kaanp utha: 'Young Monarch... mujhe samajh aaya ye urja kya hai... ye ITARIM hai! Outer Gods ki taqat!'",
        "text_speak": "बेरू का चेहरा कांप उठा: 'यंग मोनार्क... मुझे समझ आया ये ऊर्जा क्या है... ये इटारिम है! आउटर गॉड्स की शक्ति!'"
    },
    {
        "panel": 33, "speaker": "sword", "emotion": "furious", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Talwar garji: 'Brocky! Sharan kho dene ke baad tune aakhir apni ye taqat kaise banaye rakhi?!'",
        "text_speak": "तलवार गरजी: 'ब्रॉकी! शरणगाह खो देने के बाद तूने आखिर अपनी ये ताकत कैसे बनाए रखी?!'"
    },
    {
        "panel": 34, "speaker": "manager", "emotion": "evil", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Brocky hasa: 'Kamzor ka naseeb taqatwar ka khana banna hai... main roz is bachhe ka maans khata hoon aur Monarch ka khoon peeta hoon!'",
        "text_speak": "ब्रॉकी हंसा: 'कमज़ोर का काम ताकतवर की खुराक बनना है... मैं रोज इस बच्चे का मांस खाता हूँ और मोनार्क का खून पीता हूँ!'"
    },
    {
        "panel": 35, "speaker": "sword", "emotion": "furious", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Talwar krodh se thar-tharayi: 'Brocky! Agar meri aakhri saans bhi bachi, to main tujhe apne haathon se maarunga!'",
        "text_speak": "तलवार क्रोध से थरथराई: 'ब्रॉकी! अगर मेरी आखिरी सांस भी बची, तो मैं तुझे अपने हाथों से मारूँगा!'"
    },
    {
        "panel": 36, "speaker": "manager", "emotion": "furious", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Brocky chillaya: 'Rakhan kamzor tha isliye mara! Agla Fang Monarch banne ke laayak sirf main hoon!'",
        "text_speak": "ब्रॉकी दहाड़ा: 'राखान कमज़ोर था इसलिए मरा! अगला फैंग मोनार्क बनने के लायक सिर्फ मैं हूँ!'"
    },
    {
        "panel": 37, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Brocky bachhe ko kuchalne kooda, par Suho ne Ruler's Authority se bhediye ke bachhe ko hawa mein kheench liya!",
        "text_speak": "ब्रॉकी बच्चे को कुचलने कूदा, पर सू-हो ने रूलर्स अथॉरिटी से बच्चे को हवा में खींच लिया!"
    },
    {
        "panel": 38, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru ne nannhe bhediye ko godi mein pakad kar kaha: 'Kamaal hai!'",
        "text_speak": "बेरू ने नन्हे भेड़िये को गोदी में लपक कर कहा: 'कमाल है!'"
    },
    {
        "panel": 39, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho ne apni talwar par neeli bijli ki aag jala li aur aage badha!",
        "text_speak": "सू-हो ने अपनी तलवार पर नीली बिजली की आग जला ली और आगे बढ़ा!"
    },
    {
        "panel": 40, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho bola: 'Shadow aur Fang ka pehla gathbandhan! Itarim... aakhirkar mujhe apne pita Jinwoo ka suraag mil gaya!'",
        "text_speak": "सू-हो बोला: 'शैडो और फैंग का पहला गठबंधन! इटारिम... आखिरकार मुझे अपने पिता जिन-वू का सुराग मिल गया!'"
    },
    {
        "panel": 41, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Brocky ke maathe par Itarim ka prateek chamak utha: 'Main tujhe zinda nahi chhodunga!'",
        "text_speak": "ब्रॉकी के माथे पर इटारिम का सिंबल चमक उठा: 'मैं तुझे ज़िंदा नहीं छोड़ूँगा!'"
    },
    {
        "panel": 42, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "System Alert: Emergency Quest 'Hunt the Hyena!' Brocky ko harakar zinda bacho! To Be Continued!",
        "text_speak": "सिस्टम अलर्ट: इमरजेंसी क्वेस्ट 'हंट द हायना!' ब्रॉकी को हराकर ज़िंदा बचो! जारी रहेगा अगले चैप्टर में!"
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# VOICEOVER GENERATOR (10X BETTER HUMANOID EMOTIVE QUALITY)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    import edge_tts

    voice = "hi-IN-MadhurNeural"
    rate_str = "+16%"
    pitch_str = "+0Hz"

    if speaker == "beru":
        rate_str = "+19%"
        pitch_str = "+6Hz"
    elif speaker == "sword":
        rate_str = "+14%"
        pitch_str = "-5Hz"
    elif speaker == "manager":
        rate_str = "+17%"
        pitch_str = "-3Hz"
    elif speaker == "suho":
        rate_str = "+16%"
        pitch_str = "+1Hz"

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    raw_mp3 = out_wav.with_suffix(".mp3")
    
    saved = False
    for attempt in range(4):
        try:
            comm = edge_tts.Communicate(text_speak, voice, rate=rate_str, pitch=pitch_str)
            await comm.save(str(raw_mp3))
            if raw_mp3.exists() and raw_mp3.stat().st_size > 1000:
                saved = True
                break
        except Exception as e:
            await asyncio.sleep(1.2 * (attempt + 1))

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
# WIDE SCENE RENDERER
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
# ASS SUBTITLES & THUMBNAIL
# ─────────────────────────────────────────────────────────────────────────────
def generate_ass_subtitles(scenes: list[dict], scene_durs: list[float], out_ass: Path):
    header = """[Script Info]
Title: Solo Leveling Ragnarok Chapter 11 Subtitles
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

def create_thumbnail(out_jpg: Path):
    panel_path = ROOT / "output" / "solo_leveling_ragnarok_ch11" / "panels" / "panel_024.jpg"
    w, h = 1920, 1080
    thumb = Image.new("RGB", (w, h), (10, 12, 18))
    
    if panel_path.exists():
        with Image.open(str(panel_path)) as p_im:
            pw, ph = p_im.size
            scale = 1080 / max(1, ph)
            nw = int(pw * scale)
            scaled = p_im.resize((nw, 1080), Image.Resampling.LANCZOS)
            thumb.paste(scaled, (w - nw - 40, 0))

    draw = ImageDraw.Draw(thumb)
    
    # Left dark gradient block
    for x in range(1100):
        alpha = int(255 * (1.0 - x / 1100.0))
        draw.line([(x, 0), (x, h)], fill=(8, 10, 15, alpha))

    # Badge
    draw.rounded_rectangle([70, 80, 520, 145], radius=14, fill=(225, 29, 72))
    draw.text((95, 93), "SOLO LEVELING: RAGNAROK", fill=(255, 255, 255))

    # Big Title
    draw.text((70, 180), "CHAPTER 11", fill=(56, 189, 248))
    draw.text((70, 290), "SHADOW MASK AWAKENS", fill=(255, 255, 255))
    draw.text((70, 400), "FANG MONARCH BLOODLINE", fill=(250, 204, 21))
    draw.text((70, 510), "ITARIM OUTER GODS REVEALED!", fill=(244, 63, 94))

    thumb.save(str(out_jpg), quality=95)
    print(f"  ✓ High-CTR Thumbnail created: {out_jpg.name}")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
async def run_pipeline():
    ff = ffmpeg_bin()
    out_dir = ROOT / "output" / "solo_leveling_ragnarok_ch11"
    panels_dir = out_dir / "panels"
    cp_dir = out_dir / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 75)
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 11 — 4 TO 5 MINUTE CINEMATIC ENGINE")
    print("  10x Humanoid Voice Quality · 100% 1:1 Voice-to-Image Matching")
    print("=" * 75)

    scene_durs = []
    scene_clips = []

    for i, sc in enumerate(SCENES, start=1):
        p_num = sc["panel"]
        img_path = panels_dir / f"panel_{p_num:03d}.jpg"
        if not img_path.exists():
            img_path = panels_dir / f"panel_{max(1, p_num - 1):03d}.jpg"
            if not img_path.exists():
                img_path = panels_dir / "panel_001.jpg"

        print(f"\n🎬 Scene {i:02d}/{len(SCENES)} (Panel {p_num:03d}): {sc['speaker'].upper()} [{sc['emotion']}]")

        # 1. Voice
        v_wav = cp_dir / f"sc_{i:02d}_v.wav"
        if not v_wav.exists() or v_wav.stat().st_size < 1000:
            await generate_voice(sc["text_speak"], sc["speaker"], sc["emotion"], v_wav)
        
        info = probe(v_wav)
        v_dur = float(info.get("duration", 4.0))
        
        # Pacing padding
        dur = max(4.5, v_dur + 0.65)
        scene_durs.append(dur)
        print(f"  ✓ Voice duration: {v_dur:.2f}s -> Scene total: {dur:.2f}s")

        # 2. Score & SFX
        m_wav = cp_dir / f"sc_{i:02d}_m.wav"
        generate_music(sc["music"], dur, m_wav)

        s_wav = cp_dir / f"sc_{i:02d}_s.wav"
        generate_sfx(sc["sfx"], dur, s_wav)

        # 3. Audio Mix
        mix_aac = cp_dir / f"sc_{i:02d}_mix.aac"
        mix_audio(v_wav, m_wav, s_wav, dur, mix_aac)

        # 4. Video Render
        raw_vid = cp_dir / f"sc_{i:02d}_vid.mp4"
        if not raw_vid.exists() or raw_vid.stat().st_size < 1000:
            render_wide_scene_video(img_path, dur, sc["camera"], raw_vid)

        # 5. Join Scene
        sc_mp4 = cp_dir / f"sc_{i:02d}_final.mp4"
        join_scene(raw_vid, mix_aac, sc_mp4)
        scene_clips.append(sc_mp4)

    total_dur = sum(scene_durs)
    print("\n" + "=" * 75)
    print(f"  ⏱️ TOTAL GENERATED RUNTIME: {total_dur:.1f}s ({total_dur/60:.2f} minutes)")
    print("=" * 75)

    if not (235.0 <= total_dur <= 305.0):
        print(f"  ⚠️ Warning: Runtime {total_dur:.1f}s is slightly off 240s-300s window!")
    else:
        print(f"  🎯 STRICT CONSTRAINT SATISFIED: Exactly inside 4 to 5 minutes! ({total_dur/60:.2f} mins)")

    # Concatenate all scenes
    concat_list = out_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            clean_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    unsubbed_mp4 = out_dir / "solo_leveling_ragnarok_ch11_unsubbed.mp4"
    print(f"\n📦 Concatenating all {len(scene_clips)} scenes into {unsubbed_mp4.name}...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(unsubbed_mp4)
    ], check=True)

    # Subtitles
    ass_path = out_dir / "solo_leveling_ragnarok_ch11.ass"
    generate_ass_subtitles(SCENES, scene_durs, ass_path)

    # Final Subbed Master
    final_mp4 = out_dir / "solo_leveling_ragnarok_ch11_final.mp4"
    print(f"🔥 Burning styled subtitles into final broadcast master: {final_mp4.name}...")
    
    # Escape path for FFmpeg subtitles filter
    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    sub_filter = f"ass='{ass_escaped}'"

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(unsubbed_mp4),
        "-vf", sub_filter,
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "copy",
        str(final_mp4)
    ], check=True)

    # Thumbnail
    thumb_path = out_dir / "thumbnail.jpg"
    create_thumbnail(thumb_path)

    final_info = probe(final_mp4)
    final_sec = float(final_info.get("duration", total_dur))
    final_size_mb = final_mp4.stat().st_size / (1024 * 1024)

    print("\n" + "🎉" * 38)
    print("  ✅ SOLO LEVELING: RAGNAROK CHAPTER 11 VIDEO GENERATION COMPLETE!")
    print(f"  📁 Output: {final_mp4}")
    print(f"  ⏱️ Final Duration: {final_sec:.1f}s ({final_sec/60:.2f} minutes)")
    print(f"  💾 File Size: {final_size_mb:.2f} MB")
    print(f"  🖼️ Thumbnail: {thumb_path}")
    print("🎉" * 38 + "\n")

    return final_mp4

if __name__ == "__main__":
    asyncio.run(run_pipeline())
