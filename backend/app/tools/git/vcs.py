from __future__ import annotations
import os
import subprocess
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError
from app.utils.security import enforce_project_root


def _run_git(args: list[str], project_root: str) -> tuple[int, str, str]:
    abs_root = enforce_project_root(".", project_root)
    if not abs_root:
        return -1, "", "Access to project root denied"
    try:
        proc = subprocess.run(["git"] + args, cwd=abs_root, capture_output=True, text=True, timeout=15)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return -1, "", "Git is not installed on system"
    except Exception as e:
        return -1, "", str(e)


@tool_registry.register(
    name="git_status",
    category=ToolCategory.GIT,
    description="Show git working tree status (untracked, modified, staged files).",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_git_status(project_root: str = "./projects") -> dict[str, Any]:
    code, stdout, stderr = _run_git(["status", "--short"], project_root)
    if code != 0:
        return {"status": "error", "message": stderr or "Not a git repository"}

    files = []
    for line in stdout.strip().split("\n"):
        if line.strip():
            state = line[:2].strip()
            filename = line[3:].strip()
            files.append({"state": state, "file": filename})

    return {"status": "clean" if not files else "dirty", "changed_files_count": len(files), "files": files}


@tool_registry.register(
    name="git_diff",
    category=ToolCategory.GIT,
    description="Show working tree diff (staged or unstaged changes).",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_git_diff(project_root: str = "./projects", staged: bool = False) -> dict[str, Any]:
    args = ["diff", "--cached"] if staged else ["diff"]
    code, stdout, stderr = _run_git(args, project_root)
    return {"staged": staged, "diff": stdout[:8000], "error": stderr if code != 0 else None}


@tool_registry.register(
    name="git_log",
    category=ToolCategory.GIT,
    description="Show recent git commit history.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_git_log(project_root: str = "./projects", count: int = 10) -> dict[str, Any]:
    code, stdout, stderr = _run_git(["log", f"-n{count}", "--pretty=format:%h|%an|%ad|%s", "--date=short"], project_root)
    if code != 0:
        return {"error": stderr or "Failed to read git log"}

    commits = []
    for line in stdout.strip().split("\n"):
        if line:
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({"hash": parts[0], "author": parts[1], "date": parts[2], "message": parts[3]})

    return {"count": len(commits), "commits": commits}


@tool_registry.register(
    name="git_show",
    category=ToolCategory.GIT,
    description="Show commit details and diff for a specific commit hash or HEAD.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_git_show(commit_ref: str = "HEAD", project_root: str = "./projects") -> dict[str, Any]:
    code, stdout, stderr = _run_git(["show", commit_ref], project_root)
    return {"ref": commit_ref, "details": stdout[:6000], "error": stderr if code != 0 else None}


@tool_registry.register(
    name="git_branch",
    category=ToolCategory.GIT,
    description="List git branches and identify the current active branch.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_git_branch(project_root: str = "./projects") -> dict[str, Any]:
    code, stdout, stderr = _run_git(["branch", "-a"], project_root)
    if code != 0:
        return {"error": stderr or "Not a git repository"}

    current = ""
    branches = []
    for line in stdout.strip().split("\n"):
        clean = line.strip()
        if line.startswith("*"):
            current = clean[2:]
            branches.append(current)
        elif clean:
            branches.append(clean)

    return {"current_branch": current, "all_branches": branches}


@tool_registry.register(
    name="git_checkout",
    category=ToolCategory.GIT,
    description="Switch branch or checkout a specific file/commit.",
    permission=PermissionTier.READ_WRITE,
    timeout=15,
)
async def tool_git_checkout(target: str, project_root: str = "./projects") -> dict[str, Any]:
    code, stdout, stderr = _run_git(["checkout", target], project_root)
    return {"target": target, "success": code == 0, "output": (stdout + "\n" + stderr).strip()}


@tool_registry.register(
    name="git_create_branch",
    category=ToolCategory.GIT,
    description="Create and switch to a new git branch.",
    permission=PermissionTier.READ_WRITE,
    timeout=15,
)
async def tool_git_create_branch(branch_name: str, project_root: str = "./projects") -> dict[str, Any]:
    code, stdout, stderr = _run_git(["checkout", "-b", branch_name], project_root)
    return {"branch": branch_name, "success": code == 0, "output": (stdout + "\n" + stderr).strip()}


@tool_registry.register(
    name="git_stash",
    category=ToolCategory.GIT,
    description="Stash uncommitted changes with an optional message.",
    permission=PermissionTier.READ_WRITE,
    timeout=15,
)
async def tool_git_stash(message: str = "", project_root: str = "./projects") -> dict[str, Any]:
    args = ["stash", "push", "-m", message] if message else ["stash"]
    code, stdout, stderr = _run_git(args, project_root)
    return {"success": code == 0, "output": (stdout + "\n" + stderr).strip()}


@tool_registry.register(
    name="git_restore",
    category=ToolCategory.GIT,
    description="Restore or discard working directory modifications for a file (destructive).",
    permission=PermissionTier.DESTRUCTIVE,
    timeout=15,
)
async def tool_git_restore(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    code, stdout, stderr = _run_git(["restore", file_path], project_root)
    return {"file_path": file_path, "success": code == 0, "output": (stdout + "\n" + stderr).strip()}


@tool_registry.register(
    name="git_commit",
    category=ToolCategory.GIT,
    description="Create a git commit with staged or all changes. Requires SYSTEM permission.",
    permission=PermissionTier.SYSTEM,
    timeout=20,
)
async def tool_git_commit(message: str, all_files: bool = True, project_root: str = "./projects") -> dict[str, Any]:
    if not message.strip():
        raise ToolValidationError("Commit message cannot be empty")

    if all_files:
        _run_git(["add", "-A"], project_root)

    code, stdout, stderr = _run_git(["commit", "-m", message], project_root)
    return {"success": code == 0, "message": message, "output": (stdout + "\n" + stderr).strip()}


@tool_registry.register(
    name="git_tag",
    category=ToolCategory.GIT,
    description="Create or list git tags.",
    permission=PermissionTier.READ_WRITE,
    timeout=15,
)
async def tool_git_tag(tag_name: Optional[str] = None, project_root: str = "./projects") -> dict[str, Any]:
    if tag_name:
        code, stdout, stderr = _run_git(["tag", tag_name], project_root)
        return {"tag": tag_name, "success": code == 0, "output": (stdout + "\n" + stderr).strip()}
    else:
        code, stdout, stderr = _run_git(["tag", "-l"], project_root)
        tags = [t for t in stdout.strip().split("\n") if t]
        return {"tags": tags}


@tool_registry.register(
    name="git_merge",
    category=ToolCategory.GIT,
    description="Merge a branch into the current active branch.",
    permission=PermissionTier.SYSTEM,
    timeout=30,
)
async def tool_git_merge(source_branch: str, project_root: str = "./projects") -> dict[str, Any]:
    code, stdout, stderr = _run_git(["merge", source_branch], project_root)
    return {"source_branch": source_branch, "success": code == 0, "output": (stdout + "\n" + stderr).strip()}
