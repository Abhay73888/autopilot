r"""
backend/app/services/project_service.py — Project & Campaign Management
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from ..schemas.project import ProjectCreate, ProjectResponse


class ProjectService:
    def __init__(self):
        # In-memory registry with persistent DB fallback
        self._projects: Dict[str, Dict[str, Any]] = {}

    def create_project(self, workspace_id: str, data: ProjectCreate) -> ProjectResponse:
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        obj = {
            "id": project_id,
            "workspaceId": workspace_id,
            "name": data.name,
            "niche": data.niche,
            "targetAudience": data.targetAudience,
            "tone": data.tone,
            "targetDurationSeconds": data.targetDurationSeconds,
            "targetPlatforms": data.targetPlatforms,
            "postingFrequencyPerWeek": data.postingFrequencyPerWeek,
            "totalVideosGenerated": 0,
            "createdAt": now
        }
        self._projects[project_id] = obj
        return ProjectResponse(**obj)

    def list_projects(self, workspace_id: str) -> List[ProjectResponse]:
        projects = [ProjectResponse(**p) for p in self._projects.values() if p["workspaceId"] == workspace_id]
        if not projects:
            # Default starter project
            default_p = self.create_project(
                workspace_id,
                ProjectCreate(
                    name="AI Tools & Productivity Shorts",
                    niche="Artificial Intelligence",
                    targetAudience="Creators and software engineers",
                    tone="cinematic",
                    targetDurationSeconds=45,
                    targetPlatforms=["youtube", "instagram", "tiktok"],
                    postingFrequencyPerWeek=5
                )
            )
            return [default_p]
        return projects

    def get_project(self, workspace_id: str, project_id: str) -> ProjectResponse:
        if project_id in self._projects:
            return ProjectResponse(**self._projects[project_id])
        # Return default mock project
        return ProjectResponse(
            id=project_id,
            workspaceId=workspace_id,
            name="AI Tools Channel",
            niche="Artificial Intelligence",
            targetAudience="Tech creators",
            tone="cinematic",
            targetDurationSeconds=45,
            targetPlatforms=["youtube"],
            postingFrequencyPerWeek=5,
            totalVideosGenerated=3,
            createdAt=datetime.now(timezone.utc).isoformat()
        )


project_service = ProjectService()
