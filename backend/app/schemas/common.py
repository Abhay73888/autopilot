r"""
backend/app/schemas/common.py — Standard API Response Envelope
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class MetaInfo(BaseModel):
    requestId: Optional[str] = None
    timestamp: Optional[str] = None
    total: Optional[int] = None
    page: Optional[int] = None
    limit: Optional[int] = None


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[ErrorPayload] = None
    meta: Optional[MetaInfo] = None
