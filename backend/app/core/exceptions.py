r"""
backend/app/core/exceptions.py — Standardized Error Hierarchy
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with error code and envelope metadata."""
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication required or token expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=message
        )


class TenantAccessDeniedException(AppException):
    def __init__(self, message: str = "Access to requested workspace or tenant resource is denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="TENANT_ACCESS_DENIED",
            message=message
        )


class ResourceNotFoundException(AppException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=f"{resource_type} with ID '{resource_id}' was not found"
        )


class InsufficientCreditsException(AppException):
    def __init__(self, required: int, current: int):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            code="INSUFFICIENT_CREDITS",
            message=f"Operation requires {required} credits, but workspace only has {current} available.",
            details={"requiredCredits": required, "availableCredits": current}
        )


class AutopilotBudgetExceededException(AppException):
    def __init__(self, message: str = "Workspace daily video quota or monthly budget limit reached"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="BUDGET_LIMIT_EXCEEDED",
            message=message
        )
