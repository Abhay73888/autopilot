r"""
backend/app/api/v1/integrations_instagram.py — Meta Instagram OAuth 2.0 Integration Router.

Endpoints:
- GET  /api/v1/integrations/instagram/oauth/start
- GET  /api/v1/integrations/instagram/oauth/callback
- GET  /api/v1/integrations/instagram/accounts
- POST /api/v1/integrations/instagram/disconnect
- GET  /api/v1/integrations/instagram/status
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ...core.config import settings
from ..dependencies import TenantContext, get_current_tenant_context
from ...integrations.meta_client import MetaApiClient
from ...schemas.common import ApiResponse
from ...services.publishing_service import publishing_service

router = APIRouter(prefix="/integrations/instagram", tags=["Integrations - Instagram"])


class DisconnectAccountRequest(BaseModel):
    platformAccountId: str


def generate_oauth_state(workspace_id: str, user_id: str) -> str:
    """Creates a cryptographically signed, tamper-proof state with 10-minute TTL."""
    payload = {
        "ws": workspace_id,
        "u": user_id,
        "nonce": uuid.uuid4().hex,
        "exp": int(time.time()) + 600
    }
    raw_payload = json.dumps(payload, sort_keys=True)
    sig = hmac.new(settings.secret_key.encode("utf-8"), raw_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    b64_payload = base64.urlsafe_b64encode(raw_payload.encode("utf-8")).decode("utf-8")
    return f"{b64_payload}.{sig}"


def verify_oauth_state(state_str: str) -> Dict[str, Any]:
    """Verifies state signature, structure, and expiration."""
    if not state_str or "." not in state_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed OAuth state")

    b64_payload, sig = state_str.split(".", 1)
    try:
        raw_payload = base64.urlsafe_b64decode(b64_payload.encode("utf-8")).decode("utf-8")
        payload = json.loads(raw_payload)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state encoding")

    expected_sig = hmac.new(settings.secret_key.encode("utf-8"), raw_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state signature verification failed (CSRF)")

    if payload.get("exp", 0) < time.time():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state expired. Please initiate connection again.")

    return payload


@router.get("/oauth/start", response_model=ApiResponse[Dict[str, Any]])
async def start_instagram_oauth(
    redirect_uri: Optional[str] = None,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Generates Meta OAuth dialog URL with signed state encoding authenticated tenant identity.
    """
    client = MetaApiClient(redirect_uri=redirect_uri)
    state = generate_oauth_state(ctx.workspace_id, ctx.user_id)
    auth_url = client.get_authorization_url(state=state, redirect_uri=redirect_uri)

    return ApiResponse(
        success=True,
        data={
            "authorization_url": auth_url,
            "state": state,
            "workspace_id": ctx.workspace_id
        }
    )


@router.get("/oauth/callback", response_model=ApiResponse[Dict[str, Any]])
async def instagram_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    ctx: Optional[TenantContext] = Depends(get_current_tenant_context)
):
    """
    Handles Meta OAuth redirect callback, verifies state, exchanges short-lived & long-lived
    tokens, discovers Instagram Professional accounts, and encrypts credentials.
    """
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Meta OAuth error: {error_description or error}")

    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required code or state parameter")

    # Verify HMAC state
    state_payload = verify_oauth_state(state)
    target_workspace_id = state_payload["ws"]

    # If context is authenticated, enforce strict tenant matching
    if ctx and ctx.workspace_id != target_workspace_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant OAuth connection attempt detected")

    client = MetaApiClient()

    try:
        # 1. Exchange code for short-lived token
        short_token_data = client.exchange_code_for_token(code)
        short_token = short_token_data.get("access_token")
        if not short_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to obtain access token from Meta")

        # 2. Exchange for 60-day long-lived token
        long_token_data = client.exchange_long_lived_token(short_token)
        long_token = long_token_data.get("access_token") or short_token
        expires_in = long_token_data.get("expires_in")
        token_expires_at = None
        if expires_in:
            token_expires_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + expires_in))

        # 3. Discover Instagram Business / Creator accounts
        ig_accounts = client.get_instagram_accounts(long_token)
        if not ig_accounts:
            # Fallback check if user ID is known
            return ApiResponse(
                success=False,
                error={
                    "code": "NO_INSTAGRAM_BUSINESS_ACCOUNT",
                    "message": "No Instagram Business or Creator account found. Ensure your Instagram account is Professional and linked to a Facebook Page."
                }
            )

        # 4. Connect discovered account(s)
        connected = []
        for acct in ig_accounts:
            record = publishing_service.connect_account(
                workspace_id=target_workspace_id,
                platform="instagram",
                external_account_id=acct["external_account_id"],
                username=acct["username"],
                display_name=acct["display_name"],
                profile_image_url=acct["profile_image_url"],
                access_token=long_token,
                scopes=["instagram_basic", "instagram_content_publish", "pages_show_list"],
                token_expires_at=token_expires_at,
                metadata={"page_id": acct.get("page_id"), "page_name": acct.get("page_name")}
            )
            connected.append(record)

        return ApiResponse(
            success=True,
            data={
                "status": "connected",
                "workspace_id": target_workspace_id,
                "connected_accounts": connected
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"OAuth exchange failed: {str(e)}")


@router.get("/accounts", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_instagram_accounts(ctx: TenantContext = Depends(get_current_tenant_context)):
    """
    Returns all active Instagram accounts connected to this workspace.
    Sensitive tokens are NEVER exposed in response.
    """
    accounts = publishing_service.list_accounts(ctx.workspace_id, platform="instagram")
    return ApiResponse(success=True, data=accounts)


@router.post("/disconnect", response_model=ApiResponse[Dict[str, Any]])
async def disconnect_instagram_account(
    req: DisconnectAccountRequest,
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    """
    Disconnects an Instagram account from this workspace.
    """
    success = publishing_service.disconnect_account(ctx.workspace_id, req.platformAccountId)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform account not found in workspace")
    return ApiResponse(
        success=True,
        data={
            "status": "disconnected",
            "platformAccountId": req.platformAccountId
        }
    )


@router.get("/status", response_model=ApiResponse[Dict[str, Any]])
async def get_instagram_status(ctx: TenantContext = Depends(get_current_tenant_context)):
    """
    Returns integration status and connection health.
    """
    accounts = publishing_service.list_accounts(ctx.workspace_id, platform="instagram")
    is_connected = len(accounts) > 0
    return ApiResponse(
        success=True,
        data={
            "platform": "instagram",
            "connected": is_connected,
            "accounts_count": len(accounts),
            "accounts": accounts
        }
    )
