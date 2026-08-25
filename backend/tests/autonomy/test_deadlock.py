import pytest
from app.autonomy.watchdog import Watchdog
from app.autonomy.task_graph import TaskGraph, SubTask, SubTaskStatus


class TestDeadlockDetection:
    def test_detect_circular_dependency_deadlock(self):
        wd = Watchdog()
        graph = TaskGraph(master_task_id="m_deadlock")

        s1 = SubTask(id="s1", title="Task 1", objective="Do 1", parent_task_id="m_deadlock", dependencies=["s2"])
        s2 = SubTask(id="s2", title="Task 2", objective="Do 2", parent_task_id="m_deadlock", dependencies=["s1"])

        graph.add_subtask(s1)
        graph.add_subtask(s2)

        deadlocks = wd.detect_deadlocks(graph)
        assert len(deadlocks) == 2
        assert "s1" in deadlocks
        assert "s2" in deadlocks
