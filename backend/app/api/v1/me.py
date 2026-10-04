r"""
backend/app/api/v1/me.py — User Scoped Profile, Personal Activity, and Assets API Routes
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from ...schemas.common import ApiResponse, MetaInfo
from ..dependencies import TenantContext, require_active_user
from ...services.platform_service import (
    ADMIN_BROADCAST,
    list_notifications,
    mark_notifications_read,
    query_count,
    query_one,
    query_rows,
    update_profile,
)

router = APIRouter(prefix="/me", tags=["User Space & Activity"])


class ProfileUpdatePayload(BaseModel):
    full_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


# =============================================================================
# Profile & Personal Overview
# =============================================================================

@router.get("/profile", response_model=ApiResponse[Dict[str, Any]])
async def get_my_profile(
    ctx: TenantContext = Depends(require_active_user),
):
    """Returns current authenticated user profile."""
    from core.db_base import DB_ENGINE
    user = DB_ENGINE.get_user_by_id(ctx.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    clean = {
        "id": user.get("id") or user.get("user_id"),
        "user_id": user.get("id") or user.get("user_id"),
        "email": user.get("email"),
        "full_name": user.get("full_name") or user.get("name") or "Creator",
        "role": user.get("role", "user"),
        "tier": user.get("tier", "free"),
        "credits": user.get("credits", 0),
        "status": user.get("status", "active"),
        "created_at": user.get("created_at") or user.get("created_ts"),
        "last_active_ts": user.get("last_active_ts"),
    }
    return ApiResponse(data=clean)


@router.put("/profile", response_model=ApiResponse[Dict[str, Any]])
async def update_my_profile(
    payload: ProfileUpdatePayload,
    ctx: TenantContext = Depends(require_active_user),
):
    """Updates user full name and/or preferences."""
    updated = update_profile(
        user_id=ctx.user_id,
        full_name=payload.full_name,
        preferences=payload.preferences,
    )
    return ApiResponse(data=updated)


@router.get("/overview", response_model=ApiResponse[Dict[str, Any]])
@router.get("/stats", response_model=ApiResponse[Dict[str, Any]])
async def get_my_stats(
    ctx: TenantContext = Depends(require_active_user),
):
    """Returns personal creator metrics and asset counts."""
    uid = ctx.user_id
    ws = ctx.workspace_id

    total_projects = query_count("SELECT COUNT(*) as cnt FROM series WHERE user_id = %s OR workspace_id = %s", (uid, ws))
    total_videos = query_count("SELECT COUNT(*) as cnt FROM videos WHERE user_id = %s OR workspace_id = %s", (uid, ws))
    published_videos = query_count(
        "SELECT COUNT(*) as cnt FROM videos WHERE (user_id = %s OR workspace_id = %s) AND status = 'published'",
        (uid, ws)
    )
    total_creds = query_count(
        "SELECT COUNT(*) as cnt FROM channel_credentials WHERE user_id = %s OR workspace_id = %s",
        (uid, ws)
    )

    return ApiResponse(
        data={
            "projects": total_projects,
            "videos": total_videos,
            "publishedVideos": published_videos,
            "youtubeConnections": total_creds,
        }
    )


# =============================================================================
# Personal Activity Timeline (user_id = X OR actor_id = X)
# =============================================================================

@router.get("/activity/filters", response_model=ApiResponse[Dict[str, Any]])
async def get_my_activity_filters(
    ctx: TenantContext = Depends(require_active_user),
):
    """Returns distinct actions for user's own activity."""
    rows = query_rows(
        "SELECT DISTINCT action FROM activity_log WHERE user_id = %s OR actor_id = %s ORDER BY action ASC",
        (ctx.user_id, ctx.user_id)
    )
    return ApiResponse(data={"actions": [r["action"] for r in rows if r.get("action")]})


@router.get("/activity", response_model=ApiResponse[Dict[str, Any]])
async def get_my_activity(
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(require_active_user),
):
    """
    Returns personal activity history.
    Scope: (user_id = X OR actor_id = X), ensuring admin events regarding the user
    (e.g., admin.user.blocked) correctly appear in user's timeline.
    """
    conds = ["(user_id = %s OR actor_id = %s)"]
    params: List[Any] = [ctx.user_id, ctx.user_id]

    if action:
        conds.append("action = %s")
        params.append(action)

    where = " AND ".join(conds)
    total = query_count(f"SELECT COUNT(*) as cnt FROM activity_log WHERE {where}", tuple(params))
    offset = (page - 1) * limit

    rows = query_rows(
        f"""
        SELECT id, user_id, actor_id, action, resource_type, resource_id,
               details_json, created_at
        FROM activity_log
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params + [limit, offset])
    )
    return ApiResponse(
        data={"items": rows, "total": total},
        meta=MetaInfo(total=total, page=page, limit=limit),
    )


# =============================================================================
# Personal Notifications
# =============================================================================

@router.get("/notifications", response_model=ApiResponse[Dict[str, Any]])
async def get_my_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(require_active_user),
):
    """Lists personal notifications (including system broadcasts)."""
    offset = (page - 1) * limit
    res = list_notifications(
        user_id=ctx.user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=res,
        meta=MetaInfo(total=res["total"], page=page, limit=limit),
    )


@router.post("/notifications/read", response_model=ApiResponse[Dict[str, Any]])
async def mark_my_notifications_read(
    payload: Optional[Dict[str, Any]] = None,
    ctx: TenantContext = Depends(require_active_user),
):
    """Marks specified or all notifications as read."""
    ids = payload.get("ids") if payload else None
    count = mark_notifications_read(user_id=ctx.user_id, notification_ids=ids)
    return ApiResponse(data={"markedRead": count})


# =============================================================================
# Ownership-Scoped Assets (Cross-User Returns 404, NEVER 403)
# =============================================================================

@router.get("/projects", response_model=ApiResponse[Dict[str, Any]])
async def get_my_projects(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(require_active_user),
):
    """Lists current user's projects/series."""
    uid = ctx.user_id
    ws = ctx.workspace_id
    total = query_count("SELECT COUNT(*) as cnt FROM series WHERE user_id = %s OR workspace_id = %s", (uid, ws))
    offset = (page - 1) * limit

    rows = query_rows(
        """
        SELECT id, workspace_id, user_id, title, description, genre, tone, created_at
        FROM series
        WHERE user_id = %s OR workspace_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (uid, ws, limit, offset)
    )
    return ApiResponse(
        data={"items": rows, "total": total},
        meta=MetaInfo(total=total, page=page, limit=limit),
    )


@router.get("/projects/{project_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_my_single_project(
    project_id: str,
    ctx: TenantContext = Depends(require_active_user),
):
    """
    Returns single project details.
    Strict ground rule: Cross-user access returns 404, NOT 403.
    """
    row = query_one(
        "SELECT * FROM series WHERE id = %s AND (user_id = %s OR workspace_id = %s)",
        (project_id, ctx.user_id, ctx.workspace_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(data=dict(row))


@router.get("/videos", response_model=ApiResponse[Dict[str, Any]])
async def get_my_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(require_active_user),
):
    """Lists current user's videos."""
    uid = ctx.user_id
    ws = ctx.workspace_id
    total = query_count("SELECT COUNT(*) as cnt FROM videos WHERE user_id = %s OR workspace_id = %s", (uid, ws))
    offset = (page - 1) * limit

    rows = query_rows(
        """
        SELECT id, user_id, workspace_id, title, topic, status, duration_sec,
               yt_video_id, yt_published_at, views, likes, comments, created_at
        FROM videos
        WHERE user_id = %s OR workspace_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (uid, ws, limit, offset)
    )
    return ApiResponse(
        data={"items": rows, "total": total},
        meta=MetaInfo(total=total, page=page, limit=limit),
    )


@router.get("/videos/{video_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_my_single_video(
    video_id: str,
    ctx: TenantContext = Depends(require_active_user),
):
    """
    Returns single video details.
    Strict ground rule: Cross-user access returns 404, NOT 403.
    """
    row = query_one(
        "SELECT * FROM videos WHERE id = %s AND (user_id = %s OR workspace_id = %s)",
        (video_id, ctx.user_id, ctx.workspace_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Video not found")
    return ApiResponse(data=dict(row))


@router.get("/youtube", response_model=ApiResponse[Dict[str, Any]])
async def get_my_youtube_connection(
    ctx: TenantContext = Depends(require_active_user),
):
    """
    Returns user's connected YouTube channel details.
    Strict ground rule: Secrets masked (id + length only, never raw token).
    """
    row = query_one(
        "SELECT id, workspace_id, user_id, channel_id, channel_title, account_type, status, encrypted_token, token_expires_at, created_at FROM channel_credentials WHERE user_id = %s OR workspace_id = %s ORDER BY created_at DESC LIMIT 1",
        (ctx.user_id, ctx.workspace_id)
    )
    if not row:
        return ApiResponse(data={"connected": False, "channel": None})

    raw_enc = row.get("encrypted_token") or ""
    clean_channel = {
        "id": row.get("id"),
        "channel_id": row.get("channel_id") or "not recorded",
        "channel_title": row.get("channel_title") or "YouTube Channel",
        "status": row.get("status", "connected"),
        "token_masked": f"enc_token_{row['id'][:8]}... ({len(raw_enc)} bytes)" if raw_enc else "not recorded",
        "token_length": len(raw_enc),
        "created_at": row.get("created_at"),
    }
    return ApiResponse(data={"connected": True, "channel": clean_channel})


@router.get("/usage", response_model=ApiResponse[Dict[str, Any]])
async def get_my_usage_ledger(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(require_active_user),
):
    """Returns AI usage records for the current user's workspace."""
    ws = ctx.workspace_id
    total = query_count("SELECT COUNT(*) as cnt FROM usage_ledger WHERE workspace_id = %s", (ws,))
    offset = (page - 1) * limit

    rows = query_rows(
        """
        SELECT id, workspace_id, provider, model, tokens_in, tokens_out, cost_usd, created_at
        FROM usage_ledger
        WHERE workspace_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (ws, limit, offset)
    )
    return ApiResponse(
        data={"items": rows, "total": total},
        meta=MetaInfo(total=total, page=page, limit=limit),
    )
