"""
core/ffmpeg.py — ffmpeg dhoondhne aur chalane wala helper.

Kyun alag file? Kyunki ffmpeg 3 jagah ho sakta hai aur beginner ko ye pata nahi hota:
  1. System PATH mein (`brew install ffmpeg` / `apt install ffmpeg`) — sabse accha
  2. imageio-ffmpeg package ke andar (pip se aata hai, koi admin permission nahi chahiye)
  3. FFMPEG_BINARY env variable mein (manual path)

Ye file teeno check karti hai aur jo mile use leti hai. Agar kuch na mile to
saaf Hinglish mein batati hai ki kya install karna hai.

Saath mein: har ffmpeg command log hoti hai aur error aane pe ffmpeg ka
asli stderr Hinglish explanation ke saath dikhta hai (silently fail nahi).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path


try:
    from .logbook import Logbook
except ImportError:  # `python core/ffmpeg.py` seedha chalane pe
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.logbook import Logbook

log = Logbook("ffmpeg")


class FFmpegMissing(RuntimeError):
    """ffmpeg mila hi nahi — beginner ko kya karna hai wo message mein hai."""


@lru_cache(maxsize=1)
def ffmpeg_bin() -> str:
    """ffmpeg ka path. Ek baar dhoondh kar yaad rakh leta hai."""
    # 1) manual override
    env = os.environ.get("FFMPEG_BINARY", "").strip()
    if env and Path(env).exists():
        return env
    # 2) system PATH
    found = shutil.which("ffmpeg")
    if found:
        return found
    # 3) pip wala bundled binary
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if Path(p).exists():
            log.info("System ffmpeg nahi mila — imageio-ffmpeg ka bundled binary use kar rahe hain")
            return p
    except Exception:  # noqa: BLE001
        pass
    raise FFmpegMissing(
        "ffmpeg nahi mila. Teen mein se koi ek karo:\n"
        "  1) System install (best):  Mac: `brew install ffmpeg`  |  "
        "Linux: `sudo apt install ffmpeg`  |  Windows: `winget install Gyan.FFmpeg`\n"
        "  2) Bina admin ke:          `pip install imageio-ffmpeg`\n"
        "  3) Manual path:            .env mein FFMPEG_BINARY=/poora/path/ffmpeg daalo\n"
        "Install ke baad terminal band karke naya kholo (PATH refresh ke liye)."
    )


@lru_cache(maxsize=1)
def ffprobe_bin() -> str | None:
    """ffprobe optional hai. Na ho to core/mp3.py se kaam chal jaata hai."""
    env = os.environ.get("FFPROBE_BINARY", "").strip()
    if env and Path(env).exists():
        return env
    return shutil.which("ffprobe")


@lru_cache(maxsize=1)
def capabilities() -> dict:
    """
    ffmpeg ke andar kya-kya hai, wo pata karo. Har build alag hota hai!
    (Is sandbox mein maine dekha: libass hai par drawtext NAHI hai —
     isliye code drawtext pe depend nahi karta, sirf ASS subtitles use karta hai.)
    """
    caps = {"drawtext": False, "ass": False, "zoompan": False, "xfade": False,
            "loudnorm": False, "alimiter": False, "sidechaincompress": False,
            "libx264": False, "aac": False}
    try:
        out = subprocess.run([ffmpeg_bin(), "-hide_banner", "-filters"],
                             capture_output=True, text=True, timeout=30).stdout
        for f in ("drawtext", "ass", "zoompan", "xfade", "loudnorm", "alimiter", "sidechaincompress"):
            caps[f] = f" {f} " in out
        enc = subprocess.run([ffmpeg_bin(), "-hide_banner", "-encoders"],
                             capture_output=True, text=True, timeout=30).stdout
        caps["libx264"] = "libx264" in enc
        caps["aac"] = " aac " in enc
    except Exception as e:  # noqa: BLE001
        log.warn("ffmpeg capabilities check fail hua", reason=str(e)[:120])
    return caps


def run(args: list[str], *, what: str = "ffmpeg", timeout: int = 900,
        quiet: bool = True) -> subprocess.CompletedProcess:
    """
    ffmpeg chalao. Fail ho to asli stderr + Hinglish hint ke saath exception.
    `args` mein 'ffmpeg' shabd mat daalna — wo khud lag jaata hai.
    """
    cmd = [ffmpeg_bin(), "-y", "-nostdin", "-hide_banner",
           "-loglevel", "error" if quiet else "info", *args]
    log.debug(f"RUN {what}", cmd=" ".join(cmd[:14]) + (" ..." if len(cmd) > 14 else ""))
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"{what}: ffmpeg {timeout}s mein khatam nahi hua. "
            f"Ya to video bahut lamba hai, ya machine slow hai. "
            f"config.yaml mein video_length_sec kam karke dekho.") from e
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        raise RuntimeError(f"{what} fail (exit {proc.returncode}):\n{err[-1200:]}\n"
                           f"→ Matlab: {_explain_ffmpeg(err)}")
    return proc


def _explain_ffmpeg(err: str) -> str:
    """ffmpeg ke common errors ka Hinglish matlab."""
    e = err.lower()
    pairs = [
        ("no such file", "Koi input file nahi mili. Pehle Phase 2 chalao (`python run_phase2.py`)."),
        ("unknown filter", "Tumhare ffmpeg build mein ye filter nahi hai. "
                           "Poora build install karo (brew/apt wala), minimal nahi."),
        ("invalid argument", "Filter ko odd (visham) dimensions mile. H.264 ko even chahiye — "
                             "code even-rounding karta hai, ye bug report karo."),
        ("does not contain any stream", "Input file khaali ya corrupt hai."),
        ("height not divisible by 2", "Resolution even honi chahiye. config.yaml mein 1080x1920 rakho."),
        ("permission denied", "Output folder mein likhne ki permission nahi."),
        ("no space left", "Disk full hai. output/ folder saaf karo."),
        ("encoder 'libx264' not found", "Tumhara ffmpeg bina libx264 ke bana hai. "
                                        "Instagram ko H.264 chahiye — dusra build install karo."),
    ]
    for needle, meaning in pairs:
        if needle in e:
            return meaning
    return "Naya error hai — upar wala ffmpeg output padho, usme aksar saaf likha hota hai."


def probe(path: str | Path) -> dict:
    """
    Video/audio file ki jaankari (duration, codec, resolution...).
    ffprobe ho to poora JSON, na ho to ffmpeg ke stderr se basic info nikal lete hain
    (imageio-ffmpeg sirf ffmpeg deta hai, ffprobe nahi — isliye ye fallback zaroori hai).
    """
    fp = ffprobe_bin()
    if not fp:
        return _probe_via_ffmpeg(path)
    try:
        out = subprocess.run(
            [fp, "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", str(path)],
            capture_output=True, text=True, timeout=60).stdout
        return json.loads(out or "{}")
    except Exception as e:  # noqa: BLE001
        log.warn("probe fail", file=str(path), reason=str(e)[:120])
        return {}


def _probe_via_ffmpeg(path: str | Path) -> dict:
    """
    ffprobe ke bina fallback: `ffmpeg -i file` chalao aur uske stderr se
    duration/codec/resolution parse karo. Output ffprobe jaisa hi shape rakhte hain
    taaki caller ko farq na pade.
    """
    import re
    try:
        proc = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", str(path)],
                              capture_output=True, text=True, timeout=60)
        err = proc.stderr
    except Exception as e:  # noqa: BLE001
        log.warn("probe fallback fail", reason=str(e)[:120])
        return {}

    out: dict = {"format": {}, "streams": [], "_source": "ffmpeg-stderr"}

    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", err)
    if m:
        h, mn, sec = int(m.group(1)), int(m.group(2)), float(m.group(3))
        out["format"]["duration"] = str(h * 3600 + mn * 60 + sec)

    m = re.search(r"bitrate:\s*(\d+)\s*kb/s", err)
    if m:
        out["format"]["bit_rate"] = str(int(m.group(1)) * 1000)

    for sm in re.finditer(r"Stream #\d+:\d+.*?: Video: (\w+).*?, (\w+).*?, (\d+)x(\d+)"
                          r"(?:.*?, ([\d.]+) fps)?", err):
        out["streams"].append({
            "codec_type": "video", "codec_name": sm.group(1),
            "pix_fmt": sm.group(2),
            "width": int(sm.group(3)), "height": int(sm.group(4)),
            "r_frame_rate": f"{sm.group(5)}/1" if sm.group(5) else None,
        })
    for sm in re.finditer(r"Stream #\d+:\d+.*?: Audio: (\w+).*?, (\d+) Hz, (\w+)", err):
        out["streams"].append({
            "codec_type": "audio", "codec_name": sm.group(1),
            "sample_rate": sm.group(2), "channel_layout": sm.group(3),
        })

    try:
        out["format"]["size"] = str(Path(path).stat().st_size)
    except OSError:
        pass
    return out


if __name__ == "__main__":
    print("ffmpeg :", ffmpeg_bin())
    print("ffprobe:", ffprobe_bin() or "❌ nahi hai (chalega, par validate.py kam detail dega)")
    print("caps   :")
    for k, v in capabilities().items():
        print(f"   {'✅' if v else '❌'} {k}")
