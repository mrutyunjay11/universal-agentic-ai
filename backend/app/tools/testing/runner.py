from __future__ import annotations
import asyncio
import os
import re
import shutil
import subprocess
import time
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError
from app.utils.security import enforce_project_root

_TEST_RUN_HISTORY: list[dict[str, Any]] = []


def _detect_test_framework(project_root: str) -> Optional[dict[str, Any]]:
    if os.path.exists(os.path.join(project_root, "pytest.ini")) or os.path.exists(os.path.join(project_root, "pyproject.toml")) or os.path.exists(os.path.join(project_root, "conftest.py")):
        return {"framework": "pytest", "cmd": ["pytest", "-v"]}
    if os.path.exists(os.path.join(project_root, "package.json")):
        if shutil.which("npm") or shutil.which("npx"):
            return {"framework": "jest", "cmd": ["npm", "test", "--", "--no-coverage"]}
    if os.path.exists(os.path.join(project_root, "Cargo.toml")):
        return {"framework": "cargo", "cmd": ["cargo", "test"]}
    if os.path.exists(os.path.join(project_root, "go.mod")):
        return {"framework": "go", "cmd": ["go", "test", "-v", "./..."]}
    return None


def _parse_pytest_output(stdout: str) -> dict[str, int]:
    passed = len(re.findall(r"PASSED", stdout))
    failed = len(re.findall(r"FAILED", stdout))
    skipped = len(re.findall(r"SKIPPED", stdout))
    return {"passed": passed, "failed": failed, "skipped": skipped}


@tool_registry.register(
    name="run_tests",
    category=ToolCategory.TESTING,
    description="Auto-detect project test suite (pytest, jest, cargo, go) and run full tests, returning structured results.",
    permission=PermissionTier.EXECUTE,
    timeout=120,
)
async def tool_run_tests(project_root: str = "./projects", custom_args: str = "") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    if not abs_root:
        raise ToolSecurityError("Path denied", "path_traversal")

    fw = _detect_test_framework(abs_root)
    if not fw:
        # Fallback to python -m unittest
        fw = {"framework": "unittest", "cmd": ["python3", "-m", "unittest", "discover"]}

    cmd = list(fw["cmd"])
    if custom_args:
        cmd.extend(custom_args.split())

    start = time.time()
    try:
        proc = subprocess.run(cmd, cwd=abs_root, capture_output=True, text=True, timeout=120)
        duration = round(time.time() - start, 2)
        counts = _parse_pytest_output(proc.stdout) if fw["framework"] == "pytest" else {}

        res = {
            "framework": fw["framework"],
            "command": " ".join(cmd),
            "duration_seconds": duration,
            "status": "passed" if proc.returncode == 0 else "failed",
            "return_code": proc.returncode,
            "counts": counts,
            "stdout": proc.stdout[:6000],
            "stderr": proc.stderr[:3000],
        }
        _TEST_RUN_HISTORY.append(res)
        return res
    except subprocess.TimeoutExpired:
        return {"framework": fw["framework"], "status": "timeout", "error": "Test suite timed out after 120s"}
    except Exception as e:
        return {"framework": fw["framework"], "status": "error", "error": str(e)}


@tool_registry.register(
    name="run_test_file",
    category=ToolCategory.TESTING,
    description="Run tests in a specific test file.",
    permission=PermissionTier.EXECUTE,
    timeout=60,
)
async def tool_run_test_file(test_file: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    file_path = enforce_project_root(test_file, project_root)
    if not file_path or not os.path.isfile(file_path):
        raise ToolValidationError(f"Test file not found: {test_file}")

    if test_file.endswith(".py"):
        cmd = ["pytest", "-v", file_path]
    elif test_file.endswith((".js", ".ts", ".jsx", ".tsx")):
        cmd = ["npx", "jest", file_path]
    elif test_file.endswith(".rs"):
        cmd = ["cargo", "test", "--test", os.path.splitext(os.path.basename(test_file))[0]]
    else:
        cmd = ["pytest", "-v", file_path]

    try:
        proc = subprocess.run(cmd, cwd=abs_root, capture_output=True, text=True, timeout=60)
        return {
            "test_file": test_file,
            "status": "passed" if proc.returncode == 0 else "failed",
            "return_code": proc.returncode,
            "stdout": proc.stdout[:4000],
            "stderr": proc.stderr[:2000],
        }
    except Exception as e:
        return {"test_file": test_file, "status": "error", "error": str(e)}


@tool_registry.register(
    name="run_test_pattern",
    category=ToolCategory.TESTING,
    description="Run tests matching a specific test function or test case name pattern (e.g. -k 'test_login').",
    permission=PermissionTier.EXECUTE,
    timeout=60,
)
async def tool_run_test_pattern(pattern: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    cmd = ["pytest", "-k", pattern, "-v"]

    try:
        proc = subprocess.run(cmd, cwd=abs_root, capture_output=True, text=True, timeout=60)
        return {
            "pattern": pattern,
            "status": "passed" if proc.returncode == 0 else "failed",
            "stdout": proc.stdout[:4000],
            "stderr": proc.stderr[:2000],
        }
    except Exception as e:
        return {"pattern": pattern, "error": str(e)}


@tool_registry.register(
    name="debug_command",
    category=ToolCategory.TESTING,
    description="Run a command under debugger or verbose diagnostic flags to capture crash traces.",
    permission=PermissionTier.EXECUTE,
    timeout=60,
)
async def tool_debug_command(command: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    try:
        proc = subprocess.run(command, shell=True, cwd=abs_root, capture_output=True, text=True, timeout=60)
        return {
            "command": command,
            "return_code": proc.returncode,
            "stdout": proc.stdout[:5000],
            "stderr": proc.stderr[:5000],
        }
    except Exception as e:
        return {"command": command, "error": str(e)}


@tool_registry.register(
    name="collect_test_results",
    category=ToolCategory.TESTING,
    description="Retrieve test run history and overall pass/fail metrics.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_collect_test_results() -> dict[str, Any]:
    return {"total_runs": len(_TEST_RUN_HISTORY), "history": _TEST_RUN_HISTORY[-10:]}


@tool_registry.register(
    name="compare_test_runs",
    category=ToolCategory.TESTING,
    description="Compare the two most recent test runs to verify if fixes resolved regressions.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_compare_test_runs() -> dict[str, Any]:
    if len(_TEST_RUN_HISTORY) < 2:
        return {"status": "insufficient_data", "message": "Need at least 2 test runs to compare."}

    prev = _TEST_RUN_HISTORY[-2]
    curr = _TEST_RUN_HISTORY[-1]

    return {
        "previous_status": prev.get("status"),
        "current_status": curr.get("status"),
        "improved": prev.get("status") == "failed" and curr.get("status") == "passed",
        "regressed": prev.get("status") == "passed" and curr.get("status") == "failed",
    }


@tool_registry.register(
    name="analyze_failure",
    category=ToolCategory.TESTING,
    description="Extract root causes and stack traces from raw test failure outputs.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_analyze_failure(error_output: str) -> dict[str, Any]:
    trace_lines = []
    error_summary = "Unknown failure"
    for line in error_output.split("\n"):
        if "Error:" in line or "Exception:" in line or "AssertionError" in line or "FAILED" in line:
            error_summary = line.strip()
        if "File " in line or "line " in line or "at " in line:
            trace_lines.append(line.strip())

    return {
        "summary": error_summary,
        "stack_frames": trace_lines[:10],
        "likely_issue": "Assertion or exception raised in test body",
    }


@tool_registry.register(
    name="benchmark_code",
    category=ToolCategory.TESTING,
    description="Run timing benchmark on a Python snippet or command.",
    permission=PermissionTier.EXECUTE,
    timeout=30,
)
async def tool_benchmark_code(python_code: str, iterations: int = 100) -> dict[str, Any]:
    import timeit
    try:
        t = timeit.timeit(stmt=python_code, number=iterations)
        return {
            "iterations": iterations,
            "total_time_seconds": round(t, 4),
            "avg_time_per_iteration_ms": round((t / iterations) * 1000, 4),
        }
    except Exception as e:
        return {"error": f"Benchmark failed: {e}"}
