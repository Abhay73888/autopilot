r"""
backend/app/api/v1/projects.py — Project & Campaign Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends
from ...schemas.common import ApiResponse
from ...schemas.project import ProjectCreate, ProjectResponse
from ...services.project_service import project_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ApiResponse[ProjectResponse])
async def create_project(data: ProjectCreate, ctx: TenantContext = Depends(get_current_tenant_context)):
    proj = project_service.create_project(ctx.workspace_id, data)
    return ApiResponse(success=True, data=proj)


@router.get("", response_model=ApiResponse[List[ProjectResponse]])
async def list_projects(ctx: TenantContext = Depends(get_current_tenant_context)):
    projs = project_service.list_projects(ctx.workspace_id)
    return ApiResponse(success=True, data=projs)


@router.get("/{project_id}", response_model=ApiResponse[ProjectResponse])
async def get_project(project_id: str, ctx: TenantContext = Depends(get_current_tenant_context)):
    proj = project_service.get_project(ctx.workspace_id, project_id)
    return ApiResponse(success=True, data=proj)
