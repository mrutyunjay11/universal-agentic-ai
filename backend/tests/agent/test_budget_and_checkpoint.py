from __future__ import annotations
import shutil
import tempfile
import pytest
from app.agent.state import AgentState
from app.agent.budget import budget_manager
from app.agent.checkpoint import CheckpointManager
from app.agent.memory import TaskMemory, LongTermMemory, MemoryCategory


@pytest.fixture
def temp_cp_dir():
    d = tempfile.mkdtemp(prefix="test_checkpoints_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestBudgetCheckpointMemory:
    def test_budget_exhaustion_detection(self):
        state = AgentState(original_request="Budget test")
        budget_manager.init_budget(state)

        # Exceed tool calls limit
        state.budget.max_tool_calls = 2
        state.budget.current_tool_calls = 2
        ok, reason = budget_manager.check_budget(state)
        assert ok is False
        assert "Tool call budget exceeded" in reason

    def test_checkpoint_save_and_restore(self, temp_cp_dir):
        cpm = CheckpointManager(checkpoint_dir=temp_cp_dir)
        state = AgentState(original_request="Persist me", normalized_goal="Persist goal")
        cp_id = cpm.save_checkpoint(state)
        assert cp_id is not None
        assert len(state.checkpoints) == 1

        restored = cpm.load_latest_checkpoint(state.task_id)
        assert restored is not None
        assert restored.task_id == state.task_id
        assert restored.normalized_goal == "Persist goal"

    def test_task_memory_and_long_term_memory(self):
        tm = TaskMemory(task_id="t1")
        tm.set("temp_var", 42, category="intermediate_output")
        assert tm.get("temp_var") == 42
        assert len(tm.list_entries()) == 1

        ltm = LongTermMemory()
        ltm.remember(
            entry_id="mem_1",
            category=MemoryCategory.FACT_MEMORY,
            key="Python 3.12 release",
            content="Python 3.12 was released in October 2023 with perf improvements.",
        )
        recalled = ltm.recall("Python 3.12")
        assert len(recalled) == 1
        assert "October 2023" in recalled[0].content
