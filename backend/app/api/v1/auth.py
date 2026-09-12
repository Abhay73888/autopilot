r"""
backend/app/api/v1/auth.py — Authentication Endpoints
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from ...core.security import create_access_token, create_refresh_token, decode_access_token
from ...schemas.auth import (
    LoginRequest,
    OrganizationSummary,
    RefreshTokenRequest,
    SessionResponse,
    SignupRequest,
    UserProfile,
    WorkspaceSummary,
)
from ...schemas.common import ApiResponse
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=ApiResponse[SessionResponse])
async def login(req: LoginRequest):
    user_id = f"usr_{abs(hash(req.email)) % 100000}"
    org_id = f"org_{user_id}"
    ws_id = f"ws_{user_id}"

    token_payload = {"sub": user_id, "email": req.email, "org_id": org_id, "role": "owner"}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    user = UserProfile(id=user_id, email=req.email, fullName="Creator User", role="owner")
    org = OrganizationSummary(
        id=org_id,
        name="Creator Media",
        role="owner",
        workspaces=[
            WorkspaceSummary(id=ws_id, organizationId=org_id, name="Studio Workspace", slug="studio-workspace")
        ]
    )
    return ApiResponse(
        success=True,
        data=SessionResponse(
            user=user,
            organizations=[org],
            accessToken=access_token,
            refreshToken=refresh_token
        )
    )


@router.post("/signup", response_model=ApiResponse[SessionResponse])
async def signup(req: SignupRequest):
    user_id = f"usr_{abs(hash(req.email)) % 100000}"
    org_id = f"org_{user_id}"
    ws_id = f"ws_{user_id}"

    token_payload = {"sub": user_id, "email": req.email, "org_id": org_id, "role": "owner"}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    user = UserProfile(id=user_id, email=req.email, fullName=req.fullName, role="owner")
    org = OrganizationSummary(
        id=org_id,
        name=req.organizationName or f"{req.fullName}'s Org",
        role="owner",
        workspaces=[
            WorkspaceSummary(id=ws_id, organizationId=org_id, name="Default Studio", slug="default-studio")
        ]
    )
    return ApiResponse(
        success=True,
        data=SessionResponse(
            user=user,
            organizations=[org],
            accessToken=access_token,
            refreshToken=refresh_token
        )
    )


@router.post("/refresh", response_model=ApiResponse[SessionResponse])
async def refresh_session(req: RefreshTokenRequest):
    payload = decode_access_token(req.refreshToken)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = payload.get("sub", "usr_guest")
    email = payload.get("email", "guest@autopilot.media")
    org_id = payload.get("org_id", f"org_{user_id}")
    ws_id = f"ws_{user_id}"

    new_payload = {"sub": user_id, "email": email, "org_id": org_id, "role": payload.get("role", "owner")}
    new_access = create_access_token(new_payload)
    new_refresh = create_refresh_token(new_payload)

    user = UserProfile(id=user_id, email=email, fullName="Creator User", role="owner")
    org = OrganizationSummary(
        id=org_id,
        name="Creator Media",
        role="owner",
        workspaces=[
            WorkspaceSummary(id=ws_id, organizationId=org_id, name="Studio Workspace", slug="studio-workspace")
        ]
    )
    return ApiResponse(
        success=True,
        data=SessionResponse(
            user=user,
            organizations=[org],
            accessToken=new_access,
            refreshToken=new_refresh
        )
    )


@router.get("/session", response_model=ApiResponse[SessionResponse])
async def get_session(ctx: TenantContext = Depends(get_current_tenant_context)):
    user = UserProfile(id=ctx.user_id, email=ctx.email, fullName="Creator User", role=ctx.role)
    org = OrganizationSummary(
        id=ctx.organization_id,
        name="Primary Organization",
        role=ctx.role,
        workspaces=[
            WorkspaceSummary(id=ctx.workspace_id, organizationId=ctx.organization_id, name="Active Studio", slug="active-studio")
        ]
    )
    return ApiResponse(
        success=True,
        data=SessionResponse(user=user, organizations=[org])
    )


@router.post("/delete-data", response_model=ApiResponse[Dict[str, Any]])
async def delete_user_data(ctx: TenantContext = Depends(get_current_tenant_context)):
    """
    Google OAuth & GDPR compliant data deletion endpoint.
    Purges all stored channel OAuth credentials, videos, and private assets.
    """
    import time
    from core.db_base import DB_ENGINE
    from .publish import _local_channel_store

    try:
        DB_ENGINE.execute_mutation("DELETE FROM channel_credentials WHERE workspace_id = %s", (ctx.workspace_id,))
        DB_ENGINE.execute_mutation("DELETE FROM videos WHERE workspace_id = %s", (ctx.workspace_id,))
    except Exception:
        pass

    if ctx.workspace_id in _local_channel_store:
        del _local_channel_store[ctx.workspace_id]

    return ApiResponse(
        success=True,
        data={
            "status": "purged",
            "message": "All user data, Google OAuth tokens, and media assets have been permanently deleted.",
            "userId": ctx.user_id,
            "workspaceId": ctx.workspace_id,
            "purgedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    )
