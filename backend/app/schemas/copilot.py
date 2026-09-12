r"""
backend/app/schemas/copilot.py — AI Copilot Natural Language Command Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CopilotExecuteRequest(BaseModel):
    command: str = Field(..., min_length=2, max_length=500)


class CopilotActionPlan(BaseModel):
    intent: str
    summary: str
    parameters: Dict[str, Any] = {}
    requiresApproval: bool = False
    estimatedCredits: int = 0
    confirmationToken: Optional[str] = None
