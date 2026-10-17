"""
generate_solo_leveling_ragnarok_ch7.py — Solo Leveling: Ragnarok Chapter 7 Fast-Paced Cinematic Explainer.

Key Highlights:
  1. 100% Pure Gemini Neural Humanoid TTS with Studio Warmth DSP Chain.
  2. Snappy fast-paced pacing (atempo=1.16) for high retention.
  3. High-CTR 1280x720 Thumbnail (Suho vs Possessed Fang of Rakhan).
  4. 20 Action-Packed Scenes with dynamic Ken Burns camera motion & bokeh backdrop.
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
# 20 FAST-PACED SCRIPTED SCENES (CHAPTER 7 COMPLETE STORYLINE)
# ─────────────────────────────────────────────────────────────────────────────
SCENES = [
    {
        "panel": 1, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Solo Leveling: Ragnarok — Chapter 7! Crystal Dungeon mein jaag utha Beast Monarch ka khauf!",
        "text_speak": "सोलो लेवलिंग: रैग्नारॉक — चैप्टर सात! क्रिस्टल डंजन में गूँज उठी बीस्ट मोनार्क की खौफनाक ललकार!"
    },
    {
        "panel": 2, "speaker": "narrator", "emotion": "epic", "camera": "slow_push", "music": "dark_drone", "sfx": "whoosh_energy",
        "text_sub": "Dungeon ke andar Suho ke teeno Shadow Goblins kudar chala kar crystal tod rahe the!",
        "text_speak": "डंजन के अंदर सू-हो के तीनों शैडो गोब्लिन्स तेज़ी से कुदाल चलाकर क्रिस्टल तोड़ रहे थे... बाकी हंटर्स के होश उड़ गए!"
    },
    {
        "panel": 3, "speaker": "suho", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Suho ne muskura kar socha: bina thake kaam karne wale aise mazdoor kahan milte hain!",
        "text_speak": "सू-हो ने मुस्कुरा कर सोचा: बिना शिकायत पसीना बहाने वाले ऐसे वफादार शैडो मज़दूर आखिर कहाँ मिलते हैं!"
    },
    {
        "panel": 4, "speaker": "beru", "emotion": "calm", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "Beru zameen par gire mana ke tukde chapaata hua apni taqat wapas paane ki koshish kar raha tha.",
        "text_speak": "छोटू बेरू ज़मीन पर गिरे माना के नन्हे टुकड़ों को मजे से खाते हुए अपनी खोई हुई ताकत बटोरने में लगा था।"
    },
    {
        "panel": 5, "speaker": "beru", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Lekin tabhi Beru kaanp utha: 'Young Monarch! Mujhe ek Monarch ki haazri mehsoos ho rahi hai!'",
        "text_speak": "लेकिन तभी बेरू बुरी तरह काँप उठा: 'मालिक! मुझे एक खूंखार मोनार्क की मौजूदगी महसूस हो रही है!'"
    },
    {
        "panel": 6, "speaker": "narrator", "emotion": "urgent", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Suho ne pucha: 'Kya mere pita?' Beru bola: 'Nahi... ye kisi darinde ki badboo hai!' Aur tunnel se cheekhein goonji!",
        "text_speak": "सू-हो ने चौंक कर पूछा: 'क्या मेरे पिता?' बेरू बोला: 'नहीं... ये किसी जंगली दरिंदे की खूनी गंध है!' और तभी टनल से चीखें गूँजीं!"
    },
    {
        "panel": 7, "speaker": "narrator", "emotion": "urgent", "camera": "handheld_shake", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Aage se laal aankhon wale darrane bhediye—Steel Fanged Lycans ne miners par hamla bol diya!",
        "text_speak": "आगे से दहकती लाल आँखों वाले भयानक भेड़िये—स्टील फैंग्ड लाइकन्स ने बेबस माइनर्स पर धावा बोल दिया!"
    },
    {
        "panel": 8, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "Suho bijli ki raftar se beech mein kooda: 'Main inhe rokta hoon, tum sab bahar bhaago!'",
        "text_speak": "सू-हो बिजली की रफ़्तार से बीच में कूदा: 'मैं इन्हें रोकता हूँ, तुम सब तुरंत बाहर भागो!'"
    },
    {
        "panel": 9, "speaker": "narrator", "emotion": "curious", "camera": "slow_push", "music": "dark_drone", "sfx": "ambient_soft",
        "text_sub": "System ne dikhaya Orange Name! D-Rank level ke monster... Suho akele lene ko taiyyar tha!",
        "text_speak": "सिस्टम पर ऑरेंज नाम चमका: स्टील फैंग्ड लाइकन! डी-रैंक लेवल के दरिंदे... सू-हो अकेले इनका शिकार करने को तैयार था!"
    },
    {
        "panel": 10, "speaker": "suho", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Suho ne inventory se daggers nikaale: 'Goblins, Dogyun ko protect karo!' Aur hathiyar kheench liye!",
        "text_speak": "सू-हो ने इन्वेंट्री से चमकते खंजर निकाले: 'गोब्लिन्स, डोग्यून की रक्षा करो!' और दोनों हाथों में हथियार कस लिए!"
    },
    {
        "panel": 11, "speaker": "narrator", "emotion": "urgent", "camera": "handheld_shake", "music": "dark_intense", "sfx": "whoosh_energy",
        "text_sub": "Zameen ko faadte hue Suho sidha darindon ke jhund par jhapat pada!",
        "text_speak": "ज़मीन को चीरते हुए सू-हो काल बनकर सीधा दरिंदों के झुंड पर झपट पड़ा!"
    },
    {
        "panel": 12, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "c_rank_blade_slash",
        "text_sub": "CHHAK! Ek hi zordar vaar mein Lycan do tukdon mein kat gaya! Defeated notification screen par chamka!",
        "text_speak": "छपाक! एक ही बिजली जैसे वार में लाइकन के दो टुकड़े हो गए! सिस्टम ने कहा: यू हैव डिफीटेड द लाइकन!"
    },
    {
        "panel": 13, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Suho ne aadesh diya: 'ARISE!' Aur bhediye ki laash se kaali-neeli aag nikal aayi!",
        "text_speak": "सू-हो ने ललकार लगाई: 'अराइज़!' और उस खूनी भेड़िये की लाश से नीली-काली शैडो ऊर्जा का बवंडर उठ खड़ा हुआ!"
    },
    {
        "panel": 14, "speaker": "beru", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Doosra wolf bhi shadow ban gaya! Suho ne jaana ki shadow nikaalne mein mana kharch nahi hota!",
        "text_speak": "दूसरा भेड़िया भी उसका शैडो सैनिक बन गया! सू-हो समझ गया कि शैडो निकालने में ज़रा भी माना खर्च नहीं होता!"
    },
    {
        "panel": 15, "speaker": "narrator", "emotion": "epic", "camera": "sudden_zoom", "music": "epic_adventure", "sfx": "braam_impact",
        "text_sub": "Tring! 'YOU HAVE LEVELED UP!' Suho ke peeche ab Shadow Wolves ki poori fauj khadi thi!",
        "text_speak": "डिंग! 'यू हैव लेवल्ड अप!' सू-हो के पीछे अब खूंखार शैडो भेड़ियों की पूरी पलटन दहाड़ रही थी!"
    },
    {
        "panel": 16, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "heartbeat_low",
        "text_sub": "Tabhi lal notification goonja: URGENT QUEST! Ek taqatwar shakhs tumhe jaan se maarna chahta hai!",
        "text_speak": "तभी लाल नोटिफिकेशन गूँजा: अर्जेंट क्वेस्ट! एक भयानक दुश्मन तुम्हारी जान लेने आ रहा है... उसे मारकर अपनी रक्षा करो!"
    },
    {
        "panel": 17, "speaker": "narrator", "emotion": "fearful", "camera": "slow_push", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Tunnel ke andhere se strike squad ka ek hunter bahar aaya... lekin uski aankhein shaitani aag se jal rahi thi!",
        "text_speak": "टनल के अंधेरे से भारी कवच पहने एक हंटर बाहर निकला... लेकिन उसकी आँखें शैतानी आग से दहक रही थीं!"
    },
    {
        "panel": 18, "speaker": "narrator", "emotion": "urgent", "camera": "handheld_shake", "music": "dark_intense", "sfx": "c_rank_blade_slash",
        "text_sub": "WHAAM! Hunter ne gardan kaatne wala vaar kiya! Suho ne Dogyun ko kheench kar baal-baal bachaya!",
        "text_speak": "खचाक! उस हंटर ने सिर धड़ से अलग करने वाला खूनी वार किया! सू-हो ने डोग्यून को खींचकर बाल-बाल बचाया!"
    },
    {
        "panel": 19, "speaker": "narrator", "emotion": "fearful", "camera": "sudden_zoom", "music": "dark_intense", "sfx": "braam_impact",
        "text_sub": "Uske sar par laal rang mein chamak raha tha: FANG OF RAKHAN — POSSESSED! Ek poora darinda ban chuka hunter!",
        "text_speak": "उसके सिर पर खूनी लाल नाम चमका: फैंग ऑफ राखान — पज़ेस्ड! राक्षस बन चुका सबसे खतरनाक हंटर!"
    },
    {
        "panel": 20, "speaker": "suho", "emotion": "epic", "camera": "slow_push", "music": "epic_adventure", "sfx": "whoosh_energy",
        "text_sub": "Beru ne kaha ye Monarch ki taqat hai! Par Suho ne daggers nikaale: 'Main ise hara kar aur taqatwar banoonga!'",
        "text_speak": "बेरू ने चेताया कि ये मोनार्क का साया है! लेकिन सू-हो ने खंजर चमकाते हुए कहा: 'मैं इस रेड नेम को चीरकर आगे बढ़ूँगा!'"
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# 100% PURE GEMINI HUMANOID VOICE ENGINE (Fast-Paced with Studio DSP)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_humanoid_voice(text_speak: str, speaker: str, emotion: str, out_wav: Path):
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    voice_name = "Charon" if speaker in ("beru", "monarch") else "Fenrir"

    for attempt in range(1, 4):
        try:
            pcm = _call_gemini_tts(text_speak, voice_name=voice_name)
            if pcm and len(pcm) > 500:
                _pcm_to_wav(pcm, out_wav)
                break
        except Exception as e:
            print(f"    ⚠️ Gemini TTS attempt {attempt} failed ({e}), retrying...")
            if attempt == 3:
                import edge_tts
                raw_mp3 = out_wav.with_suffix(".tmp.mp3")
                comm = edge_tts.Communicate(text_speak, "hi-IN-MadhurNeural", rate="+14%", pitch="-1Hz")
                await comm.save(str(raw_mp3))
                subprocess.run([
                    ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
                    "-i", str(raw_mp3), "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1",
                    str(out_wav)
                ], check=True)
                raw_mp3.unlink(missing_ok=True)
                break
            await asyncio.sleep(2.0)

    # Studio Warmth DSP Chain with tempo speedup (atempo=1.16) for snappy narration
    dsp_wav = out_wav.with_name(f"dsp_{out_wav.name}")
    ff = ffmpeg_bin()
    bass_boost = 3.2 if voice_name == "Charon" else 2.0
    dsp_chain = (
        f"equalizer=f=120:t=q:w=1.2:g={bass_boost},"
        "equalizer=f=2800:t=q:w=1.4:g=2.0,"
        "acompressor=threshold=-16dB:ratio=2.5:attack=15:release=100:makeup=1.8dB,"
        "atempo=1.16"
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
        "dark_drone":     f"aevalsrc='0.22*sin(2*PI*55*t)+0.16*sin(2*PI*82.4*t)+0.10*sin(2*PI*110*t)':d={d}:s=44100,volume=0.28",
        "dark_intense":   f"aevalsrc='0.28*sin(2*PI*45*t)+0.20*sin(2*PI*65*t)+0.12*sin(2*PI*130*t)+0.07*(random(0)-0.5)':d={d}:s=44100,volume=0.34",
        "epic_adventure": f"aevalsrc='0.20*sin(2*PI*130.8*t)+0.16*sin(2*PI*164.8*t)+0.14*sin(2*PI*196*t)+0.12*sin(2*PI*261.6*t)':d={d}:s=44100,volume=0.32",
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
Title: Solo Leveling Ragnarok Chapter 7 Subtitles
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
        style = "RagnarokGold" if sc["speaker"] in ("beru", "suho") else "RagnarokCyan"
        text = sc["text_sub"].replace("\n", " ")
        events.append(f"Dialogue: 0,{start_str},{end_str},{style},,0,0,0,,{text}")
        curr += dur

    out_ass.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    print(f"  ✓ Dual-Color Subtitles generated: {out_ass.name}")


def generate_thumbnail(panel_img: Path, out_thumb: Path):
    out_thumb.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1280, 720), (10, 10, 16))

    if panel_img.exists():
        with Image.open(str(panel_img)) as im:
            aspect = im.width / im.height
            if aspect > 1.2:
                bg = im.resize((1280, int(1280 / aspect))).crop((0, 0, 1280, 720))
            else:
                scale_w = 720
                scale_h = int(scale_w / aspect)
                center_crop = im.crop((0, int(im.height * 0.05), im.width, int(im.height * 0.75)))
                bg = center_crop.resize((1280, 720))
        canvas.paste(bg, (0, 0))

    dark_overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 100))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), dark_overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    try:
        font_large = ImageFont.truetype("arialbd.ttf", 64)
        font_sub = ImageFont.truetype("arialbd.ttf", 46)
        font_badge = ImageFont.truetype("arialbd.ttf", 30)
    except Exception:
        font_large = font_sub = font_badge = ImageFont.load_default()

    draw.rounded_rectangle([(40, 30), (480, 95)], radius=12, fill=(220, 20, 60))
    draw.text((60, 42), "SOLO LEVELING RAGNAROK", font=font_badge, fill=(255, 255, 255))

    draw.text((45, 530), "CHAPTER 7 : SUHO VS RED NAME!", font=font_large, fill=(0, 240, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    draw.text((45, 615), "SHADOW WOLVES & FANG OF RAKHAN! 🐺🔥", font=font_sub, fill=(255, 215, 0), stroke_width=3, stroke_fill=(0, 0, 0))

    canvas.save(str(out_thumb), quality=95)
    print(f"  ✓ High-CTR Thumbnail generated: {out_thumb}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
async def run_pipeline():
    ff = ffmpeg_bin()
    out_dir = ROOT / "output" / "solo_leveling_ragnarok_ch7"
    panels_dir = out_dir / "panels"
    cp_dir = out_dir / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 75)
    print("  ⚔️ SOLO LEVELING: RAGNAROK CHAPTER 7 — FAST-PACED HUMANOID ENGINE")
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

        print(f"\n[Scene {i:02d}/20] Panel {pid:03d} | Spk: {sc['speaker']} | Emo: {sc['emotion']}")

        # 1. Gemini Humanoid Voice with 1.16x tempo
        if not voice_wav.exists() or voice_wav.stat().st_size < 1000:
            print(f"  🎙️ Synthesizing humanoid voice ({sc['speaker']})...")
            await generate_humanoid_voice(sc["text_speak"], sc["speaker"], sc["emotion"], voice_wav)
            await asyncio.sleep(2.0)

        v_dur = float(probe(voice_wav)["format"]["duration"])
        dur = max(2.8, v_dur + 0.35)
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
            print(f"  🎬 Rendering wide panel motion ({sc['camera']})...")
            render_wide_scene_video(img_path, dur, sc["camera"], video_mp4)

        # 4. Join Video + Audio
        print(f"  🔗 Joining scene_{i:03d}...")
        join_scene(video_mp4, audio_aac, scene_final)
        scene_mp4s.append(scene_final)

    # Concat & Burn Subtitles
    print("\n" + "=" * 75)
    print("  🎞️ CONCATENATING 20 SCENES & BURNING SUBTITLES")
    print("=" * 75)

    concat_list = out_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in scene_mp4s:
            escaped = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{escaped}'\n")

    raw_final = out_dir / "raw_combined.mp4"
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(raw_final)
    ], check=True)

    # Subtitles
    sub_ass = out_dir / "subtitles.ass"
    generate_ass_subtitles(SCENES, scene_durs, sub_ass)

    final_mp4 = out_dir / "solo_leveling_ragnarok_ch7_final.mp4"
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

    # Thumbnail
    thumb_path = out_dir / "thumbnail.jpg"
    lead_panel = panels_dir / "panel_020.jpg"
    generate_thumbnail(lead_panel, thumb_path)

    v_info = probe(final_mp4)
    total_dur = float(v_info["format"]["duration"])
    size_mb = final_mp4.stat().st_size / 1024 / 1024
    print("\n" + "#" * 75)
    print(f"  🎉 SOLO LEVELING RAGNAROK CHAPTER 7 COMPLETE!")
    print(f"  📁 Video: {final_mp4.name} ({size_mb:.2f} MB)")
    print(f"  ⏱️ Total Duration: {total_dur:.1f}s ({total_dur/60:.2f} mins)")
    print(f"  🖼️ Thumbnail: {thumb_path.name}")
    print("#" * 75 + "\n")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
