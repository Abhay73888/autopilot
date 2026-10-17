"""
enhance_movie_1_5x.py — 1.5x Speedup & Visual Quality Enhancement Engine.
Applies:
- 1.5x Pacing: setpts=PTS/1.5 + atempo=1.5 (pitch-preserved speech)
- Visual Enhancement: CAS (Contrast-Adaptive Sharpening) + Color Grading (Rich Contrast & Saturation)
- Subtitles Synchronization: Rescales all .ass and .srt subtitle timestamps by / 1.5
- Manifest & Chapters Update: Rescales all 30 chapter timestamps by / 1.5
"""

import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from core.ffmpeg import ffmpeg_bin, probe

BASE_DIR = Path(__file__).parent
MOVIE_DIR = BASE_DIR / "output" / "dont_open_the_door_movie"
UNSUBBED_FEATURE = MOVIE_DIR / "feature_unsubbed.mp4"
SUB_ASS_SRC = MOVIE_DIR / "subtitles.ass"
SUB_SRT_SRC = MOVIE_DIR / "subtitles.srt"
MANIFEST_SRC = MOVIE_DIR / "manifest.json"

FINAL_TARGET = MOVIE_DIR / "final.mp4"
BACKUP_ORIGINAL = MOVIE_DIR / "final_1x_original.mp4"

SPEED = 1.5


def parse_ass_time(t_str: str) -> float:
    # Format: H:MM:SS.cs (e.g. 0:01:23.45)
    parts = t_str.strip().split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


def format_ass_time(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def parse_srt_time(t_str: str) -> float:
    # Format: HH:MM:SS,mmm
    t_str = t_str.strip().replace(",", ".")
    parts = t_str.split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


def format_srt_time(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def rescale_subtitles():
    print("📝 Rescaling subtitle timestamps by 1.5x...")
    sub_ass_out = MOVIE_DIR / "subtitles_1_5x.ass"
    sub_srt_out = MOVIE_DIR / "subtitles_1_5x.srt"

    # 1. Rescale ASS
    if SUB_ASS_SRC.exists():
        lines = SUB_ASS_SRC.read_text(encoding="utf-8").splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("Dialogue:"):
                # Dialogue: 0,0:00:00.00,0:00:26.75,CleanSub,,0,0,0,,Text
                parts = line.split(",", 9)
                if len(parts) >= 10:
                    st = parse_ass_time(parts[1]) / SPEED
                    et = parse_ass_time(parts[2]) / SPEED
                    parts[1] = format_ass_time(st)
                    parts[2] = format_ass_time(et)
                    line = ",".join(parts)
            new_lines.append(line)
        sub_ass_out.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"  ✓ Saved {sub_ass_out}")

    # 2. Rescale SRT
    if SUB_SRT_SRC.exists():
        content = SUB_SRT_SRC.read_text(encoding="utf-8")
        # Match: 00:00:00,000 --> 00:00:26,750
        def repl(match):
            st = parse_srt_time(match.group(1)) / SPEED
            et = parse_srt_time(match.group(2)) / SPEED
            return f"{format_srt_time(st)} --> {format_srt_time(et)}"

        new_srt = re.sub(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", repl, content)
        sub_srt_out.write_text(new_srt, encoding="utf-8")
        print(f"  ✓ Saved {sub_srt_out}")

    return sub_ass_out


def rescale_manifest():
    print("📑 Rescaling chapters and manifest for 1.5x speed...")
    if not MANIFEST_SRC.exists():
        return
    man = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
    man["duration_sec"] = round(man["duration_sec"] / SPEED, 2)
    man["speed_multiplier"] = 1.5
    man["enhancements"] = ["Contrast-Adaptive Sharpening (CAS 0.35)", "Anime Color & Contrast Grade (eq 1.06/1.12)", "1.5x Pacing"]
    
    for ch in man.get("chapters", []):
        ch["start_sec"] = round(ch["start_sec"] / SPEED, 2)
        m = int(ch["start_sec"] // 60)
        s = int(ch["start_sec"] % 60)
        ch["timestamp"] = f"{m:02d}:{s:02d}"

    MANIFEST_SRC.write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✓ Manifest updated with new 1.5x chapter marks ({man['duration_sec']}s total).")


def main():
    print("=" * 70)
    print("🚀 GOD MODE — 1.5x SPEEDUP & VISUAL QUALITY ENHANCER")
    print("🎬 'DON'T OPEN THE DOOR' (Enhanced Anime Horror Feature)")
    print("=" * 70)

    if not UNSUBBED_FEATURE.exists():
        raise FileNotFoundError(f"Missing {UNSUBBED_FEATURE}")

    # Backup original final.mp4 if not already backed up
    if FINAL_TARGET.exists() and not BACKUP_ORIGINAL.exists():
        print(f"📦 Backing up original final.mp4 -> {BACKUP_ORIGINAL.name}")
        shutil.copy2(FINAL_TARGET, BACKUP_ORIGINAL)

    # 1. Rescale Subtitles
    sub_ass_1_5x = rescale_subtitles()

    # 2. Rescale Manifest
    rescale_manifest()

    # 3. Escape subtitle path for FFmpeg
    sub_esc = str(sub_ass_1_5x.resolve()).replace("\\", "/").replace(":", "\\:")

    # 4. Build Filter Graph:
    # Video: Speed 1.5x + Contrast-Adaptive Sharpening (CAS) + Color Grading + Burn Subtitles
    # Audio: atempo=1.5 (pitch preservation)
    vf_chain = (
        "setpts=PTS/1.5,"
        "cas=0.35,"
        "eq=contrast=1.06:saturation=1.12:brightness=0.01,"
        f"ass='{sub_esc}'"
    )

    ff = ffmpeg_bin()
    tmp_enhanced = MOVIE_DIR / "final_enhanced_temp.mp4"

    print("\n🎥 Rendering Enhanced 1.5x Master Video (CRF 17, CAS 0.35, atempo 1.5)...")
    cmd = [
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(UNSUBBED_FEATURE),
        "-vf", vf_chain,
        "-af", "atempo=1.5",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(tmp_enhanced)
    ]
    subprocess.run(cmd, check=True)

    # Replace final.mp4
    if tmp_enhanced.exists():
        if FINAL_TARGET.exists():
            FINAL_TARGET.unlink()
        tmp_enhanced.rename(FINAL_TARGET)

    # Also clean temporary test files
    test_p = MOVIE_DIR / "test_enhanced_1_5x.mp4"
    if test_p.exists():
        test_p.unlink()

    # Probe final output
    info = probe(FINAL_TARGET)
    fmt = info.get("format", {})
    dur = float(fmt.get("duration", 0))
    sz = float(fmt.get("size", 0)) / (1024 * 1024)

    print("\n" + "=" * 70)
    print("🎉 1.5x ENHANCED MASTERPIECE READY!")
    print(f"📁 Video: {FINAL_TARGET}")
    print(f"⏱️ Duration: {dur:.1f}s ({dur/60:.2f} minutes)")
    print(f"📦 File Size: {sz:.2f} MB")
    print("✨ Features: 1.5x Speedup, CAS Line Sharpening, Popped Color Grade, Perfectly Synced Subtitles!")
    print("=" * 70)


if __name__ == "__main__":
    main()
