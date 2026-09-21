"""
pipeline/pdf_video_engine.py — PDF → Human-Like Cinematic Video Engine.

Pipeline:
  PDF Upload → Page Extraction → OCR → Manga Panel Detection → Story Analysis
  → Emotion Detection → Narration Script → Character Voice (Edge-TTS w/ emotion)
  → Audio Mix (voice + SFX + music) → Living Shot Render (Ken Burns + panel focus)
  → Subtitle Generation → Concat → Final MP4

PHILOSOPHY:
  STATIC PDF → LIVING SCENE → CINEMATIC VIDEO
  Voice = Performance, Emotion = Acting, Camera = Cinema
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

try:
    import fitz          # PyMuPDF
except ImportError:
    fitz = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from PIL import Image

from core.ffmpeg import ffmpeg_bin, probe

# ─────────────────────────────────────────────────────────────────────────────
# EMOTION → VOICE PARAMETERS MAP
# Each emotion drives: Edge-TTS rate, pitch, and style
# ─────────────────────────────────────────────────────────────────────────────
EMOTION_VOICE: dict[str, dict] = {
    "happy":      {"rate": "+8%",  "pitch": "+6Hz",  "sfx": "upbeat_chime",    "music": "light_warm"},
    "excited":    {"rate": "+18%", "pitch": "+10Hz", "sfx": "whoosh_energy",   "music": "fast_energy"},
    "curious":    {"rate": "+2%",  "pitch": "+4Hz",  "sfx": "thinking_tone",   "music": "curious_ambient"},
    "calm":       {"rate": "-4%",  "pitch": "-2Hz",  "sfx": "ambient_soft",    "music": "calm_piano"},
    "romantic":   {"rate": "-8%",  "pitch": "+4Hz",  "sfx": "heartbeat_soft",  "music": "soft_strings"},
    "sad":        {"rate": "-14%", "pitch": "-6Hz",  "sfx": "rain_soft",       "music": "sad_piano"},
    "angry":      {"rate": "+20%", "pitch": "-4Hz",  "sfx": "impact_heavy",    "music": "intense_drums"},
    "fearful":    {"rate": "-10%", "pitch": "-8Hz",  "sfx": "heartbeat_low",   "music": "dark_drone"},
    "nervous":    {"rate": "-4%",  "pitch": "+2Hz",  "sfx": "tense_pulse",     "music": "tense_strings"},
    "surprised":  {"rate": "+12%", "pitch": "+12Hz", "sfx": "shock_sting",     "music": "stinger"},
    "mysterious": {"rate": "-12%", "pitch": "-4Hz",  "sfx": "eerie_wind",      "music": "mystery_ambient"},
    "desperate":  {"rate": "+14%", "pitch": "-6Hz",  "sfx": "braam_impact",    "music": "dark_intense"},
    "hopeful":    {"rate": "-2%",  "pitch": "+3Hz",  "sfx": "ambient_light",   "music": "hopeful_piano"},
    "neutral":    {"rate": "0%",   "pitch": "0Hz",   "sfx": "ambient_soft",    "music": "light_ambient"},
}

# ─────────────────────────────────────────────────────────────────────────────
# EMOTION KEYWORD DETECTOR
# ─────────────────────────────────────────────────────────────────────────────
EMOTION_KEYWORDS = {
    "happy":      ["khushi", "hansi", "mast", "achha", "bahut achha", "superb", "great", "happy", "joy", "smile", "laugh"],
    "excited":    ["wow", "amazing", "incredible", "unbelievable", "yes!", "finally", "mila", "jeet", "victory"],
    "curious":    ["kya", "kyun", "kaise", "why", "how", "what", "wonder", "soch", "question"],
    "calm":       ["shaant", "calm", "peace", "quiet", "still", "relax", "theek"],
    "romantic":   ["pyaar", "mohabbat", "dil", "love", "heart", "romance", "ishq", "feeling"],
    "sad":        ["rona", "dard", "gham", "sad", "tears", "cry", "dukh", "loss", "alone", "akela"],
    "angry":      ["gussa", "krodh", "angry", "rage", "chillaya", "screamed", "yelled", "nahi", "never"],
    "fearful":    ["darr", "bhay", "fear", "scared", "horror", "dark", "andhere", "bhaaga", "ran"],
    "nervous":    ["ghabra", "nervous", "worried", "anxious", "heartbeat", "palms", "trembling"],
    "surprised":  ["achanak", "suddenly", "shocked", "whoa", "wait", "unexpected", "nahi soch"],
    "mysterious": ["rahasya", "mystery", "secret", "chhupi", "hidden", "shadow", "peheli"],
    "desperate":  ["bachao", "help", "please", "zaroor", "koi nahi", "alone", "desperate", "last"],
    "hopeful":    ["umeed", "hope", "maybe", "shayad", "kal", "tomorrow", "better", "ek din"],
}


def detect_emotion(text: str) -> str:
    """Detect dominant emotion from text using keyword matching."""
    text_lower = text.lower()
    scores: dict[str, int] = {e: 0 for e in EMOTION_KEYWORDS}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[emotion] += 1
    best = max(scores, key=lambda e: scores[e])
    return best if scores[best] > 0 else "neutral"


# ─────────────────────────────────────────────────────────────────────────────
# CAMERA MOTION SELECTOR
# ─────────────────────────────────────────────────────────────────────────────
EMOTION_CAMERA: dict[str, list[str]] = {
    "happy":      ["pan_right", "slow_push", "slow_pull"],
    "excited":    ["sudden_zoom", "pan_left", "pan_right"],
    "curious":    ["slow_push", "tilt_down", "tilt_up"],
    "calm":       ["breathing", "slow_pull", "pan_right"],
    "romantic":   ["breathing", "slow_push", "slow_pull"],
    "sad":        ["slow_pull", "tilt_down", "breathing_tremor"],
    "angry":      ["handheld_shake", "erratic_shake", "sudden_zoom"],
    "fearful":    ["breathing_tremor", "slow_push", "creeping_push"],
    "nervous":    ["subtle_shake", "handheld_shake", "breathing"],
    "surprised":  ["sudden_zoom", "rack_zoom_in", "pan_right"],
    "mysterious": ["creeping_push", "breathing", "slow_push"],
    "desperate":  ["erratic_shake", "handheld_shake", "sudden_zoom"],
    "hopeful":    ["slow_push", "tilt_up", "pan_right"],
    "neutral":    ["slow_push", "pan_right", "breathing"],
}

import random

def pick_camera(emotion: str, index: int = 0) -> str:
    options = EMOTION_CAMERA.get(emotion, ["slow_push", "breathing"])
    return options[index % len(options)]


# ─────────────────────────────────────────────────────────────────────────────
# PDF EXTRACTOR
# ─────────────────────────────────────────────────────────────────────────────
class PDFExtractor:
    """Extracts high-res images and OCR text from each PDF page."""

    def __init__(self, pdf_path: Path, out_dir: Path, dpi: int = 200):
        self.pdf_path = pdf_path
        self.out_dir = out_dir
        self.dpi = dpi
        out_dir.mkdir(parents=True, exist_ok=True)

    def extract_all(self) -> list[dict]:
        """Returns list of {page_num, image_path, text, width, height}."""
        pages = []
        doc = fitz.open(str(self.pdf_path))
        mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)

        # Also try pdfplumber for better text extraction
        try:
            plumber_doc = pdfplumber.open(str(self.pdf_path))
        except Exception:
            plumber_doc = None

        for i, page in enumerate(doc, start=1):
            # Render page to PNG
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img_path = self.out_dir / f"page_{i:03d}.png"
            pix.save(str(img_path))

            # Extract text
            raw_text = page.get_text("text").strip()
            if plumber_doc and len(raw_text) < 20:
                try:
                    plumber_page = plumber_doc.pages[i - 1]
                    raw_text = plumber_page.extract_text() or raw_text
                except Exception:
                    pass

            pages.append({
                "page_num": i,
                "image_path": img_path,
                "text": raw_text.replace("\n", " ").strip(),
                "width": pix.width,
                "height": pix.height,
            })
            print(f"  📄 Page {i}/{len(doc)}: {len(raw_text)} chars extracted")

        doc.close()
        if plumber_doc:
            plumber_doc.close()
        return pages


# ─────────────────────────────────────────────────────────────────────────────
# MANGA PANEL DETECTOR
# ─────────────────────────────────────────────────────────────────────────────
class MangaPanelDetector:
    """
    Detects individual manga panels within a page image using contour detection.
    Returns list of (x, y, w, h) bounding boxes sorted in reading order (top→bottom, left→right).
    """
    def detect_panels(self, image_path: Path, min_panel_area_ratio: float = 0.03) -> list[tuple[int,int,int,int]]:
        try:
            import cv2
        except ImportError:
            return []
        img = cv2.imread(str(image_path))
        if img is None:
            return []
        h, w = img.shape[:2]
        min_area = w * h * min_panel_area_ratio

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Use Canny + dilate to detect panel borders
        edges = cv2.Canny(gray, 30, 100)
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        panels = []
        for cnt in contours:
            x, y, pw, ph = cv2.boundingRect(cnt)
            area = pw * ph
            if area >= min_area and pw > 80 and ph > 80:
                panels.append((x, y, pw, ph))

        if not panels:
            # Fallback: treat whole page as single panel
            return [(0, 0, w, h)]

        # Remove duplicates and nested panels
        panels = self._deduplicate(panels)
        # Sort reading order: top-to-bottom, left-to-right
        panels.sort(key=lambda p: (p[1] // 200, p[0]))
        return panels

    def _deduplicate(self, panels: list) -> list:
        final = []
        for p in panels:
            x1, y1, w1, h1 = p
            dominated = False
            for q in panels:
                if q == p:
                    continue
                x2, y2, w2, h2 = q
                # p is inside q
                if x1 >= x2 and y1 >= y2 and (x1 + w1) <= (x2 + w2) and (y1 + h1) <= (y2 + h2):
                    dominated = True
                    break
            if not dominated:
                final.append(p)
        return final


# ─────────────────────────────────────────────────────────────────────────────
# VOICE GENERATOR (Human-Like Edge-TTS)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_human_voice(
    text: str,
    emotion: str,
    character: str,
    scene_idx: int,
    out_wav: Path,
    language: str = "hi",
) -> Path:
    """
    Generates human-like voiceover using Edge-TTS.
    Rate/pitch adapted per emotion. Character-specific voice assignment.
    """
    import edge_tts

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    tmp_mp3 = out_wav.with_suffix(".mp3")

    # Character → voice mapping (Hindi by default)
    VOICE_MAP = {
        "narrator":    ("hi-IN-MadhurNeural",  "0%",    "0Hz"),
        "male_young":  ("hi-IN-MadhurNeural",  "+4%",   "+2Hz"),
        "male_old":    ("hi-IN-MadhurNeural",  "-14%",  "-10Hz"),
        "female":      ("hi-IN-SwaraNeural",   "0%",    "+2Hz"),
        "female_soft": ("hi-IN-SwaraNeural",   "-10%",  "+6Hz"),
        "child":       ("hi-IN-SwaraNeural",   "+10%",  "+14Hz"),
    }

    ENGLISH_VOICE_MAP = {
        "narrator":    ("en-US-GuyNeural",     "0%",    "0Hz"),
        "male_young":  ("en-US-GuyNeural",     "+4%",   "+2Hz"),
        "male_old":    ("en-US-GuyNeural",     "-12%",  "-8Hz"),
        "female":      ("en-US-JennyNeural",   "0%",    "+2Hz"),
        "female_soft": ("en-US-JennyNeural",   "-8%",   "+6Hz"),
        "child":       ("en-US-JennyNeural",   "+10%",  "+12Hz"),
    }

    vmap = ENGLISH_VOICE_MAP if language == "en" else VOICE_MAP
    char_key = character.lower().replace(" ", "_") if character else "narrator"
    if char_key not in vmap:
        char_key = "narrator"
    base_voice, base_rate, base_pitch = vmap[char_key]

    # Apply emotion modifiers on top of character base
    ep = EMOTION_VOICE.get(emotion, EMOTION_VOICE["neutral"])
    em_rate_pct = int(ep["rate"].replace("%", "").replace("+", ""))
    em_pitch_hz = int(ep["pitch"].replace("Hz", "").replace("+", ""))

    # Parse base rate (e.g. "+4%" → 4)
    base_rate_pct = int(base_rate.replace("%", "").replace("+", ""))
    base_pitch_hz = int(base_pitch.replace("Hz", "").replace("+", ""))

    final_rate_pct = base_rate_pct + em_rate_pct
    final_pitch_hz = base_pitch_hz + em_pitch_hz

    rate_str = f"{final_rate_pct:+d}%"
    pitch_str = f"{final_pitch_hz:+d}Hz"

    last_err = None
    for attempt in range(1, 5):
        try:
            comm = edge_tts.Communicate(text, base_voice, rate=rate_str, pitch=pitch_str)
            await comm.save(str(tmp_mp3))
            break
        except Exception as e:
            last_err = e
            await asyncio.sleep(attempt * 2)
    else:
        raise RuntimeError(f"Voice gen failed: {last_err}")

    ff = ffmpeg_bin()
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp_mp3),
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_wav)
    ], check=True)
    if tmp_mp3.exists():
        tmp_mp3.unlink()
    return out_wav


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND MUSIC & SFX GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def synthesize_emotion_music(emotion: str, duration: float, out_path: Path) -> Path:
    """Generate procedural background music based on emotion using FFmpeg lavfi."""
    ff = ffmpeg_bin()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    d = round(duration, 3)

    music_filters = {
        "light_warm":     f"aevalsrc='0.25*sin(2*PI*261*t)+0.15*sin(2*PI*329*t)+0.1*sin(2*PI*392*t)':d={d}:s=44100,volume=0.4",
        "fast_energy":    f"anoisesrc=d={d}:c=white:r=44100:a=0.08,highpass=f=800,lowpass=f=4000,volume=0.5",
        "curious_ambient":f"aevalsrc='0.2*sin(2*PI*330*t)+0.1*sin(2*PI*440*t)':d={d}:s=44100,volume=0.3",
        "calm_piano":     f"aevalsrc='0.2*sin(2*PI*220*t)*exp(-0.5*(mod(t,2.0)))+0.1*sin(2*PI*277*t)*exp(-0.5*(mod(t-0.5,2.0)))':d={d}:s=44100,volume=0.35",
        "soft_strings":   f"aevalsrc='0.18*sin(2*PI*262*t)+0.12*sin(2*PI*330*t)+0.1*sin(2*PI*392*t)':d={d}:s=44100,lowpass=f=800,volume=0.3",
        "sad_piano":      f"aevalsrc='0.2*sin(2*PI*196*t)*exp(-0.8*(mod(t,3.0)))+0.1*sin(2*PI*233*t)*exp(-0.8*(mod(t-1.0,3.0)))':d={d}:s=44100,volume=0.35",
        "intense_drums":  f"anoisesrc=d={d}:c=brown:r=44100:a=0.5,lowpass=f=200,volume=0.6",
        "dark_drone":     f"aevalsrc='0.3*sin(2*PI*42*t)+0.15*sin(2*PI*84*t)':d={d}:s=44100,lowpass=f=120,volume=0.5",
        "tense_strings":  f"aevalsrc='0.2*sin(2*PI*233*t)+0.1*sin(2*PI*277*t)':d={d}:s=44100,volume=0.35",
        "stinger":        f"aevalsrc='0.5*sin(2*PI*880*t)*exp(-3*t)':d={min(d,0.5)}:s=44100,volume=0.7",
        "mystery_ambient":f"aevalsrc='0.15*sin(2*PI*110*t)+0.1*sin(2*PI*165*t)':d={d}:s=44100,lowpass=f=300,volume=0.3",
        "dark_intense":   f"aevalsrc='0.3*sin(2*PI*55*t)+0.2*sin(2*PI*42*t)':d={d}:s=44100,lowpass=f=150,volume=0.55",
        "hopeful_piano":  f"aevalsrc='0.2*sin(2*PI*294*t)*exp(-0.4*(mod(t,2.5)))+0.1*sin(2*PI*370*t)*exp(-0.4*(mod(t-0.6,2.5)))':d={d}:s=44100,volume=0.35",
        "light_ambient":  f"anoisesrc=d={d}:c=pink:r=44100:a=0.1,bandpass=f=800:w=600,volume=0.2",
    }

    ep = EMOTION_VOICE.get(emotion, EMOTION_VOICE["neutral"])
    music_type = ep.get("music", "light_ambient")
    flt = music_filters.get(music_type, music_filters["light_ambient"])

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_path)
    ], check=True)
    return out_path


def synthesize_sfx(sfx_name: str, duration: float, out_path: Path) -> Path:
    """Synthesize scene-appropriate sound effects."""
    ff = ffmpeg_bin()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    d = round(max(duration, 0.5), 3)

    sfx_filters = {
        "heartbeat_low":  f"aevalsrc='sin(2*PI*50*t)*exp(-30*(mod(t,1.2)))+0.7*sin(2*PI*48*t)*exp(-30*(mod(t-0.22,1.2)))':d={d}:s=44100,lowpass=f=120,volume=2.0",
        "heartbeat_soft": f"aevalsrc='0.4*sin(2*PI*50*t)*exp(-30*(mod(t,1.5)))':d={d}:s=44100,lowpass=f=100,volume=1.2",
        "eerie_wind":     f"anoisesrc=d={d}:c=pink:r=44100:a=0.3,bandpass=f=300:w=200,volume=1.5",
        "rain_soft":      f"anoisesrc=d={d}:c=pink:r=44100:a=0.2,bandpass=f=1000:w=600,volume=1.0",
        "impact_heavy":   f"aevalsrc='sin(2*PI*(60-8*t)*t)*exp(-4*t)':d={min(d,1.5)}:s=44100,volume=2.5",
        "braam_impact":   f"aevalsrc='sin(2*PI*(42-4*t)*t)*exp(-1.5*t)+0.4*sin(2*PI*84*t)*exp(-2.5*t)':d={min(d,2.0)}:s=44100,volume=3.0",
        "shock_sting":    f"aevalsrc='sin(2*PI*440*t)*exp(-5*t)':d={min(d,0.8)}:s=44100,volume=2.0",
        "whoosh_energy":  f"anoisesrc=d={d}:c=white:r=44100:a=0.2,highpass=f=500,lowpass=f=3000,volume=1.5",
        "tense_pulse":    f"aevalsrc='sin(2*PI*80*t)*exp(-10*(mod(t,0.5)))':d={d}:s=44100,volume=1.5",
        "ambient_soft":   f"anoisesrc=d={d}:c=pink:r=44100:a=0.1,bandpass=f=500:w=400,volume=0.6",
        "ambient_light":  f"anoisesrc=d={d}:c=pink:r=44100:a=0.08,bandpass=f=800:w=600,volume=0.5",
        "thinking_tone":  f"aevalsrc='0.2*sin(2*PI*440*t)*exp(-2*t)':d={min(d,1.0)}:s=44100,volume=1.0",
        "upbeat_chime":   f"aevalsrc='0.5*sin(2*PI*880*t)*exp(-4*t)+0.3*sin(2*PI*1100*t)*exp(-5*t)':d={min(d,0.8)}:s=44100,volume=1.2",
    }

    flt = sfx_filters.get(sfx_name, sfx_filters["ambient_soft"])
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", flt,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_path)
    ], check=True)
    return out_path


def mix_scene_audio(voice_wav: Path, music_wav: Path, sfx_wav: Path,
                     scene_dur: float, out_mixed: Path) -> Path:
    """Mix voiceover (1.35x), background music (0.25x ducked), SFX (0.35x)."""
    ff = ffmpeg_bin()
    out_mixed.parent.mkdir(parents=True, exist_ok=True)

    # 3-input mix: voice loud, music ducked, sfx subtle
    filter_complex = (
        "[0:a]volume=1.35,apad[v];"
        "[1:a]volume=0.25[m];"
        "[2:a]volume=0.35[s];"
        "[v][m][s]amix=inputs=3:duration=longest:dropout_transition=2,"
        f"atrim=end={scene_dur:.3f},aresample=44100"
    )
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(voice_wav),
        "-i", str(music_wav),
        "-i", str(sfx_wav),
        "-filter_complex", filter_complex,
        "-c:a", "aac", "-b:a", "192k",
        str(out_mixed)
    ], check=True)
    return out_mixed


# ─────────────────────────────────────────────────────────────────────────────
# LIVING SHOT RENDERER (with panel-crop support)
# ─────────────────────────────────────────────────────────────────────────────
def render_living_shot(
    img_path: Path,
    duration: float,
    motion: str,
    panel_crop: Optional[tuple[int,int,int,int]],  # (x, y, w, h) crop region or None
    effect: str,
    out_mp4: Path,
    w: int = 1920,
    h: int = 1080,
    fps: int = 30,
) -> Path:
    """
    Renders a living cinematic shot from a single image.
    - If panel_crop is given, first crop to panel region, then apply Ken Burns.
    - motion: slow_push | slow_pull | pan_left | pan_right | tilt_up | tilt_down |
              breathing | subtle_shake | handheld_shake | sudden_zoom | creeping_push
    - effect: color grade + grain based on emotion
    """
    ff = ffmpeg_bin()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    dur = round(duration, 3)

    # Build crop filter string if panel_crop given
    crop_filter = ""
    if panel_crop:
        cx, cy, cw, ch = panel_crop
        crop_filter = f"crop={cw}:{ch}:{cx}:{cy},"

    # Ken Burns motion
    if motion == "slow_push":
        zoom_expr = f"min(1.10, 1.02 + 0.08*t/{dur:.2f})"
        motion_flt = (
            f"scale=w='2*floor({w}*{zoom_expr}/2)':h='2*floor({h}*{zoom_expr}/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2"
        )
    elif motion == "slow_pull":
        zoom_expr = f"max(1.02, 1.10 - 0.08*t/{dur:.2f})"
        motion_flt = (
            f"scale=w='2*floor({w}*{zoom_expr}/2)':h='2*floor({h}*{zoom_expr}/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2"
        )
    elif motion == "pan_right":
        motion_flt = (
            f"scale=w='2*floor({w}*1.12/2)':h='2*floor({h}*1.12/2)',"
            f"crop={w}:{h}:'t/{dur:.2f}*(in_w-{w})':(in_h-{h})/2"
        )
    elif motion == "pan_left":
        motion_flt = (
            f"scale=w='2*floor({w}*1.12/2)':h='2*floor({h}*1.12/2)',"
            f"crop={w}:{h}:'(1-t/{dur:.2f})*(in_w-{w})':(in_h-{h})/2"
        )
    elif motion in ("tilt_down", "tilt_up"):
        y_pos = f"'t/{dur:.2f}*(in_h-{h})'" if motion == "tilt_down" else f"'(1-t/{dur:.2f})*(in_h-{h})'"
        motion_flt = (
            f"scale=w='2*floor({w}*1.08/2)':h='2*floor({h}*1.14/2)',"
            f"crop={w}:{h}:(in_w-{w})/2:{y_pos}"
        )
    elif motion in ("subtle_shake", "handheld_shake", "erratic_shake"):
        intensity = 4 if motion == "subtle_shake" else 8
        motion_flt = (
            f"scale=w='2*floor({w}*1.07/2)':h='2*floor({h}*1.07/2)',"
            f"crop={w}:{h}:"
            f"'(in_w-{w})/2 + {intensity}*sin(14*t) + {intensity//2}*cos(23*t)':"
            f"'(in_h-{h})/2 + {intensity}*cos(11*t) + {intensity//2}*sin(19*t)'"
        )
    elif motion == "breathing":
        motion_flt = (
            f"scale=w='2*floor({w}*(1.03 + 0.015*sin(2*PI*1.1*t))/2)':"
            f"h='2*floor({h}*(1.03 + 0.015*sin(2*PI*1.1*t))/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2"
        )
    elif motion in ("sudden_zoom", "rack_zoom_in", "creeping_push"):
        zoom_expr = f"1.02 + 0.20*pow(t/{dur:.2f}, 1.6)"
        motion_flt = (
            f"scale=w='2*floor({w}*{zoom_expr}/2)':h='2*floor({h}*{zoom_expr}/2)':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2"
        )
    else:
        motion_flt = (
            f"scale=w='2*floor({w}*1.05/2)':h='2*floor({h}*1.05/2)',"
            f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2"
        )

    # Color grade based on effect
    grade_map = {
        "warm":      "colorbalance=rs=0.06:gs=0.02:bs=-0.04:rm=0.03:gm=0.01:bm=-0.02",
        "cold":      "colorbalance=rs=-0.03:gs=0.01:bs=0.06:rm=-0.02:gm=0.0:bm=0.04",
        "horror":    "colorbalance=rs=0.04:gs=-0.01:bs=-0.04:rm=-0.02:gm=0.01:bm=0.03",
        "romantic":  "colorbalance=rs=0.08:gs=0.04:bs=-0.02",
        "dramatic":  "eq=contrast=1.08:saturation=1.15:brightness=-0.01",
        "bright":    "eq=contrast=1.05:saturation=1.20:brightness=0.02",
        "neutral":   "eq=contrast=1.04:saturation=1.08",
    }
    grade = grade_map.get(effect, grade_map["neutral"])

    # Full filter chain
    vf = f"{crop_filter}scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},{motion_flt},{grade},noise=alls=4:allf=t+u,vignette=PI/5,format=yuv420p"

    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-t", str(dur),
        "-i", str(img_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-r", str(fps), "-pix_fmt", "yuv420p",
        str(out_mp4)
    ], check=True)
    return out_mp4


def join_scene(video_mp4: Path, audio_aac: Path, out_mp4: Path) -> Path:
    """Mux video + audio into final scene MP4."""
    ff = ffmpeg_bin()
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(video_mp4),
        "-i", str(audio_aac),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(out_mp4)
    ], check=True)
    return out_mp4


def concat_scenes(scene_files: list[Path], out_mp4: Path) -> Path:
    """Concat all scenes using FFmpeg concat demuxer (-c copy, low RAM)."""
    ff = ffmpeg_bin()
    lst = out_mp4.parent / "concat_list.txt"
    with open(lst, "w", encoding="utf-8") as f:
        for p in scene_files:
            f.write(f"file '{p.resolve().as_posix()}'\n")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c", "copy", str(out_mp4)
    ], check=True)
    if lst.exists():
        lst.unlink()
    return out_mp4


def burn_subtitles(video_mp4: Path, sub_ass: Path, out_mp4: Path) -> Path:
    """Burn ASS subtitles into video."""
    ff = ffmpeg_bin()
    sub_esc = str(sub_ass.resolve()).replace("\\", "/").replace(":", "\\:")
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(video_mp4),
        "-vf", f"ass='{sub_esc}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "copy", "-movflags", "+faststart",
        str(out_mp4)
    ], check=True)
    return out_mp4


def generate_subtitles(pages_meta: list[dict], out_ass: Path) -> Path:
    """Generate perfectly timed ASS subtitle file from scene metadata."""
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Trebuchet MS,52,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,1.2,0,1,3,1.5,2,80,80,55,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    curr = 0.0
    for pm in pages_meta:
        dur = pm.get("duration", 10.0)
        text = pm.get("narration_text", "").replace("\n", " ").strip()
        if not text:
            curr += dur
            continue
        st = curr
        et = curr + dur
        sh = int(st // 3600); sm = int((st % 3600) // 60); ss = st % 60
        eh = int(et // 3600); em = int((et % 3600) // 60); es = et % 60
        lines.append(f"Dialogue: 0,{sh}:{sm:02d}:{ss:05.2f},{eh}:{em:02d}:{es:05.2f},Sub,,0,0,0,,{text}\n")
        curr = et

    out_ass.parent.mkdir(parents=True, exist_ok=True)
    out_ass.write_text("".join(lines), encoding="utf-8")
    return out_ass
