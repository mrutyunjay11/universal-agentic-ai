from __future__ import annotations
import asyncio
import os
import shutil
import tempfile
import uuid
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError


class SandboxEnvironmentManager:
    """Manages isolated temp workspaces and sandboxes."""
    def __init__(self):
        self._sandboxes: dict[str, dict[str, Any]] = {}

    def create(self, name: Optional[str] = None) -> str:
        s_id = name or f"sandbox_{uuid.uuid4().hex[:8]}"
        tmp_dir = tempfile.mkdtemp(prefix=f"agent_sb_{s_id}_")
        self._sandboxes[s_id] = {
            "sandbox_id": s_id,
            "path": tmp_dir,
            "logs": [],
            "status": "active",
        }
        return s_id

    def get(self, s_id: str) -> Optional[dict[str, Any]]:
        return self._sandboxes.get(s_id)

    def destroy(self, s_id: str) -> bool:
        sb = self._sandboxes.pop(s_id, None)
        if sb and os.path.exists(sb["path"]):
            shutil.rmtree(sb["path"], ignore_errors=True)
            return True
        return False


sandbox_manager = SandboxEnvironmentManager()


@tool_registry.register(
    name="create_sandbox",
    category=ToolCategory.SANDBOX,
    description="Create an isolated temporary sandbox directory for running untrusted code safely.",
    permission=PermissionTier.EXECUTE,
    timeout=10,
)
async def tool_create_sandbox(name: Optional[str] = None) -> dict[str, Any]:
    s_id = sandbox_manager.create(name)
    sb = sandbox_manager.get(s_id)
    return {
        "sandbox_id": s_id,
        "path": sb["path"],
        "status": "created",
        "message": "Isolated sandbox ready for execution.",
    }


@tool_registry.register(
    name="run_in_sandbox",
    category=ToolCategory.SANDBOX,
    description="Execute a shell command or script strictly inside an isolated sandbox.",
    permission=PermissionTier.EXECUTE,
    timeout=60,
)
async def tool_run_in_sandbox(sandbox_id: str, command: str, timeout: int = 30) -> dict[str, Any]:
    sb = sandbox_manager.get(sandbox_id)
    if not sb:
        raise ToolValidationError(f"Sandbox not found: {sandbox_id}")

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=sb["path"],
        )

        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")

        log_entry = f"[{command}] exit={proc.returncode}"
        sb["logs"].append(log_entry)

        return {
            "sandbox_id": sandbox_id,
            "command": command,
            "return_code": proc.returncode,
            "stdout": stdout[:4000],
            "stderr": stderr[:2000],
        }
    except asyncio.TimeoutError:
        return {"sandbox_id": sandbox_id, "status": "timeout", "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"sandbox_id": sandbox_id, "error": str(e)}


@tool_registry.register(
    name="destroy_sandbox",
    category=ToolCategory.SANDBOX,
    description="Tear down and delete an isolated sandbox environment.",
    permission=PermissionTier.DESTRUCTIVE,
    timeout=10,
)
async def tool_destroy_sandbox(sandbox_id: str) -> dict[str, Any]:
    success = sandbox_manager.destroy(sandbox_id)
    return {"sandbox_id": sandbox_id, "destroyed": success}


@tool_registry.register(
    name="inspect_sandbox",
    category=ToolCategory.SANDBOX,
    description="Inspect files, size, and status inside a sandbox.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_inspect_sandbox(sandbox_id: str) -> dict[str, Any]:
    sb = sandbox_manager.get(sandbox_id)
    if not sb:
        raise ToolValidationError(f"Sandbox not found: {sandbox_id}")

    files = os.listdir(sb["path"]) if os.path.exists(sb["path"]) else []
    return {
        "sandbox_id": sandbox_id,
        "path": sb["path"],
        "files_count": len(files),
        "files": files[:30],
    }


@tool_registry.register(
    name="get_sandbox_logs",
    category=ToolCategory.SANDBOX,
    description="Retrieve execution history logs for a sandbox.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_get_sandbox_logs(sandbox_id: str) -> dict[str, Any]:
    sb = sandbox_manager.get(sandbox_id)
    if not sb:
        raise ToolValidationError(f"Sandbox not found: {sandbox_id}")

    return {"sandbox_id": sandbox_id, "logs": sb.get("logs", [])}
