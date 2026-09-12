r"""
backend/app/workers/celery_app.py — Celery + Redis Distributed Job Orchestrator
"""

import os
from typing import Any, Dict
from core.logbook import Logbook

log = Logbook("celery_app")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    from celery import Celery
    celery_app = Celery(
        "autopilot_tasks",
        broker=REDIS_URL,
        backend=REDIS_URL
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )
except ImportError:
    # Fallback dummy class if celery is not installed in current environment
    class DummyCelery:
        def __init__(self, *args, **kwargs):
            self.conf = {}
        def task(self, *args, **kwargs):
            def decorator(f):
                f.delay = f
                return f
            return decorator

    celery_app = DummyCelery()


@celery_app.task(name="render_video_job")
def render_video_job(job_id: str, video_id: str, workspace_id: str, dry_run: bool = True) -> Dict[str, Any]:
    """Celery task executing real pipeline agents and rendering."""
    from .pipeline_adapter import execute_real_pipeline
    log.info("Celery Worker picked up video render job", job_id=job_id, video_id=video_id, workspace_id=workspace_id)
    return execute_real_pipeline(
        job_id=job_id,
        video_id=video_id,
        workspace_id=workspace_id,
        dry_run=dry_run
    )
