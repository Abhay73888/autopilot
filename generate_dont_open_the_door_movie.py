"""
generate_dont_open_the_door_movie.py — Master Production Script.
Transforms 30 Anime Storyboard Keyframes into a 10-Minute Living Horror Film:
"DON'T OPEN THE DOOR" (1920x1080 Widescreen, Living Motion, Edge-TTS, Sound Design, Subtitles).
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
import subprocess

from core.ffmpeg import ffmpeg_bin, probe
from pipeline.anime_horror_engine import (
    SCENES_SCRIPT,
    generate_scene_voice,
    mix_scene_audio,
    render_living_shot,
    join_shots_with_audio,
    create_cinematic_subtitles
)

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output" / "dont_open_the_door_movie"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
CLEAN_IMG_DIR = BASE_DIR / "data" / "anime_horror_scenes" / "raw_clean"
CU_IMG_DIR = BASE_DIR / "data" / "anime_horror_scenes" / "closeup"


async def main():
    print("=" * 70)
    print("🎬 GOD MODE — LIVING ANIME HORROR FILM PRODUCER")
    print("🎬 'DON'T OPEN THE DOOR' (30 Scenes · 10-Minute Living Anime Feature)")
    print("=" * 70)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    
    total_scenes = len(SCENES_SCRIPT)
    rendered_scenes: list[Path] = []
    scenes_metadata: list[dict] = []
    cumulative_time = 0.0
    
    for idx, sc in enumerate(SCENES_SCRIPT, start=1):
        sc_id = sc["id"]
        title = sc["title"]
        scene_target = CHECKPOINT_DIR / f"scene_{sc_id:02d}.mp4"
        
        print(f"\n[{idx}/{total_scenes}] Processing Scene #{sc_id:02d}: {title}")
        
        # Check if already rendered (Checkpointing)
        if scene_target.exists() and scene_target.stat().st_size > 100000:
            info = probe(scene_target)
            sc_dur = float(info.get("format", {}).get("duration", 20.0))
            print(f"  ✓ Checkpoint hit: already rendered ({sc_dur:.1f}s)")
            rendered_scenes.append(scene_target)
            scenes_metadata.append({
                "id": sc_id,
                "title": title,
                "narration": sc["narration"],
                "duration": sc_dur,
                "start_sec": cumulative_time
            })
            cumulative_time += sc_dur
            continue
            
        # 1. Image Paths
        wide_img = CLEAN_IMG_DIR / f"scene_{sc_id:02d}_wide.png"
        cu_img = CU_IMG_DIR / f"scene_{sc_id:02d}_cu.png"
        
        if not wide_img.exists() or not cu_img.exists():
            raise FileNotFoundError(f"Missing images for scene {sc_id}")
            
        # 2. Voice Generation
        voice_wav = CHECKPOINT_DIR / f"voice_{sc_id:02d}.wav"
        if not voice_wav.exists():
            print("  🎙️ Synthesizing neural Hindi voiceover...")
            await generate_scene_voice(sc_id, sc["narration"], voice_wav)
            
        # Measure voice duration
        info = probe(voice_wav)
        raw_dur = float(info.get("format", {}).get("duration", 18.0))
        # Add 1.5s breathing pause at end of scene
        scene_dur = max(16.0, raw_dur + 1.5)
        
        # 3. SFX and Audio Mixing
        mixed_audio = CHECKPOINT_DIR / f"mixed_{sc_id:02d}.aac"
        if not mixed_audio.exists():
            print(f"  🔊 Mixing horror sound design & SFX ({sc['sfx']})...")
            mix_scene_audio(voice_wav, sc.get("sfx", []), scene_dur, mixed_audio)
            
        # 4. Render Living Shots (2 Sub-Shots per scene)
        dur1 = round(scene_dur * 0.52, 2)
        dur2 = round(scene_dur - dur1, 2)
        
        shot1_plan = sc["shots"][0]
        shot2_plan = sc["shots"][1]
        
        shot1_mp4 = CHECKPOINT_DIR / f"shot1_{sc_id:02d}.mp4"
        shot2_mp4 = CHECKPOINT_DIR / f"shot2_{sc_id:02d}.mp4"
        
        if not shot1_mp4.exists() or shot1_mp4.stat().st_size < 10000:
            print(f"  🎥 Rendering Shot A ({shot1_plan['type']}, {shot1_plan['motion']}, {dur1:.1f}s)...")
            render_living_shot(
                wide_img if shot1_plan["type"] == "wide" else cu_img,
                dur1,
                shot1_plan["type"],
                shot1_plan["motion"],
                shot1_plan["effect"],
                shot1_mp4
            )
        else:
            print(f"  ✓ Shot A already rendered ({dur1:.1f}s)")
        
        if not shot2_mp4.exists() or shot2_mp4.stat().st_size < 10000:
            print(f"  🎥 Rendering Shot B ({shot2_plan['type']}, {shot2_plan['motion']}, {dur2:.1f}s)...")
            render_living_shot(
                cu_img if shot2_plan["type"] == "cu" else wide_img,
                dur2,
                shot2_plan["type"],
                shot2_plan["motion"],
                shot2_plan["effect"],
                shot2_mp4
            )
        else:
            print(f"  ✓ Shot B already rendered ({dur2:.1f}s)")
        
        # 5. Join Shots + Audio
        print(f"  🎞️ Stitches shots into Scene #{sc_id:02d} MP4...")
        join_shots_with_audio([shot1_mp4, shot2_mp4], mixed_audio, scene_target)
        
        # Cleanup shot temp files
        if shot1_mp4.exists(): shot1_mp4.unlink()
        if shot2_mp4.exists(): shot2_mp4.unlink()
        
        rendered_scenes.append(scene_target)
        scenes_metadata.append({
            "id": sc_id,
            "title": title,
            "narration": sc["narration"],
            "duration": scene_dur,
            "start_sec": cumulative_time
        })
        cumulative_time += scene_dur
        print(f"  ✅ Scene #{sc_id:02d} complete! Total cumulative: {cumulative_time/60:.2f} min")
        
    print("\n" + "=" * 70)
    print(f"🎬 ALL 30 SCENES RENDERED! Cumulative Duration: {cumulative_time:.1f}s ({cumulative_time/60:.2f} min)")
    print("=" * 70)
    
    # 6. Generate Subtitles
    print("\n📝 Generating synced cinematic subtitles (.ass and .srt)...")
    sub_ass = OUTPUT_DIR / "subtitles.ass"
    create_cinematic_subtitles(scenes_metadata, sub_ass)
    
    # Also generate .srt
    sub_srt = OUTPUT_DIR / "subtitles.srt"
    with open(sub_srt, "w", encoding="utf-8") as f:
        for idx, sm in enumerate(scenes_metadata, 1):
            s_sec = sm["start_sec"]
            e_sec = s_sec + sm["duration"]
            sh, sm_m, ss = int(s_sec//3600), int((s_sec%3600)//60), s_sec%60
            eh, em_m, es = int(e_sec//3600), int((e_sec%3600)//60), e_sec%60
            f.write(f"{idx}\n{sh:02d}:{sm_m:02d}:{int(ss):02d},{int((ss%1)*1000):03d} --> {eh:02d}:{em_m:02d}:{int(es):02d},{int((es%1)*1000):03d}\n{sm['narration']}\n\n")
            
    # 7. Stitch All 30 Scenes via FFmpeg Concat Demuxer (-c copy, low RAM)
    print("\n🔗 Concat Demuxing 30 scenes into final feature film...")
    concat_list = OUTPUT_DIR / "concat_feature_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in rendered_scenes:
            f.write(f"file '{p.resolve().as_posix()}'\n")
            
    unsubbed_feature = OUTPUT_DIR / "feature_unsubbed.mp4"
    ff = ffmpeg_bin()
    cmd_concat = [
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(unsubbed_feature)
    ]
    subprocess.run(cmd_concat, check=True)
    if concat_list.exists(): concat_list.unlink()
    
    # 8. Burn Cinematic Subtitles
    final_mp4 = OUTPUT_DIR / "final.mp4"
    print("\n🔤 Burning subtitles onto broadcast master...")
    
    # Escape path for FFmpeg subtitles filter
    sub_esc = str(sub_ass.resolve()).replace("\\", "/").replace(":", "\\:")
    cmd_sub = [
        ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(unsubbed_feature),
        "-vf", f"ass='{sub_esc}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(final_mp4)
    ]
    subprocess.run(cmd_sub, check=True)
    
    # 9. Generate Master Thumbnail Cover
    cover_jpg = OUTPUT_DIR / "cover.jpg"
    thumb_src = CLEAN_IMG_DIR / "scene_30_wide.png"
    if thumb_src.exists():
        cmd_thumb = [
            ff, "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(thumb_src),
            "-vf", "scale=1280:720",
            str(cover_jpg)
        ]
        subprocess.run(cmd_thumb, check=True)
        
    # 10. Write Manifest & YouTube Auto-Chapters
    manifest_data = {
        "title": "DON'T OPEN THE DOOR — Full Animated Horror Film (Anime Horror Episode)",
        "duration_sec": cumulative_time,
        "resolution": "1920x1080",
        "aspect_ratio": "16:9",
        "profile": "longform",
        "scenes_count": total_scenes,
        "chapters": [
            {
                "title": sm["title"],
                "start_sec": sm["start_sec"],
                "timestamp": f"{int(sm['start_sec']//60):02d}:{int(sm['start_sec']%60):02d}"
            }
            for sm in scenes_metadata
        ],
        "final_video_path": str(final_mp4),
        "cover_path": str(cover_jpg),
        "subtitles_path": str(sub_ass)
    }
    
    manifest_json = OUTPUT_DIR / "manifest.json"
    manifest_json.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print("\n" + "=" * 70)
    print("🎉 MASTERPIECE COMPLETED!")
    print(f"📁 Video: {final_mp4}")
    print(f"⏱️ Duration: {cumulative_time/60:.2f} minutes ({cumulative_time:.1f}s)")
    print(f"🖼️ Cover: {cover_jpg}")
    print(f"📑 Chapters: {len(scenes_metadata)} auto-chapters created starting at 00:00")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
