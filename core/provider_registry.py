r"""
core/provider_registry.py — Provider Abstraction & Failover Layer for AUTOPILOT.

Defines unified interfaces and fallback strategies for:
1. LLMProvider (OpenAI, Anthropic, Gemini, Moonshot/Kimi, Groq)
2. TTSProvider (Edge TTS, ElevenLabs, Local)
3. StorageProvider (Local, Cloudflare R2, AWS S3)
4. BillingProvider (Stripe, LemonSqueezy, Dodo)
"""

from __future__ import annotations

import abc
import os
from typing import Any, Dict, List, Optional

from .logbook import Logbook

log = Logbook("provider_registry")


# =====================================================================
# 1. LLM Provider Interface & Registry
# =====================================================================
class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False) -> str:
        pass

    @abc.abstractmethod
    def get_provider_name(self) -> str:
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass


class LLMFailoverRouter:
    """Intelligent router that selects the primary LLM and fails over on error."""

    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.primary_provider = os.getenv("LLM_PRIMARY", "gemini")

    def register(self, name: str, provider: BaseLLMProvider):
        self.providers[name] = provider

    def generate_with_failover(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False) -> str:
        # Preferred order: primary provider first, then any available provider
        order = [self.primary_provider] + [k for k in self.providers.keys() if k != self.primary_provider]
        last_error = None

        for name in order:
            provider = self.providers.get(name)
            if provider and provider.is_available():
                try:
                    log.info(f"Routing LLM prompt to provider: {name}")
                    return provider.generate(prompt, system_prompt, json_mode)
                except Exception as e:
                    log.warning(f"LLM Provider {name} failed, falling over...", error=str(e))
                    last_error = e

        raise RuntimeError(f"All LLM providers exhausted. Last error: {last_error}")


# =====================================================================
# 2. TTS Provider Interface
# =====================================================================
class BaseTTSProvider(abc.ABC):
    @abc.abstractmethod
    def synthesize(self, text: str, output_path: str, voice_id: Optional[str] = None) -> Dict[str, Any]:
        """Synthesizes speech and returns metadata with word alignment timestamps."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass


# =====================================================================
# 3. Storage Provider Interface (Local / Cloudflare R2 / AWS S3)
# =====================================================================
class BaseStorageProvider(abc.ABC):
    @abc.abstractmethod
    def upload_file(self, local_path: str, remote_key: str, content_type: str = "video/mp4") -> str:
        """Uploads file and returns public or presigned access URL."""
        pass

    @abc.abstractmethod
    def get_presigned_url(self, remote_key: str, expiration_seconds: int = 3600) -> str:
        pass


class LocalStorageProvider(BaseStorageProvider):
    def __init__(self, base_url: str = "http://localhost:8765/output"):
        self.base_url = base_url

    def upload_file(self, local_path: str, remote_key: str, content_type: str = "video/mp4") -> str:
        # In local storage mode, files are served directly from output directory
        filename = os.path.basename(local_path)
        return f"{self.base_url}/{filename}"

    def get_presigned_url(self, remote_key: str, expiration_seconds: int = 3600) -> str:
        return f"{self.base_url}/{remote_key}"


class CloudflareR2StorageProvider(BaseStorageProvider):
    def __init__(self):
        self.endpoint = os.getenv("STORAGE_ENDPOINT", "")
        self.bucket = os.getenv("STORAGE_BUCKET", "autopilot-production-assets")
        self.access_key = os.getenv("STORAGE_ACCESS_KEY", "")
        self.secret_key = os.getenv("STORAGE_SECRET_KEY", "")
        self.public_base_url = os.getenv("STORAGE_PUBLIC_BASE_URL", "")

    def upload_file(self, local_path: str, remote_key: str, content_type: str = "video/mp4") -> str:
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto"
        )
        s3.upload_file(local_path, self.bucket, remote_key, ExtraArgs={"ContentType": content_type})
        if self.public_base_url:
            return f"{self.public_base_url.rstrip('/')}/{remote_key.lstrip('/')}"
        return self.get_presigned_url(remote_key)

    def get_presigned_url(self, remote_key: str, expiration_seconds: int = 3600) -> str:
        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto"
        )
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": remote_key},
            ExpiresIn=expiration_seconds
        )


# =====================================================================
# 4. Vision & Multimodal Provider Interface
# =====================================================================
class BaseVisionProvider(abc.ABC):
    @abc.abstractmethod
    def analyze_image(self, image_path: str, prompt: str) -> str:
        """Analyzes an image and returns textual understanding."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass


class GeminiVisionProvider(BaseVisionProvider):
    def analyze_image(self, image_path: str, prompt: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return "Vision analysis unavailable: GEMINI_API_KEY missing."
        try:
            from google import genai
            from PIL import Image
            client = genai.Client(api_key=api_key)
            img = Image.open(image_path)
            res = client.models.generate_content(
                model=os.getenv("VISION_MODEL", "gemini-2.5-flash"),
                contents=[img, prompt]
            )
            return res.text or ""
        except Exception as e:
            return f"Vision analysis note: {e}"

    def is_available(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))


# =====================================================================
# 5. OCR Provider Interface
# =====================================================================
class BaseOCRProvider(abc.ABC):
    @abc.abstractmethod
    def extract_text(self, image_path: str) -> str:
        """Extracts text, dialogue, and coordinates from panel images."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass


class PyMuPDFOCRProvider(BaseOCRProvider):
    def extract_text(self, image_path: str) -> str:
        try:
            import fitz
            doc = fitz.open(image_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            return text.strip()
        except Exception:
            return ""

    def is_available(self) -> bool:
        return True


# =====================================================================
# 6. Music & SFX Provider Interface
# =====================================================================
class BaseMusicProvider(abc.ABC):
    @abc.abstractmethod
    def get_music_track(self, mood: str, duration_sec: float, output_path: str) -> str:
        """Generates or selects procedural background music matching scene mood."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass


class ProceduralMusicProvider(BaseMusicProvider):
    def get_music_track(self, mood: str, duration_sec: float, output_path: str) -> str:
        from core.ffmpeg import ffmpeg_bin
        import subprocess
        d = round(duration_sec, 2)
        # Procedural synthesizers for different moods
        flt_map = {
            "romance": f"aevalsrc='0.15*sin(2*PI*130.81*t)+0.10*sin(2*PI*164.81*t)+0.08*sin(2*PI*196.00*t)':d={d}:s=44100,volume=0.22",
            "action": f"aevalsrc='0.25*sin(2*PI*55*t)+0.18*sin(2*PI*82.4*t)+0.12*sin(2*PI*110*t)':d={d}:s=44100,volume=0.35",
            "suspense": f"aevalsrc='0.20*sin(2*PI*45*t)+0.14*sin(2*PI*65*t)':d={d}:s=44100,volume=0.25",
            "sad": f"aevalsrc='0.12*sin(2*PI*110*t)+0.08*sin(2*PI*130.81*t)':d={d}:s=44100,volume=0.20",
        }
        flt = flt_map.get(mood.lower(), flt_map["suspense"])
        subprocess.run([
            ffmpeg_bin(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", flt,
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ], check=True)
        return output_path

    def is_available(self) -> bool:
        return True


# =====================================================================
# 7. Video Compositor Provider Interface
# =====================================================================
class BaseVideoProvider(abc.ABC):
    @abc.abstractmethod
    def render_scene(self, image_path: str, duration_sec: float, output_mp4: str, motion_type: str = "zoom_in") -> str:
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass


class FFmpegVideoProvider(BaseVideoProvider):
    def render_scene(self, image_path: str, duration_sec: float, output_mp4: str, motion_type: str = "zoom_in") -> str:
        from core.ffmpeg import ffmpeg_bin
        import subprocess
        dur = max(1.0, round(duration_sec, 2))
        w, h = 1080, 1920
        flt = f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},scale=w='2*floor({w}*(1.01+0.04*t/{dur:.2f})/2)':h='2*floor({h}*(1.01+0.04*t/{dur:.2f})/2)':eval=frame,crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,format=yuv420p[v]"
        cmd = [
            ffmpeg_bin(), "-y", "-loop", "1", "-t", str(dur), "-i", str(image_path),
            "-filter_complex", flt, "-map", "[v]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
            "-pix_fmt", "yuv420p", str(output_mp4)
        ]
        subprocess.run(cmd, check=True)
        return output_mp4

    def is_available(self) -> bool:
        return True


# =====================================================================
# 8. AI Model Configuration Manager (Modular & Secure)
# =====================================================================
class AIModelConfigManager:
    """Manages active AI models and provider credentials securely server-side."""

    _CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ai_models_config.json")

    @classmethod
    def _ensure_loaded(cls):
        if os.path.exists(cls._CONFIG_FILE):
            try:
                import json
                with open(cls._CONFIG_FILE, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                for k, v in stored.items():
                    if v and k not in os.environ:
                        os.environ[k] = str(v)
            except Exception:
                pass

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        cls._ensure_loaded()
        return {
            "llmProvider": os.getenv("LLM_PROVIDER", "gemini"),
            "llmModel": os.getenv("LLM_MODEL", "gemini-3.5-flash-lite"),
            "hasLlmApiKey": bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")),
            "llmApiKeyMasked": "••••••••" if (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")) else "",
            "visionModel": os.getenv("VISION_MODEL", "gemini-2.5-flash"),
            "ocrModel": os.getenv("OCR_MODEL", "pymupdf_ocr"),
            "ttsProvider": os.getenv("TTS_PROVIDER", "gemini_neural"),
            "voiceModel": os.getenv("VOICE_MODEL", "Fenrir"),
            "musicProvider": os.getenv("MUSIC_PROVIDER", "procedural_mood"),
            "videoProvider": os.getenv("VIDEO_PROVIDER", "ffmpeg_hardware")
        }

    @classmethod
    def update_config(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        env_updates = {}
        if "llmProvider" in data:
            env_updates["LLM_PROVIDER"] = data["llmProvider"]
        if "llmModel" in data:
            env_updates["LLM_MODEL"] = data["llmModel"]
        if "llmApiKey" in data and data["llmApiKey"] and not data["llmApiKey"].startswith("•"):
            env_updates["GEMINI_API_KEY"] = data["llmApiKey"]
        if "visionModel" in data:
            env_updates["VISION_MODEL"] = data["visionModel"]
        if "ocrModel" in data:
            env_updates["OCR_MODEL"] = data["ocrModel"]
        if "ttsProvider" in data:
            env_updates["TTS_PROVIDER"] = data["ttsProvider"]
        if "voiceModel" in data:
            env_updates["VOICE_MODEL"] = data["voiceModel"]

        for k, v in env_updates.items():
            os.environ[k] = str(v)

        try:
            import json
            existing = {}
            if os.path.exists(cls._CONFIG_FILE):
                with open(cls._CONFIG_FILE, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing.update(env_updates)
            os.makedirs(os.path.dirname(cls._CONFIG_FILE), exist_ok=True)
            with open(cls._CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
        except Exception:
            pass

        return cls.get_config()


# =====================================================================
# 9. Storage Provider Factory & Singletons
# =====================================================================
def get_storage_provider() -> BaseStorageProvider:
    provider_type = os.getenv("STORAGE_PROVIDER", "local").lower()
    if provider_type in ("r2", "s3") and os.getenv("STORAGE_ACCESS_KEY"):
        try:
            return CloudflareR2StorageProvider()
        except Exception as e:
            log.warning("Failed to initialize Cloudflare R2 provider, using local fallback", error=str(e))
    return LocalStorageProvider()


# Global Singleton Instances
STORAGE = get_storage_provider()
LLM_ROUTER = LLMFailoverRouter()
VISION_PROVIDER = GeminiVisionProvider()
OCR_PROVIDER = PyMuPDFOCRProvider()
MUSIC_PROVIDER = ProceduralMusicProvider()
VIDEO_PROVIDER = FFmpegVideoProvider()

