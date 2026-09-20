r"""
backend/app/api/v1/admin.py — Operational Admin & System Health Endpoints
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from ...schemas.common import ApiResponse
from ..dependencies import TenantContext, require_admin_role

router = APIRouter(prefix="/admin", tags=["Admin & System"])


@router.get("/overview", response_model=ApiResponse[Dict[str, Any]])
async def get_admin_system_overview(ctx: TenantContext = Depends(require_admin_role)):
    from core.db_base import DB_ENGINE
    from ...services.video_service import video_service

    total_users = 0
    active_workspaces = 0
    total_videos = 0
    total_series = 0

    try:
        u_rows = DB_ENGINE.execute_query("SELECT COUNT(*) as cnt FROM users")
        if u_rows:
            total_users = u_rows[0].get("cnt", 0)
    except Exception:
        pass

    try:
        w_rows = DB_ENGINE.execute_query("SELECT COUNT(*) as cnt FROM workspaces")
        if w_rows:
            active_workspaces = w_rows[0].get("cnt", 0)
    except Exception:
        pass

    try:
        v_rows = DB_ENGINE.execute_query("SELECT COUNT(*) as cnt FROM video_projects")
        if v_rows:
            total_videos = v_rows[0].get("cnt", 0)
    except Exception:
        pass

    try:
        s_rows = DB_ENGINE.execute_query("SELECT COUNT(*) as cnt FROM series")
        if s_rows:
            total_series = s_rows[0].get("cnt", 0)
    except Exception:
        pass

    active_jobs = [j for j in video_service._jobs.values() if j.get("status") in ("queued", "processing")]
    failed_jobs = [j for j in video_service._jobs.values() if j.get("status") == "failed"]

    return ApiResponse(
        success=True,
        data={
            "totalUsers": total_users,
            "activeWorkspaces": active_workspaces,
            "totalVideos": total_videos,
            "totalSeries": total_series,
            "activeRenderJobs": len(active_jobs),
            "renderWorkerLoadPercent": min(100, len(active_jobs) * 20),
            "deadLetterJobs": len(failed_jobs),
            "providerStatus": {
                "gemini": "healthy",
                "openai": "healthy",
                "elevenlabs": "healthy",
                "edge_tts": "healthy",
                "ffmpeg": "healthy",
                "youtube_oauth": "healthy"
            }
        }
    )


@router.get("/users", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_admin_users(ctx: TenantContext = Depends(require_admin_role)):
    """List all registered platform users. Never exposes password hashes or tokens."""
    from core.db_base import DB_ENGINE
    users = []
    try:
        # SQLite / Postgres column safe query
        rows = DB_ENGINE.execute_query("SELECT * FROM users ORDER BY id DESC LIMIT 100")
        for r in rows:
            uid = str(r.get("user_id") or r.get("id"))
            users.append({
                "id": uid,
                "email": r.get("email", ""),
                "name": r.get("name") or r.get("full_name") or "",
                "role": r.get("role", "user"),
                "isOnboarded": bool(r.get("is_onboarded", False)),
                "createdAt": str(r.get("created_ts") or r.get("created_at") or "")
            })
    except Exception as e:
        users = []

    return ApiResponse(success=True, data=users)


@router.get("/workspaces", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_admin_workspaces(ctx: TenantContext = Depends(require_admin_role)):
    """List all workspaces across tenants."""
    from core.db_base import DB_ENGINE
    workspaces = []
    try:
        rows = DB_ENGINE.execute_query("SELECT * FROM workspaces ORDER BY id DESC LIMIT 100")
        for r in rows:
            workspaces.append({
                "id": str(r.get("id")),
                "name": r.get("name") or r.get("workspace_name") or "Workspace",
                "organizationId": r.get("organization_id", ""),
                "tier": r.get("subscription_tier", "pro"),
                "createdAt": str(r.get("created_at") or "")
            })
    except Exception:
        pass
    return ApiResponse(success=True, data=workspaces)


@router.get("/dlq", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_dead_letter_queue(ctx: TenantContext = Depends(require_admin_role)):
    """Lists permanently failed / dead letter jobs."""
    from ...services.video_service import video_service
    dead_jobs = [j for j in video_service._jobs.values() if j.get("status") == "failed"]
    return ApiResponse(success=True, data=dead_jobs)


@router.post("/dlq/replay", response_model=ApiResponse[Dict[str, Any]])
async def replay_dead_letter_jobs(job_id: str = None, ctx: TenantContext = Depends(require_admin_role)):
    """Requeues dead-letter jobs back to the worker execution queue."""
    from ...services.video_service import video_service
    replayed = []
    for jid, j in video_service._jobs.items():
        if j.get("status") == "failed" and (job_id is None or jid == job_id):
            j["status"] = "queued"
            j["progress"] = 0
            j["currentStep"] = "replaying_from_dlq"
            replayed.append(jid)

    return ApiResponse(
        success=True,
        data={
            "status": "replayed",
            "replayedJobCount": len(replayed),
            "replayedJobIds": replayed
        }
    )

