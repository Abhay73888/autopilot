"""
agents/imagegen.py — Image prompts -> asli JPG files. Fallback chain ke saath.

Chain (pehla fail ho to agla, kabhi crash nahi):
  1. pollinations       — https://image.pollinations.ai — koi API key nahi, free
  2. gemini_image       — Gemini free tier (agar key hai)
  3. local_placeholder  — gradient + text card (Pillow se, ya Pillow na ho to raw PPM->JPG nahi;
                          hum minimal BMP/PPM ki jagah Pillow use karte hain)

Hard constraint #3: silently fail mat karna. Har provider ka result log hota hai,
aur agar teeno fail ho jaayein to exception raise hoti hai (chupke se aage nahi badhte).
"""

from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from core.config import CONFIG
from core.logbook import Logbook, retry

log = Logbook("imagegen")

# Pollinations ko browser jaisa UA chahiye, warna 403 deta hai
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AUTOPILOT/1.0"

# 9:16 par chhota render — upscale ffmpeg karega.
# Kyun chhota? Free endpoint bade sizes pe timeout karta hai. 640x1138 se 1080x1920
# upscale karne pe cartoon art mein farq nahi dikhta (flat colours hain, photo nahi).
GEN_W, GEN_H = 640, 1138


class ImageGen:
    def __init__(self, providers: list[str] | None = None):
        self.providers = providers or ["pollinations", "gemini_image", "local_placeholder"]
        self.stats = {p: {"ok": 0, "fail": 0} for p in self.providers}

    # ------------------------------------------------------------------
    def generate_all(self, scenes: list[dict], out_dir: str | Path,
                     seed_base: int | None = None) -> list[dict]:
        """
        Saare scenes ki images banao.
        Return: har scene mein 'path' aur 'provider' keys add karke wapas.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for sc in scenes:
            path = out_dir / sc["file"]
            # seed fix rakhna: same story = same style feel (consistency)
            seed = sc.get("seed") or ((seed_base or 42) + sc["n"])
            provider = self.generate_one(sc["image_prompt"], path, seed=seed)
            results.append({**sc, "path": str(path), "provider": provider, "seed": seed})
        summary = {p: f"{s['ok']}✅/{s['fail']}❌" for p, s in self.stats.items() if s["ok"] or s["fail"]}
        log.ok(f"{len(results)} images ready", providers=summary, folder=str(out_dir))
        return results

    # ------------------------------------------------------------------
    def generate_one(self, prompt: str, path: Path, seed: int = 42) -> str:
        """Ek image banao. Har provider try karo. Sab fail = exception."""
        errors = []
        for prov in self.providers:
            try:
                fn = getattr(self, f"_p_{prov}")
                fn(prompt, path, seed)
                if not path.exists() or path.stat().st_size < 1000:
                    raise RuntimeError("file bani par khaali/too small hai")
                self.stats[prov]["ok"] += 1
                log.debug(f"image OK via {prov}", file=path.name, kb=path.stat().st_size // 1024)
                return prov
            except Exception as e:  # noqa: BLE001
                self.stats[prov]["fail"] += 1
                errors.append(f"{prov}: {type(e).__name__}: {str(e)[:120]}")
                log.warn(f"{prov} fail — agla provider try kar rahe hain",
                         file=path.name, reason=str(e)[:150])
        raise RuntimeError(f"Saare image providers fail ho gaye for {path.name}:\n  " +
                           "\n  ".join(errors))

    # ---------------- provider 1: pollinations ----------------
    def _p_pollinations(self, prompt: str, path: Path, seed: int):
        enc = urllib.parse.quote(prompt[:450], safe="")
        url = (f"https://image.pollinations.ai/prompt/{enc}"
               f"?width={GEN_W}&height={GEN_H}&seed={seed}&nologo=true&model=turbo")

        def _fetch():
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            try:
                with urllib.request.urlopen(req, timeout=45) as r:
                    data = r.read()
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    raise RuntimeError("Pollinations rate-limited (429)") from e
                raise
            if len(data) < 1000:
                raise RuntimeError(f"response bahut chhota ({len(data)} bytes)")
            if not (data[:2] == b"\xff\xd8" or data[:8].startswith(b"\x89PNG")):
                raise RuntimeError(f"JPEG/PNG nahi mila, mila: {data[:40]!r}")
            path.write_bytes(data)

        # 1 retry only if not 429
        try:
            _fetch()
        except RuntimeError as e:
            if "429" in str(e):
                raise
            retry(_fetch, tries=2, base_delay=2.0, log=log, what=f"pollinations {path.name}")
        time.sleep(0.5)

    # ---------------- provider 2: gemini image ----------------
    def _p_gemini_image(self, prompt: str, path: Path, seed: int):
        import base64
        import json
        import os
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("GEMINI_API_KEY nahi hai")
        model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={key}")
        body = {"contents": [{"parts": [{"text": prompt[:1800]}]}],
                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}

        def _fetch():
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        path.write_bytes(base64.b64decode(part["inlineData"]["data"]))
                        return
            raise RuntimeError("response mein koi image nahi mili")

        retry(_fetch, tries=2, base_delay=2.0, log=log, what=f"gemini image {path.name}")

    # ---------------- provider 3: local placeholder ----------------
    def _p_local_placeholder(self, prompt: str, path: Path, seed: int):
        """
        Aakhri sahara. Gradient + prompt ka chhota text card.
        Ye publish karne layak NAHI hai — validate.py isse pakdega (Phase 4).
        Iska maqsad sirf ye hai ki pipeline ruke nahi.
        """
        try:
            from PIL import Image, ImageDraw
        except ImportError as e:
            raise RuntimeError("Pillow nahi hai — `pip install Pillow` karo") from e

        h = int(hashlib.sha256(prompt.encode()).hexdigest()[:6], 16)
        c1 = ((h >> 16) % 60 + 10, (h >> 8) % 60 + 20, (h % 60) + 40)
        c2 = (c1[0] + 40, c1[1] + 30, c1[2] + 60)

        img = Image.new("RGB", (GEN_W, GEN_H), c1)
        d = ImageDraw.Draw(img)
        for y in range(GEN_H):   # vertical gradient
            t = y / GEN_H
            d.line([(0, y), (GEN_W, y)],
                   fill=tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)))
        # simple vignette-ish frame
        d.rectangle([20, 20, GEN_W - 20, GEN_H - 20], outline=(230, 230, 230), width=3)

        words = prompt.replace("SCENE:", "\nSCENE:").split()
        lines, cur = [], ""
        for w in words[:40]:
            if len(cur) + len(w) > 26:
                lines.append(cur); cur = w
            else:
                cur = f"{cur} {w}".strip()
        lines.append(cur)
        y = GEN_H // 2 - len(lines) * 12
        for ln in lines[:14]:
            d.text((40, y), ln, fill=(240, 240, 240))
            y += 24
        d.text((40, 60), "PLACEHOLDER — publish mat karna", fill=(255, 120, 120))
        img.save(path, "JPEG", quality=88)
        log.warn(f"PLACEHOLDER image bani: {path.name} — "
                 f"iska matlab pollinations aur gemini dono fail hue")


if __name__ == "__main__":
    ig = ImageGen()
    p = Path("output/_test_img.jpg")
    p.parent.mkdir(exist_ok=True)
    print("provider used:", ig.generate_one(
        "flat 2D cartoon, noir shadows, teal orange, a locked wooden door at night, "
        "vertical 9:16, no text", p))
