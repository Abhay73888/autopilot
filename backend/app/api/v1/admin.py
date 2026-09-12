r"""
backend/app/api/v1/admin.py — Operational Admin & System Health Endpoints
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from ...schemas.common import ApiResponse
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/admin", tags=["Admin & System"])


@router.get("/overview", response_model=ApiResponse[Dict[str, Any]])
async def get_admin_system_overview(ctx: TenantContext = Depends(get_current_tenant_context)):
    from ...services.video_service import video_service
    failed_jobs = [j for j in video_service._jobs.values() if j.get("status") == "failed"]
    return ApiResponse(
        success=True,
        data={
            "totalUsers": 1280,
            "activeWorkspaces": 842,
            "activeRenderJobs": 3,
            "renderWorkerLoadPercent": 42,
            "monthlyRecurringRevenueUsd": 38400.0,
            "grossMarginPercent": 90.8,
            "deadLetterJobs": len(failed_jobs),
            "providerStatus": {
                "gemini": "healthy",
                "openai": "healthy",
                "elevenlabs": "healthy",
                "modal_ffmpeg": "healthy",
                "cloudflare_r2": "healthy"
            }
        }
    )


@router.get("/dlq", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_dead_letter_queue(ctx: TenantContext = Depends(get_current_tenant_context)):
    """Lists permanently failed / dead letter jobs."""
    from ...services.video_service import video_service
    dead_jobs = [j for j in video_service._jobs.values() if j.get("status") == "failed"]
    return ApiResponse(success=True, data=dead_jobs)


@router.post("/dlq/replay", response_model=ApiResponse[Dict[str, Any]])
async def replay_dead_letter_jobs(job_id: str = None, ctx: TenantContext = Depends(get_current_tenant_context)):
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
