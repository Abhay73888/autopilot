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
# 4. Storage Provider Factory
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
