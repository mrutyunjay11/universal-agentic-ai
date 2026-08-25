from __future__ import annotations
import asyncio
import importlib
import logging
import os
import pkgutil
import time
from typing import Any, Callable, Optional

from app.tools.base import (
    BaseTool,
    FunctionalTool,
    ToolCategory,
    ToolContext,
    ToolMetadata,
    ToolResult,
)
from app.tools.permissions import PermissionTier, check_permission, requires_human_approval
from app.tools.errors import (
    ErrorType,
    StructuredError,
    ToolError,
    ToolPermissionError,
    ToolValidationError,
)
from app.tools.audit import audit_logger

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central Registry for the Universal Agentic AI Tool Ecosystem.
    Manages discovery, schema generation, permission gating, health diagnostics,
    and reliable execution.
    """
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._callbacks: list[Callable[[ToolResult], None]] = []

    @property
    def tools(self) -> dict[str, BaseTool]:
        return self._tools

    def register(
        self,
        name: Optional[str] = None,
        category: ToolCategory = ToolCategory.OTHER,
        description: Optional[str] = None,
        permission: PermissionTier = PermissionTier.READ,
        timeout: int = 30,
        requires: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
    ) -> Callable:
        """
        Decorator or direct registration helper for registering tools.
        Supports both function handlers and BaseTool instances.
        """
        def decorator(handler: Callable | BaseTool) -> Callable | BaseTool:
            if isinstance(handler, BaseTool):
                tool_instance = handler
                tool_name = name or tool_instance.metadata.name
                self._tools[tool_name] = tool_instance
                logger.info("Registered BaseTool: %s [%s] (%s)", tool_name, tool_instance.metadata.category.value, tool_instance.metadata.permission.value)
                return handler

            tool_name = name or handler.__name__
            if tool_name.startswith("tool_"):
                tool_name = tool_name[5:]

            tool_instance = FunctionalTool(
                name=tool_name,
                handler=handler,
                category=category,
                description=description or handler.__doc__ or "",
                permission=permission,
                timeout=timeout,
                requires=requires or [],
                tags=tags or [],
            )
            self._tools[tool_name] = tool_instance
            logger.info(
                "Registered tool: %s [%s] (permission: %s)",
                tool_name,
                category.value,
                permission.value,
            )
            return handler

        return decorator

    def register_tool(self, tool: BaseTool):
        """Directly registers an instance of BaseTool."""
        self._tools[tool.metadata.name] = tool
        logger.info(
            "Registered BaseTool instance: %s [%s]",
            tool.metadata.name,
            tool.metadata.category.value,
        )

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Convenience alias for get()."""
        return self.get(name)

    def list_tools(self, category: Optional[ToolCategory] = None) -> list[BaseTool]:
        if category:
            return [t for t in self._tools.values() if t.metadata.category == category]
        return list(self._tools.values())

    def get_tool_names(self) -> set[str]:
        return set(self._tools.keys())

    def get_schemas(self, format: str = "openai", category: Optional[ToolCategory] = None) -> list[dict[str, Any]]:
        tools = self.list_tools(category)
        return [t.to_schema(format=format) for t in tools]

    def health_check(self) -> dict[str, Any]:
        """
        Evaluates the health and availability status of all registered tools.
        """
        total = len(self._tools)
        available = 0
        unavailable = 0
        categories: dict[str, int] = {}
        missing_deps: dict[str, list[str]] = {}
        tool_status: dict[str, dict[str, Any]] = {}

        for name, tool in self._tools.items():
            cat = tool.metadata.category.value
            categories[cat] = categories.get(cat, 0) + 1

            is_avail, reason = tool.check_availability()
            if is_avail:
                available += 1
                tool_status[name] = {"status": "available", "permission": tool.metadata.permission.value, "category": cat}
            else:
                unavailable += 1
                missing_deps[name] = [reason or "Unknown dependency missing"]
                tool_status[name] = {
                    "status": "unavailable",
                    "reason": reason,
                    "permission": tool.metadata.permission.value,
                    "category": cat,
                }

        return {
            "total_tools": total,
            "available_tools": available,
            "unavailable_tools": unavailable,
            "categories": categories,
            "missing_dependencies": missing_deps,
            "tools": tool_status,
        }

    async def execute(
        self,
        tool_name: str,
        args: dict[str, Any],
        context: Optional[ToolContext] = None,
    ) -> ToolResult:
        """
        Executes a registered tool through the security, permission, validation,
        and auditing pipeline.
        """
        ctx = context or ToolContext()
        tool = self._tools.get(tool_name)

        if not tool:
            err = StructuredError(
                type=ErrorType.NOT_FOUND,
                message=f"Unknown tool: '{tool_name}'. Available: {sorted(self._tools.keys())}",
                retryable=False,
            )
            return ToolResult(
                tool=tool_name,
                success=False,
                output=None,
                error=err,
                permission=PermissionTier.READ,
            )

        # Enforce permission check
        if not check_permission(tool.metadata.permission, ctx.permission_granted):
            err = StructuredError(
                type=ErrorType.PERMISSION_DENIED,
                message=(
                    f"Permission denied: tool '{tool_name}' requires '{tool.metadata.permission.value}' permission, "
                    f"but session only has '{ctx.permission_granted.value}' granted."
                ),
                retryable=False,
                details={
                    "required_permission": tool.metadata.permission.value,
                    "granted_permission": ctx.permission_granted.value,
                },
            )
            return ToolResult(
                tool=tool_name,
                success=False,
                output=None,
                error=err,
                permission=tool.metadata.permission,
            )

        # Run tool
        result = await tool.run(context=ctx, **args)
        self._notify_callbacks(result)
        return result

    async def execute_with_retry(
        self,
        tool_name: str,
        args: dict[str, Any],
        context: Optional[ToolContext] = None,
        max_retries: int = 3,
    ) -> ToolResult:
        """Executes a tool with automatic retries on retryable errors."""
        last_result = None
        for attempt in range(1, max_retries + 1):
            result = await self.execute(tool_name, args, context)
            if result.success:
                return result
            
            last_result = result
            # Only retry if error is flagged as retryable
            if result.error and result.error.retryable and attempt < max_retries:
                logger.info("Retrying tool '%s' (attempt %d/%d)", tool_name, attempt + 1, max_retries)
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
            else:
                break

        return last_result or await self.execute(tool_name, args, context)

    def on_tool_call(self, callback: Callable[[ToolResult], None]):
        self._callbacks.append(callback)

    def _notify_callbacks(self, result: ToolResult):
        for cb in self._callbacks:
            try:
                cb(result)
            except Exception as e:
                logger.warning("Error in tool registry callback: %s", e)

    async def discover_tools(self, base_package: str = "app.tools"):
        """
        Dynamically and recursively discovers and imports all tool modules.
        """
        logger.info("Discovering tools from package: %s", base_package)
        try:
            package = importlib.import_module(base_package)
        except ImportError as e:
            logger.error("Failed to import tool base package %s: %s", base_package, e)
            return

        if not hasattr(package, "__path__"):
            return

        for _, modname, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            if modname in ("app.tools.base", "app.tools.registry", "app.tools.permissions", "app.tools.errors", "app.tools.audit", "app.tools.provenance"):
                continue
            try:
                importlib.import_module(modname)
                logger.debug("Imported tool module: %s", modname)
            except Exception as e:
                logger.warning("Failed to auto-import module %s: %s", modname, e)


# Global singleton tool registry
tool_registry = ToolRegistry()
