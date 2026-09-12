r"""
backend/app/services/publishing_service.py — Enterprise Publishing Orchestration Service.

Enforces:
- Multi-tenant boundary isolation across organizations and workspaces
- AES-256-GCM encryption of OAuth tokens prior to database storage
- Idempotent publishing execution (preventing duplicate reels on network retries)
- Emergency stop circuit breaker (halts publishing when workspace is paused)
- Clean provider abstraction (Instagram, YouTube, and Mock providers)
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.db_base import DB_ENGINE
from core.security import vault
from ..core.exceptions import TenantAccessDeniedException
from ..publishers.base import PublishingProvider
from ..publishers.instagram import InstagramPublisher
from ..publishers.mock_instagram import MockInstagramProvider
from .video_service import video_service

logger = logging.getLogger("autopilot.services.publishing")


class PublishingService:
    """
    Central business logic coordinator for multi-platform publishing.
    """

    def __init__(self, ig_provider: Optional[PublishingProvider] = None):
        self._ig_provider = ig_provider or InstagramPublisher()
        self._mock_provider: Optional[MockInstagramProvider] = None

    def set_mock_mode(self, enabled: bool = True, mode: str = "SUCCESS") -> MockInstagramProvider:
        """Enables or disables mock mode for automated testing."""
        if enabled:
            self._mock_provider = MockInstagramProvider(mode=mode)
            self._ig_provider = self._mock_provider
            return self._mock_provider
        else:
            self._mock_provider = None
            self._ig_provider = InstagramPublisher()
            return None

    def get_provider(self, platform: str) -> PublishingProvider:
        if platform.lower() == "instagram":
            return self._ig_provider
        raise ValueError(f"Unsupported publishing platform: {platform}")

    # =========================================================================
    # Platform Accounts Management (Multi-Tenant)
    # =========================================================================
    def get_account(self, workspace_id: str, platform_account_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves single platform account strictly scoped to workspace."""
        rows = DB_ENGINE.execute_query(
            "SELECT * FROM platform_accounts WHERE workspace_id = %s AND id = %s",
            (workspace_id, platform_account_id)
        )
        if not rows:
            return None
        return dict(rows[0])

    def list_accounts(self, workspace_id: str, platform: str = "instagram") -> List[Dict[str, Any]]:
        """Lists connected accounts for workspace with tokens redacted."""
        rows = DB_ENGINE.execute_query(
            """
            SELECT id, workspace_id, platform, external_account_id, username, display_name,
                   profile_image_url, account_type, status, token_expires_at, scopes,
                   last_synced_at, created_at, updated_at
            FROM platform_accounts
            WHERE workspace_id = %s AND platform = %s AND status != 'disconnected'
            ORDER BY created_at DESC
            """,
            (workspace_id, platform)
        )
        return [dict(r) for r in rows]

    def connect_account(
        self,
        workspace_id: str,
        platform: str,
        external_account_id: str,
        username: str,
        display_name: str,
        profile_image_url: str,
        access_token: str,
        scopes: List[str],
        token_expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Encrypts token using AES-256-GCM and inserts/updates platform account.
        """
        encrypted_token = vault.encrypt_secret(access_token)
        account_id = f"pa_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        scopes_str = ",".join(scopes)
        meta_json = json.dumps(metadata or {})

        # Upsert into platform_accounts
        query = """
        INSERT INTO platform_accounts (
            id, workspace_id, platform, external_account_id, username, display_name,
            profile_image_url, account_type, status, encrypted_access_token,
            token_expires_at, scopes, metadata_json, last_synced_at, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(workspace_id, platform, external_account_id) DO UPDATE SET
            username = EXCLUDED.username,
            display_name = EXCLUDED.display_name,
            profile_image_url = EXCLUDED.profile_image_url,
            status = 'connected',
            encrypted_access_token = EXCLUDED.encrypted_access_token,
            token_expires_at = EXCLUDED.token_expires_at,
            scopes = EXCLUDED.scopes,
            metadata_json = EXCLUDED.metadata_json,
            updated_at = EXCLUDED.updated_at,
            disconnected_at = NULL
        """
        DB_ENGINE.execute_mutation(
            query,
            (
                account_id, workspace_id, platform, external_account_id, username, display_name,
                profile_image_url, "BUSINESS", "connected", encrypted_token,
                token_expires_at, scopes_str, meta_json, now, now, now
            )
        )

        return {
            "id": account_id,
            "workspace_id": workspace_id,
            "platform": platform,
            "external_account_id": external_account_id,
            "username": username,
            "display_name": display_name,
            "status": "connected",
            "connected_at": now
        }

    def disconnect_account(self, workspace_id: str, platform_account_id: str) -> bool:
        """Marks platform account as disconnected."""
        now = datetime.now(timezone.utc).isoformat()
        rows = DB_ENGINE.execute_mutation(
            """
            UPDATE platform_accounts
            SET status = 'disconnected', disconnected_at = %s, updated_at = %s
            WHERE workspace_id = %s AND id = %s
            """,
            (now, now, workspace_id, platform_account_id)
        )
        return rows > 0

    # =========================================================================
    # Publishing Jobs Lifecycle (Idempotent & Multi-Tenant)
    # =========================================================================
    def create_publishing_job(
        self,
        workspace_id: str,
        platform_account_id: str,
        video_id: str,
        caption: str,
        scheduled_at: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        dispatch_async: bool = True
    ) -> Dict[str, Any]:
        """
        Creates an asynchronous publishing job. Guarantees idempotency:
        returns existing job if idempotency_key has already been submitted.
        """
        # 1. Emergency stop check
        ws_rows = DB_ENGINE.execute_query("SELECT is_active, autopilot_mode FROM workspaces WHERE id = %s", (workspace_id,))
        if ws_rows and not bool(ws_rows[0].get("is_active")):
            raise RuntimeError("Workspace is paused under emergency stop. Publishing rejected.")

        # 2. Account verification
        account = self.get_account(workspace_id, platform_account_id)
        if not account:
            raise TenantAccessDeniedException(f"Platform account '{platform_account_id}' not found in workspace")
        if account.get("status") == "disconnected":
            raise RuntimeError("Platform account is disconnected. Re-authenticate to publish.")

        # 3. Video verification
        video = video_service.get_video(workspace_id, video_id)
        if not video:
            raise TenantAccessDeniedException(f"Video '{video_id}' does not belong to this workspace")

        # 4. Idempotency Check
        idem_key = idempotency_key or f"pub_{workspace_id}_{platform_account_id}_{video_id}_{uuid.uuid4().hex[:8]}"
        existing = DB_ENGINE.execute_query(
            "SELECT * FROM publishing_jobs WHERE idempotency_key = %s",
            (idem_key,)
        )
        if existing:
            row = dict(existing[0])
            # IDOR verification on existing job
            if row.get("workspace_id") != workspace_id:
                raise TenantAccessDeniedException("Cross-tenant idempotency conflict")
            logger.info(f"Idempotent publish replay: returning existing job {row['id']}")
            return row

        # 5. Insert new publishing job
        job_id = f"job_pub_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        initial_status = "scheduled" if scheduled_at else "queued"

        query = """
        INSERT INTO publishing_jobs (
            id, workspace_id, platform_account_id, video_id, status,
            caption, scheduled_at, retry_count, idempotency_key, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        DB_ENGINE.execute_mutation(
            query,
            (
                job_id, workspace_id, platform_account_id, video_id, initial_status,
                caption, scheduled_at, 0, idem_key, now, now
            )
        )

        job_record = {
            "id": job_id,
            "workspace_id": workspace_id,
            "platform_account_id": platform_account_id,
            "video_id": video_id,
            "status": initial_status,
            "caption": caption,
            "scheduled_at": scheduled_at,
            "idempotency_key": idem_key,
            "created_at": now
        }

        # 6. If immediate, trigger asynchronous background worker
        if not scheduled_at and dispatch_async:
            self._dispatch_worker_async(job_id)

        return job_record

    def get_job(self, workspace_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a publishing job with tenant isolation."""
        rows = DB_ENGINE.execute_query(
            "SELECT * FROM publishing_jobs WHERE workspace_id = %s AND id = %s",
            (workspace_id, job_id)
        )
        if not rows:
            return None
        return dict(rows[0])

    def cancel_job(self, workspace_id: str, job_id: str) -> bool:
        """Cancels a queued or scheduled publishing job."""
        now = datetime.now(timezone.utc).isoformat()
        rows = DB_ENGINE.execute_mutation(
            """
            UPDATE publishing_jobs
            SET status = 'cancelled', updated_at = %s
            WHERE workspace_id = %s AND id = %s AND status IN ('queued', 'pending', 'scheduled')
            """,
            (now, workspace_id, job_id)
        )
        return rows > 0

    def list_posts(self, workspace_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists successfully published posts for workspace."""
        rows = DB_ENGINE.execute_query(
            """
            SELECT j.*, a.username, a.platform
            FROM publishing_jobs j
            JOIN platform_accounts a ON j.platform_account_id = a.id
            WHERE j.workspace_id = %s AND j.status = 'published'
            ORDER BY j.published_at DESC
            LIMIT %s
            """,
            (workspace_id, limit)
        )
        return [dict(r) for r in rows]

    def _dispatch_worker_async(self, job_id: str) -> None:
        """Dispatches publishing task to background worker."""
        try:
            from ..workers.instagram_worker import execute_publish_job
            import threading
            # Run in separate thread or worker task
            thread = threading.Thread(target=execute_publish_job, args=(job_id,), daemon=True)
            thread.start()
        except Exception as e:
            logger.error(f"Failed to dispatch publish worker for job {job_id}: {e}")


# Singleton instance
publishing_service = PublishingService()
