from __future__ import annotations
import json
import os
import shutil
import subprocess
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError
from app.utils.security import enforce_project_root


@tool_registry.register(
    name="detect_project_type",
    category=ToolCategory.PACKAGES,
    description="Detect project type, package manager, and build system from repository files.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_detect_project_type(project_root: str = "./projects") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    types = []

    if os.path.exists(os.path.join(abs_root, "requirements.txt")) or os.path.exists(os.path.join(abs_root, "pyproject.toml")):
        types.append({"language": "python", "package_manager": "pip/uv/poetry"})
    if os.path.exists(os.path.join(abs_root, "package.json")):
        types.append({"language": "javascript/typescript", "package_manager": "npm/yarn/pnpm"})
    if os.path.exists(os.path.join(abs_root, "Cargo.toml")):
        types.append({"language": "rust", "package_manager": "cargo"})
    if os.path.exists(os.path.join(abs_root, "go.mod")):
        types.append({"language": "go", "package_manager": "go modules"})
    if os.path.exists(os.path.join(abs_root, "pom.xml")):
        types.append({"language": "java", "package_manager": "maven"})

    return {"project_root": project_root, "detected_types": types}


@tool_registry.register(
    name="list_dependencies",
    category=ToolCategory.PACKAGES,
    description="List all declared project dependencies and version constraints.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_list_dependencies(project_root: str = "./projects") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    deps = {}

    req_file = os.path.join(abs_root, "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file, "r", encoding="utf-8") as f:
            deps["python_requirements"] = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    pkg_file = os.path.join(abs_root, "package.json")
    if os.path.exists(pkg_file):
        with open(pkg_file, "r", encoding="utf-8") as f:
            pkg_data = json.load(f)
            deps["node_dependencies"] = pkg_data.get("dependencies", {})
            deps["node_dev_dependencies"] = pkg_data.get("devDependencies", {})

    return {"project_root": project_root, "dependencies": deps}


@tool_registry.register(
    name="check_dependencies",
    category=ToolCategory.PACKAGES,
    description="Verify if runtime CLI tools (python, node, git, cargo, docker) are installed and accessible in PATH.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_check_dependencies() -> dict[str, Any]:
    clis = ["python3", "python", "node", "npm", "npx", "git", "cargo", "go", "docker"]
    status = {}
    for c in clis:
        path = shutil.which(c)
        status[c] = {"installed": bool(path), "path": path}

    return {"tools": status}


@tool_registry.register(
    name="install_dependency",
    category=ToolCategory.PACKAGES,
    description="Install a package (pip install, npm install, cargo add). Requires EXECUTE/SYSTEM permission.",
    permission=PermissionTier.SYSTEM,
    timeout=120,
)
async def tool_install_dependency(package_name: str, package_manager: str = "pip", project_root: str = "./projects") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    cmd = []
    if package_manager in ("pip", "pip3"):
        cmd = ["pip", "install", package_name]
    elif package_manager == "npm":
        cmd = ["npm", "install", package_name]
    elif package_manager == "cargo":
        cmd = ["cargo", "add", package_name]
    elif package_manager == "go":
        cmd = ["go", "get", package_name]
    else:
        raise ToolValidationError(f"Unsupported package manager: {package_manager}")

    proc = subprocess.run(cmd, cwd=abs_root, capture_output=True, text=True, timeout=120)
    return {
        "package": package_name,
        "package_manager": package_manager,
        "success": proc.returncode == 0,
        "output": (proc.stdout + "\n" + proc.stderr).strip()[:2000],
    }


@tool_registry.register(
    name="remove_dependency",
    category=ToolCategory.PACKAGES,
    description="Uninstall/remove a package from project dependencies.",
    permission=PermissionTier.DESTRUCTIVE,
    timeout=60,
)
async def tool_remove_dependency(package_name: str, package_manager: str = "pip", project_root: str = "./projects") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    if package_manager in ("pip", "pip3"):
        cmd = ["pip", "uninstall", "-y", package_name]
    elif package_manager == "npm":
        cmd = ["npm", "uninstall", package_name]
    elif package_manager == "cargo":
        cmd = ["cargo", "remove", package_name]
    else:
        raise ToolValidationError(f"Unsupported package manager: {package_manager}")

    proc = subprocess.run(cmd, cwd=abs_root, capture_output=True, text=True, timeout=60)
    return {"package": package_name, "success": proc.returncode == 0, "output": proc.stdout or proc.stderr}


@tool_registry.register(
    name="update_dependency",
    category=ToolCategory.PACKAGES,
    description="Update a package dependency to its latest version.",
    permission=PermissionTier.EXECUTE,
    timeout=120,
)
async def tool_update_dependency(package_name: str, package_manager: str = "pip", project_root: str = "./projects") -> dict[str, Any]:
    return await tool_install_dependency(f"{package_name} --upgrade" if package_manager == "pip" else f"{package_name}@latest", package_manager, project_root)


@tool_registry.register(
    name="detect_runtime",
    category=ToolCategory.PACKAGES,
    description="Detect active runtime versions (Python version, Node version, OS architecture).",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_detect_runtime() -> dict[str, Any]:
    import platform
    import sys
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "executable": sys.executable,
    }


@tool_registry.register(
    name="check_environment",
    category=ToolCategory.PACKAGES,
    description="Check environment variables (with secret masking) and virtual environment status.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_check_environment() -> dict[str, Any]:
    import sys
    in_venv = sys.prefix != sys.base_prefix
    return {
        "in_virtual_environment": in_venv,
        "virtual_env_path": sys.prefix if in_venv else None,
        "path_entries_count": len(os.environ.get("PATH", "").split(":")),
    }
