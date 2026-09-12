r"""
backend/app/schemas/content.py — Content Ideation and Screenplay Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IdeaGenerateRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)
    focusKeywords: List[str] = []
    curiosityTarget: int = Field(default=85, ge=0, le=100)


class IdeaItem(BaseModel):
    id: str
    topic: str
    angle: Optional[str] = None
    viralScore: int
    trendScore: int
    competitionScore: int
    retentionPotential: int
    recommendedHook: str
    status: str = "pending"


class SceneItem(BaseModel):
    sceneIndex: int
    startSecond: float
    endSecond: float
    scriptSnippet: str
    visualPrompt: str
    bRollKeyword: Optional[str] = None
    motionEffect: str = "zoom_in_slow"


class ScriptGenerateRequest(BaseModel):
    ideaId: Optional[str] = None
    topic: Optional[str] = None
    style: str = "storytelling_fast_paced"
    targetSeconds: int = 45


class ScriptResponse(BaseModel):
    id: str
    projectId: str
    title: str
    hook: str
    body: str
    payoff: str
    callToAction: str
    fullText: str
    estimatedDurationSeconds: int
    scenesBreakdown: List[SceneItem] = []
    status: str = "draft"
