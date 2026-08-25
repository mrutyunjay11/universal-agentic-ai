from __future__ import annotations
import asyncio
import os
import signal
import uuid
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError, ToolTimeoutError
from app.utils.security import validate_command, enforce_project_root


class ProcessManager:
    """Manages active background processes and output streams."""
    def __init__(self):
        self._processes: dict[str, dict[str, Any]] = {}

    def register_process(self, process_id: str, proc: asyncio.subprocess.Process, command: str, cwd: str):
        self._processes[process_id] = {
            "process_id": process_id,
            "proc": proc,
            "command": command,
            "cwd": cwd,
            "output": [],
            "status": "running",
            "return_code": None,
        }

    def get_process(self, process_id: str) -> Optional[dict[str, Any]]:
        return self._processes.get(process_id)

    def list_all(self) -> list[dict[str, Any]]:
        summary = []
        for pid, p in list(self._processes.items()):
            proc: asyncio.subprocess.Process = p["proc"]
            is_running = proc.returncode is None
            summary.append({
                "process_id": pid,
                "command": p["command"],
                "status": "running" if is_running else "finished",
                "return_code": proc.returncode,
                "cwd": p["cwd"],
            })
        return summary

    async def kill(self, process_id: str) -> bool:
        p = self._processes.get(process_id)
        if not p:
            return False
        proc: asyncio.subprocess.Process = p["proc"]
        if proc.returncode is None:
            try:
                proc.send_signal(signal.SIGTERM)
                await asyncio.sleep(0.5)
                if proc.returncode is None:
                    proc.kill()
            except ProcessLookupError:
                pass
        p["status"] = "killed"
        return True


process_manager = ProcessManager()


@tool_registry.register(
    name="execute_terminal",
    category=ToolCategory.TERMINAL,
    description="Execute a shell command with security validation, timeouts, and stdout/stderr capture.",
    permission=PermissionTier.EXECUTE,
    timeout=60,
)
async def tool_execute_terminal(
    command: str,
    project_root: str = "./projects",
    timeout: int = 30,
    env_vars: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    val = validate_command(command)
    if not val["allowed"]:
        raise ToolSecurityError(val["reason"] or "Command rejected by security policy", "command_denied")

    abs_root = enforce_project_root(".", project_root)
    if not abs_root:
        raise ToolSecurityError("Project root access denied", "path_traversal")
    os.makedirs(abs_root, exist_ok=True)

    env = {**os.environ, "DEBIAN_FRONTEND": "noninteractive"}
    if env_vars:
        env.update(env_vars)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=abs_root,
            env=env,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        return {
            "command": command,
            "return_code": proc.returncode,
            "status": "success" if proc.returncode == 0 else "failed",
            "stdout": stdout[:8000],
            "stderr": stderr[:4000],
        }

    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        raise ToolTimeoutError(f"Command timed out after {timeout} seconds: {command[:80]}", timeout)
    except (ToolSecurityError, ToolTimeoutError, ToolValidationError):
        raise
    except Exception as e:
        raise ToolValidationError(f"Execution error: {e}")


@tool_registry.register(
    name="run_background_process",
    category=ToolCategory.TERMINAL,
    description="Start a long-running background process (e.g. dev server, build watcher) and return a process ID.",
    permission=PermissionTier.EXECUTE,
    timeout=10,
)
async def tool_run_background_process(command: str, project_root: str = "./projects") -> dict[str, Any]:
    val = validate_command(command)
    if not val["allowed"]:
        raise ToolSecurityError(val["reason"] or "Command rejected", "command_denied")

    abs_root = enforce_project_root(".", project_root)
    if not abs_root:
        raise ToolSecurityError("Path denied", "path_traversal")
    os.makedirs(abs_root, exist_ok=True)

    proc_id = f"proc_{uuid.uuid4().hex[:8]}"
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=abs_root,
    )

    process_manager.register_process(proc_id, proc, command, abs_root)
    return {
        "process_id": proc_id,
        "command": command,
        "status": "started",
        "message": f"Background process started with ID {proc_id}",
    }


@tool_registry.register(
    name="get_process_status",
    category=ToolCategory.TERMINAL,
    description="Check the execution status, exit code, and liveness of a background process.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_get_process_status(process_id: str) -> dict[str, Any]:
    p = process_manager.get_process(process_id)
    if not p:
        raise ToolValidationError(f"Process ID not found: {process_id}")

    proc: asyncio.subprocess.Process = p["proc"]
    is_running = proc.returncode is None

    return {
        "process_id": process_id,
        "command": p["command"],
        "status": "running" if is_running else "finished",
        "return_code": proc.returncode,
    }


@tool_registry.register(
    name="list_processes",
    category=ToolCategory.TERMINAL,
    description="List all active and recent background processes managed by the agent.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_list_processes() -> dict[str, Any]:
    processes = process_manager.list_all()
    return {"total_processes": len(processes), "processes": processes}


@tool_registry.register(
    name="kill_process",
    category=ToolCategory.TERMINAL,
    description="Terminate or kill an active background process by process ID.",
    permission=PermissionTier.SYSTEM,
    timeout=10,
)
async def tool_kill_process(process_id: str) -> dict[str, Any]:
    success = await process_manager.kill(process_id)
    if not success:
        raise ToolValidationError(f"Could not kill process (not found or already terminated): {process_id}")

    return {"process_id": process_id, "status": "terminated"}


@tool_registry.register(
    name="read_process_output",
    category=ToolCategory.TERMINAL,
    description="Read recent stdout/stderr output lines from a background process.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_read_process_output(process_id: str, max_lines: int = 50) -> dict[str, Any]:
    p = process_manager.get_process(process_id)
    if not p:
        raise ToolValidationError(f"Process ID not found: {process_id}")

    # Read pending stdout non-blockingly
    proc: asyncio.subprocess.Process = p["proc"]
    lines = []
    if proc.stdout and not proc.stdout.at_eof():
        try:
            while len(lines) < max_lines:
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=0.2)
                if not line:
                    break
                lines.append(line.decode("utf-8", errors="replace").rstrip("\n"))
        except asyncio.TimeoutError:
            pass

    return {
        "process_id": process_id,
        "lines_read": len(lines),
        "output": "\n".join(lines),
    }


@tool_registry.register(
    name="send_process_input",
    category=ToolCategory.TERMINAL,
    description="Send a string to the standard input (stdin) of a running background process.",
    permission=PermissionTier.EXECUTE,
    timeout=5,
)
async def tool_send_process_input(process_id: str, input_text: str) -> dict[str, Any]:
    p = process_manager.get_process(process_id)
    if not p:
        raise ToolValidationError(f"Process ID not found: {process_id}")

    proc: asyncio.subprocess.Process = p["proc"]
    if proc.stdin and not proc.stdin.is_closing():
        proc.stdin.write(input_text.encode("utf-8") + b"\n")
        await proc.stdin.drain()
        return {"process_id": process_id, "bytes_sent": len(input_text), "status": "sent"}

    raise ToolValidationError(f"Process stdin is not open or available for {process_id}")
