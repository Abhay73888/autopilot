r"""
backend/app/api/v1/instagram.py — Instagram Publishing & Analytics Operations Router.

Endpoints:
- POST /api/v1/instagram/publish
- POST /api/v1/instagram/schedule
- GET  /api/v1/instagram/jobs/{job_id}
- POST /api/v1/instagram/jobs/{job_id}/cancel
- GET  /api/v1/instagram/posts
- GET  /api/v1/instagram/posts/{post_id}
- GET  /api/v1/instagram/analytics
- POST /api/v1/instagram/sync
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..dependencies import TenantContext, get_current_tenant_context
from ...schemas.common import ApiResponse
from ...services.publishing_service import publishing_service

router = APIRouter(prefix="/instagram", tags=["Instagram Publishing"])


class PublishReelRequest(BaseModel):
    platformAccountId: str = Field(..., description="ID of connected platform account in this workspace")
    videoId: str = Field(..., description="ID of rendered video to publish")
    caption: str = Field(..., description="Reel caption including hashtags (max 2200 chars)")
    shareToFeed: bool = Field(default=True, description="Whether to also display on main feed profile grid")
    idempotencyKey: Optional[str] = Field(default=None, description="Unique client key preventing duplicate publishes")


class ScheduleReelRequest(BaseModel):
    platformAccountId: str
    videoId: str
    caption: str
    scheduledAt: str = Field(..., description="ISO 8601 UTC timestamp for scheduled publication")
    timezone: str = Field(default="UTC", description="Workspace local timezone identifier")
    idempotencyKey: Optional[str] = None


@router.post("/publish", response_model=ApiResponse[Dict[str, Any]])
async def publish_reel(
    req: PublishReelRequest,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Dispatches an asynchronous Reel publishing job with idempotency protection.
    """
    try:
        job = publishing_service.create_publishing_job(
            workspace_id=ctx.workspace_id,
            platform_account_id=req.platformAccountId,
            video_id=req.videoId,
            caption=req.caption,
            idempotency_key=req.idempotencyKey
        )
        return ApiResponse(
            success=True,
            data={
                "job_id": job["id"],
                "status": job["status"],
                "video_id": job["video_id"],
                "platform_account_id": job["platform_account_id"],
                "idempotency_key": job["idempotency_key"],
                "created_at": job["created_at"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/schedule", response_model=ApiResponse[Dict[str, Any]])
async def schedule_reel(
    req: ScheduleReelRequest,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Schedules an Instagram Reel for future publication. Always stored in UTC.
    """
    try:
        job = publishing_service.create_publishing_job(
            workspace_id=ctx.workspace_id,
            platform_account_id=req.platformAccountId,
            video_id=req.videoId,
            caption=req.caption,
            scheduled_at=req.scheduledAt,
            idempotency_key=req.idempotencyKey
        )
        return ApiResponse(
            success=True,
            data={
                "job_id": job["id"],
                "status": job["status"],
                "scheduled_at": req.scheduledAt,
                "timezone": req.timezone,
                "video_id": job["video_id"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/jobs/{job_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_publishing_job_status(
    job_id: str,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Retrieves status, container ID, and external media ID for a publishing job.
    Enforces tenant isolation (User B cannot check User A's job).
    """
    job = publishing_service.get_job(ctx.workspace_id, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publishing job not found in this workspace")

    return ApiResponse(
        success=True,
        data={
            "job_id": job["id"],
            "workspace_id": job["workspace_id"],
            "video_id": job["video_id"],
            "status": job["status"],
            "external_media_id": job.get("external_media_id"),
            "external_container_id": job.get("external_container_id"),
            "retry_count": job.get("retry_count", 0),
            "error_code": job.get("error_code"),
            "error_message": job.get("error_message"),
            "published_at": job.get("published_at"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at")
        }
    )


@router.post("/jobs/{job_id}/cancel", response_model=ApiResponse[Dict[str, Any]])
async def cancel_publishing_job(
    job_id: str,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Cancels a pending or queued publishing job.
    """
    success = publishing_service.cancel_job(ctx.workspace_id, job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled (either not found or already published/failed)"
        )
    return ApiResponse(
        success=True,
        data={"job_id": job_id, "status": "cancelled"}
    )


@router.get("/posts", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_published_reels(
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Returns published Instagram Reels for this workspace.
    """
    posts = publishing_service.list_posts(ctx.workspace_id, limit=limit)
    return ApiResponse(success=True, data=posts)


@router.get("/posts/{post_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_published_reel(
    post_id: str,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Returns single published Reel details.
    """
    job = publishing_service.get_job(ctx.workspace_id, post_id)
    if not job or job.get("status") != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published Reel not found")
    return ApiResponse(success=True, data=job)


@router.get("/analytics", response_model=ApiResponse[Dict[str, Any]])
async def get_instagram_analytics(
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Aggregates performance analytics for all published Instagram Reels in workspace.
    """
    posts = publishing_service.list_posts(ctx.workspace_id, limit=100)
    total_views = sum(p.get("views", 0) for p in posts)
    total_likes = sum(p.get("likes", 0) for p in posts)
    total_comments = sum(p.get("comments", 0) for p in posts)

    return ApiResponse(
        success=True,
        data={
            "total_posts": len(posts),
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "recent_posts": posts[:10]
        }
    )


@router.post("/sync", response_model=ApiResponse[Dict[str, Any]])
async def sync_instagram_metrics(
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Triggers on-demand synchronization of Instagram Reel performance metrics.
    """
    posts = publishing_service.list_posts(ctx.workspace_id, limit=20)
    provider = publishing_service.get_provider("instagram")
    synced_count = 0

    for post in posts:
        media_id = post.get("external_media_id")
        acct_id = post.get("platform_account_id")
        if media_id and acct_id:
            acct = publishing_service.get_account(ctx.workspace_id, acct_id)
            if acct:
                try:
                    metrics = provider.get_analytics(acct, media_id)
                    synced_count += 1
                except Exception:
                    pass

    return ApiResponse(
        success=True,
        data={
            "synced_posts": synced_count,
            "workspace_id": ctx.workspace_id
        }
    )
