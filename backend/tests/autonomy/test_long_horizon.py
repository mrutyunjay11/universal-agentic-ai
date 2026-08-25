import pytest
from app.autonomy.long_horizon import LongHorizonManager
from app.autonomy.task_graph import TaskGraph, SubTask


class TestLongHorizon:
    def test_checkpoint_persistence_and_pause_resume(self):
        lh = LongHorizonManager()
        graph = TaskGraph(master_task_id="lh_task_1")
        graph.add_subtask(SubTask(id="st_1", title="Step 1", objective="Do step 1", parent_task_id="lh_task_1"))

        cp = lh.save_checkpoint("lh_task_1", "STAGE_1", graph)
        assert cp.checkpoint_id.startswith("cp_lh_task_1")

        latest = lh.get_latest_checkpoint("lh_task_1")
        assert latest is not None
        assert latest.stage_name == "STAGE_1"

        # Pause and resume
        lh.pause_task("lh_task_1")
        assert lh.is_paused("lh_task_1") is True

        lh.resume_task("lh_task_1")
        assert lh.is_paused("lh_task_1") is False
