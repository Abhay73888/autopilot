r"""
backend/app/api/v1/control.py — Administrative Control Center API Routes
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ...schemas.common import ApiResponse, MetaInfo
from ..dependencies import TenantContext, require_admin_db, request_meta
from ...services.platform_service import (
    ADMIN_BROADCAST,
    activity_filters,
    admin_edit_user,
    list_episodes,
    list_jobs,
    list_notifications,
    list_projects,
    list_usage,
    list_users,
    list_videos,
    list_youtube,
    log_activity,
    log_audit,
    mark_notifications_read,
    normalize_status,
    notify,
    notify_admins,
    platform_stats,
    query_count,
    query_one,
    query_rows,
    reports_summary,
    set_user_status,
    system_settings,
    usage_summary,
    user_overview,
)

router = APIRouter(prefix="/control", tags=["Admin Control Center"])


# Request payload models
class UserStatusUpdatePayload(BaseModel):
    status: str
    reason: Optional[str] = None


class UserEditPayload(BaseModel):
    role: Optional[str] = None
    tier: Optional[str] = None
    credits: Optional[int] = None
    full_name: Optional[str] = None
    reason: Optional[str] = None


class BroadcastPayload(BaseModel):
    title: str
    message: str
    type: str = "info"
    link: Optional[str] = None


# =============================================================================
# 1. Dashboard & Platform Overview
# =============================================================================

@router.get("/stats", response_model=ApiResponse[Dict[str, Any]])
async def get_control_stats(
    ctx: TenantContext = Depends(require_admin_db),
):
    """Returns top-level platform statistics and cluster status."""
    data = platform_stats()
    return ApiResponse(data=data)


@router.get("/dashboard", response_model=ApiResponse[Dict[str, Any]])
async def get_control_dashboard(
    ctx: TenantContext = Depends(require_admin_db),
):
    """Returns high-level summary overview for admin control dashboard."""
    stats = platform_stats()
    recent_activity = query_rows(
        "SELECT id, user_id, actor_id, action, resource_type, resource_id, created_at FROM activity_log ORDER BY created_at DESC LIMIT 10"
    )
    recent_audit = query_rows(
        "SELECT id, admin_id, target_id, action, resource, reason, created_at FROM audit_log ORDER BY created_at DESC LIMIT 10"
    )
    return ApiResponse(
        data={
            "stats": stats,
            "recentActivity": recent_activity,
            "recentAudit": recent_audit,
        }
    )


# =============================================================================
# 2. Users Management (Literal routes BEFORE parameterized /users/{user_id})
# =============================================================================

@router.get("/users/filters", response_model=ApiResponse[Dict[str, Any]])
async def get_user_filters(
    ctx: TenantContext = Depends(require_admin_db),
):
    """Returns available roles and status filters for users table."""
    return ApiResponse(
        data={
            "statuses": ["active", "blocked", "suspended"],
            "roles": ["user", "creator", "admin"],
        }
    )


@router.get("/users", response_model=ApiResponse[Dict[str, Any]])
async def get_users_list(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Lists platform users with search, role, status filtering, and pagination."""
    offset = (page - 1) * limit
    res = list_users(
        search=search,
        status=status,
        role=role,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    return ApiResponse(
        data=res,
        meta=MetaInfo(total=res["total"], page=page, limit=limit),
    )


@router.get("/users/{user_id}/overview", response_model=ApiResponse[Dict[str, Any]])
async def get_single_user_overview(
    user_id: str,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Detailed overview of a specific user: managing context, counts, and recent assets."""
    try:
        data = user_overview(user_id)
        # Enforce administrative context header standard
        u_name = data["user"].get("full_name") or data["user"].get("email")
        data["managingContext"] = f"Managing user: {u_name} ({user_id})"
        return ApiResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users/{user_id}/activity", response_model=ApiResponse[Dict[str, Any]])
async def get_user_activity(
    user_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Returns activity log specific to target user."""
    offset = (page - 1) * limit
    total = query_count(
        "SELECT COUNT(*) as cnt FROM activity_log WHERE user_id = %s OR actor_id = %s",
        (user_id, user_id)
    )
    rows = query_rows(
        """
        SELECT id, user_id, actor_id, action, resource_type, resource_id,
               details_json, ip_address, user_agent, created_at
        FROM activity_log
        WHERE user_id = %s OR actor_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user_id, user_id, limit, offset)
    )
    return ApiResponse(
        data={"items": rows, "total": total},
        meta=MetaInfo(total=total, page=page, limit=limit),
    )


@router.get("/users/{user_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_single_user(
    user_id: str,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Fetches single user details."""
    from core.db_base import DB_ENGINE
    user = DB_ENGINE.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

    clean = {
        "id": user.get("id") or user.get("user_id"),
        "user_id": user.get("id") or user.get("user_id"),
        "email": user.get("email"),
        "full_name": user.get("full_name") or user.get("name") or "User",
        "role": user.get("role", "user"),
        "tier": user.get("tier", "free"),
        "credits": user.get("credits", 0),
        "status": normalize_status(user.get("status")),
        "last_active_ts": user.get("last_active_ts") or user.get("created_at") or user.get("created_ts"),
        "block_reason": user.get("block_reason"),
        "blocked_at": user.get("blocked_at"),
        "blocked_by": user.get("blocked_by"),
        "is_onboarded": bool(user.get("is_onboarded", 0)),
        "created_at": user.get("created_at") or user.get("created_ts"),
        "managingContext": f"Managing user: {user.get('full_name') or user.get('email')} ({user_id})",
    }
    return ApiResponse(data=clean)


@router.patch("/users/{user_id}/status", response_model=ApiResponse[Dict[str, Any]])
@router.post("/users/{user_id}/status", response_model=ApiResponse[Dict[str, Any]])
async def update_user_status_endpoint(
    user_id: str,
    payload: UserStatusUpdatePayload,
    request: Request,
    ctx: TenantContext = Depends(require_admin_db),
):
    """
    Updates user account status (active, blocked, suspended).
    Audits change with admin ID and client IP.
    """
    meta = request_meta(request)
    try:
        updated = set_user_status(
            admin_id=ctx.user_id,
            target_user_id=user_id,
            new_status=payload.status,
            reason=payload.reason,
            ip_address=meta.get("ip_address"),
        )
        return ApiResponse(data=updated)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/{user_id}/block", response_model=ApiResponse[Dict[str, Any]])
async def block_user_endpoint(
    user_id: str,
    payload: UserStatusUpdatePayload,
    request: Request,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Convenience endpoint to block user."""
    meta = request_meta(request)
    try:
        updated = set_user_status(
            admin_id=ctx.user_id,
            target_user_id=user_id,
            new_status="blocked",
            reason=payload.reason or "Account blocked by administrator",
            ip_address=meta.get("ip_address"),
        )
        return ApiResponse(data=updated)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/{user_id}/unblock", response_model=ApiResponse[Dict[str, Any]])
async def unblock_user_endpoint(
    user_id: str,
    request: Request,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Convenience endpoint to unblock / reactivate user."""
    meta = request_meta(request)
    try:
        updated = set_user_status(
            admin_id=ctx.user_id,
            target_user_id=user_id,
            new_status="active",
            reason="Account unblocked by administrator",
            ip_address=meta.get("ip_address"),
        )
        return ApiResponse(data=updated)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/users/{user_id}", response_model=ApiResponse[Dict[str, Any]])
@router.put("/users/{user_id}", response_model=ApiResponse[Dict[str, Any]])
async def edit_user_endpoint(
    user_id: str,
    payload: UserEditPayload,
    request: Request,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Updates user fields (role, tier, credits, full_name) with audit logging."""
    meta = request_meta(request)
    try:
        updated = admin_edit_user(
            admin_id=ctx.user_id,
            target_user_id=user_id,
            updates=payload.model_dump(),
            ip_address=meta.get("ip_address"),
        )
        return ApiResponse(data=updated)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# 3. Activity Monitor & Telemetry
# =============================================================================

@router.get("/activity/filters", response_model=ApiResponse[Dict[str, Any]])
async def get_activity_filter_options(
    ctx: TenantContext = Depends(require_admin_db),
):
    """Returns available actions and resource types for filter dropdowns."""
    return ApiResponse(data=activity_filters())


@router.get("/activity", response_model=ApiResponse[Dict[str, Any]])
async def get_platform_activity_list(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Lists platform activity across all users and system processes."""
    conds = []
    params: List[Any] = []

    if user_id:
        conds.append("(user_id = %s OR actor_id = %s)")
        params.extend([user_id, user_id])
    if action:
        conds.append("action = %s")
        params.append(action)

    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    total = query_count(f"SELECT COUNT(*) as cnt FROM activity_log {where}", tuple(params))
    offset = (page - 1) * limit

    rows = query_rows(
        f"""
        SELECT id, user_id, actor_id, action, resource_type, resource_id,
               details_json, ip_address, user_agent, created_at
        FROM activity_log
        {where}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params + [limit, offset])
    )
    return ApiResponse(
        data={"items": rows, "total": total},
        meta=MetaInfo(total=total, page=page, limit=limit),
    )


@router.get("/activity/{activity_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_single_activity(
    activity_id: str,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Fetches details for a single activity log entry."""
    row = query_one("SELECT * FROM activity_log WHERE id = %s", (activity_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Activity record not found")
    return ApiResponse(data=dict(row))


# =============================================================================
# 4. Audit Trail
# =============================================================================

@router.get("/audit", response_model=ApiResponse[Dict[str, Any]])
async def get_audit_trail_list(
    admin_id: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Lists audit trail records documenting all administrative mutations."""
    conds = []
    params: List[Any] = []

    if admin_id:
        conds.append("admin_id = %s")
        params.append(admin_id)
    if target_id:
        conds.append("target_id = %s")
        params.append(target_id)
    if resource:
        conds.append("resource = %s")
        params.append(resource)

    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    total = query_count(f"SELECT COUNT(*) as cnt FROM audit_log {where}", tuple(params))
    offset = (page - 1) * limit

    rows = query_rows(
        f"""
        SELECT id, admin_id, target_id, action, resource, before_json, after_json,
               reason, ip_address, created_at
        FROM audit_log
        {where}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params + [limit, offset])
    )
    return ApiResponse(
        data={"items": rows, "total": total},
        meta=MetaInfo(total=total, page=page, limit=limit),
    )


@router.get("/audit/{audit_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_single_audit_record(
    audit_id: str,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Fetches single audit log entry."""
    row = query_one("SELECT * FROM audit_log WHERE id = %s", (audit_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return ApiResponse(data=dict(row))


# =============================================================================
# 5. AUTOPILOT Data: Projects (Series) & Episodes
# =============================================================================

@router.get("/projects", response_model=ApiResponse[Dict[str, Any]])
async def get_control_projects_list(
    user_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Lists all video series/projects across users with search and pagination."""
    offset = (page - 1) * limit
    res = list_projects(user_id=user_id, search=search, limit=limit, offset=offset)
    return ApiResponse(
        data=res,
        meta=MetaInfo(total=res["total"], page=page, limit=limit),
    )


@router.get("/projects/{project_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_single_project(
    project_id: str,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Fetches project/series details along with its episodes count."""
    row = query_one("SELECT * FROM series WHERE id = %s", (project_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    episodes = query_rows("SELECT id, episode_number, title, status, created_at FROM episodes WHERE series_id = %s ORDER BY episode_number ASC", (project_id,))
    data = dict(row)
    data["episodes"] = episodes
    return ApiResponse(data=data)


@router.get("/episodes", response_model=ApiResponse[Dict[str, Any]])
async def get_control_episodes_list(
    series_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Lists series episodes across the system."""
    offset = (page - 1) * limit
    res = list_episodes(series_id=series_id, limit=limit, offset=offset)
    return ApiResponse(
        data=res,
        meta=MetaInfo(total=res["total"], page=page, limit=limit),
    )


@router.get("/episodes/{episode_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_single_episode(
    episode_id: str,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Fetches single episode details."""
    row = query_one("SELECT * FROM episodes WHERE id = %s", (episode_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Episode not found")
    return ApiResponse(data=dict(row))


# =============================================================================
# 6. AUTOPILOT Data: Videos
# =============================================================================

@router.get("/videos", response_model=ApiResponse[Dict[str, Any]])
async def get_control_videos_list(
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Lists videos across the platform."""
    offset = (page - 1) * limit
    res = list_videos(status=status, user_id=user_id, search=search, limit=limit, offset=offset)
    return ApiResponse(
        data=res,
        meta=MetaInfo(total=res["total"], page=page, limit=limit),
    )


@router.get("/videos/{video_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_single_video(
    video_id: str,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Fetches single video record."""
    row = query_one("SELECT * FROM videos WHERE id = %s", (video_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Video not found")
    return ApiResponse(data=dict(row))


# =============================================================================
# 7. AUTOPILOT Data: YouTube Connections (STRICT SECRET MASKING)
# =============================================================================

@router.get("/youtube", response_model=ApiResponse[Dict[str, Any]])
async def get_control_youtube_connections(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """
    Lists connected YouTube channels.
    Strict ground rule: All tokens and credentials masked (id + length only).
    Never exposes raw tokens or secrets.
    """
    offset = (page - 1) * limit
    res = list_youtube(limit=limit, offset=offset)
    return ApiResponse(
        data=res,
        meta=MetaInfo(total=res["total"], page=page, limit=limit),
    )


@router.get("/youtube/{connection_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_single_youtube_connection(
    connection_id: str,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Fetches single YouTube connection details with token strictly masked."""
    row = query_one("SELECT id, workspace_id, user_id, channel_id, channel_title, account_type, status, encrypted_token, token_expires_at, created_at FROM channel_credentials WHERE id = %s", (connection_id,))
    if not row:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    raw_enc = row.get("encrypted_token") or ""
    d = dict(row)
    d["token_masked"] = f"enc_token_{d['id'][:8]}... ({len(raw_enc)} bytes)"
    d["token_length"] = len(raw_enc)
    d.pop("encrypted_token", None)
    return ApiResponse(data=d)


@router.post("/youtube/{connection_id}/disconnect", response_model=ApiResponse[Dict[str, Any]])
async def disconnect_youtube_connection(
    connection_id: str,
    request: Request,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Disconnects a channel credential."""
    meta = request_meta(request)
    row = query_one("SELECT * FROM channel_credentials WHERE id = %s", (connection_id,))
    if not row:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    from core.db_base import DB_ENGINE
    DB_ENGINE.execute_mutation("UPDATE channel_credentials SET status = 'disconnected' WHERE id = %s", (connection_id,))

    log_audit(
        admin_id=ctx.user_id,
        action="youtube.disconnect",
        resource="channel_credentials",
        target_id=connection_id,
        before={"status": row.get("status")},
        after={"status": "disconnected"},
        reason="Administrative disconnect",
        ip_address=meta.get("ip_address"),
    )
    return ApiResponse(data={"id": connection_id, "status": "disconnected"})


# =============================================================================
# 8. AUTOPILOT Data: AI Usage Ledger
# =============================================================================

@router.get("/usage/summary", response_model=ApiResponse[Dict[str, Any]])
async def get_control_usage_summary(
    ctx: TenantContext = Depends(require_admin_db),
):
    """Aggregates AI usage across providers and models."""
    return ApiResponse(data=usage_summary())


@router.get("/usage", response_model=ApiResponse[Dict[str, Any]])
async def get_control_usage_list(
    user_id: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Lists AI usage ledger entries with pagination."""
    offset = (page - 1) * limit
    res = list_usage(user_id=user_id, model=model, limit=limit, offset=offset)
    return ApiResponse(
        data=res,
        meta=MetaInfo(total=res["total"], page=page, limit=limit),
    )


# =============================================================================
# 9. Cluster Jobs
# =============================================================================

@router.get("/jobs", response_model=ApiResponse[Dict[str, Any]])
async def get_control_jobs_list(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Lists background video rendering and publishing jobs."""
    offset = (page - 1) * limit
    res = list_jobs(status=status, limit=limit, offset=offset)
    return ApiResponse(
        data=res,
        meta=MetaInfo(total=res["total"], page=page, limit=limit),
    )


@router.get("/jobs/{job_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_single_job(
    job_id: str,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Fetches single job details."""
    from ...services.video_service import video_service
    job = video_service._jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ApiResponse(data=job)


# =============================================================================
# 10. Reports, Settings & Notifications
# =============================================================================

@router.get("/reports/summary", response_model=ApiResponse[Dict[str, Any]])
async def get_control_reports(
    ctx: TenantContext = Depends(require_admin_db),
):
    """Returns platform reports and operational health audit."""
    return ApiResponse(data=reports_summary())


@router.get("/settings", response_model=ApiResponse[Dict[str, Any]])
async def get_control_settings(
    ctx: TenantContext = Depends(require_admin_db),
):
    """Returns non-sensitive system configurations."""
    return ApiResponse(data=system_settings())


@router.put("/settings", response_model=ApiResponse[Dict[str, Any]])
async def update_control_settings(
    payload: Dict[str, Any],
    request: Request,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Updates system configurations and audits changes."""
    meta = request_meta(request)
    log_audit(
        admin_id=ctx.user_id,
        action="system.settings.update",
        resource="system_settings",
        target_id="settings_global",
        before={},
        after=payload,
        reason=payload.get("reason"),
        ip_address=meta.get("ip_address"),
    )
    return ApiResponse(data=system_settings())


@router.get("/notifications", response_model=ApiResponse[Dict[str, Any]])
async def get_admin_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(require_admin_db),
):
    """Lists notifications for admin."""
    offset = (page - 1) * limit
    res = list_notifications(user_id=ctx.user_id, unread_only=unread_only, limit=limit, offset=offset)
    return ApiResponse(
        data=res,
        meta=MetaInfo(total=res["total"], page=page, limit=limit),
    )


@router.post("/notifications/read", response_model=ApiResponse[Dict[str, Any]])
async def mark_admin_notifications_read(
    payload: Optional[Dict[str, Any]] = None,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Marks admin notifications as read."""
    ids = payload.get("ids") if payload else None
    count = mark_notifications_read(user_id=ctx.user_id, notification_ids=ids)
    return ApiResponse(data={"markedRead": count})


@router.post("/notifications/broadcast", response_model=ApiResponse[Dict[str, Any]])
async def broadcast_notification(
    payload: BroadcastPayload,
    request: Request,
    ctx: TenantContext = Depends(require_admin_db),
):
    """Broadcasts a notification to all users."""
    meta = request_meta(request)
    item = notify(
        user_id=ADMIN_BROADCAST,
        title=payload.title,
        message=payload.message,
        type=payload.type,
        link=payload.link,
    )
    log_audit(
        admin_id=ctx.user_id,
        action="notification.broadcast",
        resource="notifications",
        target_id=item["id"],
        after=payload.model_dump(),
        ip_address=meta.get("ip_address"),
    )
    return ApiResponse(data=item)


@router.get("/profile", response_model=ApiResponse[Dict[str, Any]])
async def get_admin_profile(
    ctx: TenantContext = Depends(require_admin_db),
):
    """Returns current admin user profile."""
    from core.db_base import DB_ENGINE
    user = DB_ENGINE.get_user_by_id(ctx.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")
    return ApiResponse(
        data={
            "id": user.get("id") or user.get("user_id"),
            "email": user.get("email"),
            "full_name": user.get("full_name") or user.get("name") or "Administrator",
            "role": user.get("role", "admin"),
            "created_at": user.get("created_at") or user.get("created_ts"),
            "managingContext": f"Managing as Admin: {user.get('full_name') or user.get('email')} ({ctx.user_id})",
        }
    )
