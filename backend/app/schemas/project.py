r"""
backend/app/schemas/project.py — Project & Campaign Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    niche: str
    targetAudience: str
    tone: str = "cinematic"
    targetDurationSeconds: int = 45
    targetPlatforms: List[str] = ["youtube", "instagram", "tiktok"]
    postingFrequencyPerWeek: int = 5
    brandKitId: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    workspaceId: str
    name: str
    niche: str
    targetAudience: str
    tone: str
    targetDurationSeconds: int
    targetPlatforms: List[str]
    postingFrequencyPerWeek: int
    totalVideosGenerated: int = 0
    createdAt: str
