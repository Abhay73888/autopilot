r"""
backend/app/api/v1/workspaces.py — Workspace & Autopilot Controls
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from ...schemas.common import ApiResponse
from ...schemas.workspace import BrandKitStyle, EmergencyStopResponse, WorkspaceUpdate
from ...services.workspace_service import workspace_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("/current", response_model=ApiResponse[Dict[str, Any]])
async def get_current_workspace_info(ctx: TenantContext = Depends(get_current_tenant_context)):
    ws = workspace_service.get_workspace(ctx.workspace_id)
    return ApiResponse(success=True, data=ws)


@router.patch("/current", response_model=ApiResponse[Dict[str, Any]])
async def update_workspace_settings(updates: WorkspaceUpdate, ctx: TenantContext = Depends(get_current_tenant_context)):
    ws = workspace_service.update_workspace(ctx.workspace_id, updates)
    return ApiResponse(success=True, data=ws)


@router.post("/current/emergency-stop", response_model=ApiResponse[EmergencyStopResponse])
async def trigger_emergency_stop(ctx: TenantContext = Depends(get_current_tenant_context)):
    res = workspace_service.trigger_emergency_stop(ctx.workspace_id)
    return ApiResponse(success=True, data=res)


@router.get("/current/brand-kit", response_model=ApiResponse[BrandKitStyle])
async def get_brand_kit(ctx: TenantContext = Depends(get_current_tenant_context)):
    bk = workspace_service.get_brand_kit(ctx.workspace_id)
    return ApiResponse(success=True, data=bk)
