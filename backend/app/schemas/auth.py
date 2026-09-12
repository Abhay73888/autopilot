r"""
backend/app/schemas/auth.py — Authentication & Identity Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    fullName: Optional[str] = None
    avatarUrl: Optional[str] = None
    role: str = "editor"


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
    refreshToken: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    fullName: str
    organizationName: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refreshToken: str
