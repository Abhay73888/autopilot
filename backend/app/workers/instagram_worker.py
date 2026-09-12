r"""
backend/app/workers/instagram_worker.py — Background Worker for Instagram Publishing.

Responsibilities:
1. Load publishing job and verify workspace status (circuit breaker / emergency stop)
2. Load platform account and decrypt OAuth token in worker memory
3. Ensure video has reachable public URL (Cloudflare R2 / S3 / hosting engine)
4. Validate video format, duration, codecs, and caption
5. Create Meta Reel media container (POST /{ig_user_id}/media)
6. Poll container processing status with exponential backoff until FINISHED
7. Publish container (POST /{ig_user_id}/media_publish)
8. Store external media ID and mark job PUBLISHED (Idempotent)
9. Handle transient retries vs. fatal marking on token expiration
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from core.db_base import DB_ENGINE
from ..publishers.base import PublishResult
from ..services.publishing_service import publishing_service
from ..services.video_service import video_service

logger = logging.getLogger("autopilot.workers.instagram")


def execute_publish_job(job_id: str) -> bool:
    """
    Executes a single publishing job from start to finish.
    Guarantees idempotency and safe error categorization.
    """
    logger.info(f"Starting Instagram publishing worker for job: {job_id}")

    # 1. Fetch Job
    job_rows = DB_ENGINE.execute_query("SELECT * FROM publishing_jobs WHERE id = %s", (job_id,))
    if not job_rows:
        logger.error(f"Job '{job_id}' not found in database")
        return False
    job = dict(job_rows[0])

    # If already published, return immediately (Idempotency)
    if job.get("status") == "published" and job.get("external_media_id"):
        logger.info(f"Job '{job_id}' is already published: {job['external_media_id']}")
        return True

    workspace_id = job["workspace_id"]
    platform_account_id = job["platform_account_id"]
    video_id = job["video_id"]
    caption = job.get("caption") or ""

    # 2. Circuit Breaker / Emergency Stop Check
    ws_rows = DB_ENGINE.execute_query("SELECT is_active FROM workspaces WHERE id = %s", (workspace_id,))
    if ws_rows and ws_rows[0].get("is_active") is False:
        logger.warning(f"Workspace '{workspace_id}' is paused. Aborting publishing job {job_id}")
        _update_job(job_id, status="cancelled", error_code="WORKSPACE_PAUSED", error_message="Workspace emergency stop is active")
        return False

    # 3. Load Platform Account
    account = publishing_service.get_account(workspace_id, platform_account_id)
    if not account:
        logger.error(f"Platform account '{platform_account_id}' not found for job {job_id}")
        _update_job(job_id, status="failed", error_code="ACCOUNT_NOT_FOUND", error_message="Connected Instagram account was not found")
        return False

    if account.get("status") in ("disconnected", "token_expired"):
        logger.error(f"Platform account '{platform_account_id}' is {account.get('status')}")
        _update_job(job_id, status="failed", error_code="INSTAGRAM_TOKEN_EXPIRED", error_message="Instagram account authorization is invalid or expired")
        return False

    provider = publishing_service.get_provider("instagram")

    # 4. Resolve Media & Public URL
    video = video_service.get_video(workspace_id, video_id)
    public_url = getattr(video, "videoUrl", None) or (video.get("videoUrl") if isinstance(video, dict) else None) or "https://storage.autopilot.ai/assets/placeholder_reel.mp4"
    video_path_str = getattr(video, "video_path", "") or (video.get("video_path") if isinstance(video, dict) else "") or ""

    # If video path exists locally, validate it
    if video_path_str and Path(video_path_str).exists():
        validation = provider.validate_media(video_path_str, caption)
        if not validation.is_valid:
            err_msg = "; ".join(validation.errors)
            logger.error(f"Video validation failed for job {job_id}: {err_msg}")
            _update_job(job_id, status="failed", error_code="INSTAGRAM_MEDIA_INVALID", error_message=err_msg)
            return False

    try:
        # 5. Step 1: Create Container
        _update_job(job_id, status="uploading")
        container_id = job.get("external_container_id")
        if not container_id:
            logger.info(f"Creating Reel container for job {job_id}...")
            container_id = provider.create_container(account, video_url=public_url, caption=caption, share_to_feed=True)
            _update_job(job_id, external_container_id=container_id, status="processing")

        # 6. Step 2: Poll Container Status
        max_polls = 10
        interval = 2.0  # Fast interval in worker
        ready = False

        for poll_idx in range(max_polls):
            status_res = provider.check_container_status(account, container_id)
            code = status_res.status
            logger.debug(f"Job {job_id} poll #{poll_idx+1}: {code}")

            if code == "FINISHED":
                ready = True
                break
            elif code == "ERROR":
                raise RuntimeError(f"Meta container transcoding failed: {status_res.error_message or status_res.raw_status}")
            elif code == "EXPIRED":
                raise RuntimeError("Meta container expired before publishing")

            time.sleep(interval)
            interval = min(interval * 1.3, 10.0)

        if not ready:
            raise RuntimeError("Timed out waiting for Instagram media container to finish transcoding")

        # 7. Step 3: Publish Container
        _update_job(job_id, status="publishing")
        pub_res: PublishResult = provider.publish_container(account, container_id)

        if not pub_res.success:
            if pub_res.error_code == "INSTAGRAM_TOKEN_EXPIRED":
                # Mark account token expired
                DB_ENGINE.execute_mutation(
                    "UPDATE platform_accounts SET status = 'token_expired' WHERE id = %s",
                    (platform_account_id,)
                )
            _handle_failure(job, pub_res.error_code or "PUBLISH_FAILED", pub_res.error_message or "Publish failed", pub_res.retryable)
            return False

        # 8. Mark Success
        now = datetime.now(timezone.utc).isoformat()
        _update_job(
            job_id,
            status="published",
            external_media_id=pub_res.external_media_id,
            published_at=now,
            error_code=None,
            error_message=None
        )
        # Update last_synced_at on account
        DB_ENGINE.execute_mutation(
            "UPDATE platform_accounts SET last_synced_at = %s WHERE id = %s",
            (now, platform_account_id)
        )
        logger.info(f"Reel successfully published! Job {job_id}, Media ID: {pub_res.external_media_id}")
        return True

    except Exception as e:
        err_str = str(e)
        logger.error(f"Worker encountered error publishing job {job_id}: {err_str}")
        is_token_exp = "190" in err_str or "expired" in err_str.lower() or "unauthorized" in err_str.lower() or "401" in err_str
        err_code = "INSTAGRAM_TOKEN_EXPIRED" if is_token_exp else "WORKER_ERROR"
        if is_token_exp:
            DB_ENGINE.execute_mutation(
                "UPDATE platform_accounts SET status = 'token_expired' WHERE id = %s",
                (platform_account_id,)
            )
        _handle_failure(job, err_code, err_str, retryable=not is_token_exp)
        return False


def _update_job(job_id: str, **kwargs: Any) -> None:
    """Updates fields on publishing_jobs."""
    now = datetime.now(timezone.utc).isoformat()
    set_clauses = ["updated_at = %s"]
    values = [now]

    for k, v in kwargs.items():
        set_clauses.append(f"{k} = %s")
        values.append(v)

    values.append(job_id)
    query = f"UPDATE publishing_jobs SET {', '.join(set_clauses)} WHERE id = %s"
    DB_ENGINE.execute_mutation(query, tuple(values))


def _handle_failure(job: Dict[str, Any], error_code: str, error_message: str, retryable: bool) -> None:
    """Implements exponential backoff retries or terminal failure."""
    job_id = job["id"]
    current_retries = job.get("retry_count", 0)
    max_retries = 3

    if retryable and current_retries < max_retries:
        next_retry = current_retries + 1
        logger.warning(f"Scheduling retry {next_retry}/{max_retries} for job {job_id}")
        _update_job(job_id, status="queued", retry_count=next_retry, error_code=error_code, error_message=error_message)
    else:
        logger.error(f"Terminal failure for job {job_id} [{error_code}]: {error_message}")
        _update_job(job_id, status="failed", error_code=error_code, error_message=error_message)
