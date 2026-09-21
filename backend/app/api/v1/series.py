r"""
backend/app/api/v1/series.py — Multi-Tenant Episodic Web Series & Franchise Hub

Manages:
- Franchise Series CRUD strictly isolated by workspace
- Character bibles, world continuity, tone, and recurring cast
- Episodic context preservation across sequential episodes
- 1-Click episode video generation maintaining previous episode recap, twist, and cliffhanger
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.db_base import DB_ENGINE
from ...schemas.common import ApiResponse
from ...services.video_service import video_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/series", tags=["Series & Franchises"])


class CreateSeriesRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = ""
    genre: str = "mystery"  # mystery, romance, thriller, horror, anime, sci-fi
    tone: str = "suspense"
    cast: Optional[Dict[str, Any]] = None


class GenerateEpisodeRequest(BaseModel):
    episodeNumber: Optional[int] = None
    title: Optional[str] = None
    recapContext: Optional[str] = None
    recapPrompt: Optional[str] = None
    currentConflict: Optional[str] = None
    conflictPrompt: Optional[str] = None
    cliffhangerCta: Optional[str] = "Next episode dekhne ke liye comment karein!"
    targetDurationSeconds: int = 60
    voiceId: Optional[str] = None


@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_workspace_series(ctx: TenantContext = Depends(get_current_tenant_context)):
    """Lists all episodic franchises owned by current workspace or all if administrator."""
    is_admin = ctx.role == "admin" or ctx.user_id in ("admin_abhay", "usr_admin")
    if is_admin:
        rows = DB_ENGINE.execute_query("SELECT * FROM series WHERE user_id = 'admin_abhay' OR user_id IS NULL OR user_id = '' ORDER BY created_at DESC")
        series_list = [dict(r) for r in rows]
    else:
        series_list = DB_ENGINE.list_series(ctx.workspace_id, user_id=ctx.user_id)

    # Attach episode counts
    results = []
    for s in series_list:
        if is_admin:
            ep_rows = DB_ENGINE.execute_query("SELECT count(*) as count FROM episodes WHERE series_id = %s", (s["id"],))
            ep_count = ep_rows[0]["count"] if ep_rows else 0
        else:
            episodes = DB_ENGINE.list_episodes(ctx.workspace_id, s["id"], user_id=ctx.user_id)
            ep_count = len(episodes)
        s_data = dict(s)
        s_data["episodeCount"] = ep_count
        results.append(s_data)

    return ApiResponse(success=True, data=results)


@router.post("", response_model=ApiResponse[Dict[str, Any]])
async def create_series(req: CreateSeriesRequest, ctx: TenantContext = Depends(get_current_tenant_context)):
    """Creates a new episodic franchise with isolated characters and story bible."""
    series_id = f"ser_{uuid.uuid4().hex[:12]}"
    cast_str = json.dumps(req.cast or {})
    res = DB_ENGINE.create_series(
        series_id=series_id,
        workspace_id=ctx.workspace_id,
        user_id=ctx.user_id,
        title=req.title,
        description=req.description or "",
        genre=req.genre,
        tone=req.tone,
        cast_json=cast_str
    )
    return ApiResponse(success=True, data=res)


@router.get("/{series_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_series_details(series_id: str, ctx: TenantContext = Depends(get_current_tenant_context)):
    """Fetches series bible, characters, and chronological episode timeline."""
    is_admin = ctx.role == "admin" or ctx.user_id in ("admin_abhay", "usr_admin")
    series = DB_ENGINE.get_series(ctx.workspace_id, series_id)
    if not series:
        rows = DB_ENGINE.execute_query("SELECT * FROM series WHERE id = %s", (series_id,))
        if rows:
            if is_admin:
                series = dict(rows[0])
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access forbidden.")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series franchise not found.")

    if is_admin:
        ep_rows = DB_ENGINE.execute_query("SELECT * FROM episodes WHERE series_id = %s ORDER BY episode_number ASC", (series_id,))
        episodes = [dict(r) for r in ep_rows]
    else:
        episodes = DB_ENGINE.list_episodes(ctx.workspace_id, series_id)
    res = dict(series)
    res["episodes"] = episodes
    res["episodeCount"] = len(episodes)
    return ApiResponse(success=True, data=res)


@router.get("/{series_id}/episodes", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_series_episodes(series_id: str, ctx: TenantContext = Depends(get_current_tenant_context)):
    """Lists all sequential episodes of the franchise with recap hooks and statuses."""
    is_admin = ctx.role == "admin" or ctx.user_id in ("admin_abhay", "usr_admin")
    series = DB_ENGINE.get_series(ctx.workspace_id, series_id)
    if not series:
        rows = DB_ENGINE.execute_query("SELECT * FROM series WHERE id = %s", (series_id,))
        if rows:
            if is_admin:
                series = dict(rows[0])
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access forbidden.")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series franchise not found.")

    if is_admin:
        ep_rows = DB_ENGINE.execute_query("SELECT * FROM episodes WHERE series_id = %s ORDER BY episode_number ASC", (series_id,))
        episodes = [dict(r) for r in ep_rows]
    else:
        episodes = DB_ENGINE.list_episodes(ctx.workspace_id, series_id)
    return ApiResponse(success=True, data=episodes)


@router.post("/{series_id}/episodes/generate", response_model=ApiResponse[Dict[str, Any]])
async def generate_series_episode(
    series_id: str,
    req: GenerateEpisodeRequest,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Autonomously generates next episode maintaining story continuity:
    1. Reads existing episode memory
    2. Identifies previous recap and current cliffhanger
    3. Prompts Writer agent to craft dramatic continuity screenplay
    4. Dispatches asynchronous rendering pipeline
    """
    is_admin = ctx.role == "admin" or ctx.user_id in ("admin_abhay", "usr_admin")
    series = DB_ENGINE.get_series(ctx.workspace_id, series_id)
    if not series:
        rows = DB_ENGINE.execute_query("SELECT * FROM series WHERE id = %s", (series_id,))
        if rows:
            if is_admin:
                series = dict(rows[0])
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access forbidden.")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series franchise not found.")

    ws_for_ep = series.get("workspace_id") or ctx.workspace_id
    if is_admin:
        ep_rows = DB_ENGINE.execute_query("SELECT * FROM episodes WHERE series_id = %s ORDER BY episode_number ASC", (series_id,))
        previous_episodes = [dict(r) for r in ep_rows]
    else:
        previous_episodes = DB_ENGINE.list_episodes(ctx.workspace_id, series_id)
    next_ep_num = req.episodeNumber or (len(previous_episodes) + 1)

    # Establish story continuity from previous episode
    recap = req.recapContext or req.recapPrompt
    if not recap:
        if previous_episodes:
            last_ep = previous_episodes[-1]
            recap = f"In Episode {last_ep.get('episode_number', 1)}, {last_ep.get('conflict', 'the mystery deepened')} leading to: {last_ep.get('cliffhanger', 'an unexpected revelation')}."
        else:
            recap = f"The origin story begins in {series['title']}."

    conflict = req.currentConflict or req.conflictPrompt or f"At the climax, a shocking secret changes everything for our characters."
    cliffhanger = req.cliffhangerCta or "What happens next? Comment your theory below!"

    # Call real Writer agent for series continuity script with offline fallback
    if os.getenv("AUTOPILOT_TEST_MODE") == "1":
        script_data = {
            "title": req.title or f"{series['title']} | Ep {next_ep_num}",
            "topic": f"Episode {next_ep_num} of {series['title']}",
            "recap": recap,
            "conflict": conflict,
            "cliffhanger": cliffhanger,
            "scenes": [
                {"scene_num": 1, "narration": f"Pichhle episode mein: {recap[:50]}...", "duration_sec": 4.0},
                {"scene_num": 2, "narration": f"Aur ab: {conflict[:70]}...", "duration_sec": 6.0},
                {"scene_num": 3, "narration": cliffhanger, "duration_sec": 4.0}
            ],
            "total_duration_sec": float(req.targetDurationSeconds or 30.0),
            "hashtags": ["series", "cliffhanger", "viral"]
        }
    else:
        try:
            from agents.writer import Writer
            from core.db import DB
            from core.llm import LLM

            writer = Writer(db=DB(), llm=LLM())
            script_data = writer.write_series_episode(
                series_name=series["title"],
                episode_num=next_ep_num,
                recap=recap,
                conflict=conflict,
                cliffhanger_cta=cliffhanger,
                length_sec=req.targetDurationSeconds
            )
        except Exception:
            script_data = {
                "title": req.title or f"{series['title']} | Ep {next_ep_num}",
                "topic": f"Episode {next_ep_num} of {series['title']}",
                "recap": recap,
                "conflict": conflict,
                "cliffhanger": cliffhanger,
                "scenes": [
                    {"scene_num": 1, "narration": f"Pichhle episode mein: {recap[:50]}...", "duration_sec": 4.0},
                    {"scene_num": 2, "narration": f"Aur ab: {conflict[:70]}...", "duration_sec": 6.0},
                    {"scene_num": 3, "narration": cliffhanger, "duration_sec": 4.0}
                ],
                "total_duration_sec": float(req.targetDurationSeconds or 30.0),
                "hashtags": ["series", "cliffhanger", "viral"]
            }

    episode_id = f"ep_{uuid.uuid4().hex[:12]}"
    ep_title = req.title or script_data.get("title", f"{series['title']} | Episode {next_ep_num}")

    # Save episode record in multi-tenant episodes table
    DB_ENGINE.create_episode(
        episode_id=episode_id,
        series_id=series_id,
        workspace_id=ws_for_ep,
        user_id=ctx.user_id,
        episode_number=next_ep_num,
        title=ep_title,
        recap=recap,
        conflict=conflict,
        cliffhanger=cliffhanger,
        script_json=json.dumps(script_data),
        status="rendering"
    )

    # Dispatch video generation job
    from ...schemas.video import VideoGenerateRequest
    gen_req = VideoGenerateRequest(
        projectId=series_id,
        scriptId=episode_id,
        voiceId=req.voiceId or "hi_m_intense",
        resolution="1080x1920",
        fps=30
    )
    job_response = video_service.queue_video_generation(ctx.workspace_id, gen_req, user_id=ctx.user_id)

    # Associate video ID with episode
    DB_ENGINE.update_episode(episode_id, status="rendering", video_id=job_response.videoId)

    return ApiResponse(
        success=True,
        data={
            "episodeId": episode_id,
            "seriesId": series_id,
            "seriesTitle": series["title"],
            "episodeNumber": next_ep_num,
            "title": ep_title,
            "status": "rendering",
            "jobId": job_response.jobId,
            "videoId": job_response.videoId,
            "script": script_data
        }
    )
