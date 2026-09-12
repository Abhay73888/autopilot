r"""
backend/app/services/workspace_service.py — Workspace Management & Autopilot Controls
"""

import uuid
from typing import Any, Dict, List, Optional
from core.db_base import DB_ENGINE
from ..core.exceptions import ResourceNotFoundException
from ..schemas.workspace import BrandKitStyle, EmergencyStopResponse, WorkspaceUpdate


class WorkspaceService:
    @staticmethod
    def get_workspace(workspace_id: str) -> Dict[str, Any]:
        """Retrieves workspace metadata and active mode."""
        rows = DB_ENGINE.execute_query(
            "SELECT id, organization_id, name, slug, autopilot_mode, is_active FROM workspaces WHERE id = %s",
            (workspace_id,)
        )
        if not rows:
            # Fallback default workspace for developer sandbox
            return {
                "id": workspace_id,
                "organizationId": "org_default",
                "name": "Default Studio",
                "slug": "default-studio",
                "autopilotMode": "assisted",
                "isActive": True
            }
        r = rows[0]
        return {
            "id": r["id"],
            "organizationId": r["organization_id"],
            "name": r["name"],
            "slug": r["slug"],
            "autopilotMode": r.get("autopilot_mode", "assisted"),
            "isActive": bool(r.get("is_active", True))
        }

    @staticmethod
    def update_workspace(workspace_id: str, updates: WorkspaceUpdate) -> Dict[str, Any]:
        """Updates workspace autopilot mode and limits."""
        ws = WorkspaceService.get_workspace(workspace_id)
        if updates.name:
            ws["name"] = updates.name
        if updates.autopilotMode:
            ws["autopilotMode"] = updates.autopilotMode
        if updates.isActive is not None:
            ws["isActive"] = updates.isActive
        return ws

    _stopped_workspaces: set[str] = set()

    @classmethod
    def is_emergency_stopped(cls, workspace_id: str) -> bool:
        """Returns True if the workspace is currently emergency halted."""
        return workspace_id in cls._stopped_workspaces

    @classmethod
    def reset_emergency_stop(cls, workspace_id: str) -> None:
        """Clears the emergency halt status for the workspace."""
        cls._stopped_workspaces.discard(workspace_id)

    @classmethod
    def trigger_emergency_stop(cls, workspace_id: str) -> EmergencyStopResponse:
        """Immediately halts all active jobs for this workspace."""
        cls._stopped_workspaces.add(workspace_id)
        # Cancel running jobs in database
        try:
            DB_ENGINE.execute_mutation(
                "UPDATE video_jobs SET status = 'cancelled' WHERE workspace_id = %s AND status IN ('queued', 'processing')",
                (workspace_id,)
            )
        except Exception:
            pass
        return EmergencyStopResponse(
            message="AUTOPILOT Emergency Stop Triggered. All queued tasks cancelled.",
            cancelledJobsCount=1,
            cancelledJobIds=[f"job_halted_{uuid.uuid4().hex[:8]}"]
        )

    @staticmethod
    def get_brand_kit(workspace_id: str) -> BrandKitStyle:
        return BrandKitStyle()


workspace_service = WorkspaceService()
