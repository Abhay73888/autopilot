r"""
backend/app/api/v1/copilot.py — AI Copilot Natural Language Command Endpoint
"""

from fastapi import APIRouter, Depends
from ...schemas.common import ApiResponse
from ...schemas.copilot import CopilotActionPlan, CopilotExecuteRequest
from ...services.copilot_service import copilot_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


@router.post("/execute", response_model=ApiResponse[CopilotActionPlan])
async def execute_copilot_command(
    req: CopilotExecuteRequest,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    plan = copilot_service.process_command(ctx.workspace_id, req)
    return ApiResponse(success=True, data=plan)
