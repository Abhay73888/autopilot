r"""
backend/app/publishers/mock_instagram.py — Mock Instagram Publisher Provider for Testing.

Provides deterministic, offline emulation of Meta Graph API v21.0 responses:
- Simulated container creation
- Simulated asynchronous transcoding and status polling
- Configurable error modes (SUCCESS, RATE_LIMIT, TOKEN_EXPIRED, INVALID_MEDIA, PROCESSING_TIMEOUT, UPLOAD_ERROR)
- Zero external HTTP calls
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from .base import ContainerStatus, PublishingProvider, PublishResult, ValidationResult


class MockInstagramProvider(PublishingProvider):
    """
    High-fidelity mock provider for automated unit, integration, and security tests.
    """

    def __init__(self, mode: str = "SUCCESS"):
        self.mode = mode
        self.poll_counts: Dict[str, int] = {}
        self.published_jobs: List[str] = []

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def validate_account(self, account_record: Dict[str, Any]) -> bool:
        if self.mode == "TOKEN_EXPIRED":
            return False
        return account_record.get("status") != "disconnected"

    def validate_media(self, video_path: str, caption: str) -> ValidationResult:
        if self.mode == "INVALID_MEDIA":
            return ValidationResult(
                is_valid=False,
                errors=["Video duration 120.0s exceeds Instagram API strict limit of 90.0s"]
            )
        if len(caption) > 2200:
            return ValidationResult(
                is_valid=False,
                errors=["Caption length exceeds 2200 characters"]
            )
        return ValidationResult(
            is_valid=True,
            duration_sec=25.0,
            resolution="1080x1920",
            codec="h264+aac",
            file_size_bytes=15000000
        )

    def create_container(
        self,
        account_record: Dict[str, Any],
        video_url: str,
        caption: str,
        share_to_feed: bool = True
    ) -> str:
        if self.mode == "TOKEN_EXPIRED":
            raise RuntimeError("Meta API 401: Token has expired")
        if self.mode == "RATE_LIMIT":
            raise RuntimeError("Meta API 429: Publishing rate limit hit")
        if self.mode == "UPLOAD_ERROR":
            raise RuntimeError("Meta API 500: Failed to fetch video from public URL")

        container_id = f"mock_cnt_{uuid.uuid4().hex[:12]}"
        self.poll_counts[container_id] = 0
        return container_id

    def check_container_status(
        self,
        account_record: Dict[str, Any],
        container_id: str
    ) -> ContainerStatus:
        if self.mode == "PROCESSING_TIMEOUT":
            return ContainerStatus(status="IN_PROGRESS", container_id=container_id)
        if self.mode == "UPLOAD_ERROR":
            return ContainerStatus(status="ERROR", container_id=container_id, error_message="Video transcode failed")

        count = self.poll_counts.get(container_id, 0)
        self.poll_counts[container_id] = count + 1

        # Simulate 1 in-progress poll before ready
        if count == 0:
            return ContainerStatus(status="IN_PROGRESS", container_id=container_id)
        return ContainerStatus(status="FINISHED", container_id=container_id)

    def publish_container(
        self,
        account_record: Dict[str, Any],
        container_id: str
    ) -> PublishResult:
        if self.mode == "TOKEN_EXPIRED":
            return PublishResult(
                success=False,
                error_code="INSTAGRAM_TOKEN_EXPIRED",
                error_message="Meta authorization code expired (code 190)",
                retryable=False
            )
        if self.mode == "RATE_LIMIT":
            return PublishResult(
                success=False,
                error_code="INSTAGRAM_RATE_LIMITED",
                error_message="Rate limit reached",
                retryable=True
            )
        if self.mode == "PROCESSING_TIMEOUT":
            return PublishResult(
                success=False,
                error_code="INSTAGRAM_TRANSIENT_ERROR",
                error_message="Container not ready yet",
                retryable=True
            )

        media_id = f"mock_ig_media_{uuid.uuid4().hex[:12]}"
        self.published_jobs.append(media_id)
        return PublishResult(
            success=True,
            external_media_id=media_id,
            permalink=f"https://www.instagram.com/reel/{media_id}/"
        )

    def get_analytics(
        self,
        account_record: Dict[str, Any],
        external_media_id: str
    ) -> Dict[str, Any]:
        return {
            "reach": 15420,
            "video_views": 18200,
            "likes": 1240,
            "comments": 85,
            "shares": 340,
            "saved": 210
        }
