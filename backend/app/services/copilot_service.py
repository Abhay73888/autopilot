r"""
backend/app/services/copilot_service.py — Guardrailed Natural Language Action Dispatcher
"""

import uuid
from typing import Any, Dict
from ..schemas.copilot import CopilotActionPlan, CopilotExecuteRequest


class CopilotService:
    @staticmethod
    def process_command(workspace_id: str, request: CopilotExecuteRequest) -> CopilotActionPlan:
        cmd = request.command.lower()
        if "pause" in cmd or "stop" in cmd:
            return CopilotActionPlan(
                intent="PAUSE_AUTOPILOT",
                summary="Pause all active generation and publishing workflows for this workspace.",
                parameters={"action": "pause"},
                requiresApproval=True,
                estimatedCredits=0,
                confirmationToken=f"tok_{uuid.uuid4().hex[:12]}"
            )
        elif "analytics" in cmd or "hook" in cmd or "performance" in cmd:
            return CopilotActionPlan(
                intent="SHOW_ANALYTICS",
                summary="Retrieve top-performing hooks and retention curves across your published videos.",
                parameters={"timeframe": "30d", "metric": "retention"},
                requiresApproval=False,
                estimatedCredits=0
            )
        elif "mystery" in cmd or "video" in cmd or "short" in cmd or "create" in cmd:
            return CopilotActionPlan(
                intent="BATCH_CREATE_VIDEOS",
                summary="Research, write scripts, synthesize voice, and render 3 new short-form videos.",
                parameters={"quantity": 3, "topic": "Tech Mysteries & AI", "targetDurationSeconds": 45},
                requiresApproval=True,
                estimatedCredits=30,
                confirmationToken=f"tok_{uuid.uuid4().hex[:12]}"
            )
        else:
            return CopilotActionPlan(
                intent="EXPLORE_CONTENT_STRATEGY",
                summary="Analyze active campaign niche and propose 5 high-velocity content angles.",
                parameters={"action": "recommend_strategy"},
                requiresApproval=False,
                estimatedCredits=1
            )


copilot_service = CopilotService()
