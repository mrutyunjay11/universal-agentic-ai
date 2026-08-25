from __future__ import annotations
import os
import shutil
import tempfile
import pytest
from app.tools.registry import tool_registry
from app.tools.base import ToolContext
from app.tools.permissions import PermissionTier


@pytest.fixture
def temp_code_dir():
    d = tempfile.mkdtemp(prefix="test_code_tools_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.mark.asyncio
class TestCodeTools:
    async def test_symbol_extraction_python(self, temp_code_dir):
        ctx = ToolContext(project_root=temp_code_dir, permission_granted=PermissionTier.SYSTEM)
        py_code = """
class Calculator:
    def __init__(self):
        pass

    def add(self, a: int, b: int) -> int:
        \"\"\"Add two numbers.\"\"\"
        return a + b

async def fetch_data(url: str):
    return url
"""
        await tool_registry.execute("write_file", {"file_path": "calc.py", "content": py_code}, ctx)

        sym_res = await tool_registry.execute("find_symbols", {"file_path": "calc.py"}, ctx)
        assert sym_res.success
        symbols = sym_res.output["symbols"]
        names = [s["name"] for s in symbols]
        assert "Calculator" in names
        assert "add" in names
        assert "fetch_data" in names

    async def test_find_references_and_callers(self, temp_code_dir):
        ctx = ToolContext(project_root=temp_code_dir, permission_granted=PermissionTier.SYSTEM)
        file1 = "def helper(): return 42\ndef main(): return helper()"
        file2 = "from file1 import helper\nresult = helper()"

        await tool_registry.execute("write_file", {"file_path": "file1.py", "content": file1}, ctx)
        await tool_registry.execute("write_file", {"file_path": "file2.py", "content": file2}, ctx)

        ref_res = await tool_registry.execute("find_references", {"symbol_name": "helper"}, ctx)
        assert ref_res.success
        assert ref_res.output["reference_count"] >= 3

        call_res = await tool_registry.execute("find_callers", {"function_name": "helper"}, ctx)
        assert call_res.success
        assert call_res.output["callers_count"] >= 2

    async def test_analyze_code(self, temp_code_dir):
        ctx = ToolContext(project_root=temp_code_dir, permission_granted=PermissionTier.SYSTEM)
        code = "# Header comment\ndef foo():\n    pass\n\n# Another comment\n"
        await tool_registry.execute("write_file", {"file_path": "sample.py", "content": code}, ctx)

        analysis = await tool_registry.execute("analyze_code", {"file_path": "sample.py"}, ctx)
        assert analysis.success
        assert analysis.output["total_lines"] >= 4
        assert analysis.output["comment_lines"] >= 2

    async def test_detect_language(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        res1 = await tool_registry.execute("detect_language", {"file_path": "index.tsx"}, ctx)
        assert res1.output["language"] == "typescript"

        res2 = await tool_registry.execute("detect_language", {"file_path": "main.rs"}, ctx)
        assert res2.output["language"] == "rust"
