r"""
backend/app/services/activity_tracking.py — Activity Tracking Helper for API Routers
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import Request
from .platform_service import log_activity


def record(
    action: str,
    request: Optional[Request] = None,
    user_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience helper invoked across API routers to register activity telemetry.
    Extracts client IP, user agent, and passes through to platform_service.log_activity.
    """
    ip = ip_address
    ua = user_agent

    if request:
        if not ip:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                ip = forwarded.split(",")[0].strip()
            elif request.client:
                ip = request.client.host
        if not ua:
            ua = request.headers.get("User-Agent")

    target_user = user_id or actor_id or "usr_system"
    target_actor = actor_id or user_id or "usr_system"

    return log_activity(
        user_id=target_user,
        action=action,
        actor_id=target_actor,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip,
        user_agent=ua,
    )
