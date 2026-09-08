"""
pipeline/sound.py — Modular Cinematic Sound Design Engine (Phase B)

Provides synthetic, royalty-free sound design layers via ffmpeg lavfi:
  1. Heartbeat: 50Hz dual-thump ("lub-dub") pulse with BPM ramp (60 -> 110)
     and volume swell (-20dB -> -14dB).
  2. Riser: 200Hz -> 600Hz frequency sweep peaking at reveal point.
  3. Sub-bass hit: 42Hz punch with fast exponential decay (0.6s) at reveal.
  4. Flash-cut click: 0.03s white-noise transient for high-tension cuts.
  5. Room tone: Subtle pink noise (-32dB) bed for dialogue.
  6. Dynamic ducking: Sidechain compressor (-14dB ducking when narration active).
  7. Master limiter: alimiter (limit=0.9) before -14 LUFS loudnorm.

Zero copyrighted audio, zero external files, pure ffmpeg synthetic filters.
"""

from __future__ import annotations

import math
from typing import Any
from core.config import CONFIG
from core.ffmpeg import capabilities
from core.logbook import Logbook

log = Logbook("sound")


def build_heartbeat_filter(total_sec: float, start_idx: int,
                           bpm_start: float = 60.0, bpm_end: float = 110.0) -> tuple[list[str], list[str], str]:
    """
    Heartbeat: 50Hz dual-thump (lub=40ms, dub=30ms, gap=120ms).
    BPM ramps from bpm_start to bpm_end.
    Volume swells from -20dB (0.10) to -14dB (0.20) as tension mounts.
    """
    inputs = ["-f", "lavfi", "-t", f"{total_sec:.2f}", "-i", "sine=frequency=50:sample_rate=44100"]
    # Phase calculation: f(t) = (bpm_start + (bpm_end - bpm_start)*t/total) / 60
    # Integral of f(t)dt = (bpm_start/60)*t + 0.5 * ((bpm_end - bpm_start)/(60*total)) * t^2
    f0 = bpm_start / 60.0
    f_rate = (bpm_end - bpm_start) / (60.0 * max(1.0, total_sec))
    k = 0.5 * f_rate
    # volume eval expression: lub (p < 0.04) and dub (0.16 <= p < 0.19)
    # volume swell: 0.09 + 0.11 * (t / total_sec)
    expr = (f"volume=eval=frame:volume='if(lt(mod(t+{k:.6f}*t*t\\,1.0)\\,0.04)+"
            f"between(mod(t+{k:.6f}*t*t\\,1.0)\\,0.16\\,0.19)\\,"
            f"(0.09+0.11*t/{max(1.0, total_sec):.2f})\\,0.0)'")
    filt = [f"[{start_idx}:a]{expr},aformat=channel_layouts=stereo[heartbeat]"]
    return inputs, filt, "[heartbeat]"


def build_riser_filter(reveal_sec: float, start_idx: int, dur_sec: float = 2.5,
                       f_start: float = 200.0, f_end: float = 600.0) -> tuple[list[str], list[str], str]:
    """
    Riser: 200Hz -> 600Hz frequency sweep with exponential volume build (-24dB to -6dB).
    Peaks right at reveal_sec.
    """
    dur = min(dur_sec, max(0.5, reveal_sec))
    st = max(0.0, reveal_sec - dur)
    # Sweep rate k = (f_end - f_start) / (2 * dur)
    k = (f_end - f_start) / (2.0 * dur)
    expr = f"aevalsrc=sin(2*PI*({f_start:.1f}*t+{k:.2f}*t*t))*(0.06*exp(2.1*t/{dur:.2f})):s=44100:d={dur:.2f}"
    inputs = ["-f", "lavfi", "-t", f"{dur:.2f}", "-i", expr]
    delay_ms = int(st * 1000)
    filt = [f"[{start_idx}:a]adelay={delay_ms}|{delay_ms},aformat=channel_layouts=stereo[riser]"]
    return inputs, filt, "[riser]"


def build_sub_hit_filter(reveal_sec: float, start_idx: int, dur_sec: float = 0.6,
                         freq: float = 42.0) -> tuple[list[str], list[str], str]:
    """
    Sub-bass hit: 42Hz sine burst with fast exponential decay (0.6s) at reveal_sec.
    Volume: -3dB (0.70).
    """
    expr = f"aevalsrc=sin(2*PI*{freq:.1f}*t)*(0.70*exp(-5*t)):s=44100:d={dur_sec:.2f}"
    inputs = ["-f", "lavfi", "-t", f"{dur_sec:.2f}", "-i", expr]
    delay_ms = int(max(0.0, reveal_sec) * 1000)
    filt = [f"[{start_idx}:a]adelay={delay_ms}|{delay_ms},aformat=channel_layouts=stereo[sub_hit]"]
    return inputs, filt, "[sub_hit]"


def build_room_tone_filter(total_sec: float, start_idx: int) -> tuple[list[str], list[str], str]:
    """
    Room tone: Subtle pink noise (-32dB) bed low-passed at 1200Hz.
    Prevents digital 'dead air' silence in audio pauses.
    """
    inputs = ["-f", "lavfi", "-t", f"{total_sec:.2f}", "-i",
              "anoisesrc=color=pink:sample_rate=44100:amplitude=0.025"]
    filt = [f"[{start_idx}:a]lowpass=f=1200,volume=0.4,aformat=channel_layouts=stereo[room_tone]"]
    return inputs, filt, "[room_tone]"


def build_sound_design_package(total: float, cuts: list[float],
                               reveal_sec: float | None = None,
                               cfg_override: dict | None = None) -> dict[str, Any]:
    """
    Build modular sound design layers based on config.
    Returns:
      inputs: list of ffmpeg CLI input flags
      parts: filter_complex filter strings
      bg_label: label for mixed background audio
      applied: dictionary of applied effects
    """
    cfg = cfg_override or (CONFIG.get("effects") or {}).get("sound") or {}
    do_heartbeat = cfg.get("heartbeat", True)
    do_riser = cfg.get("riser", True)
    do_sub_hit = cfg.get("sub_hit", True)
    do_flash_click = cfg.get("flash_click", True)
    do_room_tone = cfg.get("room_tone", True)
    do_ducking = cfg.get("ducking", True)
    do_limiter = cfg.get("master_limiter", True)

    inputs: list[str] = []
    parts: list[str] = []
    applied: dict[str, Any] = {}

    # Drone (Baseline atmosphere: 55Hz & 110.7Hz sines)
    inputs += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "sine=frequency=55:sample_rate=44100"]
    inputs += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "sine=frequency=110.7:sample_rate=44100"]
    # Drone mixer: inputs 1 and 2
    parts.append(
        "[1:a][2:a]amix=inputs=2:duration=shortest[dr0];"
        "[dr0]volume=0.025,lowpass=f=200,"
        f"afade=t=in:st=0:d=2,afade=t=out:st={max(0.1, total-2):.2f}:d=2,"
        "aformat=channel_layouts=stereo[drone]"
    )
    bg_sublayers = ["[drone]"]
    cur_idx = 3  # 0=narration, 1,2=drone

    # Reveal timing determination
    if reveal_sec is None:
        reveal_sec = total * 0.75 if total > 4.0 else total * 0.5

    # Heartbeat
    if do_heartbeat:
        hb_in, hb_f, hb_lbl = build_heartbeat_filter(total, cur_idx)
        inputs += hb_in
        parts += hb_f
        bg_sublayers.append(hb_lbl)
        cur_idx += hb_in.count("-i")
        applied["heartbeat"] = {"bpm": "60->110", "vol": "-20dB->-14dB"}

    # Riser
    if do_riser and reveal_sec > 2.0:
        rs_in, rs_f, rs_lbl = build_riser_filter(reveal_sec, cur_idx)
        inputs += rs_in
        parts += rs_f
        bg_sublayers.append(rs_lbl)
        cur_idx += rs_in.count("-i")
        applied["riser"] = {"start": round(max(0.0, reveal_sec - 2.5), 2), "sweep": "200Hz->600Hz"}

    # Sub-hit
    if do_sub_hit and reveal_sec > 1.0:
        sh_in, sh_f, sh_lbl = build_sub_hit_filter(reveal_sec, cur_idx)
        inputs += sh_in
        parts += sh_f
        bg_sublayers.append(sh_lbl)
        cur_idx += sh_in.count("-i")
        applied["sub_hit"] = {"time": round(reveal_sec, 2), "freq": "42Hz"}

    # Room Tone
    if do_room_tone:
        rt_in, rt_f, rt_lbl = build_room_tone_filter(total, cur_idx)
        inputs += rt_in
        parts += rt_f
        bg_sublayers.append(rt_lbl)
        cur_idx += rt_in.count("-i")
        applied["room_tone"] = {"level": "-32dB", "color": "pink"}

    # Whoosh & Flash Clicks on cuts
    whoosh_labels = []
    wi = 0
    for c in cuts:
        if not (0.3 < c < total - 0.3):
            continue
        # Check if near reveal for click
        is_tension_cut = abs(c - reveal_sec) < 2.0 if reveal_sec else False
        if is_tension_cut and do_flash_click:
            inputs += ["-f", "lavfi", "-t", "0.03", "-i",
                       "anoisesrc=color=white:sample_rate=44100:amplitude=0.3"]
            delay_ms = int(c * 1000)
            parts.append(f"[{cur_idx}:a]highpass=f=2000,lowpass=f=8000,"
                         f"volume=0.25,adelay={delay_ms}|{delay_ms},"
                         f"aformat=channel_layouts=stereo[clk{wi}]")
            whoosh_labels.append(f"[clk{wi}]")
            cur_idx += 1

        # Standard whoosh transition
        inputs += ["-f", "lavfi", "-t", "0.7", "-i",
                   "anoisesrc=color=brown:sample_rate=44100:amplitude=0.5"]
        delay_ms = int(max(0, (c - 0.25)) * 1000)
        parts.append(f"[{cur_idx}:a]highpass=f=300,lowpass=f=6000,"
                     f"afade=t=in:st=0:d=0.12,afade=t=out:st=0.25:d=0.45,"
                     f"volume=0.10,adelay={delay_ms}|{delay_ms},"
                     f"aformat=channel_layouts=stereo[wh{wi}]")
        whoosh_labels.append(f"[wh{wi}]")
        cur_idx += 1
        wi += 1

    if whoosh_labels:
        parts.append(f"{''.join(whoosh_labels)}amix=inputs={len(whoosh_labels)}:"
                     f"duration=longest:normalize=0[transitions]")
        bg_sublayers.append("[transitions]")
        applied["transitions"] = len(whoosh_labels)

    # Combine background layers into single [bg_master]
    if len(bg_sublayers) > 1:
        parts.append(f"{''.join(bg_sublayers)}amix=inputs={len(bg_sublayers)}:"
                     f"duration=longest:normalize=0[bg_master]")
        bg_label = "[bg_master]"
    else:
        bg_label = bg_sublayers[0]

    applied["ducking"] = do_ducking
    applied["master_limiter"] = do_limiter

    return {
        "inputs": inputs,
        "parts": parts,
        "bg_label": bg_label,
        "applied": applied,
        "ducking": do_ducking,
        "limiter": do_limiter,
    }
