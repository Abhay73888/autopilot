r"""
backend/app/api/v1/copilot.py — AI Copilot Natural Language Command Endpoint
"""

from fastapi import APIRouter, Depends
from ...schemas.common import ApiResponse
from ...schemas.copilot import (
    CopilotActionPlan,
    CopilotExecuteRequest,
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotTTSRequest,
    CopilotTTSResponse,
)
from ...services.copilot_service import copilot_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


@router.post("/chat", response_model=ApiResponse[CopilotChatResponse])
async def copilot_chat(
    req: CopilotChatRequest,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """Conversational intelligence, intent detection, and voice synthesis for 3D AI Copilot."""
    res = await copilot_service.chat(
        workspace_id=ctx.workspace_id,
        request=req,
        user_id=ctx.user_id,
        role=ctx.role
    )
    return ApiResponse(success=True, data=res)


@router.post("/tts", response_model=ApiResponse[CopilotTTSResponse])
async def copilot_tts(
    req: CopilotTTSRequest,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """Direct speech generation endpoint for 3D AI Copilot."""
    res = await copilot_service.tts(req)
    return ApiResponse(success=True, data=res)


@router.post("/execute", response_model=ApiResponse[CopilotActionPlan])
@router.post("/action", response_model=ApiResponse[CopilotActionPlan])
async def execute_copilot_command(
    req: CopilotExecuteRequest,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    plan = copilot_service.process_command(ctx.workspace_id, req)
    return ApiResponse(success=True, data=plan)

