"""
agents/voice.py — TTS narration + word-level timing.

⚠️ EK ASLI PROBLEM AUR USKA HAL (jhoot nahi bolunga):

Problem 1: edge-tts mein Hindi ki sirf 2 voices hain (hi-IN-SwaraNeural female,
hi-IN-MadhurNeural male). Section 5 kehta hai "4-6 voices rotate karo" warna
YouTube duplicate-pattern clustering se throttle karega.
HAL: hum VOICE PROFILES banate hain = base voice × rate × pitch.
2 base voices × alag pitch/rate = 6 clearly alag sounding narrators.
Ye asli alag voice actors jitna alag nahi hai, par audio fingerprint alag ho jaata hai
aur sunne mein bhi farq saaf pata chalta hai.

Problem 2: edge-tts ka WordBoundary event abhi (test kiya, July 2026) khaali aata hai —
Microsoft ne server-side band kar diya lagta hai. Iska matlab asli word timestamps
nahi milte.
HAL: hum per-line audio banate hain (har line ki apni MP3, exact duration measured
via core/mp3.py) aur us line ke andar words ko syllable-weight se distribute karte hain.
Line boundaries EXACT hain (measured), words ke andar ka timing approximate hai (±80ms).
Karaoke subtitles ke liye ye kaafi accha hai. Perfect chahiye to Whisper chahiye hoga,
jo local pe bhaari hai aur ₹0 constraint mein CPU-only slow chalega.
"""

from __future__ import annotations

import asyncio
import base64
import json
import math
import os
import re
import subprocess
import threading
import urllib.error
import urllib.request
import wave
from pathlib import Path

from core.config import CONFIG
from core.db import DB
from core.ffmpeg import ffmpeg_bin
from core.logbook import Logbook, retry
from core.mp3 import duration_sec
from core.quota import Quota, QuotaExceeded

log = Logbook("voice")


class _GeminiTTSRateLimited(Exception):
    """429 rate limit — turant edge-tts fallback karo, retry mat karo."""

# ---------------------------------------------------------------------
# GEMINI TTS VOICES & PROFILES (Phase A)
# ---------------------------------------------------------------------
GEMINI_VOICES = {
    "masculine": ["Charon", "Fenrir", "Orus", "Enceladus", "Algenib"],
    "feminine": ["Kore", "Aoede", "Leda", "Despina", "Sulafat"],
    "male": ["Charon", "Fenrir", "Orus", "Enceladus", "Algenib"],
    "female": ["Kore", "Aoede", "Leda", "Despina", "Sulafat"],
}

GEMINI_NARRATOR_PROFILES = {
    "gem_m_grave":   {"voice": "Charon",    "rate": "+0%", "pitch": "+0Hz", "gender": "male",   "desc": "deep, authoritative crime narrator (Gemini)"},
    "gem_m_breathy": {"voice": "Enceladus", "rate": "+0%", "pitch": "+0Hz", "gender": "male",   "desc": "breathy, suspense reveal (Gemini)"},
    "gem_f_firm":    {"voice": "Kore",      "rate": "+0%", "pitch": "+0Hz", "gender": "female", "desc": "firm, clear investigative narrator (Gemini)"},
    "gem_f_smooth":  {"voice": "Despina",   "rate": "+0%", "pitch": "+0Hz", "gender": "female", "desc": "smooth, eerie storyteller (Gemini)"},
}

# ---------------------------------------------------------------------
# 6 VOICE PROFILES — rotation ke liye.
# rate/pitch se same base voice ka character kaafi badal jaata hai.
# ---------------------------------------------------------------------
VOICE_PROFILES = {
    "hi_f_calm":     {"voice": "hi-IN-SwaraNeural",  "rate": "-4%",  "pitch": "-2Hz",
                      "gender": "female", "desc": "shaant, dheemi — documentary narrator"},
    "hi_f_urgent":   {"voice": "hi-IN-SwaraNeural",  "rate": "+12%", "pitch": "+6Hz",
                      "gender": "female", "desc": "tez, tension wali — breaking news feel"},
    "hi_f_whisper":  {"voice": "hi-IN-SwaraNeural",  "rate": "-8%",  "pitch": "-8Hz",
                      "gender": "female", "desc": "gehri, raaz kholti hui"},
    "hi_m_grave":    {"voice": "hi-IN-MadhurNeural", "rate": "-6%",  "pitch": "-6Hz",
                      "gender": "male",   "desc": "bhaari, gambhir — crime doc"},
    "hi_m_narrator": {"voice": "hi-IN-MadhurNeural", "rate": "+2%",  "pitch": "+0Hz",
                      "gender": "male",   "desc": "neutral storyteller"},
    "hi_m_intense":  {"voice": "hi-IN-MadhurNeural", "rate": "+14%", "pitch": "+8Hz",
                      "gender": "male",   "desc": "tez, aggressive — thriller"},
}
VOICE_PROFILES.update(GEMINI_NARRATOR_PROFILES)

# English/Hinglish ke liye (config.language se switch hota hai)
VOICE_PROFILES_EN = {
    "en_f_calm":     {"voice": "en-IN-NeerjaNeural",   "rate": "-4%",  "pitch": "-2Hz",
                      "gender": "female", "desc": "calm Indian English narrator"},
    "en_f_expr":     {"voice": "en-IN-NeerjaExpressiveNeural", "rate": "+6%", "pitch": "+4Hz",
                      "gender": "female", "desc": "expressive, dramatic"},
    "en_m_grave":    {"voice": "en-IN-PrabhatNeural",  "rate": "-6%",  "pitch": "-6Hz",
                      "gender": "male",   "desc": "deep, serious"},
    "en_m_intense":  {"voice": "en-IN-PrabhatNeural",  "rate": "+12%", "pitch": "+6Hz",
                      "gender": "male",   "desc": "urgent thriller"},
}

# Suspense pacing (Section 6): reveal se pehle 300ms pause
PAUSE_DEFAULT_MS = 220      # normal line gap
PAUSE_REVEAL_MS = 300       # reveal se pehle extra
PAUSE_HOOK_MS = 150         # hook ke baad chhota — momentum banaye rakho

# Ye shabd batate hain ki agli line ek "reveal" hai -> pehle pause daalo
REVEAL_MARKERS = ["lekin", "magar", "phir", "asli", "sach", "aakhir", "par ",
                  "but ", "however", "truth", "actually", "turns out"]


# Session-level flag: agar Gemini TTS 429 de to baaki saari lines edge-tts se karo
_gemini_tts_rate_limited: bool = False
_elevenlabs_quota_exceeded: bool = False



def profiles() -> dict:
    """Config ki language ke hisaab se sahi profile set."""
    return VOICE_PROFILES if str(CONFIG.get("language", "Hindi")).lower().startswith("hi") \
        else VOICE_PROFILES_EN


class Voice:
    def __init__(self, db: DB | None = None):
        self.db = db or DB()
        self.profiles = profiles()

    # ------------------------------------------------------------------
    def pick_profile(self) -> str:
        """Aisi voice chuno jo pichhle 4 videos mein use na hui ho (clustering se bachav)."""
        options = list(self.profiles)

        # ⭐ PHASE 8: chal raha experiment sab pe bhaari hai
        try:
            from agents.scientist import Scientist
            sci = Scientist(self.db)
            forced = sci.forced_value("voice_id")
            if forced and forced in self.profiles:
                log.info(f"Experiment chal raha hai — voice forced: {forced}")
                return forced
            # high-confidence losers ko rotation se hatao (Section 6)
            for bad in sci.losers().get("voice_id", []):
                if bad in options and len(options) > 2:
                    options.remove(bad)
                    log.debug(f"Voice '{bad}' rotation se hataya (A/B mein haara)")
        except Exception as e:  # noqa: BLE001
            log.debug(f"Scientist check skip: {str(e)[:80]}")

        # learnings dekho — koi voice jeeti hui hai to usse prefer karo
        winners = [r["winner"] for r in self.db.active_learnings("voice_id")
                   if r["confidence"] == "high" and r["winner"] in self.profiles]
        recent = self.db.recent_values("voice_id", 4)
        if winners and winners[0] not in recent:
            log.info(f"Winning voice use kar rahe hain: {winners[0]}")
            return winners[0]
        pick = self.db.pick_rotated("voice_id", options, avoid_last=4)
        log.info(f"Voice chuni: {pick} ({self.profiles[pick]['desc']})", last4=recent)
        return pick

    # ------------------------------------------------------------------
    def narrate(self, lines: list[dict | str], out_dir: str | Path,
                profile_id: str | None = None) -> dict:
        """
        Har line ki alag MP3 banao (exact duration mil jaati hai),
        phir un sabko jodkar narration.mp3 + timing JSON banao.
        """
        profile_id = profile_id or self.pick_profile()
        prof = dict(self.profiles[profile_id])
        out_dir = Path(out_dir)
        (out_dir / "lines").mkdir(parents=True, exist_ok=True)

        norm_lines = []
        for i, item in enumerate(lines):
            if isinstance(item, dict):
                norm_lines.append({
                    "i": i,
                    "speaker": item.get("speaker", "narrator"),
                    "text": item.get("text", "").strip(),
                    "emotion": item.get("emotion", "neutral"),
                    "role": item.get("role", "body" if (0 < i < len(lines)-1) else ("hook" if i == 0 else "ending")),
                    "persona": item.get("persona", ""),
                })
            else:
                norm_lines.append({
                    "i": i,
                    "speaker": "narrator",
                    "text": str(item).strip(),
                    "emotion": "neutral",
                    "role": "body" if (0 < i < len(lines)-1) else ("hook" if i == 0 else "ending"),
                    "persona": "",
                })

        # Narrator voice
        narr_gender = prof.get("gender", "male")
        narr_gem_voice = prof.get("voice") if prof.get("voice") in (GEMINI_VOICES["masculine"] + GEMINI_VOICES["feminine"]) else ("Charon" if narr_gender == "male" else "Kore")
        prof["gemini_voice"] = narr_gem_voice

        # Character voice mapping — narrator aur character voice kabhi same nahi
        char_voices = {}
        for l in norm_lines:
            spk = l["speaker"]
            if spk != "narrator" and spk not in char_voices:
                c_gender = "female" if narr_gender == "male" else "male"
                avail = [v for v in GEMINI_VOICES[c_gender] if v != narr_gem_voice]
                chosen = avail[len(char_voices) % len(avail)] if avail else ("Kore" if narr_gem_voice != "Kore" else "Despina")
                char_voices[spk] = {
                    "voice": chosen,
                    "gemini_voice": chosen,
                    "gender": c_gender,
                    "rate": "+4%",
                    "pitch": "+2Hz" if c_gender == "female" else "-2Hz",
                    "desc": f"Character {spk} ({chosen})",
                }

        clips = []
        for l in norm_lines:
            i = l["i"]
            path = out_dir / "lines" / f"line_{i+1:02d}.mp3"
            spk = l["speaker"]
            line_prof = char_voices.get(spk, prof)
            ok = self._synth(l, path, line_prof)
            dur = duration_sec(path) if (path.exists() and path.stat().st_size > 0) else 0.0
            if dur <= 0:
                dur = max(1.2, len(l["text"].split()) / 2.6)
                log.warn(f"Line {i+1} ka audio nahi bana — {dur:.1f}s silence daal rahe hain",
                         line=l["text"][:60])
                ok = "silence"
                created_silent = False
                try:
                    fb = ffmpeg_bin()
                    cmd = [
                        fb, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
                        "-f", "lavfi", "-t", f"{dur:.3f}",
                        "-i", "anullsrc=channel_layout=mono:sample_rate=24000",
                        "-codec:a", "libmp3lame", "-b:a", "64k",
                        str(path)
                    ]
                    subprocess.run(cmd, stdin=subprocess.DEVNULL, check=True, capture_output=True, timeout=30)
                    if path.exists() and path.stat().st_size > 0:
                        created_silent = True
                except Exception as e:
                    log.warn(f"Silent audio generation fail ({str(e)[:80]}) — clip hata rahe hain")
                    path.unlink(missing_ok=True)

                if not created_silent:
                    clips.append({
                        "i": i, "text": l["text"], "speaker": spk,
                        "voice_name": line_prof.get("voice", ""),
                        "path": str(path), "dur": 0.0, "engine": "missing",
                        "role": l["role"], "emotion": l["emotion"]
                    })
                    continue

            clips.append({
                "i": i, "text": l["text"], "speaker": spk,
                "voice_name": line_prof.get("voice", ""),
                "path": str(path), "dur": dur, "engine": ok,
                "role": l["role"], "emotion": l["emotion"]
            })

        timeline = self._build_timeline(clips)
        merged = out_dir / "narration.mp3"
        pauses_applied = self._concat(clips, merged, timeline)

        if not pauses_applied:
            timeline = self._build_timeline(clips, no_pauses=True)
            log.warn("Pauses lagaye nahi ja sake (ffmpeg missing) — timeline bina pause ke "
                     "recompute kiya taaki subtitles sync rahein.")

        total = timeline[-1]["end"] if timeline else 0.0
        words_fallback = [w for ln in timeline for w in ln["words"]]
        words_final = words_fallback
        if merged.exists() and merged.stat().st_size > 1000:
            try:
                from pipeline.subtitles import align_with_groq
                groq_words = align_with_groq(merged)
                if groq_words and len(groq_words) >= max(3, len(words_fallback) // 2):
                    words_final = groq_words
                    log.ok(f"Subtitles: Groq Whisper frame-perfect alignment active ({len(words_final)} words)")
            except Exception as e:
                log.debug(f"Groq alignment fallback to timeline: {e}")

        result = {
            "voice_id": profile_id,
            "voice": prof["voice"],
            "narrator_voice": prof.get("gemini_voice") or prof.get("voice"),
            "character_voices": {spk: cinfo["voice"] for spk, cinfo in char_voices.items()},
            "rate": prof["rate"],
            "pitch": prof["pitch"],
            "audio_path": str(merged),
            "duration_sec": round(total, 2),
            "lines": timeline,
            "words": words_final,
            "engines_used": sorted({c["engine"] for c in clips}),
        }
        (out_dir / "timing.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        log.ok(f"Narration ready: {total:.1f}s, {len(result['words'])} words",
               voice=profile_id, engines=result["engines_used"])
        self._length_check(total)
        return result

    # ------------------------------------------------------------------
    def _length_check(self, total: float):
        target = CONFIG["video_length_sec"]
        if total > 45:
            log.warn(f"Narration {total:.1f}s — 45s se lamba. YouTube Shorts sweet spot "
                     f"22-45s hai. Writer se chhota script mangwao.")
        elif total < 22:
            log.warn(f"Narration {total:.1f}s — 22s se chhota. Sub-15s content 2026 mein "
                     f"collapse ho gaya. Script lamba karo ya pauses badhao.")
        elif abs(total - target) > 8:
            log.info(f"Narration {total:.1f}s (target {target}s) — range ke andar hai, theek hai.")

    # ---------------- TTS engines ----------------
    def _synth(self, line_item: dict | str, path: Path, prof: dict) -> str:
        """gemini_tts -> edge_tts -> gtts -> espeak. Pehla jo chale."""
        global _gemini_tts_rate_limited
        if isinstance(line_item, dict):
            text = line_item.get("text", "")
            emotion = line_item.get("emotion", "neutral")
            speaker = line_item.get("speaker", "narrator")
            role = line_item.get("role", "body")
            persona = line_item.get("persona", "")
        else:
            text = str(line_item)
            emotion = "neutral"
            speaker = "narrator"
            role = "body"
            persona = ""

        configured_engines = CONFIG.get("voice", {}).get("engine_order", None)
        if configured_engines:
            engines = list(configured_engines)
        else:
            engines = []
            eleven_key = os.environ.get("ELEVENLABS_API_KEY") or CONFIG.get("ELEVENLABS_API_KEY")
            if eleven_key and not _elevenlabs_quota_exceeded:
                engines.append("elevenlabs")
            engines.extend(["gemini_tts", "edge_tts", "gtts", "espeak"])

        # 429 rate limit hit ho chuka hai is session mein — Gemini skip karo
        if _gemini_tts_rate_limited and "gemini_tts" in engines:
            log.debug("Gemini TTS rate-limited (session) — edge-tts se shuru kar rahe hain")
            engines = [e for e in engines if e != "gemini_tts"]

        errors = []
        for engine in engines:
            try:
                if engine == "elevenlabs":
                    self._tts_elevenlabs(text, path, prof, emotion=emotion, persona=persona, role=role)
                elif engine == "gemini_tts":
                    self._tts_gemini_tts(text, path, prof, emotion=emotion, persona=persona, role=role)
                else:
                    getattr(self, f"_tts_{engine}")(text, path, prof)
                if path.exists() and path.stat().st_size > 500:
                    _apply_speaker_audio_style(path, speaker, emotion, role)
                    return engine
                raise RuntimeError("file khaali bani")
            except _GeminiTTSRateLimited:
                _gemini_tts_rate_limited = True
                log.warn("Gemini TTS 429 — session ke liye edge-tts fallback activate")
                errors.append(f"{engine}: 429 rate limited")
                continue
            except Exception as e:  # noqa: BLE001
                errors.append(f"{engine}: {str(e)[:100]}")
                log.debug(f"{engine} fail: {str(e)[:120]}")
        log.error("Saare TTS engines fail: " + " | ".join(errors))
        path.unlink(missing_ok=True)
        return ""

    def _tts_elevenlabs(self, text: str, path: Path, prof: dict, *, emotion: str = "neutral",
                         persona: str = "", role: str = "body"):
        global _elevenlabs_quota_exceeded
        key = os.environ.get("ELEVENLABS_API_KEY") or CONFIG.get("ELEVENLABS_API_KEY")
        if not key:
            raise RuntimeError("No ELEVENLABS_API_KEY configured")

        gender = prof.get("gender", "male")
        # George: JBFqnCBsd6RMkjVDRZzb (Warm Storyteller), Sarah: EXAVITQu4vr4xnSDxMaL (Mature, Confident)
        voice_id = prof.get("elevenlabs_voice") or ("JBFqnCBsd6RMkjVDRZzb" if gender == "male" else "EXAVITQu4vr4xnSDxMaL")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        stability = 0.48
        similarity_boost = 0.82
        style = 0.20
        if emotion in ("panicked", "urgent", "trembling", "nervous"):
            stability = 0.32
            style = 0.38
        elif emotion in ("whispers", "cold", "serious"):
            stability = 0.62
            style = 0.25

        payload = json.dumps({
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "xi-api-key": key,
                "Content-Type": "application/json",
                "User-Agent": "Autopilot/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                audio_bytes = resp.read()
                if len(audio_bytes) < 500:
                    raise RuntimeError("ElevenLabs empty response")
                with open(path, "wb") as f:
                    f.write(audio_bytes)
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 403, 429):
                _elevenlabs_quota_exceeded = True
                log.warn(f"ElevenLabs status {e.code} — auto fallback to Gemini/EdgeTTS")
            raise

    def _tts_gemini_tts(self, text: str, path: Path, prof: dict, *, emotion: str = "neutral",
                        persona: str = "", role: str = "body"):
        voice_name = prof.get("gemini_voice") or prof.get("voice") or "Charon"
        if voice_name not in GEMINI_VOICES["masculine"] and voice_name not in GEMINI_VOICES["feminine"]:
            voice_name = "Charon" if prof.get("gender") == "male" else "Kore"

        prompt = (
            f"# AUDIO PROFILE: {prof.get('desc', 'Narrator')} — {persona or 'Suspense narrator'}\n"
            f"### DIRECTOR'S NOTES\n"
            f"Style: Hindi suspense storytelling for a 30-second vertical video. Low, controlled intensity. No radio-announcer energy.\n"
            f"Pacing: Slightly slower than conversational. Pause 300ms before any reveal.\n"
            f"Accent: Standard Hindi as spoken in Delhi/UP. Clear Devanagari pronunciation.\n"
            f"#### TRANSCRIPT\n"
            f"[{emotion}] {text}"
        )
        pcm = _call_gemini_tts(prompt, voice_name=voice_name, db=self.db)
        wav = path.with_suffix(".wav")
        _pcm_to_wav(pcm, wav)
        cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
               "-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "128k", str(path)]
        subprocess.run(cmd, stdin=subprocess.DEVNULL, check=True, capture_output=True, timeout=30)
        wav.unlink(missing_ok=True)

    def _tts_edge_tts(self, text: str, path: Path, prof: dict):
        """
        edge-tts ko dedicated thread mein chalao.
        - asyncio.run() nested loop se deadlock hota hai → thread solve karta hai.
        - subprocess CLI Windows pe network hang karta hai → Python API better hai.
        - 25s hard timeout: agar Microsoft server respond nahi kiya → exception.
        """
        import edge_tts
        import threading

        voice = prof.get("voice", "hi-IN-SwaraNeural")
        if not voice.startswith("hi-") and not voice.startswith("en-"):
            voice = "hi-IN-MadhurNeural" if prof.get("gender") == "male" else "hi-IN-SwaraNeural"
        rate = prof.get("rate", "+0%")
        pitch = prof.get("pitch", "+0Hz")

        err_holder: list[Exception] = []

        def _worker():
            import asyncio as _aio

            async def _stream():
                c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                with open(path, "wb") as f:
                    async for chunk in c.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])

            try:
                _aio.run(_stream())
            except Exception as e:
                err_holder.append(e)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join(timeout=25)

        if t.is_alive():
            # Thread stuck — Microsoft server ne respond nahi kiya
            raise RuntimeError("edge-tts 25s timeout — network hang")
        if err_holder:
            raise err_holder[0]
        if not path.exists() or path.stat().st_size < 500:
            raise RuntimeError("edge-tts ne khaali file banayi")




    def _tts_gtts(self, text: str, path: Path, prof: dict):
        from gtts import gTTS
        v = prof.get("voice", "")
        lang = "hi" if v.startswith("hi") or not v.startswith("en") else "en"
        gTTS(text=text, lang=lang, tld="co.in", slow=False).save(str(path))

    def _tts_espeak(self, text: str, path: Path, prof: dict):
        """Offline last resort. Robotic lagta hai — publish layak nahi, par pipeline chalti rehti hai."""
        wav = path.with_suffix(".wav")
        v = prof.get("voice", "")
        lang = "hi" if v.startswith("hi") or not v.startswith("en") else "en-in"
        binary = "espeak-ng"
        subprocess.run([binary, "-v", lang, "-s", "150", "-w", str(wav), text],
                       check=True, capture_output=True, timeout=60)
        try:
            subprocess.run([ffmpeg_bin(), "-y", "-nostdin", "-i", str(wav), "-codec:a", "libmp3lame",
                            "-b:a", "128k", str(path)], check=True, capture_output=True, timeout=60)
            wav.unlink(missing_ok=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise RuntimeError("espeak ne WAV banaya par ffmpeg nahi mila MP3 ke liye")
        log.warn("espeak fallback use hua — awaaz robotic hogi, publish mat karna")

    # ---------------- timeline + word timing ----------------
    def _build_timeline(self, clips: list[dict], no_pauses: bool = False) -> list[dict]:
        """
        Har line ka exact start/end (measured MP3 duration se) +
        us line ke andar words ka approximate timing (syllable weight se).
        """
        t = 0.0
        out = []
        for c in clips:
            if no_pauses or c["i"] == 0:
                gap = 0.0
            elif _is_reveal(c["text"]) or c.get("role") == "reveal":
                gap = PAUSE_REVEAL_MS / 1000
            elif c["i"] == 1:
                gap = PAUSE_HOOK_MS / 1000
            else:
                gap = PAUSE_DEFAULT_MS / 1000
            start = t + gap
            end = start + c["dur"]
            whisper_words = _align_words_whisper(c["path"], c["text"], start, end)
            words = whisper_words if whisper_words else _distribute_words(c["text"], start, end)
            out.append({
                "i": c["i"], "text": c["text"], "speaker": c.get("speaker", "narrator"),
                "voice_name": c.get("voice_name", ""), "engine": c.get("engine", ""),
                "role": c.get("role", "body"), "emotion": c.get("emotion", "neutral"),
                "start": round(start, 3), "end": round(end, 3),
                "pause_before": round(gap, 3),
                "words": words,
            })
            t = end
        return out

    def _concat(self, clips: list[dict], out_path: Path, timeline: list[dict]) -> bool:
        """Sab line-MP3s ko pauses ke saath jodo."""
        existing = [c for c in clips if Path(c["path"]).exists() and Path(c["path"]).stat().st_size > 0]
        if not existing:
            log.error("Koi audio clip nahi bani — narration.mp3 khaali rahega")
            out_path.write_bytes(b"")
            return True

        try:
            self._concat_ffmpeg(existing, out_path, timeline)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            log.warn("ffmpeg se concat nahi hua — raw concat kar rahe hain.",
                     reason=str(e)[:120])

        with open(out_path, "wb") as f:
            for c in existing:
                f.write(Path(c["path"]).read_bytes())
        return False

    def _concat_ffmpeg(self, clips: list[dict], out_path: Path, timeline: list[dict]):
        """ffmpeg concat filter: clip, silence, clip, silence... exact pauses ke saath."""
        inputs, filters, parts = [], [], []
        idx = 0
        for n, c in enumerate(clips):
            gap = timeline[n]["pause_before"] if n < len(timeline) else 0.0
            if gap > 0.01:
                inputs += ["-f", "lavfi", "-t", f"{gap:.3f}",
                           "-i", "anullsrc=channel_layout=mono:sample_rate=24000"]
                parts.append(f"[{idx}:a]"); idx += 1
            inputs += ["-i", c["path"]]
            parts.append(f"[{idx}:a]"); idx += 1
        filters.append("".join(parts) + f"concat=n={len(parts)}:v=0:a=1[out]")
        cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error", *inputs,
               "-filter_complex", ";".join(filters), "-map", "[out]",
               "-codec:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", str(out_path)]
        subprocess.run(cmd, stdin=subprocess.DEVNULL, check=True, capture_output=True, timeout=180)


# ---------------------------------------------------------------------
# AUDIO HELPERS (Phase A)
# ---------------------------------------------------------------------
def _pcm_to_wav(pcm_bytes: bytes, wav_path: Path | str, sample_rate: int = 24000):
    """Raw 16-bit LE mono PCM ko WAV file mein likho."""
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


def _split_by_silence(wav_path: str | Path, expected_lines: int) -> list[tuple[float, float]] | None:
    """
    Audio ko silencedetect se line boundaries pe split karo.
    expected_lines audio clips chahiye -> expected_lines - 1 gaps milne chahiye.
    Return: list of (start_sec, end_sec) segments, ya None agar mismatch ho.
    """
    wav_path = Path(wav_path)
    if expected_lines <= 1:
        dur = duration_sec(wav_path)
        return [(0.0, dur)] if dur > 0 else None

    cmd = [
        ffmpeg_bin(), "-y", "-nostdin", "-hide_banner",
        "-i", str(wav_path),
        "-af", "silencedetect=noise=-35dB:d=0.25",
        "-f", "null", "-"
    ]
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    except Exception as e:
        log.warn("silencedetect execution fail", reason=str(e)[:100])
        return None

    err = proc.stderr or ""
    starts = [float(m.group(1)) for m in re.finditer(r"silence_start:\s*([\d.]+)", err)]
    ends = [float(m.group(1)) for m in re.finditer(r"silence_end:\s*([\d.]+)", err)]

    if len(starts) != expected_lines - 1:
        log.debug(f"silencedetect gaps mismatch: {len(starts)} gaps vs {expected_lines - 1} expected")
        return None

    dur = duration_sec(wav_path)
    cuts = []
    for i in range(len(starts)):
        s = starts[i]
        e = ends[i] if i < len(ends) else s + 0.25
        cuts.append(round((s + e) / 2.0, 3))

    segments = []
    prev = 0.0
    for c in cuts:
        segments.append((prev, c))
        prev = c
    segments.append((prev, dur))
    return segments


def _call_gemini_tts(text_or_prompt: str, *, voice_name: str = "Charon",
                     multi_speakers: list[dict] | None = None,
                     model: str | None = None, db: DB | None = None) -> bytes:
    """
    Gemini TTS REST API call (raw urllib se — SDK nahi).
    Return: raw PCM 16-bit LE 24000Hz mono bytes.
    """
    q = Quota(db or DB())
    q.check_and_spend("gemini_tts_requests", 1, reason="tts:gemini")

    if os.environ.get("AUTOPILOT_MOCK_MODE") == "true":
        import math
        import struct
        sample_rate = 24000
        duration = 1.0
        pcm_bytes = bytearray()
        for i in range(int(sample_rate * duration)):
            sample = int(32767 * 0.2 * math.sin(2 * math.pi * 440 * i / sample_rate))
            pcm_bytes.extend(struct.pack("<h", sample))
        return bytes(pcm_bytes)

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        env_file = Path(CONFIG.get("_root", ".")) / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY nahi mili")

    model_name = model or os.environ.get("GEMINI_TTS_MODEL") or CONFIG.get("voice", {}).get("gemini_tts_model", "gemini-2.5-flash-preview-tts")

    if multi_speakers:
        body = {
            "contents": [{"parts": [{"text": text_or_prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "multiSpeakerVoiceConfig": {
                        "speakerVoiceConfigs": [
                            {"speaker": s["speaker"], "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": s.get("voiceName", "Charon")}}}
                            for s in multi_speakers
                        ]
                    }
                }
            }
        }
    else:
        body = {
            "contents": [{"parts": [{"text": text_or_prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": voice_name}
                    }
                }
            }
        }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    def _post():
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Quota exhausted — retry se koi fayda nahi, turant fallback karo
                raise _GeminiTTSRateLimited(f"429 Too Many Requests") from e
            raise

    # 429 pe retry NAHI — seedha raise hoga, retry() se BAHAR rakhna zaroori hai
    import urllib.error as _ue
    try:
        data = _post()
    except _GeminiTTSRateLimited:
        raise  # turant, koi delay nahi
    except Exception as first_err:
        # Transient error (5xx, timeout) — ek baar aur try
        import time as _time
        log.warn("Gemini TTS pehli koshish fail — 2s baad retry", reason=str(first_err)[:120])
        _time.sleep(2.0)
        try:
            data = _post()
        except _GeminiTTSRateLimited:
            raise
        except Exception as e:
            log.error("Gemini TTS generateContent 2 koshishon ke baad bhi fail", e)
            raise

    try:
        b64_pcm = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        return base64.b64decode(b64_pcm)
    except Exception as e:
        txt = ""
        try:
            txt = data["candidates"][0]["content"]["parts"][0].get("text", "")
        except Exception:
            pass
        raise RuntimeError(f"Gemini TTS audio data nahi mila: {txt[:100]} ({e})") from e


def _apply_speaker_audio_style(mp3_path: Path, speaker: str, emotion: str, role: str):
    """
    Per-speaker audio processing:
    - Narrator: dry, compressor + highpass
    - Characters: subtle room feel (aecho=0.8:0.7:40:0.25)
    - Whisper/reveal: volume +2dB, lowpass=f=6000
    """
    filters = []
    if speaker == "narrator":
        filters.append("highpass=f=80,acompressor=threshold=0.12:ratio=3:attack=5:release=50")
    else:
        filters.append("aecho=0.8:0.7:40:0.25")

    if role == "reveal" or emotion == "whispers":
        filters.append("volume=1.25,lowpass=f=6000")

    if not filters:
        return

    chain = ",".join(filters)
    tmp_path = mp3_path.with_suffix(".filtered.mp3")
    cmd = [
        ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(mp3_path), "-af", chain,
        "-codec:a", "libmp3lame", "-b:a", "128k", str(tmp_path)
    ]
    try:
        subprocess.run(cmd, stdin=subprocess.DEVNULL, check=True, capture_output=True, timeout=30)
        if tmp_path.exists() and tmp_path.stat().st_size > 0:
            tmp_path.replace(mp3_path)
    except Exception as e:
        log.warn("Speaker filter apply fail — raw audio used", reason=str(e)[:80])
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------
def _is_reveal(text: str) -> bool:
    low = " " + text.lower()
    return any(m in low for m in REVEAL_MARKERS)


_VOWELS = "aeiouAEIOUअआइईउऊएऐओऔािीुूेैोौ"


def _syllables(word: str) -> int:
    """
    Mota-moti syllable count — bolne ka time isse proportional hota hai.
    Devanagari mein har vowel-sign ek matra = ek beat. Latin mein vowel groups.
    """
    w = re.sub(r"[^\w\u0900-\u097F]", "", word)
    if not w:
        return 1
    if re.search(r"[\u0900-\u097F]", w):
        # Devanagari: consonants (jinpe halant nahi) + vowel signs
        n = len(re.findall(r"[\u0915-\u0939\u0958-\u095F]", w)) - len(re.findall(r"\u094D", w))
        n += len(re.findall(r"[\u0905-\u0914]", w))
        return max(1, n)
    n = len(re.findall(r"[aeiouAEIOU]+", w))
    return max(1, n)


def _distribute_words(text: str, start: float, end: float) -> list[dict]:
    """
    Line ke andar words ko syllable-weight ke hisaab se time do.
    Line boundaries EXACT hain; andar ka split approximate (±80ms) hai.
    Karaoke highlight ke liye ye kaafi accha lagta hai.
    """
    words = [w for w in text.split() if w]
    if not words:
        return []
    weights = [_syllables(w) + 0.35 for w in words]   # +0.35 = har word ka fixed overhead
    total_w = sum(weights)
    span = max(0.05, end - start)
    out, t = [], start
    for w, wt in zip(words, weights):
        d = span * wt / total_w
        out.append({"w": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    out[-1]["end"] = round(end, 3)   # rounding drift theek karo
    return out


_WHISPER_MODEL = None
_WHISPER_LOCK = threading.Lock()

def _get_whisper_model():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        with _WHISPER_LOCK:
            if _WHISPER_MODEL is None:
                from faster_whisper import WhisperModel
                _WHISPER_MODEL = WhisperModel("base", device="cpu", compute_type="int8")
    return _WHISPER_MODEL


def _align_words_whisper(audio_path: str | Path, text: str, start: float, end: float) -> list[dict] | None:
    """
    Optional faster-whisper word timing.
    Agar faster-whisper installed hai to use karo, warna None (fallback to syllable-weight).
    """
    p = Path(audio_path)
    if not p.exists() or p.stat().st_size == 0:
        return None
    try:
        model = _get_whisper_model()
        segments, _ = model.transcribe(str(p), word_timestamps=True, language="hi")
        words_out = []
        for segment in segments:
            for word in segment.words:
                w_text = word.word.strip()
                if w_text:
                    words_out.append({
                        "w": w_text,
                        "start": round(start + word.start, 3),
                        "end": round(start + word.end, 3),
                    })
        if words_out:
            return words_out
    except Exception as e:
        log.debug(f"faster-whisper word alignment skip ({str(e)[:80]}) — syllable-weight use kar rahe hain")
    return None



if __name__ == "__main__":
    v = Voice()
    r = v.narrate(["Is gaon ke chaudah log ek hi raat mein gayab ho gaye.",
                   "Police pahunchi to darwaze andar se band the.",
                   "Lekin chai abhi bhi garam thi."],
                  "output/_test_voice")
    print(json.dumps({k: r[k] for k in ("voice_id", "duration_sec", "engines_used")},
                     indent=2, ensure_ascii=False))
    for ln in r["lines"]:
        print(f"  {ln['start']:5.2f}-{ln['end']:5.2f}  {ln['text'][:50]}")
