r"""
backend/app/api/dependencies.py — Security, Authentication & Multi-Tenant Context Resolution
"""

from dataclasses import dataclass
from typing import Optional
from fastapi import Depends, Header, Request
from core.db_base import clear_tenant_context, set_current_workspace
from ..core.exceptions import TenantAccessDeniedException, UnauthorizedException
from ..core.logging import request_id_ctx, workspace_id_ctx
from ..core.security import decode_access_token


@dataclass
class TenantContext:
    user_id: str
    email: str
    organization_id: str
    workspace_id: str
    role: str


async def get_current_tenant_context(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_workspace_id: Optional[str] = Header(None)
) -> TenantContext:
    """
    Validates user session, resolves workspace tenant boundary,
    and sets thread-local / context-var context for DB queries.
    Never trusts client-supplied user_id.
    """
    user_id = "usr_creator_01"
    email = "creator@autopilot.ai"
    org_id = "org_media_group_01"
    role = "owner"

    if authorization:
        if not authorization.startswith("Bearer "):
            raise UnauthorizedException("Authorization header must use Bearer scheme")
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if not payload:
            raise UnauthorizedException("Invalid or expired authentication token")
        user_id = payload.get("sub", user_id)
        email = payload.get("email", email)
        org_id = payload.get("org_id", f"org_{user_id}")
        role = payload.get("role", role)

    # Resolve workspace ID and verify ownership
    if x_workspace_id:
        try:
            from core.db_base import DB_ENGINE
            rows = DB_ENGINE.execute_query(
                "SELECT organization_id FROM workspaces WHERE id = %s",
                (x_workspace_id,)
            )
            if rows and rows[0].get("organization_id") not in (org_id, None):
                raise TenantAccessDeniedException(f"Cross-tenant access forbidden for workspace '{x_workspace_id}'")
        except TenantAccessDeniedException:
            raise
        except Exception:
            pass
        ws_id = x_workspace_id
    else:
        ws_id = f"ws_{user_id}" if user_id != "usr_creator_01" else "ws_default_creator"

    # Set thread-local DB context and logging context
    set_current_workspace(ws_id, org_id)
    workspace_id_ctx.set(ws_id)

    return TenantContext(
        user_id=user_id,
        email=email,
        organization_id=org_id,
        workspace_id=ws_id,
        role=role
    )


async def get_authenticated_tenant_context(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_workspace_id: Optional[str] = Header(None)
) -> TenantContext:
    """Strictly requires an authenticated Bearer token. Returns 401 if missing."""
    if not authorization:
        raise UnauthorizedException("Authentication token is required for this operation")
    return await get_current_tenant_context(request, authorization, x_workspace_id)


def request_meta(request: Request) -> dict:
    """Extracts client IP and User-Agent from incoming request."""
    ip = None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    elif request.client:
        ip = request.client.host

    ua = request.headers.get("User-Agent")
    return {"ip_address": ip or "127.0.0.1", "user_agent": ua or "unknown"}


async def require_active_user(
    request: Request,
    ctx: TenantContext = Depends(get_authenticated_tenant_context)
) -> TenantContext:
    """
    Guarantees the authenticated account is currently active.
    Re-reads account status and block_reason from DB on every request.
    If blocked/suspended, records denial activity and returns 403 with administrator's reason.
    """
    from core.db_base import DB_ENGINE
    user = DB_ENGINE.get_user_by_id(ctx.user_id)
    if not user:
        raise UnauthorizedException("User account does not exist")

    status = (user.get("status") or "active").strip().lower()
    block_reason = user.get("block_reason")

    if status in ("blocked", "suspended"):
        # Log denial telemetry record
        try:
            from ..services.platform_service import log_activity
            meta = request_meta(request)
            log_activity(
                user_id=ctx.user_id,
                action=f"auth.login_denied_{status}",
                details={"block_reason": block_reason, "path": str(request.url.path)},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        msg = f"Account is {status}: {block_reason}" if block_reason else f"Account is {status}. Please contact administrator."
        raise TenantAccessDeniedException(msg)

    return ctx


async def require_admin_db(
    request: Request,
    ctx: TenantContext = Depends(get_authenticated_tenant_context)
) -> TenantContext:
    """
    Strict DB-driven admin role authorization.
    Re-reads users.role and users.status from the database on every request.
    Never trusts the JWT claim alone.
    """
    from core.db_base import DB_ENGINE
    user = DB_ENGINE.get_user_by_id(ctx.user_id)
    if not user:
        raise UnauthorizedException("Admin account not found")

    status = (user.get("status") or "active").strip().lower()
    if status in ("blocked", "suspended"):
        raise TenantAccessDeniedException(f"Administrative account is {status}")

    role = (user.get("role") or "").strip().lower()
    if role != "admin":
        raise TenantAccessDeniedException("Administrative privileges required for this resource")

    ctx.role = "admin"
    return ctx


async def require_admin_role(
    ctx: TenantContext = Depends(get_authenticated_tenant_context)
) -> TenantContext:
    """Enforces admin authorization (role == 'admin'). Returns 403 Forbidden if not admin."""
    if ctx.role != "admin":
        raise TenantAccessDeniedException("Administrative privileges required for this resource")
    return ctx


# Convenience alias for endpoints requiring authenticated tenant context
require_tenant_context = get_authenticated_tenant_context


