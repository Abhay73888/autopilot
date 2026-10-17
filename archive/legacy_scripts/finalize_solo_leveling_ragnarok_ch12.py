"""
finalize_solo_leveling_ragnarok_ch12.py — Calibrates Chapter 12 to strictly 4.54 minutes (272.0s).
Single-pass speedup + subtitle burn-in.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.ffmpeg import ffmpeg_bin, probe
from generate_solo_leveling_ragnarok_ch12 import SCENES

OUT_DIR = ROOT / "output" / "solo_leveling_ragnarok_ch12"
FINAL_DIR = OUT_DIR / "checkpoints_final"

def generate_tight_ass_subtitles(scenes: list[dict], scene_durs: list[float], factor: float, out_ass: Path):
    header = """[Script Info]
Title: Solo Leveling Ragnarok Chapter 12 Subtitles (Calibrated 4.5m)
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
        tight_dur = dur / factor
        start_s = curr
        end_s = curr + tight_dur
        style = "RagnarokGold" if sc["speaker"] in ["manager", "beru"] else "RagnarokCyan"
        text = sc["text_sub"].replace("\n", "\\N")
        events.append(f"Dialogue: 0,{fmt_time(start_s)},{fmt_time(end_s)},{style},,0,0,0,,{text}")
        curr = end_s

    out_ass.parent.mkdir(parents=True, exist_ok=True)
    with open(out_ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")
    print(f"  ✓ Calibrated Subtitles generated: {out_ass.name}")

def main():
    ff = ffmpeg_bin()
    clips = []
    scene_durs = []

    print("\n" + "=" * 75)
    print("  ⚔️ CALIBRATING SOLO LEVELING: RAGNAROK CH 12 TO STRICT 4–5 MINS")
    print("=" * 75)

    for i in range(1, len(SCENES) + 1):
        sc_mp4 = FINAL_DIR / f"sc_{i:02d}_final.mp4"
        if not sc_mp4.exists():
            raise FileNotFoundError(f"Missing scene: {sc_mp4}")
        clips.append(sc_mp4)
        info = probe(sc_mp4)
        dur = float(info["format"]["duration"])
        scene_durs.append(dur)

    raw_total = sum(scene_durs)
    target_total = 272.0
    factor = round(raw_total / target_total, 4)
    print(f"  Current raw total: {raw_total:.1f}s ({raw_total/60:.2f} mins)")
    print(f"  Target calibrated: {target_total:.1f}s ({target_total/60:.2f} mins)")
    print(f"  Calibrated tempo factor: {factor:.4f}x")

    # Step 1: Concat list
    concat_list = OUT_DIR / "concat_list_tight.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in clips:
            clean_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    temp_concat = OUT_DIR / "temp_concat.mp4"
    print("\n[1/3] Fast stream-concatenating 40 scene clips...")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(temp_concat)
    ], check=True)

    # Step 2: Calibrated Subtitles
    ass_path = OUT_DIR / "solo_leveling_ragnarok_ch12_tight.ass"
    generate_tight_ass_subtitles(SCENES, scene_durs, factor, ass_path)

    # Step 3: Fast Single-Pass Speedup + Subtitle Burn
    final_mp4 = OUT_DIR / "solo_leveling_ragnarok_ch12_final.mp4"
    print(f"\n[2/3] Burning calibrated ASS subtitles and applying tempo factor {factor:.4f}x...")
    
    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    
    # Filter complex
    v_flt = f"setpts=PTS/{factor:.4f},ass='{ass_escaped}'"
    a_flt = f"atempo={factor:.4f}"

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(temp_concat),
        "-vf", v_flt,
        "-af", a_flt,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(final_mp4)
    ], check=True)

    # Clean up temp concat
    if temp_concat.exists():
        temp_concat.unlink()

    # Step 4: Verify Duration
    print("\n[3/3] Probing finalized master...")
    final_info = probe(final_mp4)
    final_dur = float(final_info["format"]["duration"])
    final_mb = final_mp4.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 75)
    print(f"  ⏱️ VERIFIED FINAL RUNTIME: {final_dur:.1f}s ({final_dur/60:.2f} minutes)")
    print(f"  💾 File Size: {final_mb:.2f} MB")
    print("=" * 75)

    if not (240.0 <= final_dur <= 300.0):
        raise ValueError(f"CRITICAL: Final duration {final_dur:.1f}s is not within 240s-300s window!")

    print(f"  🎯 100% SUCCESS: Strictly within 4 to 5 minutes! ({final_dur/60:.2f} mins)\n")

if __name__ == "__main__":
    main()
