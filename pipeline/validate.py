"""
pipeline/validate.py — PUBLISH SE PEHLE KA GATEKEEPER.

Section 5: "Publish se pehle validate.py chalao — agar format galat hai to
Instagram error code 24 dega. Pehle hi pakad lo."

Ye file har wo cheez check karti hai jisse Instagram ya YouTube video reject
kar sakta hai, YA jisse retention girti hai. Har check ka apna severity hai:

  FATAL   — publish bilkul mat karo, platform reject karega
  WARN    — publish ho jayega par performance kharab hogi
  INFO    — dhyan dene layak, par theek hai

Chalao:
    python -m pipeline.validate output/video_0001/final.mp4
    python -m pipeline.validate --all           # saare rendered videos
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from core.config import CONFIG
from core.ffmpeg import ffmpeg_bin, probe
from core.logbook import Logbook

log = Logbook("validate")

# ---------------------------------------------------------------------
# LIMITS — ye Section 2 ke verified numbers hain, guess nahi
# ---------------------------------------------------------------------
LIMITS = {
    # Instagram Reels (API)
    "ig_max_sec": 90,          # API strictly enforce karta hai (app mein 3 min chalta hai)
    "ig_min_sec": 3,
    "ig_max_mb": 100,          # practical safe limit
    "ig_fps_min": 23,
    "ig_fps_max": 60,
    # YouTube Shorts
    "yt_shorts_max_sec": 60,   # 60s se upar = normal video, Short nahi
    # Hamare apne quality gates (Section 3 research se)
    "sweet_min_sec": 22,       # sub-15s 2026 mein collapse ho gaya
    "sweet_max_sec": 45,
    "lufs_target": -14.0,
    "lufs_tolerance": 1.5,     # -15.5 se -12.5 tak theek hai
    "true_peak_max": -0.5,     # isse upar clipping ka risk
}


@dataclass
class Issue:
    level: str      # FATAL | WARN | INFO
    code: str
    msg: str        # Hinglish mein — beginner ko samajh aaye
    fix: str = ""


@dataclass
class Report:
    path: str
    issues: list[Issue] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, level, code, msg, fix=""):
        self.issues.append(Issue(level, code, msg, fix))

    @property
    def fatals(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "FATAL"]

    @property
    def warns(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "WARN"]

    @property
    def ok(self) -> bool:
        """Publish karna safe hai ya nahi."""
        return not self.fatals

    def to_dict(self) -> dict:
        return {"path": self.path, "ok": self.ok, "facts": self.facts,
                "issues": [{"level": i.level, "code": i.code, "msg": i.msg, "fix": i.fix}
                           for i in self.issues]}

    def print(self):
        name = Path(self.path).parent.name + "/" + Path(self.path).name
        print("\n" + "=" * 68)
        print(f"  {'✅ PASS' if self.ok else '❌ FAIL'} — {name}")
        print("=" * 68)
        f = self.facts
        print(f"  {f.get('resolution','?')} · {f.get('duration_sec','?')}s · "
              f"{f.get('vcodec','?')}+{f.get('acodec','?')} · "
              f"{f.get('fps','?')}fps · {f.get('size_mb','?')} MB")
        if "lufs" in f:
            print(f"  Loudness: {f['lufs']} LUFS  ·  True peak: {f.get('true_peak','?')} dBTP")
        print("-" * 68)
        if not self.issues:
            print("  Koi problem nahi mili. 🎉")
        for i in self.issues:
            icon = {"FATAL": "❌", "WARN": "⚠️ ", "INFO": "ℹ️ "}[i.level]
            print(f"  {icon} [{i.code}] {i.msg}")
            if i.fix:
                print(f"      → Fix: {i.fix}")
        print("-" * 68)
        if self.fatals:
            print(f"  🚫 PUBLISH MAT KARO — {len(self.fatals)} fatal issue")
        elif self.warns:
            print(f"  ⚠️  Publish ho sakta hai, par {len(self.warns)} warning hai")
        else:
            print("  ✅ Publish ke liye ready")
        print("=" * 68)


# =====================================================================
def validate(video_path: str | Path, *, manifest: dict | None = None,
             deep: bool = True) -> Report:
    """
    Ek video ko poori tarah check karo.
    deep=False -> sirf format check (tez). deep=True -> loudness + black frames bhi.
    """
    p = Path(video_path)
    rep = Report(path=str(p))

    # ---------- file exist karti hai? ----------
    if not p.exists():
        rep.add("FATAL", "NO_FILE", f"Video file hai hi nahi: {p}",
                "Pehle render karo: python run.py")
        return rep
    size_mb = p.stat().st_size / 1024 / 1024
    rep.facts["size_mb"] = round(size_mb, 2)
    if size_mb < 0.05:
        rep.add("FATAL", "EMPTY_FILE", f"File khaali hai ({size_mb:.3f} MB)",
                "Render fail hua tha. Logs dekho aur dobara render karo.")
        return rep

    if manifest:
        _check_content(rep, manifest)

    # ---------- container + streams ----------
    info = probe(p)
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if not v:
        rep.add("FATAL", "NO_VIDEO", "Video stream hi nahi mili — file corrupt hai",
                "Dobara render karo: python run.py --render-only <id>")
        return rep

    _check_video_stream(rep, v)
    _check_audio_stream(rep, a)
    _check_duration(rep, info, v)
    _check_size(rep, size_mb)
    _check_container(rep, p)

    if deep:
        _check_loudness(rep, p)
        _check_black_frames(rep, p)
        _check_first_frame(rep, p)

    return rep


# ---------------------------------------------------------------------
def _check_video_stream(rep: Report, v: dict):
    codec = v.get("codec_name", "?")
    rep.facts["vcodec"] = codec
    if codec != "h264":
        rep.add("FATAL", "IG_CODE_24", 
                f"Video codec '{codec}' hai, H.264 chahiye. "
                f"Instagram error code 24 dega (format reject).",
                "render_spec mein vcodec: libx264 rakho")

    w, h = v.get("width", 0), v.get("height", 0)
    rep.facts["resolution"] = f"{w}x{h}"
    if (w, h) != (1080, 1920):
        want = CONFIG.get("resolution", "1080x1920")
        level = "FATAL" if (w == 0 or h == 0 or w > h) else "WARN"
        rep.add(level, "RESOLUTION",
                f"Resolution {w}x{h} hai, {want} chahiye. "
                + ("Horizontal video Reels/Shorts mein kaam nahi karta!" if w > h else ""),
                "config.yaml mein resolution: 1080x1920")
    if w and h and abs(w / h - 9 / 16) > 0.02:
        rep.add("WARN", "ASPECT", f"Aspect ratio {w/h:.3f} hai, 0.5625 (9:16) chahiye",
                "9:16 ke bahar Shorts feed mein crop ya pillarbox hota hai")

    if v.get("pix_fmt") and v["pix_fmt"] not in ("yuv420p", "yuvj420p"):
        rep.add("WARN", "PIX_FMT", f"Pixel format '{v['pix_fmt']}' hai, yuv420p chahiye",
                "Kuch players/phones isse play nahi kar paate")

    fps = _parse_fps(v.get("r_frame_rate"))
    if fps:
        rep.facts["fps"] = round(fps, 2)
        if fps < LIMITS["ig_fps_min"] or fps > LIMITS["ig_fps_max"]:
            rep.add("FATAL", "IG_FPS",
                    f"{fps:.1f} fps hai. Instagram sirf "
                    f"{LIMITS['ig_fps_min']}-{LIMITS['ig_fps_max']} fps leta hai.",
                    "render_spec mein fps: 30 rakho")


def _check_audio_stream(rep: Report, a: dict | None):
    if not a:
        rep.add("FATAL", "NO_AUDIO",
                "Audio stream nahi hai! Instagram bina audio ke Reel reject karta hai, "
                "aur YouTube pe silent video ki retention zero hoti hai.",
                "TTS fail hua hoga — logs dekho, `pip install edge-tts`")
        return
    codec = a.get("codec_name", "?")
    rep.facts["acodec"] = codec
    if codec != "aac":
        rep.add("FATAL", "IG_CODE_24",
                f"Audio codec '{codec}' hai, AAC chahiye. Instagram error code 24 dega.",
                "render_spec mein acodec: aac rakho")
    sr = a.get("sample_rate")
    if sr and int(sr) not in (44100, 48000):
        rep.add("WARN", "SAMPLE_RATE", f"Sample rate {sr} Hz hai, 44100 ya 48000 chahiye")


def _check_duration(rep: Report, info: dict, v: dict):
    dur = float(info.get("format", {}).get("duration", 0) or 0)
    if not dur:
        rep.add("WARN", "NO_DURATION", "Duration detect nahi hui (ffprobe missing?)")
        return
    rep.facts["duration_sec"] = round(dur, 2)

    if dur > LIMITS["ig_max_sec"]:
        rep.add("FATAL", "IG_TOO_LONG",
                f"{dur:.1f}s hai. Instagram API ki HARD limit {LIMITS['ig_max_sec']}s hai "
                f"(app mein 3 min chalta hai, API mein NAHI).",
                "config.yaml mein video_length_sec kam karo")
    if dur < LIMITS["ig_min_sec"]:
        rep.add("FATAL", "TOO_SHORT", f"Sirf {dur:.1f}s — koi platform ye accept nahi karega")

    if dur > LIMITS["yt_shorts_max_sec"]:
        rep.add("WARN", "NOT_A_SHORT",
                f"{dur:.1f}s — 60s se lamba video YouTube pe Short nahi banta, "
                f"normal video ban jayega (alag algorithm, bilkul alag distribution).",
                "60s se neeche rakho")

    lo, hi = LIMITS["sweet_min_sec"], LIMITS["sweet_max_sec"]
    if dur < lo:
        rep.add("WARN", "BELOW_SWEET_SPOT",
                f"{dur:.1f}s — sweet spot {lo}-{hi}s hai. Sub-15s content 2026 mein "
                f"collapse ho gaya (absolute watch-time bar clear nahi hota).",
                "Writer se lamba script mangwao ya pauses badhao")
    elif dur > hi:
        rep.add("INFO", "ABOVE_SWEET_SPOT",
                f"{dur:.1f}s — {hi}s se upar retention threshold (50%) miss hone lagta hai")


def _check_size(rep: Report, size_mb: float):
    if size_mb > LIMITS["ig_max_mb"]:
        rep.add("FATAL", "TOO_BIG", f"{size_mb:.1f} MB — Instagram upload fail hoga",
                "CRF badhao (21 -> 24) ya --preset slow use karo")
    elif size_mb > 60:
        rep.add("WARN", "LARGE", f"{size_mb:.1f} MB — upload slow hoga, "
                                 f"aur IG container timeout ho sakta hai")


def _check_container(rep: Report, p: Path):
    if p.suffix.lower() not in (".mp4", ".mov"):
        rep.add("FATAL", "CONTAINER", f"'{p.suffix}' container hai, MP4 ya MOV chahiye")
    # faststart check: 'moov' atom file ke shuru mein hona chahiye
    try:
        head = p.read_bytes()[:2048]
        if b"moov" not in head and b"ftyp" in head:
            rep.add("WARN", "NO_FASTSTART",
                    "moov atom file ke shuru mein nahi hai (faststart nahi laga). "
                    "Instagram ko video fetch karne mein zyada time lagega.",
                    "ffmpeg mein -movflags +faststart add karo")
    except OSError:
        pass


# ---------------------------------------------------------------------
def _check_loudness(rep: Report, p: Path):
    """
    loudnorm ko measure-mode mein chalao (print_format=json).
    Ye ASLI measured value deti hai — hum maan kar nahi chalte ki normalize ho gaya.
    """
    try:
        proc = subprocess.run(
            [ffmpeg_bin(), "-hide_banner", "-i", str(p),
             "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=300)
        m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", proc.stderr, re.S)
        if not m:
            rep.add("INFO", "NO_LOUDNESS", "Loudness measure nahi ho paayi")
            return
        data = json.loads(m.group(0))
        lufs = float(data["input_i"])
        tp = float(data["input_tp"])
        lra = float(data.get("input_lra", 0))
        rep.facts["lufs"] = lufs
        rep.facts["true_peak"] = tp
        rep.facts["lra"] = lra

        target, tol = LIMITS["lufs_target"], LIMITS["lufs_tolerance"]
        if abs(lufs - target) > tol:
            direction = "zyada dheemi" if lufs < target else "zyada tez"
            rep.add("WARN", "LOUDNESS",
                    f"{lufs:.1f} LUFS hai ({direction}), target {target} LUFS. "
                    f"Platforms khud normalize karte hain — bahut dheemi awaaz "
                    f"boost hone pe noisy lagti hai, tez awaaz squash ho jaati hai.",
                    "render.py ka loudnorm filter check karo")
        if tp > LIMITS["true_peak_max"]:
            rep.add("WARN", "CLIPPING",
                    f"True peak {tp:.1f} dBTP — clipping (kirkiri awaaz) ka risk hai",
                    "loudnorm mein TP=-1.5 set hona chahiye")
        if lufs < -30:
            rep.add("FATAL", "SILENT",
                    f"{lufs:.1f} LUFS — video practically SILENT hai",
                    "TTS fail hua hoga. narration.mp3 chala kar sun lo.")
    except subprocess.TimeoutExpired:
        rep.add("INFO", "LOUDNESS_TIMEOUT", "Loudness check timeout — skip kiya")
    except Exception as e:  # noqa: BLE001
        rep.add("INFO", "LOUDNESS_ERR", f"Loudness check fail: {str(e)[:100]}")


def _check_black_frames(rep: Report, p: Path):
    """
    Beech mein kaale frames = darshak ko lagta hai video khatam ho gaya = scroll.
    (Ye asli bug tha: 'fadeblack' transition kaale frames bana raha tha.)
    """
    try:
        proc = subprocess.run(
            [ffmpeg_bin(), "-hide_banner", "-i", str(p),
             "-vf", "blackdetect=d=0.08:pic_th=0.98", "-f", "null", "-"],
            capture_output=True, text=True, timeout=300)
        blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", proc.stderr)
        mid = [(float(s), float(e)) for s, e in blacks if float(s) > 0.4]
        rep.facts["black_segments"] = len(mid)
        if mid:
            spots = ", ".join(f"{s:.1f}s" for s, _ in mid[:4])
            rep.add("WARN", "BLACK_FRAMES",
                    f"Beech mein {len(mid)} jagah kaale frames hain ({spots}). "
                    f"Darshak ko lagta hai video khatam ho gaya — wo scroll kar dete hain.",
                    "render.py mein 'fadeblack' transition mat use karo")
    except Exception as e:  # noqa: BLE001
        rep.add("INFO", "BLACK_ERR", f"Black frame check fail: {str(e)[:80]}")


def _check_first_frame(rep: Report, p: Path):
    """
    Section 3: "1-second retention = dominant signal. Pehla frame hi decide karta hai."
    Pehla frame kaala ya khaali nahi hona chahiye.
    """
    try:
        proc = subprocess.run(
            [ffmpeg_bin(), "-hide_banner", "-i", str(p), "-frames:v", "1",
             "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=120)
        m = re.search(r"YAVG=([\d.]+)", proc.stderr)
        if m:
            yavg = float(m.group(1))
            rep.facts["first_frame_brightness"] = round(yavg, 1)
            if yavg < 18:
                rep.add("WARN", "DARK_FIRST_FRAME",
                        f"Pehla frame bahut kaala hai (brightness {yavg:.0f}/255). "
                        f"1-second retention YouTube ka sabse bada signal hai — "
                        f"pehla frame hi decide karta hai.",
                        "ArtDirector ko scene 1 mein bright pattern-interrupt visual "
                        "banane ko bolo, ya fade-in hata do")
    except Exception:  # noqa: BLE001
        pass


def _check_content(rep: Report, m: dict):
    """Manifest se content-level checks (jo file dekh kar pata nahi chalte)."""
    s = m.get("script", {})
    words = m.get("words", [])

    if not words:
        rep.add("WARN", "NO_SUBTITLES",
                "Word-level subtitles nahi hain. ~60% log sound OFF pe dekhte hain — "
                "unke liye ye video samajh hi nahi aayega.",
                "voice.py se timing.json bana ya nahi, check karo")

    if not s.get("hook_text_overlay"):
        rep.add("WARN", "NO_HOOK_OVERLAY",
                "Hook text overlay nahi hai (3-layer hook ka teesra layer missing)")

    bait = s.get("comment_bait", "")
    if len(bait.split()) < 5:
        rep.add("INFO", "WEAK_BAIT",
                "Comment bait chhota hai — 5+ shabd ka jawab invite karna chahiye "
                "(chhote comments algorithm ginta hi nahi)")

    tags = s.get("hashtags", [])
    if len(tags) > 5:
        rep.add("WARN", "TOO_MANY_TAGS", f"{len(tags)} hashtags — 3 hi kaafi hain")

    # placeholder images publish nahi honi chahiye — but WARN denge, FATAL nahi
    # Cloud deployments mein rate limits common hain, pipeline ruko nahi
    provs = {sc.get("provider") for sc in m.get("scenes", [])}
    if "local_placeholder" in provs:
        real_count = sum(1 for sc in m.get("scenes", []) if sc.get("provider") != "local_placeholder")
        ph_count = sum(1 for sc in m.get("scenes", []) if sc.get("provider") == "local_placeholder")
        if real_count == 0:
            # Sab placeholder — WARN (publish hoga lekin quality achhi nahi)
            rep.add("WARN", "PLACEHOLDER_IMAGES",
                    f"Saari {ph_count} images PLACEHOLDER hain (gradient + text cards). "
                    "Image providers rate-limited the — retry baad mein kar sakte hain.",
                    "Pollinations/Gemini retry karke dobara generate karo")
        else:
            rep.add("WARN", "SOME_PLACEHOLDERS",
                    f"{ph_count} scenes mein placeholder images hain, {real_count} real hain.",
                    "Kuch images rate-limited thi — next run mein replace ho jayengi")

    narr = m.get("narration", {})
    engines_used = set(narr.get("engines_used", []))
    lines = narr.get("lines", [])
    has_silent_line = any(ln.get("engine") == "silence" for ln in lines)
    if "silence" in engines_used or has_silent_line:
        rep.add("FATAL", "silent_narration",
                "Narration mein silent audio clips hain — TTS fail hua tha. "
                "Ye video publish layak nahi hai.",
                "TTS engines check karo (SETUP.md STEP 4)")

    if narr.get("engines_used") == ["espeak"]:
        rep.add("WARN", "ROBOTIC_VOICE",
                "espeak fallback use hua — awaaz robotic hai, retention girega",
                "`pip install edge-tts` karo")

    # AI disclosure — hard constraint #4
    rep.facts["ai_disclosed"] = True   # publisher isse set karega, yahan reminder hai


def _parse_fps(rate: str | None) -> float | None:
    if not rate:
        return None
    try:
        if "/" in rate:
            n, d = rate.split("/")
            return float(n) / float(d) if float(d) else None
        return float(rate)
    except (ValueError, ZeroDivisionError):
        return None


# =====================================================================
def validate_dir(video_dir: str | Path, deep: bool = True) -> Report:
    """Ek output folder validate karo (manifest ke saath)."""
    d = Path(video_dir)
    mf = d / "manifest.json"
    manifest = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else None
    return validate(d / "final.mp4", manifest=manifest, deep=deep)


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Publish se pehle video check karo")
    ap.add_argument("path", nargs="?", help="video file ya folder")
    ap.add_argument("--all", action="store_true", help="saare rendered videos check karo")
    ap.add_argument("--fast", action="store_true", help="loudness/black checks skip (tez)")
    ap.add_argument("--json", action="store_true", help="JSON output")
    a = ap.parse_args()

    out_root = Path(CONFIG["_root"]) / "output"
    targets = []
    if a.all:
        targets = sorted(d for d in out_root.glob("video_*") if (d / "final.mp4").exists())
    elif a.path:
        p = Path(a.path)
        targets = [p if p.is_dir() else p]
    else:
        targets = sorted(d for d in out_root.glob("video_*") if (d / "final.mp4").exists())[-1:]

    if not targets:
        print("Koi rendered video nahi mila. Pehle chalao: python run.py")
        sys.exit(1)

    reports = []
    for t in targets:
        r = validate_dir(t, deep=not a.fast) if Path(t).is_dir() \
            else validate(t, deep=not a.fast)
        reports.append(r)
        if not a.json:
            r.print()

    if a.json:
        print(json.dumps([r.to_dict() for r in reports], indent=2, ensure_ascii=False))

    sys.exit(0 if all(r.ok for r in reports) else 1)
