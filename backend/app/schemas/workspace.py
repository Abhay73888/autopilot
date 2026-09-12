r"""
backend/app/schemas/workspace.py — Workspace, Brand Kit, and Autopilot Mode Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BrandKitStyle(BaseModel):
    name: str = "Modern Creator"
    primaryColor: str = "#6366F1"
    secondaryColor: str = "#EC4899"
    accentColor: str = "#10B981"
    fontFamily: str = "Inter"
    captionStyle: Dict[str, Any] = Field(default_factory=lambda: {
        "font": "Inter Bold",
        "size": 72,
        "color": "#FFFFFF",
        "highlightColor": "#FFCC00",
        "animation": "word_highlight",
        "position": "bottom_center"
    })
    voicePreference: Dict[str, Any] = Field(default_factory=lambda: {
        "provider": "edge",
        "voiceId": "en-US-ChristopherNeural",
        "speed": 1.05
    })
    watermarkUrl: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    autopilotMode: Optional[str] = None  # manual | assisted | full_autopilot
    isActive: Optional[bool] = None
    maxDailyRenders: Optional[int] = None
    monthlyBudgetUsd: Optional[float] = None


class EmergencyStopResponse(BaseModel):
    message: str
    cancelledJobsCount: int
    cancelledJobIds: List[str] = []
