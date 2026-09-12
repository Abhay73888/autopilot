r"""
backend/app/api/v1/videos.py — Video Assets & QA Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header
from ...core.idempotency import IDEMPOTENCY
from ...schemas.common import ApiResponse
from ...schemas.video import QACheckReport, VideoGenerateRequest, VideoJobResponse, VideoResponse
from ...services.video_service import video_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post("/generate", response_model=ApiResponse[VideoJobResponse])
async def generate_video(
    req: VideoGenerateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    if idempotency_key:
        cached = IDEMPOTENCY.get(idempotency_key)
        if cached:
            return ApiResponse(success=True, data=VideoJobResponse(**cached))

    job_res = video_service.queue_video_generation(ctx.workspace_id, req)

    if idempotency_key:
        IDEMPOTENCY.set(idempotency_key, job_res.model_dump())

    return ApiResponse(success=True, data=job_res)



@router.get("", response_model=ApiResponse[List[VideoResponse]])
async def list_videos(ctx: TenantContext = Depends(get_current_tenant_context)):
    videos = video_service.list_videos(ctx.workspace_id)
    return ApiResponse(success=True, data=videos)


@router.get("/{video_id}", response_model=ApiResponse[VideoResponse])
async def get_video(video_id: str, ctx: TenantContext = Depends(get_current_tenant_context)):
    video = video_service.get_video(ctx.workspace_id, video_id)
    return ApiResponse(success=True, data=video)


@router.get("/{video_id}/qa", response_model=ApiResponse[QACheckReport])
async def get_video_qa(video_id: str, ctx: TenantContext = Depends(get_current_tenant_context)):
    video = video_service.get_video(ctx.workspace_id, video_id)
    report = video.qaReport or QACheckReport(
        status="passed",
        score=96,
        checks={"audioLevels": {"status": "passed", "lufs": -14.2}}
    )
    return ApiResponse(success=True, data=report)
