r"""
backend/app/api/v1/scripts.py — Screenplay & Visual Director Endpoints
"""

from fastapi import APIRouter, Depends
from ...schemas.common import ApiResponse
from ...schemas.content import ScriptGenerateRequest, ScriptResponse
from ...services.content_service import content_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/scripts", tags=["Scripts"])


@router.post("/generate", response_model=ApiResponse[ScriptResponse])
async def generate_script(
    req: ScriptGenerateRequest,
    project_id: str = "proj_default",
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    script = content_service.generate_script(ctx.workspace_id, project_id, req)
    return ApiResponse(success=True, data=script)
