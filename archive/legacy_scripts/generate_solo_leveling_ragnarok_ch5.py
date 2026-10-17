"""
generate_solo_leveling_ragnarok_ch5.py — Solo Leveling: Ragnarok Chapter 5 Cinematic Hindi Explainer Video.

Key Technical Guarantees & Features:
  1. 100% Full-Length Humanoid Voice: Neural TTS ('hi-IN-MadhurNeural' with custom DSP chain:
     tube warmth EQ, presence boost, de-esser, broadcast compression, and dynamic pacing).
  2. High-CTR 1280x720 Thumbnail featuring Suho's epic "Arise" climax with glowing text.
  3. 35 Calibrated Cinematic Scenes with pan & scan motion (Ken Burns), bokeh backgrounds,
     procedural ambient soundtrack & battle SFX.
  4. Dual-Color ASS Subtitles (Ragnarok Cyan & Monarch Gold).
"""

import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.ffmpeg import ffmpeg_bin, probe

# ─────────────────────────────────────────────────────────────────────────────
# 35 SCRIPTED SCENES (CHAPTER 5 COMPLETE STORYLINE)
# ─────────────────────────────────────────────────────────────────────────────
SCENES = [
    # [ACT 1: ENTERING THE SHADOW DUNGEON & SURVIVAL QUEST]
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Solo Leveling: Ragnarok — Chapter 5! The Shadow Dungeon aur pehla 'ARISE'!",
        "text_speak": "सोलो लेवलिंग: रैग्नारॉक — चैप्टर पाँच! द शैडो डंजन और पहला 'अराइज़'!"
    },
    {
        "panel": 2, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Beru ne ailaan kiya: 'Ye murdon ki sarzameen hai... THE SHADOW DUNGEON!'",
        "text_speak": "बेरू ने सम्मान से सिर झुकाया: 'यह मुर्दों की पावन सरज़मीन है... द शैडो डंजन! जहाँ सिर्फ मालिक की इजाज़त से ही कोई कदम रख सकता है!'"
    },
    {
        "panel": 3, "speaker": "suho", "emotion": "curious", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho ne charon taraf dekha: 'Ye dungeon kam aur tabah shahar zyada lag raha hai...'",
        "text_speak": "चारों तरफ टूटी गगनचुंबी इमारतें थीं। सू-हो बुदबुदाया: 'यह किसी डंजन से ज़्यादा तबाह हो चुका वीरान शहर लग रहा है...'"
    },
    {
        "panel": 4, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Slippers pehne khandar mein chalte hue... Suho ko ajeeb sa apnapan mehsoos hua.",
        "text_speak": "टूटे पत्थरों पर चलते हुए... न जाने क्यों, सू-हो को इस भयानक जगह में एक अजीब सा अपनापन महसूस होने लगा।"
    },
    {
        "panel": 5, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "shock_sting",
        "text_sub": "TING! [QUEST NOTICE: SURVIVE 4 HOURS]! Saaye kamzor maalik ko qubool nahi karenge!",
        "text_speak": "टिंग! तभी सुनहरी रोशनी चमकी: सर्वाइवल क्वेस्ट! इस डंजन के खूंखार साये कमज़ोर इंसान को कभी अपना मालिक नहीं मानेंगे! चार घंटे ज़िंदा बचकर दिखाओ!"
    },

    # [ACT 2: GOBLIN SCOUT AMBUSH & FIRST BATTLE]
    {
        "panel": 6, "speaker": "beru", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Beru cheekha: 'Chaukanna rahiye, Young Monarch! Dard aur azaab ka waqt shuru hone wala hai!'",
        "text_speak": "बेरू घबराकर चिल्लाया: 'चौकन्ना रहिए, यंग मोनार्क! भयानक दर्द और इम्तिहान का वक़्त आ चुका है!'"
    },
    {
        "panel": 7, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "SWOOSH! Achanak aasman se ek patthar ki kulhaadi Suho ki gardan par aayi! Suho baal-baal bacha!",
        "text_speak": "सनसनाती हुई एक भारी पत्थर की कुल्हाड़ी सू-हो की गर्दन को छूती हुई निकली! सू-हो ने पलक झपकते ही चकमा दिया!"
    },
    {
        "panel": 8, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "KRRRK! Samne se ek laal aankhon wala rakshas gurraya: [GOBLIN SCOUT]!",
        "text_speak": "मलबे से लाल-अंगारे जैसी आँखों वाला एक खूंखार राक्षस गुर्राया: गोब्लिन स्काउट!"
    },
    {
        "panel": 9, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne dekha: 'Iske naam par koi color nahi hai... matlab ye mere barabar ya kamzor hai!'",
        "text_speak": "सू-हो की नज़र उसके नाम पर पड़ी: 'इसके नाम पर कोई रंग नहीं है... यानी यह मेरे ही लेवल का है या मुझसे भी कमज़ोर!'"
    },

    # [ACT 3: TAKING THE AXE & WAR HORN ALARM]
    {
        "panel": 10, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Suho ne aage badhkar gobling ka haath marod diya aur uski kulhaadi chheen li!",
        "text_speak": "गोब्लिन ने दोबारा वार किया, लेकिन सू-हो ने झपटकर उसका हाथ मरोड़ दिया और कुल्हाड़ी उसी से छीन ली!"
    },
    {
        "panel": 11, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "CHOP! Suho ne kulhaadi gobling ke seene mein utaar di! [ITEM: GOBLIN STONE AXE] prapt hua!",
        "text_speak": "एक झटके में सू-हो ने कुल्हाड़ी गोब्लिन पर दे मारी! नोटिफिकेशन आया: गोब्लिन स्टोन एक्स हासिल हुई!"
    },
    {
        "panel": 12, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "shock_sting",
        "text_sub": "PUUUU—! Achanak khandar ki chhat se doosre scout ne yuddh ka bigul baja diya!",
        "text_speak": "तभी ऊँचाई से युद्ध के बिगुल की गूँज उठी! दूसरे स्काउट ने पूरे कबीले को जंग का बुलावा दे दिया था!"
    },
    {
        "panel": 13, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "RUMBLE! Khandaron se vishaal GOBLIN CENTURION aur unki poori sena nikal aayi!",
        "text_speak": "ज़मीन काँप उठी! मलबे को चीरते हुए एक भीमकाय गोब्लिन सेंचुरियन और उसकी पूरी हथियारबंद सेना बाहर निकल आई!"
    },

    # [ACT 4: BERU'S EXCUSES & RULER'S AUTHORITY TELEKINESIS]
    {
        "panel": 14, "speaker": "beru", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho ne madad maangi toh Beru bola: 'Monarch se door hone ke karan mera mana kam hai... aap khud ladiye!'",
        "text_speak": "सू-हो ने मदद माँगी तो बेरू बहाने बनाने लगा: 'मालिक से दूर होने के कारण मेरा माना कम है... और मैं लड़ा तो आपका एक्सपी कम हो जाएगा!'"
    },
    {
        "panel": 15, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Gooblin jhapat pade! Suho muskuraya: 'Toh chalo, is shakti ko aazmate hain!'",
        "text_speak": "दर्जनों गोब्लिन्स हवा में उछल पड़े! सू-हो मुस्कुराया: 'तो चलो, अपनी असली ताकत को आज़माते हैं!'"
    },
    {
        "panel": 16, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "ZOOM! Zameen par padi kulhaadi hawa mein tairi aur gobling ka sar faad diya! [RULER'S AUTHORITY LV. 1]!",
        "text_speak": "ज़मीन पर पड़ी कुल्हाड़ी नीली रोशनी से चमकी और गोली की रफ़्तार से उड़कर गोब्लिन की खोपड़ी चीर गई! रूलर्स अथॉरिटी!"
    },

    # [ACT 5: ARROW CATCH, FLASHBACK & ITARIM INVASION]
    {
        "panel": 17, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Tirandazon ne teer chalaye! Suho ne hawa mein teer pakda aur wapas unhi ke seene mein ghoñp diya!",
        "text_speak": "तीरंदाजों ने हमला किया! सू-हो ने उड़ता हुआ तीर हाथ में लपका और उल्टी दिशा में फेंककर आर्चर को भेद दिया!"
    },
    {
        "panel": 18, "speaker": "beru", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Beru hairan tha: 'Bachpan mein bhi ye Ruler's Authority se khiloune udaya karte the...'",
        "text_speak": "बेरू की आँखें खुली रह गईं: 'बचपन में भी छोटे मोनार्क इसी रूलर्स अथॉरिटी से अपने खिलौने और बोतलें हवा में तैराया करते थे...'"
    },
    {
        "panel": 19, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Aman ki duniya mein ye taqat bojh thi... par ab Itarim ke hamle se ye shakti vishwa ki dhaal banegi!",
        "text_speak": "शांति की दुनिया में यह ताक़त महज़ एक अभिशाप थी... लेकिन अब जब अंतरिक्ष के इतारिम देवता हमला कर रहे हैं, यही शक्ति दुनिया की ढाल बनेगी!"
    },
    {
        "panel": 20, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "LEVEL UP! Suho ne anuman lagaya: 'Ruler's Authority ka weight limit abhi lagbhag 10kg hai.'",
        "text_speak": "लेवल अप! सू-हो ने हिसाब लगाया: 'रूलर्स अथॉरिटी की वज़न सीमा अभी लगभग दस किलो के आसपास है।'"
    },

    # [ACT 6: SWARM SURROUNDING & EXPLOSIVE COUNTER]
    {
        "panel": 21, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Gooblin sena ne Suho ko charon taraf se gher liya! Daggers aur talwarein lehrane lagin!",
        "text_speak": "हथियारबंद राक्षसों के झुंड ने सू-हो को चारों तरफ से घेर लिया! मौत का घेरा कसता जा रहा था!"
    },
    {
        "panel": 22, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Centurion ka vaar pada! HP ghata: 160/190! Suho: 'Dard toh ho raha hai...'",
        "text_speak": "विशाल सेंचुरियन का भारी वार सू-हो पर लगा! एचपी गिरकर एक सौ साठ पर आ गया! सू-हो ने दाँत भींचे: 'दर्द तो हो रहा है...'"
    },
    {
        "panel": 23, "speaker": "suho", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "'LEKIN...!' Suho hawa mein uchhla aur talwaro ke toofan ki tarah kood pada!",
        "text_speak": "'लेकिन...!' सू-हो हवा में उछला और बिजली की तेज़ी से घूमते हुए दर्जनों गलों को एक साथ रेत दिया!"
    },

    # [ACT 7: THRILL OF BATTLE, RESILIENCE & 4X LEVEL UP]
    {
        "panel": 24, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ki aankhon mein neeli aag jali: 'Main kamzor hone se zyada... is yuddh mein zinda mehsoos kar raha hoon!'",
        "text_speak": "सू-हो की आँखों में नीली ज्वाला भड़क उठी: 'कमज़ोर और बेबस रहने से कहीं बेहतर है... मैं इस ख़ून-खराबे में खुद को ज़िंदा महसूस कर रहा हूँ!'"
    },
    {
        "panel": 25, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Lahu ki nadiyaan behne lagin! HP: 118... 84... aakhiri 53 bacha! Par Suho nahi ruka!",
        "text_speak": "चारों तरफ चीख-पुकार मच गई! एचपी घटकर एक सौ अठारह... चौरासी... और त्रेपन पर पहुँच गया! लेकिन सू-हो की तलवार नहीं थमी!"
    },
    {
        "panel": 26, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "TING! [SKILL: RESILIENCE LV. 1] hasil hui! Aur LEVEL UP 4 baar ek sath hua!",
        "text_speak": "टिंग! नया पैसिव स्किल अनलॉक: रेजिलिएंस लेवल वन! डिफेन्स बीस परसेंट बढ़ गया! और एक के बाद एक चार बार लेवल अप का धमाका हुआ!"
    },

    # [ACT 8: 4-HOUR SURVIVAL COMPLETE & SHADOW EXTRACTION RUNE]
    {
        "panel": 27, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Char ghante poore hue... charon taraf lashon ka dher laga tha. Khandar shant ho chuka tha.",
        "text_speak": "चार घंटे का वक़्त पूरा हुआ... ज़मीन पर सैकड़ों लाशों का ढेर लगा था और पूरा खंडर ख़ामोशी में डूब गया।"
    },
    {
        "panel": 28, "speaker": "beru", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho thak kar baitha tha. Beru khushi ke aansu bahate hue taliyaan baja raha tha: 'Mahaan Young Monarch!'",
        "text_speak": "हांफते हुए सू-हो मलबे पर बैठ गया। बेरू खुशी के आँसू बहाते हुए तालियाँ पीटने लगा: 'अद्भुत! मुझे अपने युवा मालिक पर पूरा भरोसा था!'"
    },
    {
        "panel": 29, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "TING! [QUEST REWARD: RUNE STONE — SHADOW EXTRACTION]! Beru ki aankhein chamak uthin!",
        "text_speak": "टिंग! सुनहरी विंडो खुली: क्वेस्ट रिवॉर्ड — रून स्टोन: शैडो एक्सट्रैक्शन! बेरू का रोम-रोम उत्साह से काँप उठा!"
    },
    {
        "panel": 30, "speaker": "suho", "emotion": "curious", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho muskuraya: 'Matlab main koi aam insaan nahi... main toh Shadow Silver Spoon lekar paida hua tha!'",
        "text_speak": "सू-हो मुस्कुराते हुए बोला: 'मतलब मैं कोई मामूली अन-अवेकन्ड नहीं... बल्कि शैडो सिल्वर स्पून मुँह में लेकर पैदा हुआ था!'"
    },

    # [ACT 9: LEARNING SHADOW EXTRACTION & COMMAND WORD]
    {
        "panel": 31, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "CRACK! Suho ne rune stone mutthi mein tod diya! Kaala mana uske jism mein sama gaya: [SHADOW EXTRACTION]!",
        "text_speak": "कड़क! सू-हो ने रून स्टोन को मुट्ठी में चूर-चूर कर दिया! अंधेरी जादुई ऊर्जा उसकी रगों में समा गई: शैडो एक्सट्रैक्शन सीख लिया गया!"
    },
    {
        "panel": 32, "speaker": "suho", "emotion": "serious", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho Centurion ki laash ke paas gaya: 'Kya main murdon ko saaye mein badal sakta hoon...?'",
        "text_speak": "सू-हो विशाल गोब्लिन सेंचुरियन की बेजान लाश के पास पहुँचा: 'तो क्या मैं सच में मुर्दों को अपने साए के सैनिकों में बदल सकता हूँ...?'"
    },
    {
        "panel": 33, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "System Window: [Shadow Extraction ke liye ek alag Command chuniye]! Beru dum saadh kar intezar karne laga!",
        "text_speak": "सिस्टम ने पूछा: 'शैडो एक्सट्रैक्शन के लिए एक विशेष कमांड चुनिए!' बेरू अपनी सांसें थामकर इंतज़ार करने लगा!"
    },

    # [ACT 10: THE ICONIC CLIMAX — ARISE!]
    {
        "panel": 34, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne socha: 'Agar ye aadesh hai... toh ise seedha aur teekha hona chahiye.'",
        "text_speak": "सू-हो ने गहरी सांस ली: 'अगर यह कोई आदेश है... तो इसे बिल्कुल सीधा और बेबाक होना चाहिए।'"
    },
    {
        "panel": 35, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho ne neeli bijli se bhara haath hawa mein uthaya! Zameen se kaale saaye phat pade: 'ARISE!'",
        "text_speak": "सू-हो ने नीली बिजली से चमकता हाथ आसमान की ओर उठाया! ज़मीन चीरते हुए काले साये दहाड़ उठे: 'अराइज़!' उठ खड़े हो!"
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# 100% HUMANOID STUDIO-MASTERED VOICE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
async def generate_humanoid_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    import edge_tts
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    raw_mp3 = out_wav.with_name(f"raw_{out_wav.stem}.mp3")
    ff = ffmpeg_bin()

    if speaker in ("beru", "monarch"):
        voice_id = "hi-IN-MadhurNeural"
        voice_rate = "+2%"
        voice_pitch = "-6Hz"   # Deep, booming shadow authority
        bass_gain = 6.5
    else:
        # Suho / Heroic Narrator
        voice_id = "hi-IN-MadhurNeural"
        voice_rate = "+10%"
        voice_pitch = "-2Hz"   # Youthful, heroic resonance
        bass_gain = 5.0

    for attempt in range(1, 4):
        try:
            comm = edge_tts.Communicate(text_speak, voice_id, rate=voice_rate, pitch=voice_pitch)
            await comm.save(str(raw_mp3))
            if raw_mp3.exists() and raw_mp3.stat().st_size > 1000:
                break
        except Exception:
            if attempt == 3:
                raise
            await asyncio.sleep(1.5)

    dsp_chain = (
        f"equalizer=f=130:t=q:w=1.2:g={bass_gain:.1f},"
        "equalizer=f=2600:t=q:w=1.4:g=3.5,"
        "equalizer=f=7200:t=q:w=2.0:g=-4.5,"
        "acompressor=threshold=-18dB:ratio=3.5:attack=10:release=80:makeup=2.8dB,"
        "atempo=1.12"
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
        "dark_drone":     f"aevalsrc='0.22*sin(2*PI*55*t)+0.16*sin(2*PI*82.4*t)+0.10*sin(2*PI*110*t)':d={d}:s=44100,volume=0.32",
        "dark_intense":   f"aevalsrc='0.28*sin(2*PI*45*t)+0.20*sin(2*PI*65*t)+0.12*sin(2*PI*130*t)+0.07*(random(0)-0.5)':d={d}:s=44100,volume=0.38",
        "epic_adventure": f"aevalsrc='0.20*sin(2*PI*130.8*t)+0.16*sin(2*PI*164.8*t)+0.14*sin(2*PI*196*t)+0.12*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.36",
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
        "[1:a]volume=0.22[m];"
        "[2:a]volume=0.30[s];"
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
Title: Solo Leveling Ragnarok Chapter 5 Subtitles
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

    # High CTR Header and Footer text
    try:
        font_large = ImageFont.truetype("arialbd.ttf", 64)
        font_sub = ImageFont.truetype("arialbd.ttf", 46)
        font_badge = ImageFont.truetype("arialbd.ttf", 36)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    # Red badge
    draw.rounded_rectangle([(40, 30), (450, 95)], radius=12, fill=(220, 20, 60))
    draw.text((60, 42), "SOLO LEVELING RAGNAROK", font=font_badge, fill=(255, 255, 255))

    # Main hook text
    draw.text((45, 540), "CHAPTER 5 : THE FIRST 'ARISE'!", font=font_large, fill=(0, 240, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    draw.text((45, 625), "SHADOW EXTRACTION UNLOCKED! 🔥", font=font_sub, fill=(255, 215, 0), stroke_width=3, stroke_fill=(0, 0, 0))

    canvas.save(str(out_thumb), quality=95)
    print(f"  ✓ High-CTR Thumbnail generated: {out_thumb}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
async def run_pipeline():
    ff = ffmpeg_bin()
    out_dir = ROOT / "output" / "solo_leveling_ragnarok_ch5"
    panels_dir = out_dir / "panels"
    cp_dir = out_dir / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 75)
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 5 — 100% HUMANOID VOICE ENGINE")
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

        print(f"\n[Scene {i:02d}/35] Panel {pid:03d} | Spk: {sc['speaker']} | Emo: {sc['emotion']}")

        # 1. 100% Humanoid Voice
        if not voice_wav.exists() or voice_wav.stat().st_size < 1000:
            print(f"  🎙️ Synthesizing 100% humanoid voice ({sc['speaker']})...")
            await generate_humanoid_voice(sc["text_speak"], sc["speaker"], sc["emotion"], voice_wav)

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
    print("  🎞️ CONCATENATING 35 SCENES & BURNING SUBTITLES")
    print("=" * 75)

    concat_list = out_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in scene_mp4s:
            escaped = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{escaped}'\n")

    raw_combined = out_dir / "solo_leveling_ragnarok_ch5_raw.mp4"
    print(f"  📦 Concatenating into {raw_combined}...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(raw_combined)
    ], check=True)

    # Subtitles
    ass_path = out_dir / "solo_leveling_ragnarok_ch5.ass"
    generate_ass_subtitles(SCENES[:len(scene_durs)], scene_durs, ass_path)
    print(f"  ✓ Dual-color subtitles saved: {ass_path}")

    # Burn subtitles
    final_output = out_dir / "solo_leveling_ragnarok_ch5_final.mp4"
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
    thumb_source = panels_dir / "panel_035.jpg"
    if not thumb_source.exists():
        thumb_source = panels_dir / "panel_024.jpg"
    generate_thumbnail(thumb_source, thumb_path)

    total_dur = float(probe(final_output)["format"]["duration"])
    size_mb = final_output.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 75)
    print(f"  🎉 SOLO LEVELING: RAGNAROK CHAPTER 5 RENDERED SUCCESSFULLY!")
    print(f"  📁 Video: {final_output}")
    print(f"  ⏱️ Duration: {total_dur:.1f}s (~{total_dur/60:.2f} min)")
    print(f"  💾 File Size: {size_mb:.1f} MB")
    print(f"  🖼️ Thumbnail: {thumb_path}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
