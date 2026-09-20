r"""
backend/app/schemas/copilot.py — AI Copilot Natural Language Command Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CopilotExecuteRequest(BaseModel):
    command: Optional[str] = None
    prompt: Optional[str] = None


class CopilotActionPlan(BaseModel):
    intent: str
    summary: str
    tool: Optional[str] = None
    parameters: Dict[str, Any] = {}
    requiresApproval: bool = False
    estimatedCredits: int = 0
    confirmationToken: Optional[str] = None
    status: str = "completed"
    result: Optional[Dict[str, Any]] = None
