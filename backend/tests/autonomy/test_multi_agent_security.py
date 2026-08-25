import pytest
from app.autonomy.delegation import DelegationEngine
from app.autonomy.task_graph import SubTask
from app.tools.permissions import PermissionTier


class TestMultiAgentSecurity:
    def test_permission_tier_inheritance_and_restriction(self):
        engine = DelegationEngine()
        subtask = SubTask(
            id="sub_sec_1",
            title="Read only task",
            objective="Inspect data files",
            parent_task_id="m_sec",
            permission_tier=PermissionTier.READ,
        )

        scoped = engine.build_scoped_context(subtask)
        assert scoped["permission_tier"] == PermissionTier.READ.value
