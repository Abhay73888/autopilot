r"""
backend/app/publishers/base.py — Abstract Publishing Provider Contract.

Standardizes publishing providers across Instagram, YouTube, TikTok, etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_sec: float = 0.0
    resolution: Optional[str] = None
    codec: Optional[str] = None
    file_size_bytes: int = 0


@dataclass
class ContainerStatus:
    status: str  # "FINISHED" | "IN_PROGRESS" | "ERROR" | "EXPIRED"
    container_id: str
    error_message: Optional[str] = None
    raw_status: Optional[str] = None


@dataclass
class PublishResult:
    success: bool
    external_media_id: Optional[str] = None
    permalink: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retryable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class PublishingProvider(ABC):
    """Abstract interface defining required capabilities for any publishing destination."""

    @abstractmethod
    def validate_account(self, account_record: Dict[str, Any]) -> bool:
        """Verifies token validity and account health."""
        ...

    @abstractmethod
    def validate_media(self, video_path: str, caption: str) -> ValidationResult:
        """Enforces platform-specific duration, codec, aspect ratio, and caption rules."""
        ...

    @abstractmethod
    def create_container(
        self,
        account_record: Dict[str, Any],
        video_url: str,
        caption: str,
        share_to_feed: bool = True
    ) -> str:
        """Creates a media ingestion container or uploads payload."""
        ...

    @abstractmethod
    def check_container_status(
        self,
        account_record: Dict[str, Any],
        container_id: str
    ) -> ContainerStatus:
        """Polls transcoding or processing status."""
        ...

    @abstractmethod
    def publish_container(
        self,
        account_record: Dict[str, Any],
        container_id: str
    ) -> PublishResult:
        """Publishes the processed container to the live account."""
        ...

    @abstractmethod
    def get_analytics(
        self,
        account_record: Dict[str, Any],
        external_media_id: str
    ) -> Dict[str, Any]:
        """Fetches post metrics (views, reach, likes, saves, etc.)."""
        ...
