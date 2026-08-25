from __future__ import annotations
import difflib
import fnmatch
import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError
from app.tools.provenance import create_provenance, SourceType
from app.utils.security import enforce_project_root, path_safe

EDIT_BACKUP_DIR = ".agent-backups"


def _get_backup_dir(project_root: str) -> str:
    return os.path.join(project_root, EDIT_BACKUP_DIR)


def _backup_file(file_path: str, project_root: str) -> Optional[str]:
    safe = path_safe(file_path, project_root)
    if not safe:
        return None
    backup_dir = _get_backup_dir(project_root)
    os.makedirs(backup_dir, exist_ok=True)
    rel_path = os.path.relpath(file_path, project_root)
    backup_name = rel_path.replace("/", "__") + "." + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    backup_path = os.path.join(backup_dir, backup_name)
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception:
        return None


@tool_registry.register(
    name="read_file",
    category=ToolCategory.FILE,
    description="Read file content with line numbers and optional line range (1-indexed). Returns text content.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_read_file(file_path: str, project_root: str = "./projects", line_start: int = 0, line_end: int = 0) -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        raise ToolSecurityError(f"Path access denied or outside root: {file_path}", "path_traversal")
    if not os.path.isfile(abs_path):
        raise ToolValidationError(f"File not found: {file_path}")

    # Check file size (limit to 10MB)
    size = os.path.getsize(abs_path)
    if size > 10 * 1024 * 1024:
        raise ToolValidationError(f"File exceeds 10MB limit ({size} bytes): {file_path}")

    # Detect binary
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return {
            "file_path": file_path,
            "type": "binary",
            "size_bytes": size,
            "message": "File appears to be binary and cannot be rendered as text.",
        }

    total_lines = len(lines)
    start_idx = max(0, line_start - 1) if line_start > 0 else 0
    end_idx = min(total_lines, line_end) if line_end > 0 and line_end >= line_start else total_lines
    selected_lines = lines[start_idx:end_idx]

    content = "".join(selected_lines)
    prov = create_provenance(
        source_type=SourceType.CODE_FILE,
        uri=f"file://{os.path.abspath(abs_path)}",
        content=content,
        title=os.path.basename(file_path),
    )

    return {
        "file_path": file_path,
        "total_lines": total_lines,
        "line_start": start_idx + 1 if total_lines > 0 else 0,
        "line_end": end_idx,
        "content": content,
        "_provenance": prov,
    }


@tool_registry.register(
    name="write_file",
    category=ToolCategory.FILE,
    description="Write content to a file with atomic replacement and automatic backup.",
    permission=PermissionTier.READ_WRITE,
    timeout=10,
)
async def tool_write_file(file_path: str, content: str, project_root: str = "./projects", overwrite: bool = True) -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        raise ToolSecurityError(f"Path access denied: {file_path}", "path_traversal")

    if os.path.exists(abs_path) and not overwrite:
        raise ToolValidationError(f"File already exists: {file_path}. Set overwrite=True to replace.")

    if os.path.exists(abs_path):
        _backup_file(abs_path, project_root)

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    atomic_path = abs_path + ".atomic"
    try:
        with open(atomic_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(atomic_path, abs_path)
    except Exception as e:
        if os.path.exists(atomic_path):
            os.remove(atomic_path)
        raise e

    return {
        "file_path": file_path,
        "bytes_written": len(content.encode("utf-8")),
        "lines": content.count("\n") + (1 if content and not content.endswith("\n") else 0),
        "status": "created" if not os.path.exists(abs_path) else "overwritten",
    }


@tool_registry.register(
    name="edit_file",
    category=ToolCategory.FILE,
    description="Edit a file by replacing an exact matching old_string with new_string. Backs up file before modification.",
    permission=PermissionTier.READ_WRITE,
    timeout=10,
)
async def tool_edit_file(file_path: str, old_string: str, new_string: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"File not found or inaccessible: {file_path}")

    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if old_string not in content:
        raise ToolValidationError(f"Target string not found in {file_path}. Exact match required.")

    occurrences = content.count(old_string)
    if occurrences > 1:
        raise ToolValidationError(f"Target string matched {occurrences} times. Must be unique.")

    backup_path = _backup_file(abs_path, project_root)
    new_content = content.replace(old_string, new_string, 1)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return {
        "file_path": file_path,
        "status": "edited",
        "backup_created": bool(backup_path),
        "occurrences_replaced": 1,
    }


@tool_registry.register(
    name="apply_diff",
    category=ToolCategory.FILE,
    description="Apply a unified diff patch to a target file with rollback protection.",
    permission=PermissionTier.READ_WRITE,
    timeout=10,
)
async def tool_apply_diff(file_path: str, unified_diff: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"File not found: {file_path}")

    with open(abs_path, "r", encoding="utf-8") as f:
        original = f.readlines()

    backup_path = _backup_file(abs_path, project_root)
    try:
        patched = difflib.patch(original, unified_diff.splitlines(keepends=True))
    except Exception as e:
        raise ToolValidationError(f"Failed to parse diff: {e}")

    if patched is None:
        raise ToolValidationError(f"Patch did not apply cleanly to {file_path}")

    with open(abs_path, "w", encoding="utf-8") as f:
        f.writelines(patched)

    return {"file_path": file_path, "status": "patch_applied", "backup_created": bool(backup_path)}


@tool_registry.register(
    name="multi_replace_file",
    category=ToolCategory.FILE,
    description="Perform multiple non-contiguous exact text replacements in a single file safely.",
    permission=PermissionTier.READ_WRITE,
    timeout=10,
)
async def tool_multi_replace_file(file_path: str, replacements: list[dict[str, str]], project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"File not found: {file_path}")

    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()

    for idx, rep in enumerate(replacements):
        old_str = rep.get("old_string", "")
        if old_str not in content:
            raise ToolValidationError(f"Replacement chunk #{idx+1} not found in {file_path}")

    _backup_file(abs_path, project_root)
    for rep in replacements:
        content = content.replace(rep["old_string"], rep["new_string"], 1)

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"file_path": file_path, "replacements_count": len(replacements), "status": "multi_replaced"}


@tool_registry.register(
    name="delete_file",
    category=ToolCategory.FILE,
    description="Delete a file with automatic backup creation before deletion.",
    permission=PermissionTier.DESTRUCTIVE,
    timeout=10,
)
async def tool_delete_file(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"File not found: {file_path}")

    backup_path = _backup_file(abs_path, project_root)
    os.remove(abs_path)

    return {"file_path": file_path, "deleted": True, "backup_saved": backup_path}


@tool_registry.register(
    name="rollback_file",
    category=ToolCategory.FILE,
    description="Revert a file to its latest automatic backup state.",
    permission=PermissionTier.DESTRUCTIVE,
    timeout=10,
)
async def tool_rollback_file(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    backup_dir = _get_backup_dir(project_root)
    if not os.path.isdir(backup_dir):
        raise ToolValidationError("No backup history available for project.")

    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        raise ToolSecurityError(f"Path denied: {file_path}", "path_traversal")

    rel_path = os.path.relpath(abs_path, project_root)
    prefix = rel_path.replace("/", "__")
    backups = sorted([f for f in os.listdir(backup_dir) if f.startswith(prefix)], reverse=True)
    if not backups:
        raise ToolValidationError(f"No previous backups found for {file_path}")

    latest_backup = os.path.join(backup_dir, backups[0])
    shutil.copy2(latest_backup, abs_path)

    return {"file_path": file_path, "restored_from": backups[0], "status": "rolled_back"}


@tool_registry.register(
    name="file_exists",
    category=ToolCategory.FILE,
    description="Check whether a file or directory exists and get basic type info.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_file_exists(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        return {"file_path": file_path, "exists": False, "reason": "Path access denied"}

    exists = os.path.exists(abs_path)
    return {
        "file_path": file_path,
        "exists": exists,
        "is_file": os.path.isfile(abs_path) if exists else False,
        "is_directory": os.path.isdir(abs_path) if exists else False,
    }


@tool_registry.register(
    name="list_directory",
    category=ToolCategory.FILE,
    description="List directory contents with file metadata (size, type, modified time).",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_list_directory(dir_path: str = ".", project_root: str = "./projects", recursive: bool = False, max_items: int = 100) -> dict[str, Any]:
    abs_path = enforce_project_root(dir_path, project_root)
    if not abs_path or not os.path.isdir(abs_path):
        raise ToolValidationError(f"Directory not found: {dir_path}")

    entries = []
    if recursive:
        for root, dirs, files in os.walk(abs_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", EDIT_BACKUP_DIR)]
            for name in dirs + files:
                full = os.path.join(root, name)
                is_dir = os.path.isdir(full)
                stat = os.stat(full)
                entries.append({
                    "name": name,
                    "path": os.path.relpath(full, project_root),
                    "type": "directory" if is_dir else "file",
                    "size_bytes": stat.st_size if not is_dir else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                })
                if len(entries) >= max_items:
                    break
            if len(entries) >= max_items:
                break
    else:
        for name in sorted(os.listdir(abs_path)):
            if name.startswith(".") or name in (EDIT_BACKUP_DIR, "__pycache__"):
                continue
            full = os.path.join(abs_path, name)
            is_dir = os.path.isdir(full)
            stat = os.stat(full)
            entries.append({
                "name": name,
                "path": os.path.relpath(full, project_root),
                "type": "directory" if is_dir else "file",
                "size_bytes": stat.st_size if not is_dir else 0,
                "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            })
            if len(entries) >= max_items:
                break

    return {"dir_path": dir_path, "total_entries": len(entries), "entries": entries}


@tool_registry.register(
    name="get_file_metadata",
    category=ToolCategory.FILE,
    description="Retrieve comprehensive file metadata (stat, hashes, permissions, mime).",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_get_file_metadata(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.exists(abs_path):
        raise ToolValidationError(f"Path not found: {file_path}")

    stat = os.stat(abs_path)
    is_dir = os.path.isdir(abs_path)
    sha256 = ""
    if not is_dir:
        hasher = hashlib.sha256()
        with open(abs_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        sha256 = hasher.hexdigest()

    return {
        "file_path": file_path,
        "is_file": not is_dir,
        "is_directory": is_dir,
        "size_bytes": stat.st_size if not is_dir else 0,
        "created": datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": sha256,
        "extension": os.path.splitext(file_path)[1],
    }


@tool_registry.register(
    name="copy_file",
    category=ToolCategory.FILE,
    description="Copy a file or directory within the workspace.",
    permission=PermissionTier.READ_WRITE,
    timeout=10,
)
async def tool_copy_file(source_path: str, dest_path: str, project_root: str = "./projects") -> dict[str, Any]:
    src_abs = enforce_project_root(source_path, project_root)
    dst_abs = enforce_project_root(dest_path, project_root)
    if not src_abs or not os.path.exists(src_abs):
        raise ToolValidationError(f"Source path not found: {source_path}")
    if not dst_abs:
        raise ToolSecurityError(f"Destination path access denied: {dest_path}", "path_traversal")

    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
    if os.path.isdir(src_abs):
        shutil.copytree(src_abs, dst_abs, dirs_exist_ok=True)
    else:
        shutil.copy2(src_abs, dst_abs)

    return {"source": source_path, "destination": dest_path, "status": "copied"}


@tool_registry.register(
    name="move_file",
    category=ToolCategory.FILE,
    description="Move or rename a file/directory within the workspace.",
    permission=PermissionTier.READ_WRITE,
    timeout=10,
)
async def tool_move_file(source_path: str, dest_path: str, project_root: str = "./projects") -> dict[str, Any]:
    src_abs = enforce_project_root(source_path, project_root)
    dst_abs = enforce_project_root(dest_path, project_root)
    if not src_abs or not os.path.exists(src_abs):
        raise ToolValidationError(f"Source path not found: {source_path}")
    if not dst_abs:
        raise ToolSecurityError(f"Destination path access denied: {dest_path}", "path_traversal")

    _backup_file(src_abs, project_root) if os.path.isfile(src_abs) else None
    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
    shutil.move(src_abs, dst_abs)

    return {"source": source_path, "destination": dest_path, "status": "moved"}


@tool_registry.register(
    name="create_directory",
    category=ToolCategory.FILE,
    description="Create a directory path within the workspace.",
    permission=PermissionTier.READ_WRITE,
    timeout=5,
)
async def tool_create_directory(dir_path: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(dir_path, project_root)
    if not abs_path:
        raise ToolSecurityError(f"Path access denied: {dir_path}", "path_traversal")

    os.makedirs(abs_path, exist_ok=True)
    return {"dir_path": dir_path, "status": "created"}


@tool_registry.register(
    name="search_files",
    category=ToolCategory.FILE,
    description="Search for files matching glob pattern (e.g. '*.py', '**/*.tsx') in workspace.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_search_files(pattern: str, dir_path: str = ".", project_root: str = "./projects", max_results: int = 50) -> dict[str, Any]:
    abs_dir = enforce_project_root(dir_path, project_root)
    if not abs_dir or not os.path.isdir(abs_dir):
        raise ToolValidationError(f"Directory not found: {dir_path}")

    matches = []
    for root, dirs, files in os.walk(abs_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", EDIT_BACKUP_DIR)]
        for file in files:
            rel = os.path.relpath(os.path.join(root, file), project_root)
            if fnmatch.fnmatch(file, pattern) or fnmatch.fnmatch(rel, pattern):
                matches.append(rel)
                if len(matches) >= max_results:
                    break
        if len(matches) >= max_results:
            break

    return {"pattern": pattern, "match_count": len(matches), "files": matches}
