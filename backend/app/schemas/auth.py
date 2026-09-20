r"""
backend/app/schemas/auth.py — Authentication & Identity Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Use robust string type for email to guarantee zero dependency failures in container environments
EmailStr = str


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    fullName: Optional[str] = None
    name: Optional[str] = None
    avatarUrl: Optional[str] = None
    role: str = "user"
    isOnboarded: bool = False


class WorkspaceSummary(BaseModel):
    id: str
    organizationId: str
    name: str
    slug: str
    autopilotMode: str = "assisted"
    isActive: bool = True


class OrganizationSummary(BaseModel):
    id: str
    name: str
    role: str
    workspaces: List[WorkspaceSummary] = []


class SessionResponse(BaseModel):
    user: UserProfile
    organizations: List[OrganizationSummary] = []
    accessToken: Optional[str] = None
    token: Optional[str] = None
    refreshToken: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    fullName: Optional[str] = None
    name: Optional[str] = None
    workspaceName: Optional[str] = None
    organizationName: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refreshToken: str


class OnboardingCompleteRequest(BaseModel):
    workspaceName: Optional[str] = None
    defaultDurationSeconds: Optional[int] = 60
    defaultLanguage: Optional[str] = "Hindi"
    preferences: Optional[Dict[str, Any]] = None
    defaultVoice: Optional[str] = "hi_m_intense"
    contentNiche: Optional[str] = "Mystery & Suspense"
    connectedYouTube: bool = False
