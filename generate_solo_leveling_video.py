"""
generate_solo_leveling_video.py — Solo Leveling Chapter 1: Cinematic Hindi Explainer Video.

A full human-like narrated cinematic video experience from the 58-page PDF:
  • High-res page images with blurred-background 1080p widescreen composition
  • Dynamic Ken Burns camera movements (slow push, slow pull, tilt, shake, sudden zoom)
  • Human-like Hindi character voice acting (Jin-Woo, Ju-Hee, Kim, Song, Narrator)
  • 3-track audio mix (voice + procedural mood score + SFX)
  • Perfectly synced ASS subtitles
  • Checkpoint system: caches every rendered scene so interruption resumes seamlessly
  • Final 1080p MP4 compilation
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
# SCENE DEFINITIONS (58 Pages of Solo Leveling Chapter 1)
# ─────────────────────────────────────────────────────────────────────────────
SCENES_DATA = [
    # [PROLOGUE: THE TEMPLE OF DEATH]
    {"page": 1, "speaker": "jinwoo", "emotion": "desperate", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
     "text": "Mera naam Sung Jin-Woo hai... aur lagta hai, meri kahani yahin khatam hone wali hai."},
    {"page": 2, "speaker": "narrator", "emotion": "sad", "camera": "breathing", "music": "dark_drone", "sfx": "heartbeat_low",
     "text": "Ek aam E-Rank Hunter, jise poori duniya mazaak samajhti thi..."},
    {"page": 3, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
     "text": "Khoon se lathpath, tooti hui talwar ke saath zameen par gira hua... Jin-Woo saans lene ke liye tadap raha tha."},
    {"page": 4, "speaker": "narrator", "emotion": "fearful", "camera": "tilt_down", "music": "dark_drone", "sfx": "blood_impact",
     "text": "Uska pair buri tarah kaat diya gaya tha... charon taraf sirf laal khoon ka samandar faila tha."},
    {"page": 5, "speaker": "jinwoo", "emotion": "desperate", "camera": "slow_push", "music": "dark_drone", "sfx": "heartbeat_low",
     "text": "Hunters Association ka sabse kamzor shaks... The Weakest Hunter of All Mankind!"},
    {"page": 6, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_pull", "music": "dark_intense", "sfx": "braam_impact",
     "text": "Aur uske samne khadi thi... patthar ki aisi vishaal moortiyan, jinki neeli aakhein maut ka paighaam de rahi thi!"},
    {"page": 7, "speaker": "jinwoo", "emotion": "fearful", "camera": "breathing", "music": "dark_intense", "sfx": "heartbeat_low",
     "text": "Maine kabhi nahi socha tha... ki mere saath aisa hoga... kabhi nahi!"},
    {"page": 8, "speaker": "narrator", "emotion": "desperate", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "whoosh_energy",
     "text": "Upar se ek vishaal bhaar-bharkam barcha seedha uski taraf gir raha tha!"},
    {"page": 9, "speaker": "jinwoo", "emotion": "angry", "camera": "handheld_shake", "music": "dark_intense", "sfx": "impact_heavy",
     "text": "Kambakht... kya main sach mein yahin marne wala hoon?!"},
    {"page": 10, "speaker": "narrator", "emotion": "dramatic", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "impact_heavy",
     "text": "Maha-vinaashkaari prahaar! Ek jhatke mein sab kuch tabah!"},
    {"page": 11, "speaker": "narrator", "emotion": "fearful", "camera": "handheld_shake", "music": "dark_intense", "sfx": "blood_impact",
     "text": "Aur charon taraf sirf andhera... aur khoon ki cheekh!"},

    # [ACT 1: THE TITLE & BACKSTORY]
    {"page": 12, "speaker": "narrator", "emotion": "excited", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
     "text": "Lekin ye ant nahi... ye toh shuruat hai Solo Leveling ki! Aakhir Jin-Woo is maut ke kuen tak kaise pahuncha?"},
    {"page": 13, "speaker": "narrator", "emotion": "calm", "camera": "pan_right", "music": "city_ambient", "sfx": "ambient_soft",
     "text": "Chaliye chalte hain kuch ghante pehle... Seoul, South Korea ke ek aam din par."},
    # Page 14 is ad -> skipped in processing
    {"page": 15, "speaker": "jinwoo", "emotion": "calm", "camera": "slow_push", "music": "city_ambient", "sfx": "ambient_soft",
     "text": "Mera naam Sung Jin-Woo hai. Agar meri thodi si taakat aur regeneration ko chhod dein..."},
    {"page": 16, "speaker": "jinwoo", "emotion": "sad", "camera": "tilt_down", "music": "city_ambient", "sfx": "ambient_soft",
     "text": "...toh khud ko Hunter kehna bhi sharmnaak lagta hai."},
    {"page": 17, "speaker": "jinwoo", "emotion": "sad", "camera": "slow_pull", "music": "sad_piano", "sfx": "ambient_soft",
     "text": "Har mission par chot khana, aur maut ke muh se baal-baal bachna... meri roz ki aadat ban chuki hai."},
    {"page": 18, "speaker": "jinwoo", "emotion": "calm", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
     "text": "Maut se khelne ka ye dhandha... main apni khushi se nahi kar raha."},
    {"page": 19, "speaker": "narrator", "emotion": "curious", "camera": "pan_left", "music": "mystery_ambient", "sfx": "ambient_soft",
     "text": "Seoul ki ek construction site par achanak ek Dungeon Gate khul gaya tha."},
    {"page": 20, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_push", "music": "mystery_ambient", "sfx": "portal_hum",
     "text": "Dusri duniya ka raasta... ek aisi jagah jahan se ya toh daulat milti hai, ya phir sirf maut!"},
    {"page": 21, "speaker": "jinwoo", "emotion": "sad", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
     "text": "Meri bimaar maa ke aspatal ke bill chukane ke liye... mere jaise aam ladke ke paas Hunter banne ke alawa koi raasta nahi tha."},

    # [ACT 2: THE HUNTER CAMP & THE RUNNING GAG]
    {"page": 22, "speaker": "narrator", "emotion": "calm", "camera": "pan_right", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Gate ke bahar ek coffee truck par hunters ikattha ho rahe the."},
    {"page": 23, "speaker": "bak", "emotion": "happy", "camera": "sudden_zoom", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Arrey Kim! Bahut din baad dikhe bhai!"},
    {"page": 24, "speaker": "narrator", "emotion": "calm", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Ye Bak tha... ek purana hunter jo raiding chhod chuka tha."},
    {"page": 25, "speaker": "bak", "emotion": "happy", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Meri biwi doosre bachhe se pregnant hai yaar... kharche badh gaye hain, isliye wapas aana pada!"},
    {"page": 26, "speaker": "kim", "emotion": "calm", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Sahi baat hai bhai... zinda rehne ke liye raid se badhkar paisa kahan milega!"},
    {"page": 27, "speaker": "bak", "emotion": "nervous", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Bas darr lag raha hai... itne lambe break ke baad meri skills aur kharab na ho gayi hon."},
    {"page": 28, "speaker": "kim", "emotion": "excited", "camera": "sudden_zoom", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Arrey dekho, Sung Jin-Woo aa gaya! Aao Sung, shukr hai tum aa gaye!"},
    {"page": 29, "speaker": "jinwoo", "emotion": "calm", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Namaste Mr. Kim... aaj bhi main aap logon ke bharose hi hoon, haha!"},
    {"page": 30, "speaker": "kim", "emotion": "happy", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Suno Sung, kuch khaya peeya ya nahi?"},
    {"page": 31, "speaker": "bak", "emotion": "curious", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
     "text": "Kim bhai... ye ladka koi zabardast high-rank hunter hai kya? Sab isse dekh kar itne khush kyun hain?"},
    {"page": 32, "speaker": "kim", "emotion": "excited", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
     "text": "Hehehe... tumhare jaane ke baad aaya hai ye. Iska nickname pata hai kya hai?"},
    {"page": 33, "speaker": "kim", "emotion": "happy", "camera": "sudden_zoom", "music": "curious_ambient", "sfx": "shock_sting",
     "text": "Duniya ka sabse kamzor hunter! The World's Weakest!"},
    {"page": 34, "speaker": "bak", "emotion": "surprised", "camera": "slow_push", "music": "curious_ambient", "sfx": "ambient_soft",
     "text": "Hain? Sabse kamzor? Mujhe laga koi S-Rank legend hoga!"},
    {"page": 35, "speaker": "kim", "emotion": "happy", "camera": "pan_right", "music": "curious_ambient", "sfx": "ambient_soft",
     "text": "Bhai ye E-Rank dungeon mein bhi ghayal ho jata hai! Agar ye raid mein hai, matlab dungeon aasaan hoga, isliye sab khush hain!"},
    {"page": 36, "speaker": "jinwoo", "emotion": "calm", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Main tum budhon ki saari baatein peeche khada sun raha hoon... kya kismat hai meri!"},
    {"page": 37, "speaker": "narrator", "emotion": "sad", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
     "text": "Jin-Woo thoda mood theek karne coffee lene gaya... lekin wahan bhi bad-kismati ne peechha nahi chhoda!"},
    # Page 38: Ad cropped out
    {"page": 38, "speaker": "jinwoo", "emotion": "sad", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
     "crop_bottom": True, "text": "Coffee bhi khatam ho gayi... mera din hi kharab hai."},
    {"page": 39, "speaker": "jinwoo", "emotion": "sad", "camera": "slow_push", "music": "sad_piano", "sfx": "ambient_soft",
     "text": "Koi baat nahi bhaiya... aadat hai mujhe."},

    # [ACT 3: JU-HEE THE HEALER]
    {"page": 40, "speaker": "juhee", "emotion": "surprised", "camera": "sudden_zoom", "music": "soft_strings", "sfx": "shock_sting",
     "text": "Jin-Woo!! Tum phir se chot kha kar aa gaye?!"},
    {"page": 41, "speaker": "narrator", "emotion": "happy", "camera": "slow_push", "music": "soft_strings", "sfx": "ambient_soft",
     "text": "Ye thi Miss Ju-Hee... ek khoobsurat B-Rank healer, jo hamesha Jin-Woo ki fikr karti thi."},
    {"page": 42, "speaker": "juhee", "emotion": "angry", "camera": "slow_push", "music": "soft_strings", "sfx": "ambient_soft",
     "text": "Apne chehre ka haal dekho! Har baar hunting par jaate ho aur zakhmi hokar aate ho!"},
    {"page": 43, "speaker": "juhee", "emotion": "sad", "camera": "slow_pull", "music": "soft_strings", "sfx": "ambient_soft",
     "text": "Sach sach batao... hospital tak jana pada tha na tumhe pichhli baar?"},
    {"page": 44, "speaker": "jinwoo", "emotion": "sad", "camera": "slow_push", "music": "soft_strings", "sfx": "ambient_soft",
     "text": "Haan... E-Rank dungeon tha, aur poori team mein akela main hi zakhmi hua tha."},
    {"page": 45, "speaker": "juhee", "emotion": "angry", "camera": "slow_push", "music": "soft_strings", "sfx": "ambient_soft",
     "text": "Woh log healer tak nahi le gaye?! Apni suraksha ke ghamand mein tumhe akele chhod diya?!"},
    {"page": 46, "speaker": "jinwoo", "emotion": "sad", "camera": "slow_push", "music": "soft_strings", "sfx": "ambient_soft",
     "text": "Galti unki nahi hai Miss Ju-Hee... main hi kamzor hoon. Meri aukaat hi aisi hai."},
    {"page": 47, "speaker": "juhee", "emotion": "calm", "camera": "tilt_down", "music": "soft_strings", "sfx": "ambient_soft",
     "text": "Chalo ab... Gate mein jaane ka waqt ho gaya hai. Sambhal kar rehna mere paas."},

    # [ACT 4: THE RAID COMMENCES — INTO THE ABYSS]
    {"page": 48, "speaker": "narrator", "emotion": "curious", "camera": "slow_pull", "music": "mystery_ambient", "sfx": "portal_hum",
     "text": "Sabhi hunters vishaal neeli roshni wale Gate ke samne jama ho gaye."},
    {"page": 49, "speaker": "narrator", "emotion": "dramatic", "camera": "slow_push", "music": "mystery_ambient", "sfx": "ambient_soft",
     "text": "Ek anubhavi veteran hunter, Mr. Song Chi-Yul aage aaye."},
    {"page": 50, "speaker": "song", "emotion": "calm", "camera": "slow_push", "music": "mystery_ambient", "sfx": "ambient_soft",
     "text": "Dosto! Is raid mein sabse high rank mera hai... agar aap sab chahein, toh main party leader ban sakta hoon."},
    {"page": 51, "speaker": "hunter", "emotion": "excited", "camera": "pan_right", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Haan Mr. Song! Aapke rehte hume kisi baat ka darr nahi! Let's go!"},
    {"page": 52, "speaker": "jinwoo", "emotion": "happy", "camera": "slow_push", "music": "light_warm", "sfx": "ambient_soft",
     "text": "Mr. Song, kripya hamara khayal rakhiyega."},
    {"page": 53, "speaker": "song", "emotion": "dramatic", "camera": "slow_pull", "music": "epic_adventure", "sfx": "whoosh_energy",
     "text": "Theek hai team... Dungeon ke andar dakhil hote hain!"},
    {"page": 54, "speaker": "kim", "emotion": "happy", "camera": "pan_left", "music": "epic_adventure", "sfx": "ambient_soft",
     "text": "Chalo dosto! Aur Sung Jin-Woo... peeche rehkar dobara zakhmi mat ho jana, hahah!"},
    {"page": 55, "speaker": "song", "emotion": "calm", "camera": "slow_push", "music": "epic_adventure", "sfx": "ambient_soft",
     "text": "Chalo Jin-Woo... himmat mat haarna."},
    {"page": 56, "speaker": "jinwoo", "emotion": "hopeful", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "ambient_soft",
     "text": "Aaj main apna sabse behtar koshish karunga! Chahe kuch bhi ho jaye!"},
    {"page": 57, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_drone", "sfx": "portal_hum",
     "text": "Lekin Jin-Woo ko ye zara bhi andaza nahi tha... ki is Gate ke andar uska intezaar maut ka sabse bhayanak mandir kar raha hai!"},
    {"page": 58, "speaker": "narrator", "emotion": "excited", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
     "text": "Yahin se shuru hone wali hai ek kamzor ladke ke Shadow Monarch banne ki dastan! Subscribe karein agle chapter ke liye!"}
]

# ─────────────────────────────────────────────────────────────────────────────
# CHARACTER VOICE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
SPEAKER_CONFIG = {
    "narrator": {"voice": "hi-IN-MadhurNeural", "rate": "+12%", "pitch": "+0Hz"},
    "jinwoo":   {"voice": "hi-IN-MadhurNeural", "rate": "+15%", "pitch": "+3Hz"},
    "juhee":    {"voice": "hi-IN-SwaraNeural",  "rate": "+12%", "pitch": "+4Hz"},
    "kim":      {"voice": "hi-IN-MadhurNeural", "rate": "+10%", "pitch": "-6Hz"},
    "bak":      {"voice": "hi-IN-MadhurNeural", "rate": "+10%", "pitch": "-4Hz"},
    "song":     {"voice": "hi-IN-MadhurNeural", "rate": "+6%",  "pitch": "-10Hz"},
    "hunter":   {"voice": "hi-IN-MadhurNeural", "rate": "+14%", "pitch": "-2Hz"},
}

EMOTION_VOICE_MOD = {
    "desperate":  {"rate_mod": 4,  "pitch_mod": -4},
    "fearful":    {"rate_mod": -4, "pitch_mod": -4},
    "sad":        {"rate_mod": -6, "pitch_mod": -3},
    "dramatic":   {"rate_mod": 2,  "pitch_mod": -2},
    "angry":      {"rate_mod": 8,  "pitch_mod": +2},
    "excited":    {"rate_mod": 6,  "pitch_mod": +4},
    "calm":       {"rate_mod": 0,  "pitch_mod": 0},
    "happy":      {"rate_mod": 4,  "pitch_mod": +2},
    "curious":    {"rate_mod": 2,  "pitch_mod": +2},
    "nervous":    {"rate_mod": 0,  "pitch_mod": +2},
    "surprised":  {"rate_mod": 6,  "pitch_mod": +6},
    "hopeful":    {"rate_mod": 2,  "pitch_mod": +2},
}


async def generate_speech(text: str, speaker: str, emotion: str, out_wav: Path):
    """Generate human-like speech via Edge-TTS."""
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
            comm = edge_tts.Communicate(text, base_voice, rate=final_rate, pitch=final_pitch)
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
    """Generate procedural music using FFmpeg audio synthesizer."""
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "dark_drone":      f"aevalsrc='0.22*sin(2*PI*55*t)+0.15*sin(2*PI*82.4*t)+0.10*sin(2*PI*110*t)+0.05*sin(2*PI*164.8*t)':d={d}:s=44100,volume=0.35",
        "dark_intense":    f"aevalsrc='0.28*sin(2*PI*45*t)+0.20*sin(2*PI*65*t)+0.12*sin(2*PI*130*t)+0.08*(random(0)-0.5)':d={d}:s=44100,volume=0.40",
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
    """Generate procedural sound effect."""
    ff = ffmpeg_bin()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    filters = {
        "heartbeat_low":  f"aevalsrc='0.35*sin(2*PI*45*t)*pow(max(0,sin(2*PI*1.2*t)),10)':d={d}:s=44100",
        "portal_hum":     f"aevalsrc='0.25*sin(2*PI*60*t)+0.15*sin(2*PI*(60+8*sin(2*PI*0.5*t))*t)':d={d}:s=44100",
        "whoosh_energy":  f"aevalsrc='0.3*exp(-4*t)*sin(2*PI*(300-200*t)*t)':d={d}:s=44100",
        "impact_heavy":   f"aevalsrc='0.4*exp(-6*t)*sin(2*PI*50*t)+0.2*exp(-10*t)*(random(0)-0.5)':d={d}:s=44100",
        "blood_impact":   f"aevalsrc='0.3*exp(-5*t)*sin(2*PI*70*t)+0.15*exp(-8*t)*(random(0)-0.5)':d={d}:s=44100",
        "shock_sting":    f"aevalsrc='0.35*exp(-3*t)*sin(2*PI*520*t)+0.25*exp(-3*t)*sin(2*PI*554*t)':d={d}:s=44100",
        "braam_impact":   f"aevalsrc='0.4*exp(-1.5*t)*sin(2*PI*40*t)+0.25*exp(-2*t)*sin(2*PI*80*t)':d={d}:s=44100",
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
    """Mix voice, background score, and SFX with dynamic ducking."""
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


def render_scene_video(img_path: Path, duration: float, camera: str, out_mp4: Path):
    """
    Render 1080p widescreen video from vertical manga page:
      - Background: blurred, darkened, zoomed 1920x1080 canvas
      - Foreground: crisp centered manga page
      - Camera movement: Ken Burns zoom, pan, or tilt
    """
    ff = ffmpeg_bin()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    dur = round(duration, 3)
    w, h = 1920, 1080

    # Build filter graph
    # Background: crop 1920x1080 + boxblur
    bg_flt = f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=25:5,eq=brightness=-0.18:contrast=0.95[bg]"

    # Foreground scale to fit height 1040 (leaving 20px top/bottom margin)
    if camera == "tilt_down":
        # Scan page from top to bottom
        fg_flt = (
            f"[0:v]scale=w=-1:h='max(1040, 2337*0.6)':eval=init[fg_raw];"
            f"[fg_raw]crop=w=iw:h=1040:x=0:y='(ih-1040)*t/{dur:.2f}'[fg]"
        )
    elif camera in ("sudden_zoom", "slow_push"):
        fg_flt = f"[0:v]scale=-1:1040[fg]"
    else:
        fg_flt = f"[0:v]scale=-1:1040[fg]"

    # Overlay centered
    overlay_flt = "[bg][fg]overlay=(W-w)/2:(H-h)/2[comp]"

    # Subtle overall Ken Burns zoom
    if camera == "slow_push":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.05*t/{dur:.2f})/2)':h='2*floor({h}*(1.01+0.05*t/{dur:.2f})/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p"
        )
    elif camera == "slow_pull":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.06-0.05*t/{dur:.2f})/2)':h='2*floor({h}*(1.06-0.05*t/{dur:.2f})/2)':eval=frame,"
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
    elif camera == "breathing":
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.02+0.015*sin(2*PI*1.1*t))/2)':h='2*floor({h}*(1.02+0.015*sin(2*PI*1.1*t))/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p"
        )
    else:
        comp_scale = (
            f"[comp]scale=w='2*floor({w}*(1.01+0.03*t/{dur:.2f})/2)':h='2*floor({h}*(1.01+0.03*t/{dur:.2f})/2)':eval=frame,"
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
    """Generate styled ASS subtitles."""
    out_ass.parent.mkdir(parents=True, exist_ok=True)

    header = """[Script Info]
Title: Solo Leveling Ch 1 Hindi Recap
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3.5,1.5,2,40,40,65,1
Style: JinWoo,Arial,52,&H0080FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3.5,1.5,2,40,40,65,1
Style: JuHee,Arial,52,&H00FFB0FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3.5,1.5,2,40,40,65,1

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
        style = "JinWoo" if speaker == "jinwoo" else ("JuHee" if speaker == "juhee" else "Default")
        t_start = to_ass_time(current_time + 0.1)
        t_end = to_ass_time(current_time + dur - 0.1)
        text = sm["text"]
        lines.append(f"Dialogue: 0,{t_start},{t_end},{style},,0,0,0,,{text}\n")
        current_time += dur

    with open(out_ass, "w", encoding="utf-8") as f:
        f.writelines(lines)


async def main():
    out_dir = ROOT / "output" / "solo_leveling_ch1"
    pages_dir = out_dir / "pages"
    cp_dir = out_dir / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("⚔️ SOLO LEVELING CHAPTER 1 — CINEMATIC HINDI EXPLAINER VIDEO")
    print(f"📁 Output Directory: {out_dir}")
    print("=" * 70)

    # Process page 38 (crop out top 45% ad)
    p38_raw = pages_dir / "page_038.png"
    p38_clean = pages_dir / "page_038_clean.png"
    if p38_raw.exists() and not p38_clean.exists():
        im = Image.open(p38_raw)
        w, h = im.size
        # Keep bottom 55%
        cropped = im.crop((0, int(h * 0.44), w, h))
        cropped.save(str(p38_clean))
        print("  ✓ Cropped ad from page 38 -> page_038_clean.png")

    scenes_meta = []
    total_scenes = len(SCENES_DATA)

    for i, item in enumerate(SCENES_DATA, start=1):
        pid = item["page"]
        speaker = item["speaker"]
        emotion = item["emotion"]
        camera = item["camera"]
        music = item["music"]
        sfx = item["sfx"]
        text = item["text"]
        use_crop = item.get("crop_bottom", False)

        img_file = pages_dir / ("page_038_clean.png" if use_crop else f"page_{pid:03d}.png")
        scene_mp4 = cp_dir / f"scene_{i:03d}_p{pid:03d}.mp4"

        # Checkpoint check
        if scene_mp4.exists() and scene_mp4.stat().st_size > 50000:
            info = probe(scene_mp4)
            dur = float(info["format"]["duration"])
            print(f"[{i:02d}/{total_scenes}] ✓ Cached scene {i:02d} (page {pid:03d}, {dur:.1f}s)")
            scenes_meta.append({"index": i, "page": pid, "duration": dur, "text": text, "speaker": speaker, "mp4": scene_mp4})
            continue

        print(f"\n[{i:02d}/{total_scenes}] 🎬 Processing Scene #{i:02d} (Page {pid:03d}, Speaker={speaker}, Emotion={emotion})...")

        # 1. Voice
        voice_wav = cp_dir / f"voice_{i:03d}.wav"
        if not voice_wav.exists() or voice_wav.stat().st_size < 1000:
            await generate_speech(text, speaker, emotion, voice_wav)

        vinfo = probe(voice_wav)
        vdur = float(vinfo["format"]["duration"])
        scene_dur = max(4.5, vdur + 0.8)  # Voice duration + 0.8s breathing room

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

        # 6. Join
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
        scenes_meta.append({"index": i, "page": pid, "duration": scene_dur, "text": text, "speaker": speaker, "mp4": scene_mp4})

    # Subtitles
    print("\n📝 Generating Subtitles...")
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

    # Thumbnail
    print("\n🖼️ Creating YouTube Cover Thumbnail...")
    cover_jpg = out_dir / "cover.jpg"
    # Composite dramatic cover from page 6 (statue) or page 12 (logo)
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(pages_dir / "page_006.png"),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=contrast=1.15:saturation=1.2",
        str(cover_jpg)
    ], check=True)

    info = probe(final_mp4)
    dur = float(info["format"]["duration"])
    size_mb = final_mp4.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 70)
    print("🎉 VIDEO GENERATION COMPLETE!")
    print(f"🎬 Video: {final_mp4}")
    print(f"⏱️ Duration: {dur:.1f}s ({dur/60:.2f} minutes)")
    print(f"📦 Size: {size_mb:.2f} MB")
    print(f"🖼️ Thumbnail: {cover_jpg}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
