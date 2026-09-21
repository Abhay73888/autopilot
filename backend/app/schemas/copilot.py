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


class CopilotVoiceSettings(BaseModel):
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: str = "+0Hz"
    emotion: str = "auto"
    voice_id: Optional[str] = None


class CopilotChatRequest(BaseModel):
    message: str
    language: str = "auto"  # "en", "hi", "bho", "auto"
    context: Optional[Dict[str, Any]] = None
    voice_settings: Optional[CopilotVoiceSettings] = None
    generate_speech: bool = True


class CopilotChatResponse(BaseModel):
    reply: str
    language: str  # "en", "hi", "bho"
    language_display: str
    audio_base64: Optional[str] = None
    audio_format: str = "audio/mp3"
    intent: str = "CONVERSATION"
    tool: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    robot_state: str = "SUCCESS"


class CopilotTTSRequest(BaseModel):
    text: str
    language: str = "auto"
    voice_settings: Optional[CopilotVoiceSettings] = None


class CopilotTTSResponse(BaseModel):
    audio_base64: str
    audio_format: str = "audio/mp3"
    duration_est: float = 0.0
    language: str = "en"

