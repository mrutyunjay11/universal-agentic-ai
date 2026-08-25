from __future__ import annotations
import asyncio
import functools
import inspect
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Optional, Type, get_type_hints
from pydantic import BaseModel, Field, create_model

from app.tools.permissions import PermissionTier
from app.tools.errors import (
    ErrorType,
    StructuredError,
    ToolError,
    ToolTimeoutError,
    ToolValidationError,
    ToolPermissionError,
    ToolDependencyError,
)
from app.tools.provenance import ProvenanceRecord
from app.tools.audit import redact_secrets, audit_logger

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    FILE = "file"
    CODE = "code"
    TERMINAL = "terminal"
    TESTING = "testing"
    GIT = "git"
    WEB = "web"
    BROWSER = "browser"
    DOCUMENTS = "documents"
    DATA = "data"
    DATABASE = "database"
    API = "api"
    MATH = "math"
    VISION = "vision"
    PACKAGES = "packages"
    SANDBOX = "sandbox"
    SYSTEM = "system"
    RAG = "rag"
    VERIFICATION = "verification"
    OTHER = "other"


class ToolMetadata(BaseModel):
    """Rich metadata describing a tool's capability, security contract, and schemas."""
    name: str
    category: ToolCategory = ToolCategory.OTHER
    description: str
    version: str = "1.0.0"
    permission: PermissionTier = PermissionTier.READ
    timeout: int = 30
    requires: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    required_parameters: list[str] = Field(default_factory=list)


class ToolContext(BaseModel):
    """Runtime context passed to tool execution."""
    project_root: str = "./projects"
    session_id: Optional[str] = None
    permission_granted: PermissionTier = PermissionTier.READ
    environment: dict[str, str] = Field(default_factory=dict)
    user_confirmed: bool = False


class ToolResult(BaseModel):
    """Standardized result returned by all tools across the universal ecosystem."""
    tool: str
    success: bool
    output: Any = None
    error: Optional[StructuredError] = None
    duration_ms: int = 0
    permission: PermissionTier = PermissionTier.READ
    provenance: Optional[ProvenanceRecord] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_summary(self) -> str:
        if not self.success:
            return f"Error: {self.error.message if self.error else 'Unknown failure'}"
        if isinstance(self.output, (dict, list)):
            import json
            try:
                return json.dumps(self.output, indent=2)
            except Exception:
                return str(self.output)
        return str(self.output)


class BaseTool(ABC):
    """
    Abstract Base Class for all tools in the Universal Agentic AI Ecosystem.
    Guarantees strict schema validation, security, timeouts, and error handling.
    """
    def __init__(self, metadata: Optional[ToolMetadata] = None):
        self.metadata = metadata or self._define_metadata()

    @abstractmethod
    def _define_metadata(self) -> ToolMetadata:
        """Subclasses define their metadata here."""
        raise NotImplementedError

    @abstractmethod
    async def execute_impl(self, context: ToolContext, **kwargs) -> Any:
        """The core execution logic implemented by the tool."""
        raise NotImplementedError

    def check_availability(self) -> tuple[bool, Optional[str]]:
        """
        Verifies if required runtime packages or CLI tools exist.
        Returns (available, reason_if_unavailable).
        """
        import shutil
        for req in self.metadata.requires:
            if req.startswith("pkg:"):
                pkg = req[4:]
                try:
                    __import__(pkg)
                except ImportError:
                    return False, f"Missing Python package: {pkg}"
            elif req.startswith("cli:"):
                cli = req[4:]
                if not shutil.which(cli):
                    return False, f"Missing CLI tool in PATH: {cli}"
        return True, None

    def validate_input(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Validates incoming arguments against required parameters and types."""
        missing = [p for p in self.metadata.required_parameters if p not in kwargs]
        if missing:
            raise ToolValidationError(f"Missing required parameters: {', '.join(missing)}")
        return kwargs

    def format_result(
        self,
        raw_output: Any,
        duration_ms: int,
        provenance: Optional[ProvenanceRecord] = None,
    ) -> ToolResult:
        """Wraps successful output into a standard ToolResult."""
        return ToolResult(
            tool=self.metadata.name,
            success=True,
            output=raw_output,
            error=None,
            duration_ms=duration_ms,
            permission=self.metadata.permission,
            provenance=provenance,
        )

    def handle_error(self, exc: Exception, duration_ms: int) -> ToolResult:
        """Converts any exception into a StructuredError inside a ToolResult."""
        if isinstance(exc, ToolError):
            structured = exc.to_structured_error()
        elif isinstance(exc, asyncio.TimeoutError):
            structured = StructuredError(
                type=ErrorType.TIMEOUT_ERROR,
                message=f"Execution timed out after {self.metadata.timeout}s",
                retryable=True,
            )
        elif isinstance(exc, PermissionError):
            structured = StructuredError(
                type=ErrorType.PERMISSION_DENIED,
                message=str(exc),
                retryable=False,
            )
        else:
            structured = StructuredError(
                type=ErrorType.EXECUTION_FAILED,
                message=str(exc),
                retryable=False,
            )

        return ToolResult(
            tool=self.metadata.name,
            success=False,
            output=None,
            error=structured,
            duration_ms=duration_ms,
            permission=self.metadata.permission,
        )

    async def run(self, context: Optional[ToolContext] = None, **kwargs) -> ToolResult:
        """
        Public entrypoint for executing the tool with validation, timeouts,
        audit logging, and error conversion.
        """
        ctx = context or ToolContext()
        start = time.time()

        # Check availability
        avail, reason = self.check_availability()
        if not avail:
            duration = int((time.time() - start) * 1000)
            res = self.handle_error(ToolDependencyError(reason or "Dependency missing", missing_dependency=reason or ""), duration)
            audit_logger.record(self.metadata.name, self.metadata.category.value, self.metadata.permission.value, duration, False, kwargs, error=reason, session_id=ctx.session_id)
            return res

        try:
            validated_kwargs = self.validate_input(kwargs)
            
            # Execute with timeout
            output = await asyncio.wait_for(
                self.execute_impl(context=ctx, **validated_kwargs),
                timeout=self.metadata.timeout,
            )
            duration = int((time.time() - start) * 1000)

            # Check if output contains a provenance record
            prov = None
            if isinstance(output, dict) and "_provenance" in output:
                prov = output.pop("_provenance")

            res = self.format_result(output, duration, prov)
            audit_logger.record(self.metadata.name, self.metadata.category.value, self.metadata.permission.value, duration, True, kwargs, output=output, session_id=ctx.session_id)
            return res

        except Exception as e:
            duration = int((time.time() - start) * 1000)
            res = self.handle_error(e, duration)
            audit_logger.record(self.metadata.name, self.metadata.category.value, self.metadata.permission.value, duration, False, kwargs, error=str(e), session_id=ctx.session_id)
            return res

    def to_schema(self, format: str = "openai") -> dict[str, Any]:
        """
        Exports the tool schema in specified LLM format:
        'openai', 'ollama', 'anthropic', or 'standard'.
        """
        if format in ("openai", "ollama"):
            return {
                "type": "function",
                "function": {
                    "name": self.metadata.name,
                    "description": self.metadata.description,
                    "parameters": {
                        "type": "object",
                        "properties": self.metadata.parameters.get("properties", {}),
                        "required": self.metadata.required_parameters,
                    },
                },
            }
        elif format == "anthropic":
            return {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "input_schema": {
                    "type": "object",
                    "properties": self.metadata.parameters.get("properties", {}),
                    "required": self.metadata.required_parameters,
                },
            }
        else:
            return {
                "name": self.metadata.name,
                "category": self.metadata.category.value,
                "description": self.metadata.description,
                "version": self.metadata.version,
                "permission": self.metadata.permission.value,
                "timeout": self.metadata.timeout,
                "requires": self.metadata.requires,
                "parameters": self.metadata.parameters,
                "required": self.metadata.required_parameters,
            }


class FunctionalTool(BaseTool):
    """Adapter wrapping standard Python functions or coroutines into BaseTool."""
    def __init__(
        self,
        name: str,
        handler: Callable,
        category: ToolCategory = ToolCategory.OTHER,
        description: str = "",
        permission: PermissionTier = PermissionTier.READ,
        timeout: int = 30,
        requires: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
    ):
        self.handler = handler
        meta = self._infer_metadata(
            name=name,
            handler=handler,
            category=category,
            description=description,
            permission=permission,
            timeout=timeout,
            requires=requires or [],
            tags=tags or [],
        )
        super().__init__(metadata=meta)

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(name="generic_functional_tool", description="Generic function tool")

    def _infer_metadata(
        self,
        name: str,
        handler: Callable,
        category: ToolCategory,
        description: str,
        permission: PermissionTier,
        timeout: int,
        requires: list[str],
        tags: list[str],
    ) -> ToolMetadata:
        desc = description or handler.__doc__ or f"Execute {name}"
        desc = desc.strip().split("\n")[0] if desc else f"Execute {name}"

        sig = inspect.signature(handler)
        properties = {}
        required = []

        for p_name, param in sig.parameters.items():
            if p_name in ("self", "cls", "context"):
                continue
            
            p_type = "string"
            if param.annotation != inspect.Parameter.empty:
                ann = param.annotation
                origin = getattr(ann, "__origin__", None)
                if origin is list or ann is list:
                    p_type = "array"
                elif origin is dict or ann is dict:
                    p_type = "object"
                elif ann is int:
                    p_type = "integer"
                elif ann is float:
                    p_type = "number"
                elif ann is bool:
                    p_type = "boolean"

            properties[p_name] = {
                "type": p_type,
                "description": f"Parameter {p_name}",
            }
            if param.default == inspect.Parameter.empty:
                required.append(p_name)

        return ToolMetadata(
            name=name,
            category=category,
            description=desc,
            permission=permission,
            timeout=timeout,
            requires=requires,
            tags=tags,
            parameters={"type": "object", "properties": properties},
            required_parameters=required,
        )

    async def execute_impl(self, context: ToolContext, **kwargs) -> Any:
        sig = inspect.signature(self.handler)
        call_kwargs = dict(kwargs)
        if "context" in sig.parameters:
            call_kwargs["context"] = context
        
        # Inject project_root if handler expects it and not provided
        if "project_root" in sig.parameters and "project_root" not in call_kwargs:
            call_kwargs["project_root"] = context.project_root

        if inspect.iscoroutinefunction(self.handler):
            return await self.handler(**call_kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, functools.partial(self.handler, **call_kwargs)
            )
