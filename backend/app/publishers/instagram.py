r"""
backend/app/publishers/instagram.py — Concrete Instagram Professional Publishing Provider.

Coordinates between AUTOPILOT publishing orchestration, MetaApiClient, and the
AES-256-GCM encrypted vault for secure credential handling.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.security import vault
from ..integrations.meta_client import (
    InstagramAuthError,
    InstagramClientError,
    InstagramMediaError,
    InstagramPermissionError,
    InstagramRateLimitError,
    InstagramTransientError,
    MetaApiClient,
)
from ..services.reel_validator import validate_reel
from .base import ContainerStatus, PublishingProvider, PublishResult, ValidationResult

logger = logging.getLogger("autopilot.publishers.instagram")


class InstagramPublisher(PublishingProvider):
    """
    Production-grade Instagram Reels publisher for professional (Business/Creator) accounts.
    """

    def __init__(self, client: Optional[MetaApiClient] = None):
        self.client = client or MetaApiClient()

    def _get_decrypted_token(self, account_record: Dict[str, Any]) -> str:
        """Extracts and decrypts access token from encrypted platform account."""
        encrypted_token = account_record.get("encrypted_access_token")
        if not encrypted_token:
            raise InstagramAuthError("Platform account has no stored access token")
        try:
            return vault.decrypt_secret(encrypted_token)
        except Exception as e:
            raise InstagramAuthError(f"Failed to decrypt stored platform token: {e}") from e

    def validate_account(self, account_record: Dict[str, Any]) -> bool:
        """Verifies account credentials and checks if token is still active."""
        try:
            token = self._get_decrypted_token(account_record)
            ext_id = account_record.get("external_account_id")
            if not ext_id:
                return False
            profile = self.client.get_account_profile(ext_id, token)
            return bool(profile.get("id"))
        except (InstagramAuthError, InstagramPermissionError):
            return False
        except Exception as e:
            logger.warning(f"Error checking Instagram account health: {e}")
            return False

    def validate_media(self, video_path: str, caption: str) -> ValidationResult:
        """Validates video format, duration, codecs, and caption limits."""
        return validate_reel(video_path, caption)

    def create_container(
        self,
        account_record: Dict[str, Any],
        video_url: str,
        caption: str,
        share_to_feed: bool = True
    ) -> str:
        """Step 1: Dispatches container creation request to Meta."""
        token = self._get_decrypted_token(account_record)
        ig_user_id = str(account_record.get("external_account_id"))
        return self.client.create_reels_container(
            ig_user_id=ig_user_id,
            video_url=video_url,
            caption=caption,
            access_token=token,
            share_to_feed=share_to_feed
        )

    def check_container_status(
        self,
        account_record: Dict[str, Any],
        container_id: str
    ) -> ContainerStatus:
        """Step 2: Checks processing state of container."""
        token = self._get_decrypted_token(account_record)
        res = self.client.check_container_status(container_id, token)
        status_code = res.get("status_code", "UNKNOWN")
        return ContainerStatus(
            status=status_code,
            container_id=container_id,
            raw_status=res.get("status")
        )

    def publish_container(
        self,
        account_record: Dict[str, Any],
        container_id: str
    ) -> PublishResult:
        """Step 3: Publishes container to feed and returns external media ID."""
        token = self._get_decrypted_token(account_record)
        ig_user_id = str(account_record.get("external_account_id"))
        try:
            media_id = self.client.publish_container(ig_user_id, container_id, token)
            permalink = self.client.get_media_permalink(media_id, token)
            return PublishResult(
                success=True,
                external_media_id=media_id,
                permalink=permalink
            )
        except InstagramAuthError as e:
            return PublishResult(
                success=False,
                error_code="INSTAGRAM_TOKEN_EXPIRED",
                error_message=str(e),
                retryable=False
            )
        except InstagramPermissionError as e:
            return PublishResult(
                success=False,
                error_code="INSTAGRAM_PERMISSION_DENIED",
                error_message=str(e),
                retryable=False
            )
        except InstagramRateLimitError as e:
            return PublishResult(
                success=False,
                error_code="INSTAGRAM_RATE_LIMITED",
                error_message=str(e),
                retryable=True
            )
        except InstagramTransientError as e:
            return PublishResult(
                success=False,
                error_code="INSTAGRAM_TRANSIENT_ERROR",
                error_message=str(e),
                retryable=True
            )
        except InstagramClientError as e:
            return PublishResult(
                success=False,
                error_code="INSTAGRAM_PUBLISH_FAILED",
                error_message=str(e),
                retryable=e.retryable
            )

    def get_analytics(
        self,
        account_record: Dict[str, Any],
        external_media_id: str
    ) -> Dict[str, Any]:
        """Fetches post-publish metrics from Meta."""
        token = self._get_decrypted_token(account_record)
        return self.client.get_media_insights(external_media_id, token)
