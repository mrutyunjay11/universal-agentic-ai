from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorType(str, Enum):
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    DEPENDENCY_MISSING = "dependency_missing"
    SECURITY_VIOLATION = "security_violation"
    EXECUTION_FAILED = "execution_failed"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    UNKNOWN_ERROR = "unknown_error"


class StructuredError(BaseModel):
    """
    Standardized, structured error format returned by all tools.
    Provides actionable metadata for self-correcting agent loops.
    """
    type: ErrorType = ErrorType.UNKNOWN_ERROR
    message: str
    retryable: bool = False
    details: Optional[dict[str, Any]] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "message": self.message,
            "retryable": self.retryable,
            "details": self.details or {},
        }


class ToolError(Exception):
    """Base exception for all tool runtime failures."""
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.EXECUTION_FAILED,
        retryable: bool = False,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.retryable = retryable
        self.details = details or {}

    def to_structured_error(self) -> StructuredError:
        return StructuredError(
            type=self.error_type,
            message=self.message,
            retryable=self.retryable,
            details=self.details,
        )


class ToolValidationError(ToolError):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, ErrorType.VALIDATION_ERROR, retryable=False, details=details)


class ToolTimeoutError(ToolError):
    def __init__(self, message: str, timeout_seconds: int = 30):
        super().__init__(message, ErrorType.TIMEOUT_ERROR, retryable=True, details={"timeout": timeout_seconds})


class ToolPermissionError(ToolError):
    def __init__(self, message: str, required_tier: str, granted_tier: str):
        super().__init__(
            message,
            ErrorType.PERMISSION_DENIED,
            retryable=False,
            details={"required_permission": required_tier, "granted_permission": granted_tier},
        )


class ToolDependencyError(ToolError):
    def __init__(self, message: str, missing_dependency: str):
        super().__init__(
            message,
            ErrorType.DEPENDENCY_MISSING,
            retryable=False,
            details={"missing_dependency": missing_dependency},
        )


class ToolSecurityError(ToolError):
    def __init__(self, message: str, violation_type: str):
        super().__init__(
            message,
            ErrorType.SECURITY_VIOLATION,
            retryable=False,
            details={"violation": violation_type},
        )
