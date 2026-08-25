from __future__ import annotations
from app.tools.base import (
    BaseTool,
    FunctionalTool,
    ToolCategory,
    ToolContext,
    ToolMetadata,
    ToolResult,
)
from app.tools.permissions import PermissionTier, check_permission
from app.tools.errors import (
    ErrorType,
    StructuredError,
    ToolError,
    ToolTimeoutError,
    ToolValidationError,
    ToolPermissionError,
    ToolDependencyError,
    ToolSecurityError,
)
from app.tools.provenance import (
    ProvenanceRecord,
    SourceType,
    create_provenance,
    compute_content_hash,
)
from app.tools.audit import audit_logger, redact_secrets, AuditEvent
from app.tools.registry import tool_registry

# Import all tool domains to trigger automatic registration
import app.tools.file
import app.tools.code
import app.tools.terminal
import app.tools.testing
import app.tools.git
import app.tools.web
import app.tools.browser
import app.tools.documents
import app.tools.data
import app.tools.database
import app.tools.api
import app.tools.math
import app.tools.vision
import app.tools.packages
import app.tools.sandbox
import app.tools.system
import app.tools.rag
import app.tools.verification

__all__ = [
    "BaseTool",
    "FunctionalTool",
    "ToolCategory",
    "ToolContext",
    "ToolMetadata",
    "ToolResult",
    "PermissionTier",
    "check_permission",
    "ErrorType",
    "StructuredError",
    "ToolError",
    "ToolTimeoutError",
    "ToolValidationError",
    "ToolPermissionError",
    "ToolDependencyError",
    "ToolSecurityError",
    "ProvenanceRecord",
    "SourceType",
    "create_provenance",
    "compute_content_hash",
    "audit_logger",
    "redact_secrets",
    "AuditEvent",
    "tool_registry",
]
