from __future__ import annotations
import os
import re
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_DANGEROUS_PATTERNS: list[re.Pattern] = [
    re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+(?:/|~)(?:\s|$|\*)"),
    re.compile(r"\brm\s+-rf\s+/etc(?:\s|$|\*)"),
    re.compile(r"\brm\s+-rf\s+/usr(?:\s|$|\*)"),
    re.compile(r"\brm\s+-rf\s+/var(?:\s|$|\*)"),
    re.compile(r"\bdd\s+if="),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bfdisk\b"),
    re.compile(r"\bparted\b"),
    re.compile(r"\bmkswap\b"),
    re.compile(r"\breboot\b"),
    re.compile(r"\bshutdown\b"),
    re.compile(r"\bpoweroff\b"),
    re.compile(r"\biptables\b"),
    re.compile(r"\bpasswd\b"),
    re.compile(r"\bsudo\b"),
    re.compile(r"\bsu\b"),
    re.compile(r">\s*/dev/"),
]

_SHELLCODE_PATTERNS: list[re.Pattern] = [
    re.compile(r"subprocess\.(call|Popen|run|check_call)", re.IGNORECASE),
    re.compile(r"os\.system\s*\("),
    re.compile(r"os\.popen\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"\beval\s*\("),
    re.compile(r"__import__\s*\("),
    re.compile(r"compile\s*\(.*\bexec\b"),
]


def path_safe(file_path: str, project_root: str) -> bool:
    abs_root = os.path.abspath(os.path.expanduser(project_root))
    abs_path = os.path.abspath(os.path.join(abs_root, file_path))

    if not abs_path.startswith(abs_root + os.sep) and abs_path != abs_root:
        logger.warning("Path traversal detected: %s (root: %s)", file_path, project_root)
        return False

    return True


def enforce_project_root(file_path: str, project_root: str) -> Optional[str]:
    abs_root = os.path.abspath(os.path.expanduser(project_root))
    abs_path = os.path.abspath(os.path.join(abs_root, file_path))

    if not abs_path.startswith(abs_root + os.sep) and abs_path != abs_root:
        logger.warning("Path access denied: %s (root: %s)", file_path, project_root)
        return None

    for protected in settings.protected_paths:
        protected_abs = os.path.abspath(os.path.expanduser(protected))
        if abs_path == protected_abs or abs_path.startswith(protected_abs + os.sep):
            logger.warning("Protected path access denied: %s", abs_path)
            return None

    return abs_path


def validate_command(command: str) -> dict:
    command_stripped = command.strip()

    if not command_stripped:
        return {"allowed": False, "reason": "Empty command"}

    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(command_stripped):
            return {
                "allowed": False,
                "reason": f"Command matches dangerous pattern: {pattern.pattern}",
            }

    if "curl" in command_stripped or "wget" in command_stripped:
        local_targets = ("localhost", "127.0.0.1", "0.0.0.0")
        has_local = any(t in command_stripped for t in local_targets)
        if not has_local:
            return {
                "allowed": False,
                "reason": "External network requests require approval: " + command_stripped[:100],
            }

    allowlist = settings.command_allowlist
    cmd_name = command_stripped.removeprefix("sudo ").split()[0]

    if cmd_name not in allowlist:
        return {
            "allowed": False,
            "reason": f"Command not in allowlist: {cmd_name}",
        }

    return {"allowed": True, "reason": None}


def sanitize_file_content(content: str) -> str:
    sanitized = content

    sanitized = sanitized.replace("{{", "\\{\\{").replace("}}", "\\}\\}")

    lines = sanitized.split("\n")
    result: list[str] = []
    in_code_block = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
        if in_code_block and "system" in line.lower() and ":" in line:
            line = line.replace("system", "s_y_s_t_e_m")
        result.append(line)

    return "\n".join(result)


def scan_generated_code(code: str) -> list[str]:
    issues: list[str] = []
    for i, line in enumerate(code.split("\n"), 1):
        for pattern in _SHELLCODE_PATTERNS:
            if pattern.search(line):
                issues.append(f"Line {i}: Potentially dangerous pattern: {line.strip()[:80]}")
    return issues


def is_protected_path(abs_path: str) -> bool:
    for protected in settings.protected_paths:
        protected_abs = os.path.abspath(os.path.expanduser(protected))
        if abs_path == protected_abs or abs_path.startswith(protected_abs + os.sep):
            return True
    return False
