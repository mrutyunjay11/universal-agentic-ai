import pytest
from app.autonomy.task_decomposer import TaskDecomposer


class TestTaskDecomposition:
    def test_decompose_research_goal(self):
        decomposer = TaskDecomposer()
        graph = decomposer.decompose("task_res_1", "Research and compare python async libraries")

        assert len(graph.nodes) == 3
        assert graph.is_acyclic() is True
        node_titles = [s.title for s in graph.nodes.values()]
        assert any("Primary" in t for t in node_titles)
        assert any("Verification" in t for t in node_titles)

    def test_decompose_coding_goal(self):
        decomposer = TaskDecomposer()
        graph = decomposer.decompose("task_code_1", "Implement and debug payment processing module")

        assert len(graph.nodes) == 3
        assert graph.is_acyclic() is True
        node_titles = [s.title for s in graph.nodes.values()]
        assert any("Analysis" in t for t in node_titles)
        assert any("Implementation" in t for t in node_titles)
        assert any("Testing" in t for t in node_titles)
