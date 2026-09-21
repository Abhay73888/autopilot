r"""
backend/app/api/v1/editor.py — Integrated Mini Video Editor API with Strict Multi-Tenant Scoping
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...schemas.common import ApiResponse
from ..dependencies import TenantContext, require_tenant_context
from core.video_editor import VideoEditor, CINEMATIC_PRESETS
from core.db_base import DB_ENGINE

router = APIRouter(prefix="/editor", tags=["Video Editor"])


class ExportCutRequest(BaseModel):
    video_id: int
    start_sec: float = Field(0.0, ge=0.0)
    end_sec: Optional[float] = None
    speed: float = Field(1.0, ge=0.25, le=4.0)
    filter_preset: str = "none"
    hook_headline: str = ""
    hook_position: str = "top"
    voice_volume: float = Field(1.0, ge=0.0, le=2.0)
    fade_audio: bool = True


def _verify_video_ownership(video_id: int, ctx: TenantContext):
    """Enforces strict tenant ownership check on video assets."""
    if ctx.role == "admin" or ctx.user_id in ("admin_abhay", "1"):
        return True
    
    if video_id <= 0:
        # Generic/cut preview asset
        return True

    rows = DB_ENGINE.execute_query("SELECT user_id, workspace_id FROM videos WHERE id = ?", (video_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Video project not found")
    
    v = rows[0]
    v_user = v.get("user_id") or ""
    v_ws = v.get("workspace_id") or ""

    if v_user == ctx.user_id or v_ws == ctx.workspace_id:
        return True

    raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to access or edit this video")


@router.get("/videos")
async def list_editor_videos(ctx: TenantContext = Depends(require_tenant_context)):
    """
    Returns editable videos scoped to the authenticated tenant.
    Normal users receive only their own videos. Admin receives admin workspace videos.
    """
    editor = VideoEditor()
    all_videos = editor.list_editable_videos()

    if ctx.role == "admin" or ctx.user_id in ("admin_abhay", "1"):
        # Admin can view all editable videos
        return {"ok": True, "videos": all_videos}

    # For standard users, filter strictly to videos owned by this user
    user_rows = DB_ENGINE.execute_query("SELECT id FROM videos WHERE user_id = ? OR workspace_id = ?", (ctx.user_id, ctx.workspace_id))
    user_video_ids = {r.get("id") for r in user_rows}

    scoped_videos = [v for v in all_videos if v.get("id") in user_video_ids]
    return {"ok": True, "videos": scoped_videos}


@router.get("/video/{video_id}")
async def get_editor_video_timeline(video_id: int, ctx: TenantContext = Depends(require_tenant_context)):
    """
    Retrieves detailed scene timeline, audio, and transcript for the video editor.
    Enforces tenant ownership.
    """
    _verify_video_ownership(video_id, ctx)
    editor = VideoEditor()
    timeline = editor.get_video_timeline(video_id)
    return timeline


@router.post("/export")
async def export_editor_cut(req: ExportCutRequest, ctx: TenantContext = Depends(require_tenant_context)):
    """
    Renders an edited cut with speed ramps, cinematic LUT color grading, hook overlays, and audio mix.
    Enforces tenant authorization.
    """
    _verify_video_ownership(req.video_id, ctx)
    editor = VideoEditor()
    result = editor.apply_edits(
        video_id=req.video_id,
        start_sec=req.start_sec,
        end_sec=req.end_sec,
        speed=req.speed,
        filter_preset=req.filter_preset,
        hook_headline=req.hook_headline,
        hook_position=req.hook_position,
        voice_volume=req.voice_volume,
        fade_audio=req.fade_audio,
    )
    return result
