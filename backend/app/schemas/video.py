r"""
backend/app/schemas/video.py — Video, Rendering Job, and QA Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VideoGenerateRequest(BaseModel):
    projectId: str
    scriptId: str
    voiceId: Optional[str] = "en-US-ChristopherNeural"
    captionPreset: Optional[str] = "modern_creator"
    resolution: Optional[str] = "1080x1920"
    fps: Optional[int] = 30


class VideoJobResponse(BaseModel):
    jobId: str
    videoId: str
    status: str
    estimatedTimeSeconds: int = 45
    streamUrl: str


class QACheckReport(BaseModel):
    status: str  # passed | failed
    score: int
    checks: Dict[str, Any] = {}


class VideoResponse(BaseModel):
    id: str
    workspaceId: str
    projectId: str
    title: str
    description: Optional[str] = None
    tags: List[str] = []
    durationSeconds: Optional[float] = None
    status: str
    videoUrl: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    qaReport: Optional[QACheckReport] = None
    createdAt: str
