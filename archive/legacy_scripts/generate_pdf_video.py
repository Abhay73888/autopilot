"""
generate_pdf_video.py — AUTOPILOT: PDF → Human-Like Cinematic Video.

Usage:
    python generate_pdf_video.py --pdf path/to/manga.pdf [--title "My Manga"]
                                 [--lang hi] [--output output/my_manga/]
                                 [--aspect 16:9] [--upload]

Features:
  • PDF pages → high-res image extraction
  • Manga panel detection & reading order
  • OCR text extraction (PyMuPDF + pdfplumber)
  • Emotion detection per page/panel
  • Edge-TTS human-like voice with per-emotion rate/pitch variation
  • Per-character consistent voice assignment
  • Procedural background music per emotion
  • Procedural sound effects per scene
  • Professional 3-track audio mix (voice 1.35x | music 0.25x | sfx 0.35x)
  • Living Ken Burns shots with panel-focus cropping
  • ASS subtitle generation (perfectly synced)
  • Checkpointed render (resume after crash)
  • Final concat + subtitle burn → MP4
  • Optional YouTube upload
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pipeline.pdf_video_engine import (
    PDFExtractor,
    MangaPanelDetector,
    detect_emotion,
    pick_camera,
    generate_human_voice,
    synthesize_emotion_music,
    synthesize_sfx,
    mix_scene_audio,
    render_living_shot,
    join_scene,
    concat_scenes,
    burn_subtitles,
    generate_subtitles,
    EMOTION_VOICE,
)
from core.ffmpeg import ffmpeg_bin, probe


def detect_language(text: str) -> str:
    """Simple language detection: check for Devanagari script."""
    if not text:
        return "en"
    hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    if hindi_chars / max(len(text), 1) > 0.1:
        return "hi"
    try:
        from langdetect import detect
        lang = detect(text)
        return lang if lang in ("hi", "en", "ja", "zh-cn") else "en"
    except Exception:
        return "en"


def assign_character(page_num: int, text: str, num_pages: int) -> str:
    """Simple character assignment based on context clues."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["narrator", "narration", "setting:", "scene:", "[narrator]"]):
        return "narrator"
    if any(w in text_lower for w in ["she", "her", "woh ladki", "meera", "girl", "aurat", "boli", "boli:"]):
        return "female"
    if any(w in text_lower for w in ["baba", "uncle", "old", "buzurg", "dadaji"]):
        return "male_old"
    if any(w in text_lower for w in ["bachcha", "child", "chhota"]):
        return "child"
    # Default: alternate narrator / male_young
    return "narrator" if page_num % 3 == 0 else "male_young"


def determine_effect(emotion: str, page_num: int) -> str:
    """Map emotion to color grade effect."""
    effect_map = {
        "happy": "bright",
        "excited": "bright",
        "romantic": "romantic",
        "sad": "cold",
        "fearful": "horror",
        "angry": "dramatic",
        "mysterious": "horror",
        "desperate": "dramatic",
    }
    return effect_map.get(emotion, "neutral")


async def process_page(
    page: dict,
    panels: list,
    cp_dir: Path,
    language: str,
) -> dict:
    """
    Process a single PDF page into a rendered MP4 scene with voice, music, SFX.
    Returns metadata dict for this scene.
    """
    pid = page["page_num"]
    text = page["text"]
    img_path = page["image_path"]

    scene_mp4 = cp_dir / f"scene_{pid:03d}.mp4"

    # ── Check checkpoint ──────────────────────────────────────────────────────
    if scene_mp4.exists() and scene_mp4.stat().st_size > 50000:
        info = probe(scene_mp4)
        dur = float(info["format"]["duration"])
        print(f"  ✓ Checkpoint: scene_{pid:03d}.mp4 ({dur:.1f}s)")
        return {"page_num": pid, "duration": dur, "narration_text": text, "scene_mp4": scene_mp4}

    # ── Emotion & character detection ─────────────────────────────────────────
    narration_text = text if text else f"Page {pid}"
    emotion = detect_emotion(narration_text)
    character = assign_character(pid, narration_text, 1)
    effect = determine_effect(emotion, pid)

    # ── Voice generation ──────────────────────────────────────────────────────
    voice_wav = cp_dir / f"voice_{pid:03d}.wav"
    if not voice_wav.exists():
        print(f"  🎙️ Generating voice (emotion={emotion}, char={character})...")
        if narration_text.strip():
            await generate_human_voice(narration_text, emotion, character, pid, voice_wav, language)
        else:
            # Silent 3s for pages with no text
            ff = ffmpeg_bin()
            import subprocess
            subprocess.run([
                ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "3",
                "-c:a", "pcm_s16le", str(voice_wav)
            ], check=True)

    # Measure voice duration → scene duration = voice + breathing pause
    vinfo = probe(voice_wav)
    raw_dur = float(vinfo["format"]["duration"])
    scene_dur = max(6.0, raw_dur + 1.2)  # at least 6s per page

    # ── Music ─────────────────────────────────────────────────────────────────
    music_wav = cp_dir / f"music_{pid:03d}.wav"
    if not music_wav.exists():
        print(f"  🎵 Generating background music ({emotion})...")
        synthesize_emotion_music(emotion, scene_dur, music_wav)

    # ── SFX ───────────────────────────────────────────────────────────────────
    sfx_wav = cp_dir / f"sfx_{pid:03d}.wav"
    if not sfx_wav.exists():
        ep = EMOTION_VOICE.get(emotion, EMOTION_VOICE["neutral"])
        sfx_name = ep.get("sfx", "ambient_soft")
        print(f"  🔊 Generating SFX ({sfx_name})...")
        synthesize_sfx(sfx_name, scene_dur, sfx_wav)

    # ── Audio mix ─────────────────────────────────────────────────────────────
    mixed_aac = cp_dir / f"mixed_{pid:03d}.aac"
    if not mixed_aac.exists():
        print(f"  🎚️ Mixing audio...")
        mix_scene_audio(voice_wav, music_wav, sfx_wav, scene_dur, mixed_aac)

    # ── Select primary panel (biggest or first) ────────────────────────────────
    panel_crop = None
    if panels and len(panels) > 1:
        # Pick largest panel as primary focus
        biggest = max(panels, key=lambda p: p[2] * p[3])
        panel_crop = biggest  # (x, y, w, h)

    # ── Render living shot ────────────────────────────────────────────────────
    raw_video_mp4 = cp_dir / f"raw_{pid:03d}.mp4"
    if not raw_video_mp4.exists():
        motion = pick_camera(emotion, pid)
        print(f"  🎥 Rendering living shot (motion={motion}, effect={effect}, {scene_dur:.1f}s)...")
        render_living_shot(
            img_path=img_path,
            duration=scene_dur,
            motion=motion,
            panel_crop=panel_crop,
            effect=effect,
            out_mp4=raw_video_mp4,
        )

    # ── Join video + audio ────────────────────────────────────────────────────
    print(f"  🎞️ Joining video + audio...")
    join_scene(raw_video_mp4, mixed_aac, scene_mp4)

    # Cleanup intermediate
    for tmp in [raw_video_mp4]:
        if tmp.exists():
            tmp.unlink()

    print(f"  ✅ Scene {pid:03d} done! ({scene_dur:.1f}s, emotion={emotion})")
    return {"page_num": pid, "duration": scene_dur, "narration_text": narration_text, "scene_mp4": scene_mp4}


async def main(args):
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)

    title = args.title or pdf_path.stem.replace("_", " ").title()
    out_dir = Path(args.output) if args.output else ROOT / "output" / pdf_path.stem
    cp_dir = out_dir / "checkpoints"
    pages_dir = out_dir / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    cp_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("📖 PDF → HUMAN-LIKE CINEMATIC VIDEO ENGINE")
    print(f"📄 PDF: {pdf_path.name}")
    print(f"🎬 Title: {title}")
    print("=" * 70)

    # ── STEP 1: Extract pages ─────────────────────────────────────────────────
    print("\n[1/7] 📄 Extracting PDF pages...")
    extractor = PDFExtractor(pdf_path, pages_dir, dpi=200)
    pages = extractor.extract_all()
    print(f"  → {len(pages)} pages extracted.")

    # ── Detect language ───────────────────────────────────────────────────────
    all_text = " ".join(p["text"] for p in pages)
    language = args.lang or detect_language(all_text)
    print(f"  → Detected language: {language}")

    # ── STEP 2: Manga panel detection ─────────────────────────────────────────
    print("\n[2/7] 🔍 Detecting manga panels...")
    detector = MangaPanelDetector()
    all_panels: list[list] = []
    for page in pages:
        panels = detector.detect_panels(page["image_path"])
        all_panels.append(panels)
        print(f"  Page {page['page_num']:03d}: {len(panels)} panel(s) detected.")

    # ── STEP 3: Process each page ─────────────────────────────────────────────
    print(f"\n[3/7] 🎬 Processing {len(pages)} pages into living scenes...")
    scenes_meta: list[dict] = []
    for idx, page in enumerate(pages):
        pid = page["page_num"]
        print(f"\n  [{pid}/{len(pages)}] Page #{pid}")
        meta = await process_page(page, all_panels[idx], cp_dir, language)
        scenes_meta.append(meta)

    # ── STEP 4: Generate subtitles ────────────────────────────────────────────
    print("\n[4/7] 📝 Generating synced subtitles...")
    sub_ass = out_dir / "subtitles.ass"
    generate_subtitles(scenes_meta, sub_ass)
    print(f"  ✓ Subtitles: {sub_ass}")

    # ── STEP 5: Concat all scenes ─────────────────────────────────────────────
    print("\n[5/7] 🔗 Concatenating all scenes...")
    unsubbed_mp4 = out_dir / "unsubbed.mp4"
    scene_files = [Path(sm["scene_mp4"]) for sm in scenes_meta]
    concat_scenes(scene_files, unsubbed_mp4)
    info = probe(unsubbed_mp4)
    total_dur = float(info["format"]["duration"])
    print(f"  ✓ Unsubbed feature: {total_dur:.1f}s ({total_dur/60:.2f} min)")

    # ── STEP 6: Burn subtitles ────────────────────────────────────────────────
    print("\n[6/7] 🔤 Burning subtitles...")
    final_mp4 = out_dir / "final.mp4"
    burn_subtitles(unsubbed_mp4, sub_ass, final_mp4)
    final_size = final_mp4.stat().st_size / (1024 * 1024)
    print(f"  ✓ Final: {final_mp4} ({final_size:.2f} MB)")

    # ── STEP 7: Thumbnail ─────────────────────────────────────────────────────
    print("\n[7/7] 🖼️ Generating thumbnail...")
    cover_jpg = out_dir / "cover.jpg"
    ff = ffmpeg_bin()
    import subprocess
    # Use cover page (first or page at 10% into PDF)
    cover_src = pages[min(1, len(pages)-1)]["image_path"]
    subprocess.run([
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(cover_src), "-vf", "scale=1280:720",
        str(cover_jpg)
    ], check=True)

    # ── STEP 8: Manifest ──────────────────────────────────────────────────────
    manifest = {
        "title": title,
        "pdf": str(pdf_path),
        "language": language,
        "total_pages": len(pages),
        "duration_sec": total_dur,
        "duration_min": round(total_dur / 60, 2),
        "resolution": "1920x1080",
        "final_video": str(final_mp4),
        "subtitles": str(sub_ass),
        "cover": str(cover_jpg),
        "chapters": [
            {"page": sm["page_num"], "start_sec": round(sum(s["duration"] for s in scenes_meta[:i]), 2)}
            for i, sm in enumerate(scenes_meta)
        ]
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 70)
    print("🎉 VIDEO READY!")
    print(f"📁 File: {final_mp4}")
    print(f"⏱️ Duration: {total_dur:.1f}s ({total_dur/60:.2f} min)")
    print(f"📦 Size: {final_size:.2f} MB")
    print(f"📄 Pages: {len(pages)} | Language: {language.upper()}")
    print("=" * 70)

    # ── Optional YouTube upload ────────────────────────────────────────────────
    if args.upload:
        print("\n🚀 Uploading to YouTube...")
        try:
            from agents.publisher import YouTubePublisher
            from core.db import DB
            pub = YouTubePublisher(db=DB())
            result = pub.upload_file(
                path=final_mp4,
                title=title[:95],
                description=(
                    f"{title} — Hindi Narrated Video\n\n"
                    f"PDF se bana cinematic narrated video. {len(pages)} pages.\n\n"
                    "#hindi #manga #comic #story #animation"
                ),
                tags=["hindi", "manga", "comic", "story", "animated", "narrated", "hindi story"],
                privacy="public",
                thumbnail=cover_jpg,
                language=language,
            )
            if result.get("status") == "published":
                print(f"✅ LIVE: {result['url']}")
            else:
                print(f"⚠️ Upload result: {result}")
        except Exception as e:
            print(f"⚠️ Upload failed: {e}")

    return final_mp4


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF → Human-Like Cinematic Video")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--title", default=None, help="Video title")
    parser.add_argument("--lang", default=None, help="Language code: hi or en")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--aspect", default="16:9", help="Aspect ratio (default 16:9)")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after render")
    args = parser.parse_args()
    asyncio.run(main(args))
