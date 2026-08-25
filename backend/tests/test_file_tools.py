from __future__ import annotations
import os
import shutil
import tempfile
import pytest
from app.tools.registry import tool_registry
from app.tools.base import ToolContext
from app.tools.permissions import PermissionTier


@pytest.fixture
def temp_project_dir():
    d = tempfile.mkdtemp(prefix="test_file_tools_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.mark.asyncio
class TestFileTools:
    async def test_file_lifecycle_write_read_edit_rollback(self, temp_project_dir):
        ctx = ToolContext(project_root=temp_project_dir, permission_granted=PermissionTier.SYSTEM)

        # 1. Write file
        write_res = await tool_registry.execute(
            "write_file",
            {"file_path": "hello.txt", "content": "Hello World\nLine 2\nLine 3"},
            ctx,
        )
        assert write_res.success
        assert write_res.output["bytes_written"] > 0

        # 2. File exists
        exists_res = await tool_registry.execute("file_exists", {"file_path": "hello.txt"}, ctx)
        assert exists_res.success
        assert exists_res.output["exists"] is True

        # 3. Read file
        read_res = await tool_registry.execute("read_file", {"file_path": "hello.txt", "line_start": 1, "line_end": 2}, ctx)
        assert read_res.success
        assert "Hello World" in read_res.output["content"]
        assert read_res.output["line_end"] == 2

        # 4. Edit file
        edit_res = await tool_registry.execute(
            "edit_file",
            {"file_path": "hello.txt", "old_string": "Hello World", "new_string": "Hello Universal Agent"},
            ctx,
        )
        assert edit_res.success
        assert edit_res.output["backup_created"] is True

        # Verify edited content
        read2 = await tool_registry.execute("read_file", {"file_path": "hello.txt"}, ctx)
        assert "Hello Universal Agent" in read2.output["content"]

        # 5. Rollback file
        rollback_res = await tool_registry.execute("rollback_file", {"file_path": "hello.txt"}, ctx)
        assert rollback_res.success

        # Verify rolled back content
        read3 = await tool_registry.execute("read_file", {"file_path": "hello.txt"}, ctx)
        assert "Hello World" in read3.output["content"]

    async def test_directory_operations(self, temp_project_dir):
        ctx = ToolContext(project_root=temp_project_dir, permission_granted=PermissionTier.SYSTEM)

        # Create dir
        mkdir_res = await tool_registry.execute("create_directory", {"dir_path": "src/components"}, ctx)
        assert mkdir_res.success

        # Write inside dir
        await tool_registry.execute("write_file", {"file_path": "src/components/App.tsx", "content": "export default App;"}, ctx)

        # List directory
        list_res = await tool_registry.execute("list_directory", {"dir_path": "src", "recursive": True}, ctx)
        assert list_res.success
        assert list_res.output["total_entries"] >= 1

        # Search files
        search_res = await tool_registry.execute("search_files", {"pattern": "*.tsx"}, ctx)
        assert search_res.success
        assert len(search_res.output["files"]) == 1

    async def test_delete_file(self, temp_project_dir):
        ctx = ToolContext(project_root=temp_project_dir, permission_granted=PermissionTier.SYSTEM)
        await tool_registry.execute("write_file", {"file_path": "temp.txt", "content": "delete me"}, ctx)

        del_res = await tool_registry.execute("delete_file", {"file_path": "temp.txt"}, ctx)
        assert del_res.success
        assert del_res.output["deleted"] is True
