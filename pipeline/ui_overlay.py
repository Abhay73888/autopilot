"""
pipeline/ui_overlay.py — Programmatic Mobile UI Overlays (Phase A Upgrade)

Generates transparent high-DPI (1080x1920) graphical overlays:
  1. iOS / Instagram Notification Banner (glassmorphic dark mode).
  2. Instagram DM / WhatsApp Message Bubble (sent or received).
  3. Animated Typing Dots Indicator (...) for romantic & suspense cliffhangers.

Uses pure Pillow (PIL) + Free Devanagari/Sans fonts from assets/fonts.
"""

from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from core.config import CONFIG
from core.logbook import Logbook

log = Logbook("ui_overlay")

FONTS_DIR = Path(CONFIG["_root"]) / "assets" / "fonts"


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load system or bundled font with graceful fallback."""
    font_candidates = [
        FONTS_DIR / "NotoSansDevanagari-Bold.ttf" if bold else FONTS_DIR / "NotoSansDevanagari-Regular.ttf",
        FONTS_DIR / "NotoSans-Bold.ttf" if bold else FONTS_DIR / "NotoSans-Regular.ttf",
        Path("C:/Windows/Fonts/seguiemj.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for p in font_candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_notification_banner(title: str, message: str,
                               app_name: str = "Instagram",
                               avatar_letter: str = "M",
                               out_path: str | Path = "scratch/notif_overlay.png",
                               *, width: int = 1080, height: int = 1920) -> Path:
    """
    Renders an iOS/Instagram style glassmorphic notification banner at the top of 1080x1920 canvas.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Banner dimensions
    card_w = 980
    card_h = 220
    x0 = (width - card_w) // 2
    y0 = 140
    x1 = x0 + card_w
    y1 = y0 + card_h
    corner_r = 44

    # Dark translucent card background + glow border
    draw.rounded_rectangle([x0, y0, x1, y1], radius=corner_r,
                           fill=(20, 20, 24, 235),
                           outline=(70, 70, 85, 200), width=3)

    # Avatar Circle
    av_size = 110
    av_x = x0 + 40
    av_y = y0 + (card_h - av_size) // 2
    draw.ellipse([av_x, av_y, av_x + av_size, av_y + av_size],
                 fill=(225, 48, 108, 255))  # Instagram pink/coral

    # Avatar Letter
    av_font = _get_font(52, bold=True)
    draw.text((av_x + 36, av_y + 22), avatar_letter.upper(), font=av_font, fill=(255, 255, 255, 255))

    # Text headers
    app_font = _get_font(32, bold=False)
    title_font = _get_font(42, bold=True)
    msg_font = _get_font(36, bold=False)

    text_x = av_x + av_size + 35
    draw.text((text_x, y0 + 35), f"{app_name.upper()} • now", font=app_font, fill=(170, 170, 185, 220))
    draw.text((text_x, y0 + 80), title, font=title_font, fill=(255, 255, 255, 255))
    draw.text((text_x, y0 + 138), message, font=msg_font, fill=(210, 210, 225, 240))

    img.save(out_path, "PNG")
    log.info(f"Notification banner created: {out_path}")
    return out_path


def create_dm_bubble(message: str,
                     sender_name: str = "Meera",
                     out_path: str | Path = "scratch/dm_bubble.png",
                     *, is_sent: bool = False,
                     show_typing: bool = False,
                     width: int = 1080, height: int = 1920) -> Path:
    """
    Renders an Instagram DM message bubble centered in lower-third of 1080x1920 canvas.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    msg_font = _get_font(48, bold=False)
    name_font = _get_font(32, bold=True)

    # Measure message size
    if show_typing:
        display_text = " •  •  • "
    else:
        display_text = message

    bbox = draw.textbbox((0, 0), display_text, font=msg_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    pad_x = 55
    pad_y = 35
    bw = max(240, tw + pad_x * 2)
    bh = th + pad_y * 2

    # Placement: center-lower
    y_pos = int(height * 0.58)

    if is_sent:
        # Sent bubble (Right aligned / blue-purple gradient)
        x1 = width - 110
        x0 = x1 - bw
        fill_col = (55, 115, 255, 240)
        outline_col = (90, 145, 255, 220)
        txt_col = (255, 255, 255, 255)
    else:
        # Received bubble (Left aligned / dark grey with avatar)
        x0 = 110
        x1 = x0 + bw
        fill_col = (38, 38, 44, 240)
        outline_col = (80, 80, 95, 200)
        txt_col = (255, 255, 255, 255)
        # Sender label
        draw.text((x0 + 10, y_pos - 45), sender_name, font=name_font, fill=(180, 180, 195, 220))

    draw.rounded_rectangle([x0, y_pos, x1, y_pos + bh], radius=38,
                           fill=fill_col, outline=outline_col, width=2)

    # Text inside bubble
    tx = x0 + (bw - tw) // 2
    ty = y_pos + (bh - th) // 2 - 4
    draw.text((tx, ty), display_text, font=msg_font, fill=txt_col)

    img.save(out_path, "PNG")
    log.info(f"DM bubble created: {out_path}")
    return out_path
