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
COL_GOLD = "&H0000D7FF"    # highlight colour (BGR: FF D7 00 = amber/gold)
COL_BLACK = "&H00000000"
COL_SHADOW = "&H96000000"  # semi-transparent black

FONT_NAME = "Noto Sans Devanagari"   # assets/fonts se load hota hai


def _ts(sec: float) -> str:
    """Seconds -> ASS timestamp H:MM:SS.cc"""
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _esc(text: str) -> str:
    """ASS ke special characters escape karo."""
    return (text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")
            .replace("\n", " ").strip())


def build_ass(words: list[dict], hook_text: str, out_path: str | Path,
              *, width: int = 1080, height: int = 1920,
              hook_duration: float = 3.0, words_per_group: int = 4,
              font: str = FONT_NAME) -> Path:
    """
    words: [{"w": "shabd", "start": 1.2, "end": 1.6}, ...]  (voice.py se aata hai)
    hook_text: 5-8 shabd ka curiosity-gap overlay (writer.py se)

    Return: bani hui .ass file ka path
    """
    out_path = Path(out_path)

    # Font size resolution ke hisaab se — mobile pe padhne layak hona chahiye
    sub_size = int(height * 0.039)    # 1920 -> ~74px
    hook_size = int(height * 0.045)   # 1920 -> ~86px

    head = f"""[Script Info]
; AUTOPILOT ne banaya — karaoke subtitles
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
; Sub  = neeche wale karaoke subtitles (Alignment 2 = bottom-center)
Style: Sub,{font},{sub_size},{COL_WHITE},{COL_GOLD},{COL_BLACK},{COL_SHADOW},-1,0,0,0,100,100,0,0,1,5,3,2,90,90,300,1
; Hook = upar wala curiosity-gap overlay (Alignment 8 = top-center, top third mein)
Style: Hook,{font},{hook_size},{COL_GOLD},{COL_GOLD},{COL_BLACK},{COL_SHADOW},-1,0,0,0,100,100,0,0,1,6,4,8,80,80,{int(height*0.14)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = []

    # ---------- LAYER 1: hook overlay (pehle 3 second) ----------
    if hook_text:
        lines.append(
            f"Dialogue: 1,{_ts(0.15)},{_ts(hook_duration)},Hook,,0,0,0,,"
            f"{{\\fad(180,250)}}{_esc(hook_text)}")

    # ---------- LAYER 2: karaoke subtitles ----------
    if not words:
        log.warn("Koi word timing nahi mili — sirf hook overlay banega")
    for group in _group_words(words, words_per_group):
        start = group[0]["start"]
        end = group[-1]["end"]
        if end <= start:
            continue
        # \k tag ki unit = centiseconds. Har shabd ka apna \k duration.
        parts = []
        for w in group:
            cs = max(1, int(round((w["end"] - w["start"]) * 100)))
            parts.append(f"{{\\k{cs}}}{_esc(w['w'])}")
        text = " ".join(parts)
        # \fad se soft entry/exit — jhatka nahi lagta
        lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end + 0.08)},Sub,,0,0,0,,"
                     f"{{\\fad(90,90)}}{text}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    log.ok(f"Subtitles ready: {len(lines)} events", file=out_path.name,
           words=len(words), hook=bool(hook_text))
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


def _srt_ts(sec: float) -> str:
    sec = max(0.0, sec)
    h, m = int(sec // 3600), int((sec % 3600) // 60)
    s, ms = int(sec % 60), int(round((sec % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


if __name__ == "__main__":
    demo = [{"w": w, "start": i * 0.4, "end": i * 0.4 + 0.38}
            for i, w in enumerate("Is gaon ke chaudah log gayab ho gaye".split())]
    p = build_ass(demo, "14 log. Ek raat. Zero saboot.", "output/_demo.ass")
    print(p.read_text()[:900])
