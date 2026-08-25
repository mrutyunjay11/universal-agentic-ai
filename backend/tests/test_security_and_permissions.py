from __future__ import annotations
import pytest
from app.tools.registry import tool_registry
from app.tools.base import ToolContext
from app.tools.permissions import PermissionTier, check_permission, requires_human_approval
from app.utils.security import path_safe, validate_command


class TestSecurityAndPermissions:
    def test_permission_hierarchy(self):
        # READ cannot execute WRITE or SYSTEM
        assert check_permission(PermissionTier.READ, PermissionTier.READ) is True
        assert check_permission(PermissionTier.READ_WRITE, PermissionTier.READ) is False
        assert check_permission(PermissionTier.EXECUTE, PermissionTier.READ_WRITE) is False
        assert check_permission(PermissionTier.DESTRUCTIVE, PermissionTier.SYSTEM) is True

    def test_human_approval_required_tiers(self):
        assert requires_human_approval(PermissionTier.DESTRUCTIVE) is True
        assert requires_human_approval(PermissionTier.SYSTEM) is True
        assert requires_human_approval(PermissionTier.READ) is False

    def test_path_traversal_detection(self):
        assert path_safe("../../../etc/passwd", "./projects") is False
        assert path_safe("/etc/passwd", "./projects") is False
        assert path_safe("subfolder/file.py", "./projects") is True

    def test_command_injection_filters(self):
        assert validate_command("rm -rf /")["allowed"] is False
        assert validate_command("shutdown now")["allowed"] is False
        assert validate_command("pytest -v")["allowed"] is True
        assert validate_command("git status")["allowed"] is True
