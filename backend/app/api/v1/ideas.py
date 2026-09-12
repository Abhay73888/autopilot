r"""
backend/app/api/v1/ideas.py — Ideation Lab Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends
from ...schemas.common import ApiResponse
from ...schemas.content import IdeaGenerateRequest, IdeaItem
from ...services.content_service import content_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/ideas", tags=["Content Ideation"])


@router.post("/generate", response_model=ApiResponse[List[IdeaItem]])
async def generate_ideas(
    req: IdeaGenerateRequest,
    project_id: str = "proj_default",
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    ideas = content_service.generate_ideas(ctx.workspace_id, project_id, req)
    return ApiResponse(success=True, data=ideas)
