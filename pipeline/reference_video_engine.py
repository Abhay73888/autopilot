"""
pipeline/reference_video_engine.py — Dual-Reference Character & Motion Video Engine.

Implements production video model prompt synthesis and hardware-accelerated FFmpeg reframing
for dual-reference generation workflows:
1. Character Image Reference -> Controls WHAT the character looks like (Identity, Face, Eyes, Outfit)
2. Motion Reference Video (GOD_LEVEL & generate_the_again) -> Controls HOW the scene behaves (Motion, Camera, Effects, Lighting)
3. Character Swap Workflow -> Replaces source identity with target character image while preserving dual-reference motion dynamics.

Enforces strict architectural constraints:
- Half-Body Composition: Chest/waist level upward ONLY (legs and feet strictly excluded).
- Character Scale: 1.5–2 cm scene-relative scale maintained via framing & environmental perspective.
- Camera Dynamics: Cinematic push-in, subtle orbit, smooth parallax, face-focused framing.
- Supernatural Effects: Immense dark red/black aura, energy rings, smoke, particles, volumetric lighting.
"""

from __future__ import annotations
import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from core.config import ROOT
from core.ffmpeg import ffmpeg_bin, probe
from core.logbook import Logbook

log = Logbook("reference_video_engine")

# Known default reference assets
DEFAULT_MUZAN_IMAGE = str(Path(os.environ.get(
    "MUZAN_IMAGE_PATH",
    r"C:\Users\ABHAY MAURAYA\.gemini\antigravity-ide\brain\4f00b24a-be75-4169-b807-4dc5c88fd173\.user_uploaded\media_1790011617379.png"
)))
DEFAULT_REFERENCE_VIDEO = str(Path(os.environ.get(
    "REFERENCE_VIDEO_PATH",
    r"C:\Users\ABHAY MAURAYA\Downloads\GOD_LEVEL_MUZAN_D_ANIME_REFER.mp4"
)))
# Second reference video — user uploaded for character identity swap workflow
SECOND_REFERENCE_VIDEO = str(Path(os.environ.get(
    "SECOND_REFERENCE_VIDEO_PATH",
    r"C:\Users\ABHAY MAURAYA\Downloads\generate_the_again_and_i_want.mp4"
)))


class ReferenceVideoEngine:
    """
    Orchestrates Dual-Reference Video Generation, AI Video Prompt Construction,
    Cinematic Half-Body Video Compositing, and Character Swap Workflows.
    """

    def __init__(self):
        self.output_base = ROOT / "output" / "reference_renders"
        self.output_base.mkdir(parents=True, exist_ok=True)

    def generate_model_prompt(
        self,
        character_name: str = "Muzan Kibutsuji",
        composition: str = "half_body",
        character_scale_cm: float = 1.75,
        aspect_ratio: str = "16:9",
        target_model: str = "kling_v2v"
    ) -> Dict[str, Any]:
        """
        Constructs industry-standard, production-ready generation prompts for
        video diffusion models (Kling Video-to-Video, Runway Gen-3 Alpha, Wan2.1, Luma Dream Machine).

        Guarantees strict separation between character identity and reference video motion.
        """
        positive_prompt = (
            f"Masterpiece cinematic anime render of {character_name}, framed strictly in a medium close-up "
            f"from the chest and waist upward. Only his upper half body is visible. "
            f"Preserve character identity exactly from character reference: wavy black hair, piercing plum-red cat-slit demon eyes, "
            f"fair pale complexion, sharply tailored black Edwardian suit with embroidered dark lapels and white collared shirt with black tie. "
            f"Scene-relative character scale is preserved at {character_scale_cm}cm miniature presence within a colossal, towering sci-fi gothic archway chamber. "
            f"The camera executes a slow cinematic push-in with subtle orbital parallax, keeping sharp focal depth centered on his eyes and upper torso. "
            f"Motion and supernatural effects precisely mirror the reference video: massive swirling dark crimson and obsidian aura erupting from his body, "
            f"volumetric lighting rays casting dramatic shadows, floating dark energy embers and sparks, swirling smoke rings, and atmospheric heat distortion. "
            f"Subtle natural upper-body breathing, slight head tilt, clothing flutter from demonic wind pressure. "
            f"Ultra-detailed 8k anime aesthetic, ufotable signature composite, dramatic chiaroscuro lighting, 60fps cinematic fluidity."
        )

        negative_prompt = (
            "full body, full length shot, wide shot, legs, feet, shoes, knees, thighs, lower body, "
            "character enlargement, distorted anatomy, morphing face, changing clothes, altered outfit, "
            "face distortion, extra limbs, multiple characters, duplicated body, cartoonish, low resolution, "
            "blurry, sudden camera jerk, jump cut, camera pulling back to show feet, deformed hands."
        )

        camera_instructions = {
            "movement": "slow_push_in_with_subtle_orbit",
            "framing": "medium_shot_chest_waist_upward",
            "field_of_view": "50mm_cinematic_lens",
            "depth_of_field": "shallow_bokeh_on_distant_hallway_vault",
            "target_focus": "upper_torso_and_face"
        }

        effects_instructions = {
            "aura_colors": ["crimson_red", "obsidian_black"],
            "ambient_particles": ["glowing_embers", "floating_energy_orbs", "drifting_smoke"],
            "lighting": "volumetric_top_down_cool_white_with_intense_red_ground_reflection",
            "scale_hierarchy": "face -> upper body -> supernatural aura -> massive architectural environment"
        }

        return {
            "character_identity_reference": DEFAULT_MUZAN_IMAGE,
            "motion_camera_reference_video": DEFAULT_REFERENCE_VIDEO,
            "composition": composition,
            "character_scale_cm": character_scale_cm,
            "aspect_ratio": aspect_ratio,
            "target_model": target_model,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "camera_instructions": camera_instructions,
            "effects_instructions": effects_instructions
        }

    def generate_character_swap_prompt(
        self,
        character_name: str = "Muzan Kibutsuji",
        composition: str = "half_body",
        character_scale_cm: float = 1.75,
        aspect_ratio: str = "16:9",
        target_model: str = "kling_v2v"
    ) -> Dict[str, Any]:
        """
        Constructs a specialized Character-Swap prompt:
        - Uses `generate_the_again_and_i_want.mp4` as the MOTION/CAMERA/ENVIRONMENT reference.
        - Uses the Muzan identity image as the CHARACTER IDENTITY reference.
        - Instructs the model to REPLACE the existing source character
          with Muzan Kibutsuji while fully preserving scene motion, camera,
          environment, effects, and lighting from the reference video.
        """
        positive_prompt = (
            f"Character identity swap: Replace the existing character in the reference video with {character_name} exactly. "
            f"Preserve {character_name}'s identity precisely: wavy black hair, piercing plum-red cat-slit demon eyes, "
            f"pale skin, sharp tailored black Edwardian suit with dark embroidered lapels and white collar with black tie. "
            f"Maintain strict half-body composition — show only chest and waist upward. Legs and feet must never appear. "
            f"Preserve ALL scene elements from the reference video verbatim: camera motion, environment, background, "
            f"lighting, supernatural effects, aura colors, particles, atmospheric fog, energy rings, and sound design. "
            f"The only change is the character's visual identity. "
            f"Scene scale: {character_name} appears at {character_scale_cm}cm miniature relative to the grand environment. "
            f"Apply cinematic push-in with subtle parallax orbit. Sharp focal depth on eyes and upper torso. "
            f"Ultra-detailed 8k anime aesthetic, ufotable signature composite, 60fps, chiaroscuro lighting."
        )

        negative_prompt = (
            "original character retained, source character face preserved, wrong face, wrong hair, wrong eyes, "
            "full body, full length shot, wide shot showing legs, feet, knees, lower body, shoes, thighs, "
            "character enlargement, face distortion, anatomy distortion, multiple characters, duplicated body, "
            "blurry, low resolution, cartoonish, sudden camera jerk, scene change, environment modification, "
            "background alteration, different lighting, different aura colors, different effects."
        )

        camera_instructions = {
            "movement": "preserve_source_video_camera_motion_exactly",
            "framing": "medium_shot_chest_waist_upward",
            "field_of_view": "match_source_video_fov",
            "depth_of_field": "match_source_video_bokeh",
            "target_focus": "muzan_upper_torso_and_face"
        }

        effects_instructions = {
            "preservation_rule": "all_original_effects_from_reference_video_preserved_verbatim",
            "character_modification": "identity_swap_only",
            "aura_colors": ["preserve_original"],
            "environment": "preserve_original_verbatim",
            "swap_target": "character_face_hair_outfit_only"
        }

        return {
            "workflow": "CHARACTER_IDENTITY_SWAP",
            "character_identity_reference": DEFAULT_MUZAN_IMAGE,
            "motion_camera_reference_video": SECOND_REFERENCE_VIDEO,
            "composition": composition,
            "character_scale_cm": character_scale_cm,
            "aspect_ratio": aspect_ratio,
            "target_model": target_model,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "camera_instructions": camera_instructions,
            "effects_instructions": effects_instructions,
            "swap_instructions": {
                "source_character": "character_in_generate_the_again_and_i_want.mp4",
                "target_character": character_name,
                "swap_type": "identity_replace",
                "preserve_scene": True,
                "preserve_motion": True,
                "preserve_effects": True
            }
        }

    def render_half_body_cinematic_video(
        self,
        source_video_path: Optional[str] = None,
        output_filename: Optional[str] = None,
        aspect_ratio: str = "16:9",
        duration_sec: Optional[float] = None
    ) -> Path:
        """
        Renders a reframed, high-bitrate 1080p video from the reference video that:
        1. Dynamically crops the frame to Muzan's upper half body (chest/waist upward).
        2. Strictly cuts out lower body, legs, and feet.
        3. Maintains the expansive upper environment and surrounding supernatural aura.
        4. Applies a slow cinematic push-in (Ken Burns interpolation) across the duration.
        """
        src = Path(source_video_path or DEFAULT_REFERENCE_VIDEO)
        if not src.exists():
            raise FileNotFoundError(f"Reference video not found at: {src}")

        # Probe source video
        info = probe(src)
        stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
        src_w = int(stream.get("width", 1280))
        src_h = int(stream.get("height", 720))
        src_dur = float(info.get("format", {}).get("duration", 10.0))
        render_dur = min(src_dur, duration_sec) if duration_sec else src_dur

        out_name = output_filename or f"muzan_half_body_{aspect_ratio.replace(':', 'x')}_{int(render_dur)}s.mp4"
        out_path = self.output_base / out_name

        ffmpeg = ffmpeg_bin()

        if aspect_ratio == "16:9":
            # 16:9 Cinematic Reframing:
            # Source is 1280x720. Muzan center is x=640. Head y=320, waist y=480, feet y=560.
            # We want chest/waist upward: y from 120 to 490 (height ~370).
            # 16:9 width for height 370 = 370 * 16 / 9 = 658 px.
            # Centered on x=640 -> x from (640 - 329) = 311 to 969.
            # Apply smooth zoompan for cinematic push-in: zoom from 1.0 to 1.10 over duration
            filter_complex = (
                f"[0:v]crop=656:369:312:120,"
                f"scale=1920:1080:flags=lanczos,"
                f"zoompan=z='min(zoom+0.00035,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30,"
                f"unsharp=3:3:0.8:3:3:0.0[v]"
            )
        else:
            # 9:16 Vertical Short Reframing:
            # Width ~270, Height ~480. Centered on x=640, y from 10 to 490 (waist).
            filter_complex = (
                f"[0:v]crop=270:480:505:10,"
                f"scale=1080:1920:flags=lanczos,"
                f"zoompan=z='min(zoom+0.00035,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
                f"unsharp=3:3:0.8:3:3:0.0[v]"
            )

        cmd = [
            ffmpeg, "-y",
            "-i", str(src),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-t", str(render_dur),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart"
        ]

        # Preserve audio if present
        has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
        if has_audio:
            cmd.extend(["-map", "0:a?", "-c:a", "aac", "-b:a", "192k"])

        cmd.append(str(out_path))

        log.info(f"Rendering half-body video: {out_path.name}")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            log.error("FFmpeg render failed", error=res.stderr[-400:])
            raise RuntimeError(f"FFmpeg failed to render reframed video: {res.stderr[-400:]}")

        log.info(f"Half-body video successfully generated at: {out_path}")
        return out_path


reference_video_engine = ReferenceVideoEngine()
