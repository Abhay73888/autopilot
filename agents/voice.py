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
import json
import re
import subprocess
import wave
from pathlib import Path

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook
from core.mp3 import duration_sec

log = Logbook("voice")

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
    def narrate(self, lines: list[str], out_dir: str | Path,
                profile_id: str | None = None) -> dict:
        """
        Har line ki alag MP3 banao (exact duration mil jaati hai),
        phir un sabko jodkar narration.mp3 + timing JSON banao.
        """
        profile_id = profile_id or self.pick_profile()
        prof = self.profiles[profile_id]
        out_dir = Path(out_dir)
        (out_dir / "lines").mkdir(parents=True, exist_ok=True)

        clips = []
        for i, line in enumerate(lines):
            path = out_dir / "lines" / f"line_{i+1:02d}.mp3"
            ok = self._synth(line, path, prof)
            dur = duration_sec(path) if path.exists() else 0.0
            if dur <= 0:
                # fail-safe: silent clip banao taaki timing na bigde, par LOUD warning
                dur = max(1.2, len(line.split()) / 2.6)
                log.warn(f"Line {i+1} ka audio nahi bana — {dur:.1f}s silence daal rahe hain",
                         line=line[:60])
                ok = "silence"
            clips.append({"i": i, "text": line, "path": str(path), "dur": dur, "engine": ok})

        timeline = self._build_timeline(clips)
        merged = out_dir / "narration.mp3"
        pauses_applied = self._concat(clips, merged, timeline)

        # ⚠️ SYNC FIX: agar ffmpeg nahi mila to raw concat hua, matlab MP3 mein
        # pauses hain hi nahi. Aise mein timeline ko BINA pauses ke dobara banao,
        # warna subtitles har line pe ~200ms aage khisakte jaayenge (end tak ~1s desync).
        if not pauses_applied:
            timeline = self._build_timeline(clips, no_pauses=True)
            log.warn("Pauses lagaye nahi ja sake (ffmpeg missing) — timeline bina pause ke "
                     "recompute kiya taaki subtitles sync rahein. Suspense pacing "
                     "Phase 3 mein ffmpeg aane ke baad milegi.")

        total = timeline[-1]["end"] if timeline else 0.0
        result = {
            "voice_id": profile_id,
            "voice": prof["voice"],
            "rate": prof["rate"],
            "pitch": prof["pitch"],
            "audio_path": str(merged),
            "duration_sec": round(total, 2),
            "lines": timeline,
            "words": [w for ln in timeline for w in ln["words"]],
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
    def _synth(self, text: str, path: Path, prof: dict) -> str:
        """edge_tts -> gtts -> espeak. Pehla jo chale."""
        errors = []
        for engine in ("edge_tts", "gtts", "espeak"):
            try:
                getattr(self, f"_tts_{engine}")(text, path, prof)
                if path.exists() and path.stat().st_size > 500:
                    return engine
                raise RuntimeError("file khaali bani")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{engine}: {str(e)[:100]}")
                log.debug(f"{engine} fail: {str(e)[:120]}")
        log.error("Saare TTS engines fail: " + " | ".join(errors))
        return ""

    def _tts_edge_tts(self, text: str, path: Path, prof: dict):
        import edge_tts  # optional dep — requirements.txt mein justified hai

        async def run():
            c = edge_tts.Communicate(text, prof["voice"],
                                     rate=prof["rate"], pitch=prof["pitch"])
            with open(path, "wb") as f:
                async for chunk in c.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])

        asyncio.run(run())

    def _tts_gtts(self, text: str, path: Path, prof: dict):
        from gtts import gTTS
        lang = "hi" if prof["voice"].startswith("hi") else "en"
        gTTS(text=text, lang=lang, tld="co.in", slow=False).save(str(path))

    def _tts_espeak(self, text: str, path: Path, prof: dict):
        """Offline last resort. Robotic lagta hai — publish layak nahi, par pipeline chalti rehti hai."""
        wav = path.with_suffix(".wav")
        lang = "hi" if prof["voice"].startswith("hi") else "en-in"
        binary = "espeak-ng"
        subprocess.run([binary, "-v", lang, "-s", "150", "-w", str(wav), text],
                       check=True, capture_output=True, timeout=60)
        # WAV -> MP3 ke liye ffmpeg (agar hai). Nahi hai to WAV hi rakh lo.
        try:
            subprocess.run(["ffmpeg", "-y", "-i", str(wav), "-codec:a", "libmp3lame",
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

        no_pauses=True tab use hota hai jab audio mein pauses daale hi nahi ja sake
        (ffmpeg missing) — tab timeline bhi bina pause ke banni chahiye, warna desync.
        """
        t = 0.0
        out = []
        for c in clips:
            # pause: reveal line se pehle lamba (suspense pacing)
            if no_pauses or c["i"] == 0:
                gap = 0.0
            elif _is_reveal(c["text"]):
                gap = PAUSE_REVEAL_MS / 1000
            elif c["i"] == 1:
                gap = PAUSE_HOOK_MS / 1000
            else:
                gap = PAUSE_DEFAULT_MS / 1000
            start = t + gap
            end = start + c["dur"]
            out.append({
                "i": c["i"], "text": c["text"], "start": round(start, 3), "end": round(end, 3),
                "pause_before": round(gap, 3),
                "words": _distribute_words(c["text"], start, end),
            })
            t = end
        return out

    def _concat(self, clips: list[dict], out_path: Path, timeline: list[dict]) -> bool:
        """
        Sab line-MP3s ko pauses ke saath jodo.
        Return: True agar pauses lag gaye (ffmpeg mila), False agar raw concat hua.

        ffmpeg ho to proper concat (silence ke saath). Nahi ho to raw byte concat —
        MP3 frames ke liye ye chal jaata hai, par pauses nahi milte, isliye caller
        timeline recompute karta hai.
        """
        existing = [c for c in clips if Path(c["path"]).exists()]
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
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
               "-filter_complex", ";".join(filters), "-map", "[out]",
               "-codec:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", str(out_path)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)


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
