"""
pipeline/subtitles.py — word-by-word karaoke subtitles (ASS format).

Section 5 #4: "Animated subtitles — word-by-word highlight (karaoke style),
sirf static text nahi."
Section 3: "~60% log sound off pe dekhte hain -> text overlay har video mein zaroori."

Kyun ASS aur SRT nahi?
  SRT sirf static text de sakta hai. ASS mein `{\\k}` karaoke tags hote hain jo
  har shabd ko uske bolne ke time pe highlight karte hain — exactly wahi jo chahiye.
  ffmpeg ka `ass` filter libass se ye render karta hai (ye har build mein hota hai,
  jabki `drawtext` bahut builds mein missing hota hai — maine test kiya).

Do layers bante hain:
  1. HOOK overlay — pehle 1.5-3s, screen ke upar wale tihaai (top third) mein,
     bada + high contrast (Section 3 ka 3-layer hook ka teesra layer)
  2. Karaoke subtitles — neeche, har shabd bolte waqt highlight
"""

from __future__ import annotations

from pathlib import Path

from core.logbook import Logbook

log = Logbook("subtitles")

# ASS colours &HAABBGGRR format mein hote hain (BGR, RGB nahi! — aur AA = 00 matlab opaque)
COL_WHITE = "&H00FFFFFF"
COL_GOLD = "&H0000D7FF"    # BGR: FF D7 00 = amber/gold
COL_RED = "&H00303BFF"     # BGR: FF 3B 30 = crimson red
COL_PINK = "&H00552DFF"    # BGR: FF 2D 55 = hot pink/rose
COL_CYAN = "&H00FFFF00"    # BGR: 00 FF FF = vibrant cyan
COL_EMERALD = "&H0050FF00" # BGR: 00 FF 50 = neon emerald green
COL_BLACK = "&H00000000"
COL_SHADOW = "&HB4000000"  # deep black drop shadow

FONT_NAME = "Noto Sans Devanagari"   # assets/fonts se load hota hai

DANGER_KEYWORDS = {"maut", "khoon", "mar", "qatil", "danger", "loop", "dead", "laash", "blade", "fire", "toot", "khatam", "aag", "cheekh", "qurban", "marenge", "shrap"}
ROMANCE_KEYWORDS = {"pyaar", "dil", "meera", "love", "smile", "muskaan", "halka", "beautiful", "saadgi", "masoomiyat", "blush", "dhadak", "hum", "nazrein", "promise", "shaadi"}
MYSTERY_KEYWORDS = {"raaz", "sach", "3:17", "3:18", "3:16", "clock", "ghadi", "waqt", "number", "notification", "follow", "dots", "screen", "hi", "roman", "lever", "core", "shadow"}
COMEDY_KEYWORDS = {"funny", "galat", "sawal", "chammach", "paheli", "score", "dimag", "dahi", "chintu", "golu", "donut", "chocolate", "jadui", "pencil", "fail", "answer"}


def _ts(sec: float) -> str:
    """Seconds -> ASS timestamp H:MM:SS.cs (centiseconds).
    Handles durations > 10m / 1hr correctly with proper rollover.
    """
    sec = max(0.0, float(sec))
    cs = int(round(sec * 100))
    s, cs = divmod(cs, 100)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(text: str) -> str:
    """ASS ke special characters escape karo."""
    return (text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")
            .replace("\n", " ").strip())


def build_ass(words: list[dict], hook_text: str, out_path: str | Path,
              *, width: int = 1080, height: int = 1920,
              hook_duration: float = 3.0, words_per_group: int | None = None,
              font: str = FONT_NAME, style: str = "karaoke") -> Path:
    """
    words: [{"w": "shabd", "start": 1.2, "end": 1.6}, ...]  (voice.py se aata hai)
    hook_text: 5-8 shabd ka curiosity-gap overlay (writer.py se)
    style: "kinetic" (viral 1-2 word pop-bounce in center) ya "karaoke" (bottom line)

    Return: bani hui .ass file ka path
    """
    out_path = Path(out_path)

    # Resolution-adjusted sizes
    hook_size = int(height * 0.046)   # ~88px

    if style == "kinetic":
        sub_size = int(height * 0.052)     # ~100px (Bold, center eye-line)
        margin_v = int(height * 0.40)      # Center-lower (~768px from bottom)
        outline_w = 6
        shadow_d = 4
        group_size = words_per_group or 2  # 1-2 words per burst
    elif style == "clean":
        sub_size = int(height * 0.038)     # Clean, elegant size for longform
        margin_v = int(height * 0.08)      # Bottom-centered
        outline_w = 3
        shadow_d = 2
        group_size = words_per_group or 7  # 6-8 words per chunk (max 2 lines)
    else:
        sub_size = int(height * 0.039)     # ~74px
        margin_v = 300
        outline_w = 5
        shadow_d = 3
        group_size = words_per_group or 4

    head = f"""[Script Info]
; AUTOPILOT ne banaya — kinetic subtitles ({style})
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
; Sub = subtitles (Alignment 2 = bottom-center)
Style: Sub,{font},{sub_size},{COL_WHITE},{COL_GOLD},{COL_BLACK},{COL_SHADOW},-1,0,0,0,100,100,0,0,1,{outline_w},{shadow_d},2,70,70,{margin_v},1
; Hook = upar wala curiosity-gap overlay (Alignment 8 = top-center)
Style: Hook,{font},{hook_size},{COL_GOLD},{COL_GOLD},{COL_BLACK},{COL_SHADOW},-1,0,0,0,100,100,0,0,1,6,4,8,80,80,{int(height*0.14)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = []

    # ---------- LAYER 1: hook overlay (pehle 3 second) ----------
    if hook_text and style != "clean":
        lines.append(
            f"Dialogue: 1,{_ts(0.15)},{_ts(hook_duration)},Hook,,0,0,0,,"
            f"{{\\fad(180,250)}}{_esc(hook_text)}")

    # ---------- LAYER 2: kinetic / karaoke / clean subtitles ----------
    if not words:
        log.warn("Koi word timing nahi mili — sirf hook overlay banega")

    import re
    for group in _group_words(words, group_size):
        start = group[0]["start"]
        end = group[-1]["end"]
        if end <= start:
            continue

        if style == "kinetic":
            # Kinetic Center Pop: 1-2 words with scale-bounce and keyword color
            parts = []
            for w in group:
                raw_w = w["w"]
                clean_w = re.sub(r"[^\w:]", "", raw_w.lower())
                
                # Check semantic category
                if clean_w in DANGER_KEYWORDS:
                    col_tag = f"{{\\1c{COL_RED}&}}"
                    suffix = " 💥" if len(group) == 1 else ""
                elif clean_w in ROMANCE_KEYWORDS:
                    col_tag = f"{{\\1c{COL_PINK}&}}"
                    suffix = " ❤️" if len(group) == 1 else ""
                elif clean_w in MYSTERY_KEYWORDS:
                    col_tag = f"{{\\1c{COL_GOLD}&}}"
                    suffix = " ⚡" if len(group) == 1 else ""
                elif clean_w in COMEDY_KEYWORDS:
                    col_tag = f"{{\\1c{COL_EMERALD}&}}"
                    suffix = " ✨" if len(group) == 1 else ""
                else:
                    col_tag = f"{{\\1c{COL_WHITE}&}}"
                    suffix = ""
                
                parts.append(f"{col_tag}{_esc(raw_w)}{suffix}")

            inner_text = " ".join(parts)
            # ASS scale bounce: dynamic pop at 125% scale for 70ms then settle to 100%
            bounce_tag = "{\\fscx125\\fscy125\\t(0,70,\\fscx100\\fscy100)}"
            lines.append(
                f"Dialogue: 0,{_ts(start)},{_ts(end + 0.05)},Sub,,0,0,0,,"
                f"{bounce_tag}{inner_text}"
            )
        elif style == "clean":
            # Clean longform style: bottom-centred, max 2 lines
            raw_text = " ".join(w["w"] for w in group)
            words_list = raw_text.split()
            if len(raw_text) > 42 and len(words_list) > 3:
                mid = len(words_list) // 2
                line1 = _esc(" ".join(words_list[:mid]))
                line2 = _esc(" ".join(words_list[mid:]))
                display_text = f"{line1}\\N{line2}"
            else:
                display_text = _esc(raw_text)
            lines.append(
                f"Dialogue: 0,{_ts(start)},{_ts(end + 0.05)},Sub,,0,0,0,,"
                f"{{\\fad(60,60)}}{display_text}"
            )
        else:
            # Classic Karaoke: bottom-aligned with word-by-word highlight
            parts = []
            for w in group:
                cs = max(1, int(round((w["end"] - w["start"]) * 100)))
                parts.append(f"{{\\k{cs}}}{_esc(w['w'])}")
            text = " ".join(parts)
            lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end + 0.08)},Sub,,0,0,0,,"
                         f"{{\\fad(90,90)}}{text}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    log.ok(f"Subtitles ready: {len(lines)} events", file=out_path.name,
           words=len(words), hook=bool(hook_text), style=style)
    return out_path


def _group_words(words: list[dict], n: int) -> list[list[dict]]:
    """
    Words ko chhote groups mein todo (ek time pe 3-4 shabd screen pe).
    Rule: agar do words ke beech 0.6s se bada gap hai to wahan naya group
    shuru karo — matlab bolne wale ne saans li, subtitle bhi wahin tootna chahiye.
    """
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= n or w["start"] - cur[-1]["end"] > 0.6):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def build_srt(words: list[dict], out_path: str | Path, words_per_group: int = 4) -> Path:
    """
    Bonus: SRT bhi banao. YouTube pe upload karne ke liye (accessibility +
    search indexing — Shorts ab search mein bhi dikhte hain, Section 8).
    """
    out_path = Path(out_path)
    blocks = []
    for i, g in enumerate(_group_words(words, words_per_group), 1):
        s, e = g[0]["start"], g[-1]["end"]
        blocks.append(f"{i}\n{_srt_ts(s)} --> {_srt_ts(e)}\n"
                      f"{' '.join(w['w'] for w in g)}\n")
    out_path.write_text("\n".join(blocks), encoding="utf-8")
    return out_path


def build_dual_srt(lines: list[dict], out_en: str | Path, out_hi: str | Path) -> tuple[Path, Path]:
    """
    Builds both captions_en.srt and captions_hi.srt for YouTube multi-language CC.
    Enables viewers to toggle between English and Hindi with 1 tap on the CC button.
    """
    out_en = Path(out_en)
    out_hi = Path(out_hi)
    blocks_en, blocks_hi = [], []
    for i, line in enumerate(lines, 1):
        s = line.get("start", (i - 1) * 5.0)
        e = line.get("end", i * 5.0)
        text_en = line.get("text_en") or line.get("text", "")
        text_hi = line.get("text_hi") or line.get("text", "")
        blocks_en.append(f"{i}\n{_srt_ts(s)} --> {_srt_ts(e)}\n{text_en}\n")
        blocks_hi.append(f"{i}\n{_srt_ts(s)} --> {_srt_ts(e)}\n{text_hi}\n")
    out_en.write_text("\n".join(blocks_en), encoding="utf-8")
    out_hi.write_text("\n".join(blocks_hi), encoding="utf-8")
    return out_en, out_hi



def _srt_ts(sec: float) -> str:
    """Seconds -> SRT timestamp HH:MM:SS,mmm (milliseconds).
    Handles durations > 10m / 1hr correctly with proper rollover.
    """
    sec = max(0.0, float(sec))
    ms = int(round(sec * 1000))
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def align_with_groq(audio_path: str | Path, groq_key: str | None = None) -> list[dict] | None:
    """
    Groq Whisper Large v3 se audio transcribe karke exact word-level
    timestamps nikalta hai (0.3s-1.0s response time).

    Return: [{"w": "word", "start": 0.12, "end": 0.45}, ...]
    Agar fail ho ya key na ho -> None (fallback to syllable weighting).
    """
    import json
    import os
    import urllib.request
    from core.config import CONFIG

    audio_path = Path(audio_path)
    if not audio_path.exists() or audio_path.stat().st_size < 1000:
        return None

    key = groq_key or os.environ.get("GROQ_API_KEY") or CONFIG.get("GROQ_API_KEY")
    if not key:
        return None

    try:
        boundary = "----WebKitFormBoundaryAutopilotGroqWhisper"
        body = []

        # model
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="model"\r\n')
        body.append(b"whisper-large-v3")

        # response_format
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="response_format"\r\n')
        body.append(b"verbose_json")

        # timestamp_granularities[]
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="timestamp_granularities[]"\r\n')
        body.append(b"word")

        # file
        body.append(f"--{boundary}".encode())
        body.append(f'Content-Disposition: form-data; name="file"; filename="{audio_path.name}"'.encode())
        body.append(b"Content-Type: audio/mpeg\r\n")
        with open(audio_path, "rb") as f:
            body.append(f.read())

        body.append(f"--{boundary}--\r\n".encode())
        payload = b"\r\n".join(body)

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            data=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "Autopilot/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode())
            raw_words = data.get("words", [])
            if not raw_words:
                return None
            clean_words = []
            for item in raw_words:
                w_str = item.get("word", "").strip()
                if w_str:
                    clean_words.append({
                        "w": w_str,
                        "start": round(float(item.get("start", 0.0)), 3),
                        "end": round(float(item.get("end", 0.0)), 3),
                    })
            if clean_words:
                log.ok(f"Groq Whisper se {len(clean_words)} words frame-accurate align ho gaye!")
                return clean_words
    except Exception as e:
        log.warn(f"Groq Whisper alignment fail ({str(e)[:80]}) — syllable approximation use hogi")
    return None


if __name__ == "__main__":
    demo = [{"w": w, "start": i * 0.4, "end": i * 0.4 + 0.38}
            for i, w in enumerate("Is gaon ke chaudah log gayab ho gaye".split())]
    p = build_ass(demo, "14 log. Ek raat. Zero saboot.", "output/_demo.ass")
    print(p.read_text()[:900])

