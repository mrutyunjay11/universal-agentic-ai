from __future__ import annotations
import os
import platform
import sys
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.audit import redact_secrets
from app.utils.security import enforce_project_root


@tool_registry.register(
    name="get_system_info",
    category=ToolCategory.SYSTEM,
    description="Get comprehensive system diagnostic information (OS, CPU, RAM, Python version, platform).",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_get_system_info() -> dict[str, Any]:
    info = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }
    try:
        import psutil
        mem = psutil.virtual_memory()
        info["memory"] = {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "used_pct": mem.percent,
        }
        info["cpu_percent"] = psutil.cpu_percent(interval=0.05)
    except ImportError:
        pass

    return info


@tool_registry.register(
    name="get_os_info",
    category=ToolCategory.SYSTEM,
    description="Get operating system, kernel version, and architecture details.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_get_os_info() -> dict[str, Any]:
    return {
        "os_name": os.name,
        "platform": platform.system(),
        "version": platform.version(),
        "architecture": platform.architecture()[0],
    }


@tool_registry.register(
    name="get_cpu_info",
    category=ToolCategory.SYSTEM,
    description="Get CPU core count, processor model, and current CPU utilization.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_get_cpu_info() -> dict[str, Any]:
    cpu_data = {
        "cores": os.cpu_count(),
        "processor": platform.processor(),
    }
    try:
        import psutil
        cpu_data["utilization_percent"] = psutil.cpu_percent(interval=0.1)
    except ImportError:
        pass
    return cpu_data


@tool_registry.register(
    name="get_memory_info",
    category=ToolCategory.SYSTEM,
    description="Get total, available, and used RAM/Swap memory stats.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_get_memory_info() -> dict[str, Any]:
    try:
        import psutil
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "ram_total_mb": round(mem.total / (1024 ** 2), 1),
            "ram_available_mb": round(mem.available / (1024 ** 2), 1),
            "ram_used_percent": mem.percent,
            "swap_total_mb": round(swap.total / (1024 ** 2), 1),
            "swap_used_percent": swap.percent,
        }
    except ImportError:
        return {"message": "psutil not available for granular memory stats"}


@tool_registry.register(
    name="get_gpu_info",
    category=ToolCategory.SYSTEM,
    description="Check for GPU acceleration (Apple Silicon Metal / NVIDIA CUDA / ROCm).",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_get_gpu_info() -> dict[str, Any]:
    gpu_data = {"available": False, "type": "none"}
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        gpu_data = {"available": True, "type": "Apple Silicon (MPS/Metal)", "device": "Apple M-Series"}
    else:
        try:
            import torch
            if torch.cuda.is_available():
                gpu_data = {
                    "available": True,
                    "type": "NVIDIA CUDA",
                    "device_name": torch.cuda.get_device_name(0),
                    "device_count": torch.cuda.device_count(),
                }
        except ImportError:
            pass
    return gpu_data


@tool_registry.register(
    name="get_disk_info",
    category=ToolCategory.SYSTEM,
    description="Get disk space usage for project volume.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_get_disk_info(project_root: str = "./projects") -> dict[str, Any]:
    import shutil
    total, used, free = shutil.disk_usage(os.path.abspath(project_root))
    return {
        "total_gb": round(total / (1024 ** 3), 2),
        "used_gb": round(used / (1024 ** 3), 2),
        "free_gb": round(free / (1024 ** 3), 2),
        "used_pct": round((used / total) * 100, 1),
    }


@tool_registry.register(
    name="get_project_structure",
    category=ToolCategory.SYSTEM,
    description="Render a hierarchical tree representation of the workspace directory structure.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_get_project_structure(project_root: str = "./projects", max_depth: int = 3) -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    if not abs_root:
        return {"tree": "Access denied"}

    lines = []
    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", ".agent-backups")]
        level = root.replace(abs_root, "").count(os.sep)
        if level > max_depth:
            continue
        indent = "  " * level
        lines.append(f"{indent}{os.path.basename(root) or '.'}/")
        subindent = "  " * (level + 1)
        for f in files:
            if not f.startswith("."):
                lines.append(f"{subindent}{f}")

    return {"project_root": project_root, "tree": "\n".join(lines[:100])}


@tool_registry.register(
    name="check_runtime",
    category=ToolCategory.SYSTEM,
    description="Check Python interpreter path, version, and loaded C modules.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_check_runtime() -> dict[str, Any]:
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "byte_order": sys.byteorder,
    }


@tool_registry.register(
    name="check_environment_variables",
    category=ToolCategory.SYSTEM,
    description="List active environment variable keys with secret values automatically redacted.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_check_environment_variables() -> dict[str, Any]:
    sanitized_env = redact_secrets(dict(os.environ))
    return {
        "env_keys_count": len(sanitized_env),
        "variables": sanitized_env,
    }
