r"""
backend/app/core/logging.py — Structured JSON Logging with Request Tracing
"""

import contextvars
import json
import logging
import sys
import time
from typing import Any, Dict, Optional

# Context variable for request ID tracing across asynchronous calls
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)
workspace_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("workspace_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "requestId": request_id_ctx.get(),
            "workspaceId": workspace_id_ctx.get(),
        }
        if hasattr(record, "extra_data"):
            log_obj["data"] = record.extra_data
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logger(name: str = "autopilot") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger


api_logger = setup_logger("autopilot.api")
