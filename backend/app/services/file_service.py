from __future__ import annotations
import difflib
import hashlib
import os
import shutil
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.utils.security import path_safe, enforce_project_root
from app.config import settings

logger = logging.getLogger(__name__)

EDIT_BACKUP_DIR = ".agent-backups"


class FileEditError(Exception):
    pass


class FileReadError(Exception):
    pass


def _get_backup_dir(project_root: str) -> str:
    return os.path.join(project_root, EDIT_BACKUP_DIR)


def _backup_file(file_path: str, project_root: str) -> Optional[str]:
    safe = path_safe(file_path, project_root)
    if not safe:
        return None

    backup_dir = _get_backup_dir(project_root)
    os.makedirs(backup_dir, exist_ok=True)

    rel_path = os.path.relpath(file_path, project_root)
    backup_name = rel_path.replace("/", "__") + "." + datetime.utcnow().strftime(
        "%Y%m%d%H%M%S%f"
    )
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except (OSError, IOError) as e:
        logger.warning("Backup failed for %s: %s", file_path, e)
        return None


async def read_file(file_path: str, project_root: str, line_start: int = 0, line_end: int = 0) -> str:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        raise FileReadError(f"Path access denied: {file_path}")

    if not os.path.isfile(abs_path):
        raise FileReadError(f"File not found: {file_path}")

    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (OSError, IOError) as e:
        raise FileReadError(f"Cannot read file {file_path}: {e}")

    total_lines = len(lines)
    if line_start > 0:
        start = max(0, line_start - 1)
        if line_end > 0 and line_end >= line_start:
            end = min(total_lines, line_end)
        else:
            end = total_lines
        lines = lines[start:end]

    return "".join(lines)


async def write_file(file_path: str, content: str, project_root: str, force: bool = False) -> str:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        raise FileEditError(f"Path access denied: {file_path}")

    if os.path.exists(abs_path) and not force:
        raise FileEditError(
            f"File exists: {file_path}. Use force=True to overwrite."
        )

    _backup_file(abs_path, project_root) if os.path.exists(abs_path) else None

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    atomic_path = abs_path + ".atomic"
    try:
        with open(atomic_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(atomic_path, abs_path)
    except (OSError, IOError) as e:
        if os.path.exists(atomic_path):
            os.remove(atomic_path)
        raise FileEditError(f"Cannot write file {file_path}: {e}")

    return f"Written {len(content)} bytes to {file_path}"


async def edit_file(
    file_path: str,
    project_root: str,
    old_string: str,
    new_string: str,
) -> str:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        raise FileEditError(f"Path access denied: {file_path}")

    if not os.path.isfile(abs_path):
        raise FileEditError(f"File not found: {file_path}")

    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, IOError) as e:
        raise FileEditError(f"Cannot read {file_path}: {e}")

    if old_string not in content:
        raise FileEditError(
            f"old_string not found in {file_path}. Provide exact match."
        )

    backup_path = _backup_file(abs_path, project_root)

    new_content = content.replace(old_string, new_string, 1)

    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except (OSError, IOError) as e:
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, abs_path)
        raise FileEditError(f"Write failed, restored backup: {e}")

    return f"Edited {file_path}"


async def apply_diff(
    file_path: str, unified_diff: str, project_root: str
) -> str:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        raise FileEditError(f"Path access denied: {file_path}")

    if not os.path.isfile(abs_path):
        raise FileEditError(f"File not found: {file_path}")

    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            original = f.readlines()
    except (OSError, IOError) as e:
        raise FileEditError(f"Cannot read {file_path}: {e}")

    backup_path = _backup_file(abs_path, project_root)

    try:
        patched = difflib.patch(original, unified_diff.splitlines(keepends=True))
    except Exception as e:
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, abs_path)
        raise FileEditError(f"Patch application failed: {e}")

    if patched is None:
        raise FileEditError(f"Patch did not apply cleanly to {file_path}")

    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(patched)
    except (OSError, IOError) as e:
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, abs_path)
        raise FileEditError(f"Write failed, restored backup: {e}")

    return f"Applied diff to {file_path}"


def compute_file_hash(file_path: str) -> str:
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError):
        return ""


def list_directory(dir_path: str, project_root: str) -> list[dict]:
    abs_path = enforce_project_root(dir_path, project_root)
    if not abs_path:
        raise FileEditError(f"Path access denied: {dir_path}")

    if not os.path.isdir(abs_path):
        raise FileEditError(f"Directory not found: {dir_path}")

    entries: list[dict] = []
    try:
        for entry in sorted(os.listdir(abs_path)):
            if entry.startswith(".") or entry == EDIT_BACKUP_DIR:
                continue
            full = os.path.join(abs_path, entry)
            is_dir = os.path.isdir(full)
            stat = os.stat(full)
            entries.append(
                {
                    "name": entry,
                    "path": os.path.relpath(full, project_root),
                    "type": "directory" if is_dir else "file",
                    "size": stat.st_size if not is_dir else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
    except (OSError, IOError) as e:
        raise FileEditError(f"Cannot list directory {dir_path}: {e}")

    return entries


def rollback_last_edit(file_path: str, project_root: str) -> Optional[str]:
    backup_dir = _get_backup_dir(project_root)
    if not os.path.isdir(backup_dir):
        return None

    rel_path = os.path.relpath(
        enforce_project_root(file_path, project_root) or file_path,
        project_root,
    )
    prefix = rel_path.replace("/", "__")

    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith(prefix)],
        reverse=True,
    )
    if not backups:
        return None

    latest = os.path.join(backup_dir, backups[0])
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        return None

    shutil.copy2(latest, abs_path)
    return f"Rolled back {file_path} to backup {backups[0]}"


def get_file_hash(file_path: str, project_root: str) -> str:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        return ""
    return compute_file_hash(abs_path)
