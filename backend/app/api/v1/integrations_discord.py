r"""
backend/app/api/v1/integrations_discord.py — Discord OAuth 2.0 & Bot Integration Router for FastAPI.

Endpoints:
- GET  /api/v1/integrations/discord/status
- GET  /api/v1/integrations/discord/oauth/start
- GET  /api/v1/integrations/discord/oauth/callback
- POST /api/v1/integrations/discord/settings
- POST /api/v1/integrations/discord/test
- POST /api/v1/integrations/discord/disconnect
- POST /api/v1/integrations/discord/interactions
"""

from __future__ import annotations

import time
import urllib.parse
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from core.db import DB
from core.discord_service import (
    DiscordConfig,
    DiscordNotifications,
    DiscordOAuth,
    DiscordSlashCommands,
)
from ..dependencies import TenantContext, get_current_tenant_context
from ...schemas.common import ApiResponse

router = APIRouter(prefix="/integrations/discord", tags=["Integrations - Discord"])


class DiscordSettingsRequest(BaseModel):
    notify_generation: Optional[int] = None
    notify_upload: Optional[int] = None
    notify_errors: Optional[int] = None
    notify_analytics: Optional[int] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None
    webhook_url: Optional[str] = None


@router.get("/status", response_model=ApiResponse[Dict[str, Any]])
async def get_discord_status(
    ctx: TenantContext = Depends(get_current_tenant_context),
) -> ApiResponse[Dict[str, Any]]:
    """Returns the current tenant's Discord connection and configuration status."""
    with DB() as db:
        conn = db.get_discord_connection(ctx.user_id)
        return ApiResponse(
            success=True,
            data={
                "configured": DiscordConfig.is_configured(),
                "bot_active": DiscordConfig.has_bot(),
                "webhook_active": DiscordConfig.has_webhook(),
                "connected": bool(conn),
                "connection": conn,
            },
        )


@router.get("/oauth/start")
async def start_discord_oauth(
    request: Request,
    ctx: TenantContext = Depends(get_current_tenant_context),
) -> ApiResponse[Dict[str, Any]]:
    """Initiates Discord OAuth2 flow with signed state."""
    if not DiscordConfig.is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discord integration credentials not set. Set DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET.",
        )

    cb = DiscordConfig.default_redirect_uri()
    if not cb:
        host = request.headers.get("Host", "localhost:8765")
        proto = request.headers.get("X-Forwarded-Proto", "http")
        cb = f"{proto}://{host}/api/integrations/discord/oauth/callback"

    auth_url, state = DiscordOAuth.get_authorization_url(ctx.user_id, callback_url=cb)
    return ApiResponse(
        success=True,
        data={"authorizationUrl": auth_url, "state": state},
    )


@router.get("/oauth/callback")
async def discord_oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    guild_id: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
) -> RedirectResponse:
    """Validates Discord OAuth2 callback and stores encrypted tokens."""
    if error or not code or not state:
        return RedirectResponse(url="/?discord=denied", status_code=status.HTTP_302_FOUND)

    uid = DiscordOAuth.verify_state(state)
    if not uid:
        return RedirectResponse(url="/?discord=state_invalid", status_code=status.HTTP_302_FOUND)

    cb = DiscordConfig.default_redirect_uri()
    if not cb:
        host = request.headers.get("Host", "localhost:8765")
        proto = request.headers.get("X-Forwarded-Proto", "http")
        cb = f"{proto}://{host}/api/integrations/discord/oauth/callback"

    try:
        tokens = DiscordOAuth.exchange_code(code, cb)
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 604800)
        token_expires_at = int(time.time()) + expires_in

        profile = DiscordOAuth.fetch_current_user(access_token)
        discord_user_id = profile.get("id")
        username = profile.get("username") or "DiscordUser"
        global_name = profile.get("global_name") or username
        avatar = profile.get("avatar")

        guild_name = None
        if guild_id:
            try:
                guilds = DiscordOAuth.fetch_user_guilds(access_token)
                for g in guilds:
                    if str(g.get("id")) == str(guild_id):
                        guild_name = g.get("name")
                        break
            except Exception:
                pass

        with DB() as db:
            db.save_discord_connection(
                user_id=uid,
                discord_user_id=discord_user_id,
                username=username,
                global_name=global_name,
                avatar=avatar,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at,
                guild_id=guild_id or None,
                guild_name=guild_name,
            )

        return RedirectResponse(url="/?discord=connected", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        return RedirectResponse(
            url=f"/?discord=error&msg={urllib.parse.quote(str(e)[:80])}",
            status_code=status.HTTP_302_FOUND,
        )


@router.post("/settings", response_model=ApiResponse[Dict[str, Any]])
async def update_discord_settings(
    req: DiscordSettingsRequest,
    ctx: TenantContext = Depends(get_current_tenant_context),
) -> ApiResponse[Dict[str, Any]]:
    """Updates notification settings for the user's Discord integration."""
    with DB() as db:
        db.update_discord_settings(
            user_id=ctx.user_id,
            notify_generation=req.notify_generation,
            notify_upload=req.notify_upload,
            notify_errors=req.notify_errors,
            notify_analytics=req.notify_analytics,
            channel_id=req.channel_id,
            channel_name=req.channel_name,
            guild_id=req.guild_id,
            guild_name=req.guild_name,
            webhook_url=req.webhook_url,
        )
        conn = db.get_discord_connection(ctx.user_id)
        return ApiResponse(success=True, data={"connection": conn})


@router.post("/test", response_model=ApiResponse[Dict[str, Any]])
async def test_discord_notification(
    ctx: TenantContext = Depends(get_current_tenant_context),
) -> ApiResponse[Dict[str, Any]]:
    """Sends a test embed message to the user's configured Discord destination."""
    embed = DiscordNotifications.create_embed(
        title="💬 AUTOPILOT Notification Test",
        description="Your Discord integration is working properly! Video generation, rendering, and upload events will appear here.",
        color=0x10B981,
        fields=[
            {"name": "Status", "value": "✅ Live Connected", "inline": True},
            {"name": "User", "value": ctx.user_id, "inline": True},
        ],
        url=DiscordConfig.app_url(),
    )
    delivered = DiscordNotifications.dispatch(embed, user_id=ctx.user_id)
    if delivered:
        return ApiResponse(success=True, data={"message": "Test notification delivered successfully! ✅"})
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Could not deliver notification to Discord. Verify channel permissions or webhook URL.",
    )


@router.post("/disconnect", response_model=ApiResponse[Dict[str, Any]])
async def disconnect_discord(
    ctx: TenantContext = Depends(get_current_tenant_context),
) -> ApiResponse[Dict[str, Any]]:
    """Revokes active Discord connection for this tenant."""
    with DB() as db:
        db.disconnect_discord(ctx.user_id)
    return ApiResponse(success=True, data={"message": "Discord disconnected successfully."})


@router.post("/interactions")
async def discord_interactions_endpoint(request: Request) -> Dict[str, Any]:
    """Public webhook receiver for Discord Interactions (Slash Commands)."""
    body = await request.json()
    resp = DiscordSlashCommands.dispatch_interaction(body)
    return resp
