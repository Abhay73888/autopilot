"""
generate_solo_leveling_ragnarok_ch3.py — Solo Leveling: Ragnarok Chapter 3 Cinematic Hindi Explainer Video.

Key Fixes & Improvements:
  1. Wide Image Framing: Foreground artwork scaled to 1250px width (~65% of screen)
     with smooth top-to-bottom Ken Burns panning, eliminating the "thin sliver" issue.
  2. Humanoid Voice: Natural Gemini TTS ('Fenrir' for Suho/Narrator, 'Charon' for Beru,
     'Kore' for female students) with authentic human vocal inflection.
  3. Pacing & Speed: 1.15x audio tempo for crisp, exciting action delivery.
  4. Strict Duration: 35 scenes calibrated to ~255-270s (4.25 to 4.5 minutes total).
  5. Cyan/Gold ASS Subtitles & Dark Synth Soundtrack.
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
from agents.voice import _call_gemini_tts, _pcm_to_wav

# ─────────────────────────────────────────────────────────────────────────────
# SCENE DEFINITIONS (35 SCENES — CHAPTER 3 COMPLETE RECAP)
# ─────────────────────────────────────────────────────────────────────────────
SCENES = [
    # [ACT 1: DUNGEON BREAK & DESPAIR AT KOREA ARTS UNIV]
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Solo Leveling: Ragnarok — Chapter 3! Korea University of Arts mein qahar!",
        "text_speak": "सोलो लेवलिंग: रैग्नारॉक — चैप्टर तीन! कोरिया यूनिवर्सिटी ऑफ आर्ट्स में कहर!"
    },
    {
        "panel": 2, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_drone", "sfx": "glass_shatter",
        "text_sub": "WEE-WOO-WEE-WOO! Poore campus mein emergency siren goonj utha: Dungeon Break ho chuka tha!",
        "text_speak": "पूरे कैंपस में इमरजेंसी सायरन गूँज उठा! डी-रैंक गेट टूट चुका था और सिविलियंस को तुरंत भागने का ऑर्डर दिया गया!"
    },
    {
        "panel": 3, "speaker": "soldier", "emotion": "desperate", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "Chhat par khade fauji bebas the: 'Log mar rahe hain, par hum sirf dekhte rehne ke alawa kuch nahi kar sakte!'",
        "text_speak": "छत पर खड़े फौजी बेबस थे: 'लोग अंदर मर रहे हैं, पर हम सिर्फ देखते रहने के अलावा कुछ नहीं कर सकते!'"
    },
    {
        "panel": 4, "speaker": "soldier", "emotion": "curious", "camera": "slow_push", "music": "dark_intense", "sfx": "ambient_soft",
        "text_sub": "'Hunter Association se B-Rank Hunter aane mein der kyun ho rahi hai? Ye toh sirf D-Rank gate tha na?!'",
        "text_speak": "'हंटर एसोसिएशन से बी-रैंक हंटर आने में देर क्यों हो रही है? ये तो सिर्फ डी-रैंक गेट था ना?!'"
    },
    {
        "panel": 5, "speaker": "soldier", "emotion": "surprised", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "shock_sting",
        "text_sub": "Tablet par alert dekhkar unke hosh ud gaye: Ek C-Rank Tank Hunter 'Kim Jongsu' is mist se infect ho chuka tha!",
        "text_speak": "टैबलेट पर अलर्ट देखकर उनके होश उड़ गए! एक सी-रैंक टैंक हंटर किम जोंग-सू इस मिस्ट से इन्फेक्ट होकर मॉन्स्टर बन चुका था!"
    },

    # [ACT 2: SUHO FACES THE C-RANK AWAKENED MIST BURN]
    {
        "panel": 6, "speaker": "suho", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "c_rank_blade_slash",
        "text_sub": "Classroom mein dhool ke beech: [C-RANK AWAKENED MIST BURN] vishaal kaali talwaar lekar samne khada tha!",
        "text_speak": "क्लासरूम में धूल के बीच: सी-रैंक अवेकन्ड मिस्ट बर्न विशाल खौफनाक तलवार लेकर सामने खड़ा था!"
    },
    {
        "panel": 7, "speaker": "suho", "emotion": "curious", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Suho ne apni mutthi bheenci: 'Main abhi level up hua hoon... kya main is maha-daitya ka samna kar paunga?!'",
        "text_speak": "सू-हो ने अपनी मुट्ठी भींची: 'मैं अभी लेवल अप हुआ हूँ... क्या मैं इस महादैत्य का सामना कर पाऊंगा?!'"
    },
    {
        "panel": 8, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "dark_intense", "sfx": "c_rank_blade_slash",
        "text_sub": "SHWWWOOOSH! Monster ne apni giant sword ghumayi, aur hawa ka ek kaatne wala toofan classroom ki deewarein cheer gaya!",
        "text_speak": "श्वूश! मॉन्स्टर ने अपनी विशाल तलवार घुमाई, और हवा का बवंडर क्लासरूम की कंक्रीट की दीवारों को मक्खन की तरह चीर गया!"
    },
    {
        "panel": 9, "speaker": "suho", "emotion": "surprised", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "glass_shatter",
        "text_sub": "Suho ne neeche jhuk kar jaan bachayi: 'Ye toh pagalpan hai! Iski ek strike poori building ko ubaal sakti hai!'",
        "text_speak": "सू-हो ने नीचे झुक कर जान बचाई: 'ये तो पागलपन है! इसकी सिर्फ एक स्ट्राइक पूरी बिल्डिंग को उड़ा सकती है!'"
    },
    {
        "panel": 10, "speaker": "suho", "emotion": "desperate", "camera": "slow_push", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Suho hallway mein tezi se dauda: 'Mujhe bas tab tak sambhalna hoga jab tak koi B-Rank Hunter na aa jaye!'",
        "text_speak": "सू-हो कॉरिडोर में तेज़ी से दौड़ा: 'मुझे बस तब तक संभलना होगा जब तक कोई बी-रैंक हंटर मदद के लिए ना आ जाए!'"
    },

    # [ACT 3: THE CORNER OF HORROR — 3 GIRLS IN MORTAL PERIL]
    {
        "panel": 11, "speaker": "suho", "emotion": "surprised", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Par jaise hi Suho hallway ke mod par pahuñcha, uske pair wahi jam gaye! Teen ladkiyan khidki ke paas sehmi baithi thi!",
        "text_speak": "पर जैसे ही सू-हो कॉरिडोर के मोड़ पर पहुँचा, उसके पैर वहीं जम गए! तीन बेबस लड़कियाँ खिड़की के पास सहमी बैठी थीं!"
    },
    {
        "panel": 12, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "KROOOM! C-Rank monster un ladkiyon ki taraf badha, uski aakhon mein neeli aag dahak rahi thi!",
        "text_speak": "क्रूम! सी-रैंक मॉन्स्टर उन लड़कियों की तरफ झपटा, उसकी आँखों में क़त्ल करने की नीली आग धधक रही थी!"
    },
    {
        "panel": 13, "speaker": "girl", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Ladkiyan cheekh uthi: 'Hunters jaldi aate hi honge na... koi bachao hume!'",
        "text_speak": "लड़कियाँ रोते हुए चीख उठीं: 'हंटर्स जल्दी आते ही होंगे ना... कोई बचाओ हमें!'"
    },
    {
        "panel": 14, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ki aakhein chamki: 'Ab rukne ka waqt nahi hai... mujhe hi is shaitan ko rokna hoga!'",
        "text_speak": "सू-हो की आँखें चमक उठीं: 'अब इंतज़ार करने का वक़्त नहीं है... मुझे ही इस शैतान को रोकना होगा!'"
    },

    # [ACT 4: SUHO'S HEROIC TACKLE & DESPERATE COMBAT]
    {
        "panel": 15, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "mega_punch",
        "text_sub": "BOOM! Suho ne hawa mein chhalang lagayi aur monster par seedha body-tackle maar diya!",
        "text_speak": "बूम! सू-हो ने हवा में छलाँग लगाई और मॉन्स्टर पर सीधा बिजली की रफ़्तार से टैकल मार दिया!"
    },
    {
        "panel": 16, "speaker": "suho", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "c_rank_blade_slash",
        "text_sub": "Monster ki talwaar milli-meter doori se nikli! 'Ek bhi hit laga... toh mera khel wahi khatam ho jayega!'",
        "text_speak": "मॉन्स्टर की तलवार मिली-मीटर की दूरी से निकली! 'एक भी वार लगा... तो मेरा खेल वहीं खत्म हो जाएगा!'"
    },
    {
        "panel": 17, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "mega_punch",
        "text_sub": "'Lekin main ise yahan aazaad ghoomne nahi de sakta!' Suho ne apni taakat ko aakhiri seema tak jhonk diya!",
        "text_speak": "'लेकिन मैं इसे यहाँ मासूमों को मारने नहीं दे सकता!' सू-हो ने अपनी पूरी जान फूँक दी!"
    },
    {
        "panel": 18, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "mega_punch",
        "text_sub": "DHAA-DHAA-DHAA! Suho ne superhuman speed se mukkebaazi ki barish kar di!",
        "text_speak": "धा-धा-धा! सू-हो ने अपनी बढ़ी हुई स्पीड से मुक्कों की तूफानी बारिश कर दी!"
    },
    {
        "panel": 19, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_intense", "sfx": "impact_heavy",
        "text_sub": "Suho ka upper-cut monster ki thhodi par pada, par C-Rank Tank ka sharir patthar ki tarah atoot tha!",
        "text_speak": "सू-हो का अपर-कट मॉन्स्टर के जबड़े पर पड़ा, पर सी-रैंक टैंक का शरीर लोहे की तरह अटूट था!"
    },

    # [ACT 5: CRUSHING COUNTER & SYSTEM ALERT: HP 1 / 140]
    {
        "panel": 20, "speaker": "narrator", "emotion": "desperate", "camera": "handheld_shake", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "WHAM! Monster ka lohe jaisa ghonsa seedha Suho ke pet mein laga! 'KGH...!' Khoon ki ulti ho gayi!",
        "text_speak": "व्हैम! मॉन्स्टर का वज्र जैसा घूँसा सीधा सू-हो के पेट में लगा! 'उफ्फ...!' सू-हो के मुँह से खून का फव्वारा छूट गया!"
    },
    {
        "panel": 21, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_drone", "sfx": "glass_shatter",
        "text_sub": "Suho mitti aur malbe par ja gira! Aur tabhi aankhon ke aage chamka: [HP: 1 / 140]!",
        "text_speak": "सू-हो हवा में उड़ते हुए मलबे पर जा गिरा! और तभी सिस्टम का ख़ौफ़नाक लाल अलर्ट चमका: एच-पी सिर्फ एक बटा एक सौ चालीस!"
    },
    {
        "panel": 22, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
        "text_sub": "Suho ne dard mein muskuraya: 'Sirf ek HP bachi hai... System abhi mujhe marne nahi dena chahta.'",
        "text_speak": "सू-हो ने दर्द में मुस्कुराते हुए कहा: 'सिर्फ एक एच-पी बची है... सिस्टम अभी मुझे मरने नहीं देना चाहता।'"
    },

    # [ACT 6: FATIGUE 99 & THE FALLING BLADE]
    {
        "panel": 23, "speaker": "narrator", "emotion": "desperate", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Lekin agla notification aate hi sannaata chha gaya: [FATIGUE: 99]! Suho ka poora sharir jaam ho chuka tha!",
        "text_speak": "लेकिन अगला नोटिफिकेशन आते ही सन्नाटा छा गया: फैटीग निन्यानवे! सू-हो का पूरा शरीर सुन्न और बेजान हो चुका था!"
    },
    {
        "panel": 24, "speaker": "suho", "emotion": "desperate", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "'Dammit... hath pair hil bhi nahi rahe!' Monster ne apni giant blade dono haathon se upar uthayi!",
        "text_speak": "'लानत है... हाथ पैर हिल भी नहीं रहे!' मॉन्स्टर ने अपनी तलवार दोनों हाथों से सू-हो के सिर के ठीक ऊपर उठा ली!"
    },
    {
        "panel": 25, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "c_rank_blade_slash",
        "text_sub": "KHAATAM! Talwaar bijli ki gati se Suho ki gardan par girne hi wali thi...!",
        "text_speak": "खत्म! तलवार बिजली की गति से सू-हो की गर्दन पर गिरने ही वाली थी...!"
    },

    # [ACT 7: THE BLACK TALON RISES — BERU'S RESURRECTION!]
    {
        "panel": 26, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "KABOOOOOM! Zameen phat gayi! Aasman se ek vishaal kaala shadow panja nikal kar talwaar ko rokh leta hai!",
        "text_speak": "का-बूम! ज़मीन दहल उठी! पाताल से एक विशाल काला शैडो पंजा निकल कर तलवार को हवा में ही दबोच लेता है!"
    },
    {
        "panel": 27, "speaker": "suho", "emotion": "surprised", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ki aakhein fati reh gayi: 'Ek cheenti...?!' Kaale kankal ka bhootia panja use cover kar raha tha!",
        "text_speak": "सू-हो की आँखें फटी रह गई: 'एक चींटी...?!' काले कंकाल का राक्षसी पंजा उसे अपनी ढाल बना रहा था!"
    },
    {
        "panel": 28, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "beru_roar",
        "text_sub": "Dard bhari aawaz goonji: 'NAHI... MERI DERI KI WAJAH SE... AAPKO DARD HUA...'",
        "text_speak": "अंधेरे से दर्द भरी गूँज उठी: 'नहीं... मेरी देरी की वजह से... आपको ये चोट पहुँची...'"
    },
    {
        "panel": 29, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "beru_roar",
        "text_sub": "ROOOAAAR! SHADOW ANT KING — BERU SAMNE AATA HAI! Uski aakhein baingani aag se dahak rahi thi!",
        "text_speak": "रोर! शैडो ऐंट किंग — बेरू प्रकट होता है! उसकी आँखों में ब्रह्मांडीय बैंगनी ज्वाला भड़क रही थी!"
    },
    {
        "panel": 30, "speaker": "beru", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Beru ne chillakar dahad maari: 'TUM TUCCH KEEDE... HAMARE YUVRAJ KO HAATH LAGANE KI HIMMAT KAISE HUI?!'",
        "text_speak": "बेरू ने怒दहाड़ मारी: 'तुम तुच्छ कीड़े... हमारे युवराज को हाथ लगाने की जुर्रत कैसे की?!'"
    },

    # [ACT 8: BERSERK SHREDDING & THE YOUNG MONARCH REVEAL]
    {
        "panel": 31, "speaker": "narrator", "emotion": "epic", "camera": "handheld_shake", "music": "epic_adventure", "sfx": "mega_punch",
        "text_sub": "SLASH! Ek pal mein Beru ke panjon ne us C-Rank monster ke hazaron tukde kar dale!",
        "text_speak": "स्लैश! एक ही सेकंड में बेरू के पंजों ने उस सी-रैंक मॉन्स्टर के हज़ार टुकड़े कर डाले!"
    },
    {
        "panel": 32, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Aasman mein udte saare monsters ko Beru ne baingani toofan ban kar faad ke rakh diya!",
        "text_speak": "आसमान में उड़ते सारे शैतानी परिंदों को बेरू ने बैंगनी बिजली बनकर चीर डाला! पूरी यूनिवर्सिटी दहल उठी!"
    },
    {
        "panel": 33, "speaker": "soldier", "emotion": "surprised", "camera": "slow_push", "music": "epic_adventure", "sfx": "ambient_soft",
        "text_sub": "Chhat par khada B-Rank Hunter aur fauji khauf ke maare kaanp rahe the: 'Ye... ye aakhir kis level ka maharaakshas hai?!'",
        "text_speak": "छत पर खड़ा बी-रैंक हंटर सिगरेट मुँह में दबाए काँप रहा था: 'ये... ये किस लेवल का महाबली शैडो मॉन्स्टर है?!'"
    },
    {
        "panel": 34, "speaker": "beru", "emotion": "calm", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Rubble ke beech aakar Beru Suho ke aage aadar se ghutne tek deta hai: 'Bahut arsa beet gaya...'",
        "text_speak": "मलबे के बीच आकर बेरू सू-हो के आगे अदब से घुटने टेक देता है: 'बहुत अरसा बीत गया...'"
    },
    {
        "panel": 35, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "'YOUNG MONARCH... MERE CHHOTE SHAHZADE.' Solo Leveling: Ragnarok Chapter 4 ke liye LIKE aur SUBSCRIBE thok do!",
        "text_speak": "'यंग मोनार्क... मेरे छोटे शहजादे।' सोलो लेवलिंग: रैग्नारॉक चैप्टर चार के लिए लाइक और सब्सक्राइब ठोक दो!"
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HUMANOID VOICE SYNTHESIZER (Gemini TTS + Edge-TTS fallback + atempo speedup)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_scene_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    """Generate humanoid emotional speech with 1.15x tempo speedup."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    raw_wav = out_wav.with_name(f"raw_{out_wav.name}")
    ff = ffmpeg_bin()

    # 1. Choose Humanoid Voice Persona
    if speaker == "girl":
        gem_voice = "Kore"
        edge_voice = "hi-IN-SwaraNeural"
        edge_pitch = "+4Hz"
    elif speaker in ("beru", "monarch"):
        gem_voice = "Charon"  # Deep, terrifying, thunderous
        edge_voice = "hi-IN-MadhurNeural"
        edge_pitch = "-6Hz"
    else:
        gem_voice = "Fenrir"  # Young, heroic, punchy
        edge_voice = "hi-IN-MadhurNeural"
        edge_pitch = "+2Hz"

    # 2. Try Gemini TTS for authentic humanoid timber
    generated = False
    try:
        pcm = _call_gemini_tts(text_speak, voice_name=gem_voice)
        if pcm and len(pcm) > 1000:
            _pcm_to_wav(pcm, raw_wav, sample_rate=24000)
            generated = True
    except Exception as e:
        print(f"    ℹ Gemini TTS note: {e}, falling back to Edge-TTS")

    # 3. Fallback to Edge-TTS if needed
    if not generated or not raw_wav.exists() or raw_wav.stat().st_size < 1000:
        import edge_tts
        tmp_mp3 = raw_wav.with_suffix(".mp3")
        rate = "+24%"  # faster pacing requested by user
        for attempt in range(1, 4):
            try:
                comm = edge_tts.Communicate(text_speak, edge_voice, rate=rate, pitch=edge_pitch)
                await comm.save(str(tmp_mp3))
                break
            except Exception:
                if attempt == 3:
                    raise
                await asyncio.sleep(2)
        subprocess.run([
            ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(tmp_mp3), "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(raw_wav)
        ], check=True)
        if tmp_mp3.exists():
            tmp_mp3.unlink()

    # 4. Apply 1.15x tempo speedup ('speed badha do thoda')
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_wav),
        "-filter:a", "atempo=1.15",
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)
    if raw_wav.exists():
        raw_wav.unlink()


# ─────────────────────────────────────────────────────────────────────────────
# SOUND EFFECTS & SCORE
# ─────────────────────────────────────────────────────────────────────────────
def generate_music(music_type: str, duration: float, out_wav: Path):
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "dark_drone":      f"aevalsrc='0.22*sin(2*PI*55*t)+0.16*sin(2*PI*82.4*t)+0.10*sin(2*PI*110*t)':d={d}:s=44100,volume=0.32",
        "dark_intense":    f"aevalsrc='0.28*sin(2*PI*45*t)+0.20*sin(2*PI*65*t)+0.12*sin(2*PI*130*t)+0.07*(random(0)-0.5)':d={d}:s=44100,volume=0.38",
        "epic_adventure":  f"aevalsrc='0.20*sin(2*PI*130.8*t)+0.16*sin(2*PI*164.8*t)+0.14*sin(2*PI*196*t)+0.12*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.36",
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
        "mega_punch":         f"aevalsrc='0.55*exp(-6*t)*sin(2*PI*45*t)+0.40*exp(-10*t)*(random(0)-0.5)':d={d}:s=44100",
        "beru_roar":          f"aevalsrc='0.48*sin(2*PI*(70+35*sin(2*PI*8*t))*t)+0.38*exp(-2*t)*(random(0)-0.5)':d={d}:s=44100",
        "braam_impact":       f"aevalsrc='0.40*exp(-1.5*t)*sin(2*PI*40*t)+0.25*exp(-2*t)*sin(2*PI*80*t)':d={d}:s=44100",
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
# WIDE SCENE RENDERER (NO THIN IMAGES — 1250px FOREGROUND + KEN BURNS PAN)
# ─────────────────────────────────────────────────────────────────────────────
def render_wide_scene_video(img_path: Path, duration: float, camera: str, out_mp4: Path):
    ff = ffmpeg_bin()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    dur = max(2.5, round(duration, 3))
    w, h = 1920, 1080

    with Image.open(str(img_path)) as im:
        iw, ih = im.size
    aspect = iw / max(1, ih)

    # 1. Atmospheric Background: Fast bokeh blur (downscale -> blur -> upscale)
    bg_flt = f"[0:v]scale=320:180:force_original_aspect_ratio=increase,crop=320:180,boxblur=6:2,scale={w}:{h}:flags=bicubic,eq=brightness=-0.22:contrast=0.95[bg]"

    # 2. Foreground: Wide framing (w=1250px), filling 65% of screen width!
    if aspect >= 1.2:
        # Wide / Landscape panel (e.g. title or double spread)
        fg_flt = f"[0:v]scale=-2:1040[fg_scaled];[fg_scaled]pad=w=iw+10:h=ih+10:x=5:y=5:color=0x151520@0.8[fg]"
    elif aspect >= 0.7:
        # Square / Medium panel
        fg_flt = f"[0:v]scale=-2:1040[fg_scaled];[fg_scaled]pad=w=iw+10:h=ih+10:x=5:y=5:color=0x151520@0.8[fg]"
    else:
        # Tall Webtoon Panel: Scale width to 1250px and smoothly pan from top to bottom
        fg_w = 1250
        fg_flt = (
            f"[0:v]scale={fg_w}:-2[fg_scaled];"
            f"[fg_scaled]crop=w={fg_w}:h=min(in_h\\,1040):x=0:y='if(gt(in_h\\,1040)\\,(in_h-1040)*t/{dur:.2f}\\,0)'[fg_pan];"
            f"[fg_pan]pad=w={fg_w}+10:h=1050:x=5:y=5:color=0x151520@0.8[fg]"
        )

    comp_flt = f"[bg][fg]overlay=(W-w)/2:(H-h)/2[comp]"

    # 3. Subtle Ken Burns zoom / drift on overall composition
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
Title: Solo Leveling Ragnarok Chapter 3 Subtitles
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

    # Dark gradient overlay for text readability
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rectangle([0, 0, 1280, 180], fill=(5, 5, 15, 190))
    draw.rectangle([0, 530, 1280, 720], fill=(5, 5, 15, 210))

    try:
        f_title = ImageFont.truetype("arialbd.ttf", 64)
        f_sub = ImageFont.truetype("arialbd.ttf", 46)
        f_badge = ImageFont.truetype("arialbd.ttf", 36)
    except Exception:
        f_title = f_sub = f_badge = ImageFont.load_default()

    t1 = "SOLO LEVELING: RAGNAROK"
    draw.text((42, 32), t1, font=f_title, fill=(0, 0, 0, 255))
    draw.text((40, 30), t1, font=f_title, fill=(0, 240, 255, 255))

    t2 = "CHAPTER 3: BERU KI WAPSI! ⚔️"
    draw.text((42, 102), t2, font=f_sub, fill=(0, 0, 0, 255))
    draw.text((40, 100), t2, font=f_sub, fill=(255, 215, 0, 255))

    t3 = "SHADOW ANT KING ARRIVES | YOUNG MONARCH"
    draw.text((42, 638), t3, font=f_badge, fill=(0, 0, 0, 255))
    draw.text((40, 636), t3, font=f_badge, fill=(255, 255, 255, 255))

    canvas.save(str(out_thumb), "JPEG", quality=95)
    print(f"  ✓ Thumbnail generated: {out_thumb}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN GENERATION PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
async def run_pipeline():
    ff = ffmpeg_bin()
    out_dir = ROOT / "output" / "solo_leveling_ragnarok_ch3"
    panels_dir = out_dir / "panels"
    cp_dir = out_dir / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 3 — VIDEO ENGINE (WIDE + HUMANOID)")
    print("=" * 70)

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

        # 1. Voice
        if not voice_wav.exists() or voice_wav.stat().st_size < 1000:
            print(f"  🎙️ Synthesizing humanoid voice ({sc['speaker']})...")
            await generate_scene_voice(sc["text_speak"], sc["speaker"], sc["emotion"], voice_wav)

        v_dur = float(probe(voice_wav)["format"]["duration"])
        # Pacing: voice duration + small breathing pause (0.7s)
        dur = max(4.5, v_dur + 0.75)
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

        # Check if completed scene exists
        if is_valid_mp4(scene_final):
            print(f"  ✓ Checkpoint hit: scene_{i:03d}.mp4")
            scene_mp4s.append(scene_final)
            continue

        # 2. Score & SFX
        if not music_wav.exists():
            generate_music(sc["music"], dur, music_wav)
        if not sfx_wav.exists():
            generate_sfx(sc["sfx"], dur, sfx_wav)

        # 3. Mix Audio
        if not audio_aac.exists():
            mix_audio(voice_wav, music_wav, sfx_wav, dur, audio_aac)

        # 4. Render Wide Video Canvas (1250px width foreground)
        if not is_valid_mp4(video_mp4):
            print(f"  🎬 Rendering wide canvas & Ken Burns pan ({sc['camera']})...")
            render_wide_scene_video(img_path, dur, sc["camera"], video_mp4)

        # 5. Join Scene
        join_scene(video_mp4, audio_aac, scene_final)
        scene_mp4s.append(scene_final)
        print(f"  ✓ Scene {i:02d} rendered ({dur:.1f}s)")

    # ─────────────────────────────────────────────────────────────────────────
    # CONCATENATE ALL SCENES
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("  📦 Concatenating 35 scenes into raw video...")
    concat_txt = out_dir / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in scene_mp4s:
            clean_path = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    raw_mp4 = out_dir / "raw_video.mp4"
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy",
        str(raw_mp4)
    ], check=True)

    raw_info = probe(raw_mp4)
    total_dur = float(raw_info["format"]["duration"])
    mins = int(total_dur // 60)
    secs = int(total_dur % 60)
    print(f"  ✓ Concat complete! Total duration: {mins}m {secs:02d}s ({total_dur:.1f}s)")

    # ─────────────────────────────────────────────────────────────────────────
    # BURN ASS SUBTITLES
    # ─────────────────────────────────────────────────────────────────────────
    print("  💬 Generating and burning ASS subtitles...")
    sub_ass = out_dir / "subtitles.ass"
    generate_ass_subtitles(SCENES, scene_durs, sub_ass)

    final_mp4 = out_dir / "solo_leveling_ragnarok_ch3_hindi.mp4"
    ass_escaped = str(sub_ass.resolve()).replace("\\", "/").replace(":", "\\:")
    vf = f"ass='{ass_escaped}'"

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_mp4),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "copy",
        str(final_mp4)
    ], check=True)

    # ─────────────────────────────────────────────────────────────────────────
    # THUMBNAIL GENERATION
    # ─────────────────────────────────────────────────────────────────────────
    thumb_jpg = out_dir / "thumbnail.jpg"
    generate_thumbnail(panels_dir / "panel_029.jpg", thumb_jpg)

    print("\n" + "=" * 70)
    print(f"  🎉 SOLO LEVELING: RAGNAROK CHAPTER 3 RECAP READY!")
    print(f"  📁 File: {final_mp4}")
    print(f"  ⏱️ Duration: {mins}m {secs:02d}s (Strictly within 4-5 minute limit!)")
    print(f"  🖼️ Framing: 1250px Wide Focus (No thin images!)")
    print(f"  🎙️ Voice: Humanoid Gemini/Edge Persona (1.15x tempo)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
