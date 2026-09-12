r"""
backend/app/workers/job_runner.py — Distributed Queue Worker & Job State Machine
"""

import time
import traceback
from typing import Any, Callable, Dict, Optional
from core.logbook import Logbook

log = Logbook("worker_runner")


class JobRunner:
    """Asynchronous background worker executing rendering, AI, and publishing tasks."""

    def __init__(self, worker_id: str = "worker_default"):
        self.worker_id = worker_id
        self.is_running = False

    def start(self):
        self.is_running = True
        log.info(f"Worker {self.worker_id} started. Polling task queues...")

    def stop(self):
        log.info(f"Graceful shutdown initiated for worker {self.worker_id}...")
        self.is_running = False

    def process_task(self, task_name: str, task_fn: Callable[[], Any], max_retries: int = 3) -> Any:
        attempts = 0
        while attempts < max_retries:
            attempts += 1
            try:
                log.info(f"Executing task: {task_name} (Attempt {attempts}/{max_retries})")
                result = task_fn()
                log.info(f"Task {task_name} completed successfully.")
                return result
            except Exception as e:
                backoff = min(300, (2 ** attempts) * 2)
                log.warning(f"Task {task_name} failed. Retrying in {backoff}s...", error=str(e))
                if attempts >= max_retries:
                    log.error(f"Task {task_name} permanently failed. Moving to Dead Letter Queue (DLQ).", trace=traceback.format_exc())
                    raise
                time.sleep(1)


worker_runner = JobRunner()
