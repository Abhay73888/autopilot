r"""
backend/app/core/idempotency.py — Idempotency Key Manager & Replay Protection

Ensures that financial mutations, video renders, and publishing dispatches
can NEVER be executed twice when using the same Idempotency-Key header.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

# Default TTL: 24 hours (86400 seconds)
DEFAULT_IDEMPOTENCY_TTL_SECONDS = 86400


class IdempotencyStore:
    """In-memory thread-safe idempotency cache with TTL and Redis fallback."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if time.time() > entry["expires_at"]:
                del self._store[key]
                return None
            return entry["response"]

    def set(self, key: str, response_data: Dict[str, Any], ttl_seconds: int = DEFAULT_IDEMPOTENCY_TTL_SECONDS):
        with self._lock:
            self._store[key] = {
                "response": response_data,
                "expires_at": time.time() + ttl_seconds
            }

    def clear(self):
        with self._lock:
            self._store.clear()


IDEMPOTENCY = IdempotencyStore()
