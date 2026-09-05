"""
core/mp3.py — MP3 ki exact duration nikalne wala chhota parser (sirf stdlib).

Kyun chahiye? Word-level subtitle sync ke liye humein pata hona chahiye ki
audio kitne second ka hai. Options the:
  1. ffprobe chalao  -> ffmpeg install hona zaroori, aur Phase 2 mein wo abhi nahi chahiye
  2. mutagen package -> ek aur dependency
  3. Khud frame headers padho -> 40 line, zero dependency  ✅ yahi chuna

Kaam kaise karta hai: MP3 chhote-chhote "frames" ka bana hota hai. Har frame
ka header batata hai bitrate + samplerate. Har frame = 1152 samples (MPEG1 Layer3).
Sab frames gin lo -> total duration mil gaya. VBR files pe bhi sahi kaam karta hai
(kyunki hum har frame ka apna bitrate padhte hain, average nahi maante).
"""

from __future__ import annotations

from pathlib import Path

# Bitrate table — MPEG1 Layer III (kbps). Index 0 aur 15 invalid hain.
_BITRATE_V1_L3 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
# MPEG2/2.5 Layer III bitrates
_BITRATE_V2_L3 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
_SAMPLERATE = {
    3: [44100, 48000, 32000],   # MPEG1
    2: [22050, 24000, 16000],   # MPEG2
    0: [11025, 12000, 8000],    # MPEG2.5
}
_SAMPLES_PER_FRAME = {3: 1152, 2: 576, 0: 576}


def duration_sec(path: str | Path) -> float:
    """MP3 file ki duration seconds mein. File kharab ho to 0.0 return karta hai."""
    data = Path(path).read_bytes()
    i = 0

    # ID3v2 tag skip karo (start mein metadata hota hai, audio nahi)
    if data[:3] == b"ID3" and len(data) > 10:
        size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | \
               ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
        i = 10 + size

    total = 0.0
    n = len(data)
    while i < n - 4:
        # Frame sync: 11 bits sab 1 (0xFF followed by 0xEx)
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            ver = (data[i + 1] >> 3) & 0x03      # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
            layer = (data[i + 1] >> 1) & 0x03    # 1 = Layer III
            br_idx = (data[i + 2] >> 4) & 0x0F
            sr_idx = (data[i + 2] >> 2) & 0x03
            padding = (data[i + 2] >> 1) & 0x01

            if layer == 1 and ver in _SAMPLERATE and sr_idx < 3 and 0 < br_idx < 15:
                table = _BITRATE_V1_L3 if ver == 3 else _BITRATE_V2_L3
                bitrate = table[br_idx] * 1000
                samplerate = _SAMPLERATE[ver][sr_idx]
                spf = _SAMPLES_PER_FRAME[ver]
                if bitrate and samplerate:
                    frame_len = int((spf // 8) * bitrate / samplerate) + padding
                    if frame_len > 4:
                        total += spf / samplerate
                        i += frame_len
                        continue
        i += 1  # sync nahi mila — ek byte aage badho
    return round(total, 3)


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        print(f"{p}: {duration_sec(p)}s")
