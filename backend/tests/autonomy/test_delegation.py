import pytest
from app.autonomy.delegation import DelegationEngine
from app.autonomy.task_graph import SubTask, SubTaskStatus
from app.autonomy.policies import DelegationPolicy


class TestDelegation:
    def test_scoped_context_and_least_privilege(self):
        engine = DelegationEngine()
        subtask = SubTask(
            id="sub_test_1",
            title="Scoped subtask",
            objective="Analyze specific data partition",
            parent_task_id="master_1",
            inputs={"partition": "2026-Q1"},
        )
        parent_ctx = {
            "conversation_secret": "super_secret_token",
            "project_root": "/workspace/app",
        }

        scoped = engine.build_scoped_context(subtask, parent_ctx, depth=1)

        assert scoped["subtask_id"] == "sub_test_1"
        assert scoped["inputs"]["partition"] == "2026-Q1"
        assert scoped["project_root"] == "/workspace/app"
        # Verify secret conversation context is not blindly copied
        assert "conversation_secret" not in scoped

    def test_recursion_depth_limit(self):
        engine = DelegationEngine(policy=DelegationPolicy(max_delegation_depth=2))
        subtask = SubTask(
            id="sub_deep",
            title="Deep subtask",
            objective="Deep nested call",
            parent_task_id="master_1",
        )

        with pytest.raises(PermissionError, match="exceeds maximum allowed"):
            engine.build_scoped_context(subtask, depth=3)
