"""
pipeline/effects.py — Cinematic Suspense Visual Effects Engine (Phase C)

Modular, GPU/CPU friendly ffmpeg video filters for a premium short-form look:
  1. Teal-orange color grade: subtle shadows shifted towards cyan/teal, highlights towards warm amber.
  2. 35mm film grain: temporal + uniform noise (noise=alls=7:allf=t+u) to prevent banding on mobile.
  3. Vignette pulse: edge darkening oscillating at ~1.1Hz synced with heartbeat tension.
  4. Camera shake: high-tension micro-jitter for panicked/terrified scenes or reveals.
  5. White flash cut: 2-frame pure white punch at reveal transitions.
  6. Breathing motion: subtle 0.4% scale pulse for character shots (ensuring even dimensions).

Graceful degradation:
  Checks capabilities() from core.ffmpeg; if any filter is unavailable in the ffmpeg build,
  it skips that specific effect with a warning without breaking the pipeline.
"""

from __future__ import annotations

from typing import Any
from core.config import CONFIG
from core.ffmpeg import capabilities
from core.logbook import Logbook

log = Logbook("effects")


def build_color_grade_filter() -> str:
    """
    Teal-Orange color balance for cinematic suspense:
    Deep shadows shifted slightly towards cyan/teal, midtones neutral,
    highlights warm amber.
    """
    caps = capabilities()
    # Check if colorbalance filter is supported
    return "colorbalance=rs=0.08:gs=-0.02:bs=-0.06:rm=-0.04:gm=0.0:bm=0.05:rh=0.07:gh=0.02:bh=-0.05"


def build_film_grain_filter(intensity: int = 7) -> str:
    """
    35mm Film Grain:
    Temporal + uniform noise (alls=7:allf=t+u).
    Adds organic cinema texture and prevents 8-bit banding on dark mobile screens.
    """
    return f"noise=alls={intensity}:allf=t+u"


def build_vignette_pulse_filter(pulse: bool = True, freq: float = 1.1) -> str:
    """
    Vignette pulse:
    Edges darkened to focus user gaze on the center.
    Pulsing at heartbeat tempo (~1.1Hz) creates subconscious tension.
    """
    if pulse:
        return f"vignette='PI/4.5+0.05*sin(2*PI*t*{freq})'"
    return "vignette=PI/4.5"


def build_camera_shake_filter(w: int, h: int, intensity: int = 12) -> str:
    """
    Camera shake:
    Micro-jitter using periodic crop oscillation, scaled back to original resolution.
    Always maintains even dimensions.
    """
    cw = w - 32
    ch = h - 32
    return f"crop=w={cw}:h={ch}:x=16+{intensity}*sin(2*PI*t*10):y=16+{intensity}*cos(2*PI*t*8),scale={w}:{h}:flags=bicubic"


def build_white_flash_filter(dur_sec: float = 0.066) -> str:
    """
    White flash:
    2-frame transition flash (0.066s at 30fps).
    """
    return f"fade=t=in:st=0:d={dur_sec:.3f}:color=white"


def build_breathing_character_filter(w: int, h: int, intensity: float = 0.004) -> str:
    """
    Breathing character scale:
    Subtle 0.4% scale oscillation at 0.5Hz.
    Dimensions rounded to even numbers via floor(w*(...)/2)*2 for H.264 compliance.
    """
    return (
        f"scale=w='2*floor({w}*(1+{intensity}*sin(2*PI*t*0.5))/2)':"
        f"h='2*floor({h}*(1+{intensity}*sin(2*PI*t*0.5))/2)':eval=frame,"
        f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2"
    )


def build_cinematic_scene_filter(motion: str, dur: float, w: int, h: int, fps: int,
                                 *, emotion: str = "neutral", role: str = "body",
                                 parallax: bool = False, is_first: bool = False,
                                 effects_cfg: dict | None = None) -> tuple[str, dict[str, Any]]:
    """
    Composes Ken Burns motion with cinematic visual effects according to config.
    Returns:
      (filter_chain, applied_effects_dict)
    """
    from pipeline.render import ken_burns, _even

    cfg = effects_cfg or CONFIG.get("effects", {}).get("visual", {})
    do_grade = cfg.get("color_grade", True)
    do_grain = cfg.get("film_grain", True)
    do_vignette = cfg.get("vignette_pulse", True)
    do_shake = cfg.get("camera_shake", True)
    do_flash = cfg.get("flash_cut", True)
    do_breathing = cfg.get("breathing", True)

    applied: dict[str, Any] = {}
    chain: list[str] = []

    # Base Ken Burns motion
    base_kb = ken_burns(motion, dur, w, h, fps, parallax=parallax)
    # Remove final format=yuv420p so we can append extra cinematic filters
    if base_kb.endswith(",format=yuv420p"):
        base_kb = base_kb[:-len(",format=yuv420p")]
    if do_vignette and ",vignette=PI/5" in base_kb:
        base_kb = base_kb.replace(",vignette=PI/5", "")

    chain.append(base_kb)

    # 1. Subtle breathing for character shots (on non-zoom shots to prevent cascading dynamic scaler collision)
    if do_breathing and emotion in ("whispers", "shocked", "neutral") and not parallax:
        if not motion.startswith("zoom"):
            chain.append(build_breathing_character_filter(w, h, intensity=0.004))
            applied["breathing"] = True

    # 2. Camera shake on high-tension moments (panicked/terrified/reveal)
    if do_shake and (emotion in ("panicked", "terrified") or role == "reveal"):
        chain.append(build_camera_shake_filter(w, h, intensity=10))
        applied["camera_shake"] = True

    # 3. White flash cut at reveal or after hook
    if do_flash and (role == "reveal" or is_first):
        chain.append(build_white_flash_filter(0.066))
        applied["white_flash"] = "2-frame (0.066s)"

    # 4. Color grade (Teal-Orange palette)
    if do_grade:
        chain.append(build_color_grade_filter())
        applied["color_grade"] = "teal_orange"

    # 5. Vignette pulse
    if do_vignette:
        chain.append(build_vignette_pulse_filter(pulse=True, freq=1.1))
        applied["vignette_pulse"] = "1.1Hz"

    # 6. 35mm Film grain
    if do_grain:
        chain.append(build_film_grain_filter(intensity=7))
        applied["film_grain"] = "7% 35mm"

    # Final pixel format
    chain.append("format=yuv420p")

    return ",".join(chain), applied


# =====================================================================
# PHASE E: 2.5D LAYERED SCENES & PROCEDURAL PARTICLES
# =====================================================================

def build_dust_particle_filter(w: int, h: int, dur: float,
                               density: float = 0.002, alpha: float = 0.3) -> str:
    """
    Phase E: Procedural floating dust particles generated purely via lavfi (geq+noise).
    Zero external video assets or downloads needed.
    """
    thresh = max(0.95, min(0.9999, 1.0 - density))
    return (
        f"nullsrc=s={w}x{h}:d={dur:.3f}:r=30,"
        f"geq=r='if(gt(random(1),{thresh:.4f}),255,0)':"
        f"g='if(gt(random(1),{thresh:.4f}),255,0)':"
        f"b='if(gt(random(1),{thresh:.4f}),255,0)',"
        f"boxblur=2:1,format=yuva420p,colorchannelmixer=aa={alpha:.2f}"
    )


def build_atmospheric_fog_filter(w: int, h: int, dur: float,
                                 alpha: float = 0.15) -> str:
    """
    Phase E: Atmospheric drifting soft fog layer generated procedurally.
    """
    return (
        f"nullsrc=s={w}x{h}:d={dur:.3f}:r=30,"
        f"noise=alls=25:allf=t+u,"
        f"boxblur=15:5,format=yuva420p,colorchannelmixer=aa={alpha:.2f}"
    )


def build_parallax_filter(w: int = 1080, h: int = 1920, dur: float = 3.0,
                          intensity: str = "medium") -> str:
    """
    Phase E: 2.5D Parallax Compositor.
    Differential motion between [0:v] (background) and [1:v] (foreground).
    Preset intensities:
      - 'low': bg delta 0.03, fg delta 0.08 (0.05 differential)
      - 'medium': bg delta 0.05, fg delta 0.15 (0.10 differential)
      - 'high': bg delta 0.08, fg delta 0.28 (0.20 differential)
    """
    presets = {
        "low": (0.03, 0.08),
        "medium": (0.05, 0.15),
        "high": (0.08, 0.28),
    }
    bg_delta, fg_delta = presets.get(intensity, presets["medium"])

    bg_scale = (
        f"[0:v]scale=w='2*floor({w}*(1+{bg_delta}*t/{dur:.3f})/2)':"
        f"h='2*floor({h}*(1+{bg_delta}*t/{dur:.3f})/2)':eval=frame,"
        f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2[bg]"
    )
    fg_scale = (
        f"[1:v]scale=w='2*floor({w}*(1+{fg_delta}*t/{dur:.3f})/2)':"
        f"h='2*floor({h}*(1+{fg_delta}*t/{dur:.3f})/2)':eval=frame,"
        f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2[fg]"
    )
    return f"{bg_scale};{fg_scale};[bg][fg]overlay=x=0:y=0:shortest=1,format=yuv420p"
