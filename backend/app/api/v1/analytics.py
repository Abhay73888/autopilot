r"""
backend/app/api/v1/analytics.py — Performance Metrics & Content Scientist Endpoints
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from ...schemas.common import ApiResponse
from ...services.analytics_service import analytics_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/analytics", tags=["Analytics & Scientist"])


@router.get("/overview", response_model=ApiResponse[Dict[str, Any]])
async def get_analytics_overview(timeframe: str = "30d", ctx: TenantContext = Depends(get_current_tenant_context)):
    overview = analytics_service.get_workspace_overview(ctx.workspace_id, timeframe)
    return ApiResponse(success=True, data=overview)


@router.get("/scientist/recommendations", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_content_scientist_insights(ctx: TenantContext = Depends(get_current_tenant_context)):
    insights = analytics_service.get_scientist_recommendations(ctx.workspace_id)
    return ApiResponse(success=True, data=insights)


@router.post("/poll", response_model=ApiResponse[Dict[str, Any]])
async def trigger_analytics_poll(ctx: TenantContext = Depends(get_current_tenant_context)):
    """Triggers quota-aware polling loop for channels connected to current workspace."""
    poll_result = analytics_service.poll_workspace_channels(ctx.workspace_id)
    return ApiResponse(success=True, data=poll_result)
