import pytest
from app.autonomy.task_graph import TaskGraph, SubTask, SubTaskStatus


class TestTaskGraph:
    def test_ready_subtasks_resolution(self):
        graph = TaskGraph(master_task_id="master_1")
        s1 = SubTask(id="s1", title="Step 1", objective="Do 1", parent_task_id="master_1")
        s2 = SubTask(id="s2", title="Step 2", objective="Do 2", parent_task_id="master_1", dependencies=["s1"])
        graph.add_subtask(s1)
        graph.add_subtask(s2)

        # Initially only s1 is ready
        ready = graph.get_ready_subtasks()
        assert len(ready) == 1
        assert ready[0].id == "s1"

        # Mark s1 completed
        s1.status = SubTaskStatus.COMPLETED

        # Now s2 should be ready
        ready2 = graph.get_ready_subtasks()
        assert len(ready2) == 1
        assert ready2[0].id == "s2"

    def test_cycle_detection(self):
        graph = TaskGraph(master_task_id="master_1")
        s1 = SubTask(id="s1", title="Step 1", objective="Do 1", parent_task_id="master_1", dependencies=["s2"])
        s2 = SubTask(id="s2", title="Step 2", objective="Do 2", parent_task_id="master_1", dependencies=["s1"])
        graph.add_subtask(s1)
        graph.add_subtask(s2)

        assert graph.is_acyclic() is False
