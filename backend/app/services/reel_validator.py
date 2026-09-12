r"""
backend/app/services/reel_validator.py — Technical Validator for Instagram Reels.

Strictly validates videos against official Meta Instagram Graph API v21.0 specs:
- MP4 / MOV container
- H.264 video codec + AAC audio codec
- Vertical aspect ratio 9:16 (typically 1080x1920)
- Duration between 3s and 90s (API strict limit)
- File size <= 1GB
- Caption length <= 2200 characters
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional

from ..publishers.base import ValidationResult

MAX_IG_REEL_SEC = 90.0
MIN_IG_REEL_SEC = 3.0
MAX_IG_FILE_BYTES = 1024 * 1024 * 1024  # 1 GB
MAX_IG_CAPTION_CHARS = 2200


def validate_reel(video_path_str: str, caption: str = "") -> ValidationResult:
    """
    Validates a video file against Instagram Reel technical requirements.
    """
    errors: List[str] = []
    warnings: List[str] = []
    video_path = Path(video_path_str)

    # 1. Existence check
    if not video_path.exists():
        return ValidationResult(
            is_valid=False,
            errors=[f"Video file not found at path: {video_path_str}"]
        )

    # 2. File size check
    file_size = video_path.stat().st_size
    if file_size == 0:
        return ValidationResult(
            is_valid=False,
            errors=["Video file is empty (0 bytes)"],
            file_size_bytes=0
        )
    if file_size > MAX_IG_FILE_BYTES:
        errors.append(f"File size {file_size / (1024*1024):.1f}MB exceeds Instagram maximum limit of 1GB")

    # 3. File extension
    ext = video_path.suffix.lower()
    if ext not in (".mp4", ".mov"):
        errors.append(f"File extension '{ext}' unsupported. Instagram Reels require .mp4 or .mov container")

    # 4. Caption length & hashtag validation
    if len(caption) > MAX_IG_CAPTION_CHARS:
        errors.append(f"Caption length ({len(caption)} chars) exceeds maximum limit of {MAX_IG_CAPTION_CHARS} characters")
    hashtags = re.findall(r"#\w+", caption)
    if len(hashtags) > 30:
        errors.append(f"Caption contains {len(hashtags)} hashtags. Meta limits to maximum 30 hashtags per post")

    # 5. Deep inspection via ffprobe if available
    duration_sec = 0.0
    resolution = None
    vcodec = None
    acodec = None

    probe_data = _run_ffprobe(str(video_path))
    if probe_data:
        format_info = probe_data.get("format", {})
        streams = probe_data.get("streams", [])

        # Duration
        dur_str = format_info.get("duration")
        if dur_str:
            try:
                duration_sec = float(dur_str)
            except ValueError:
                pass

        # Streams inspection
        for s in streams:
            codec_type = s.get("codec_type")
            if codec_type == "video" and not vcodec:
                vcodec = s.get("codec_name")
                width = s.get("width")
                height = s.get("height")
                if width and height:
                    resolution = f"{width}x{height}"
                    # Aspect ratio check: 9:16 vertical ratio (e.g. 1080x1920)
                    ratio = width / height
                    if ratio > 0.65:  # Wider than ~9:14 is not vertical Reel format
                        errors.append(f"Invalid aspect ratio ({width}x{height}, ratio {ratio:.2f}). Instagram Reels must be vertical 9:16 (recommended 1080x1920)")
            elif codec_type == "audio" and not acodec:
                acodec = s.get("codec_name")

        # Codec requirements: H.264 & AAC
        if vcodec and vcodec.lower() not in ("h264", "avc1"):
            errors.append(f"Video codec '{vcodec}' unsupported. Instagram requires H.264 (AVC)")
        if acodec and acodec.lower() not in ("aac", "mp4a"):
            warnings.append(f"Audio codec '{acodec}' might cause processing issues. Recommended audio codec is AAC")

        # Duration bounds
        if duration_sec > 0:
            if duration_sec < MIN_IG_REEL_SEC:
                errors.append(f"Video duration {duration_sec:.1f}s is shorter than minimum allowed {MIN_IG_REEL_SEC}s")
            elif duration_sec > MAX_IG_REEL_SEC:
                errors.append(f"Video duration {duration_sec:.1f}s exceeds Instagram API strict limit of {MAX_IG_REEL_SEC}s")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        duration_sec=duration_sec,
        resolution=resolution,
        codec=f"{vcodec}+{acodec}" if vcodec else None,
        file_size_bytes=file_size
    )


def _run_ffprobe(file_path: str) -> Optional[dict]:
    """Runs ffprobe on the target file and returns parsed JSON output."""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout:
            return json.loads(res.stdout)
    except Exception:
        pass
    return None
