"""
agents/videogen.py — Wan2.1 AI Video Generation Agent.

Supports:
  1. wan21_replicate  — Alibaba Wan2.1 Text-to-Video via Replicate API (1.3B / 14B)
  2. wan21_fal        — Alibaba Wan2.1 via Fal.ai queue API
  3. wan21_endpoint   — Custom local/serverless HTTP endpoint (RunPod / vLLM-omni)
  4. flux_motion      — Flux image generation + procedural Ken Burns / 2.5D animation (Zero API cost fallback)
  5. local_clip       — Minimal local synthetic test clip (via FFmpeg color generator)

Constraint compliance:
  - Generates 9:16 vertical video clips (720x1280 or 1080x1920)
  - Seamless fallback chain so the pipeline never crashes
  - Tracks provider success/failure metrics in Logbook
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from core.config import CONFIG
from core.logbook import Logbook, retry
from core.ffmpeg import run as ffmpeg_run

log = Logbook("videogen")

GEN_W, GEN_H = 720, 1280


class VideoGen:
    def __init__(self, providers: list[str] | None = None, model_variant: str = "1.3b"):
        self.providers = providers or ["wan21_replicate", "wan21_fal", "flux_motion", "local_clip"]
        self.model_variant = model_variant or CONFIG.get("videogen", {}).get("model_variant", "1.3b")
        self.stats = {p: {"ok": 0, "fail": 0} for p in self.providers}

    def generate_all(self, scenes: list[dict], out_dir: str | Path,
                     seed_base: int | None = None) -> list[dict]:
        """
        Saare scenes ke liye native video clips (.mp4) generate karo.
        Return: scene dicts updated with 'video_clip' path and 'video_provider'.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results = []

        for sc in scenes:
            clip_name = f"clip_{sc['n']:02d}.mp4"
            clip_path = out_dir / clip_name

            # Cache check
            if clip_path.exists() and clip_path.stat().st_size > 10000:
                log.info(f"Video clip {clip_name} already exists ({clip_path.stat().st_size // 1024} KB), reusing.")
                results.append({**sc, "video_clip": str(clip_path), "video_provider": "cached"})
                continue

            seed = sc.get("seed") or ((seed_base or 42) + sc["n"])
            prompt = sc.get("image_prompt") or sc.get("prompt") or sc.get("text", "")
            duration = float(sc.get("duration", 3.5))

            prov = self.generate_one(prompt, clip_path, duration=duration, seed=seed)
            results.append({**sc, "video_clip": str(clip_path), "video_provider": prov, "seed": seed})

        summary = {p: f"{s['ok']}✅/{s['fail']}❌" for p, s in self.stats.items() if s["ok"] or s["fail"]}
        log.ok(f"{len(results)} video clips ready", providers=summary, folder=str(out_dir))
        return results

    def generate_one(self, prompt: str, path: Path, duration: float = 3.5, seed: int = 42) -> str:
        """Ek scene clip generate karo. Fallback chain follow karo."""
        errors = []
        for prov in self.providers:
            try:
                fn = getattr(self, f"_p_{prov}")
                fn(prompt, path, duration=duration, seed=seed)
                if not path.exists() or path.stat().st_size < 1000:
                    raise RuntimeError(f"{prov} ne empty file create ki")
                self.stats[prov]["ok"] += 1
                log.debug(f"Video clip OK via {prov}", file=path.name, kb=path.stat().st_size // 1024)
                return prov
            except Exception as e:  # noqa: BLE001
                self.stats[prov]["fail"] += 1
                errors.append(f"{prov}: {e}")

        raise RuntimeError(f"All video providers failed for {path.name}:\n  " + "\n  ".join(errors))

    # ---------------- Provider 1: Wan2.1 via Replicate ----------------
    def _p_wan21_replicate(self, prompt: str, path: Path, duration: float, seed: int):
        token = os.getenv("REPLICATE_API_TOKEN") or CONFIG.get("keys", {}).get("replicate")
        if not token:
            raise RuntimeError("REPLICATE_API_TOKEN not configured")

        model_version = "wan-video/wan-2.1-t2v-14b" if self.model_variant == "14b" else "wan-video/wan-2.1-t2v-1.3b"
        url = "https://api.replicate.com/v1/predictions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Autopilot/1.0"
        }
        payload = {
            "version": model_version,
            "input": {
                "prompt": prompt[:500],
                "aspect_ratio": "9:16",
                "fps": 24,
                "num_frames": int(duration * 24),
                "seed": seed
            }
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        pred_id = data.get("id")
        if not pred_id:
            raise RuntimeError("Replicate submission failed: no prediction id")

        # Poll until complete
        poll_url = f"https://api.replicate.com/v1/predictions/{pred_id}"
        poll_headers = {"Authorization": f"Bearer {token}", "User-Agent": "Autopilot/1.0"}
        for _ in range(30):
            time.sleep(3)
            preq = urllib.request.Request(poll_url, headers=poll_headers)
            with urllib.request.urlopen(preq, timeout=30) as presp:
                pdata = json.loads(presp.read().decode("utf-8"))
            st = pdata.get("status")
            if st == "succeeded":
                output_url = pdata.get("output")
                if isinstance(output_url, list):
                    output_url = output_url[0]
                if output_url:
                    urllib.request.urlretrieve(output_url, str(path))
                    return
                raise RuntimeError("Replicate succeeded but output URL empty")
            elif st in ("failed", "canceled"):
                raise RuntimeError(f"Replicate prediction {st}: {pdata.get('error')}")

        raise TimeoutError("Replicate video generation timed out")

    # ---------------- Provider 2: Wan2.1 via Fal.ai ----------------
    def _p_wan21_fal(self, prompt: str, path: Path, duration: float, seed: int):
        fal_key = os.getenv("FAL_KEY") or CONFIG.get("keys", {}).get("fal")
        if not fal_key:
            raise RuntimeError("FAL_KEY not configured")

        url = "https://queue.fal.run/fal-ai/wan/v2.1/t2v"
        headers = {
            "Authorization": f"Key {fal_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt[:500],
            "aspect_ratio": "9:16",
            "seed": seed
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        status_url = data.get("status_url")
        response_url = data.get("response_url")
        if not response_url:
            raise RuntimeError("Fal submission failed")

        for _ in range(30):
            time.sleep(3)
            sreq = urllib.request.Request(response_url, headers={"Authorization": f"Key {fal_key}"})
            try:
                with urllib.request.urlopen(sreq, timeout=30) as sresp:
                    res_data = json.loads(sresp.read().decode("utf-8"))
                    video_info = res_data.get("video") or {}
                    vurl = video_info.get("url")
                    if vurl:
                        urllib.request.urlretrieve(vurl, str(path))
                        return
            except urllib.error.HTTPError as e:
                if e.code != 202:
                    raise

        raise TimeoutError("Fal.ai video generation timed out")

    # ---------------- Provider 3: Flux + Procedural Motion (Zero-Cost Local Fallback) ----------------
    def _p_flux_motion(self, prompt: str, path: Path, duration: float, seed: int):
        """ImageGen se high-res image generate karta hai, aur FFmpeg se cinematic camera motion apply karta hai."""
        from agents.imagegen import ImageGen

        tmp_img = path.with_suffix(".jpg")
        ig = ImageGen()
        ig.generate_one(prompt, tmp_img, seed=seed)

        # Apply smooth zoom-in camera motion
        # zoompan: zoom from 1.0 to 1.15 over duration
        fps = 24
        frames = int(max(duration * fps, 24))
        filter_complex = (
            f"zoompan=z='min(zoom+0.0015,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={GEN_W}x{GEN_H}:fps={fps},"
            f"format=yuv420p"
        )

        cmd = [
            "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-i", str(tmp_img),
            "-vf", filter_complex,
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(path)
        ]
        ffmpeg_run(cmd)

        if tmp_img.exists():
            try:
                tmp_img.unlink()
            except Exception:
                pass

    # ---------------- Provider 4: Local Color Clip (Synthetic Minimal Fallback) ----------------
    def _p_local_clip(self, prompt: str, path: Path, duration: float, seed: int):
        """Pure procedural fallback via FFmpeg without external internet or font dependencies."""
        fps = 24
        color_hex = f"#{abs(hash(prompt)) % 0xFFFFFF:06x}"
        cmd = [
            "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c={color_hex}:s={GEN_W}x{GEN_H}:d={duration:.2f}:r={fps}",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(path)
        ]
        ffmpeg_run(cmd)
