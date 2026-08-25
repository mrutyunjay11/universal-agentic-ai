import pytest
from app.context.context_graph import ContextGraph


class TestContextGraph:
    def test_graph_nodes_edges_and_bounded_neighborhood(self):
        graph = ContextGraph()

        # Add nodes
        graph.add_node("lib_fastapi", "ENTITY", "FastAPI Framework")
        graph.add_node("claim_pydantic", "CLAIM", "FastAPI supports Pydantic v2")
        graph.add_node("doc_release_notes", "DOCUMENT", "FastAPI 0.100 Release Notes")

        # Add edges
        graph.add_edge("lib_fastapi", "claim_pydantic", "DEFINED_IN")
        graph.add_edge("claim_pydantic", "doc_release_notes", "VERIFIED_BY")

        # Query bounded neighborhood
        neighbors = graph.get_bounded_neighborhood("lib_fastapi", max_depth=1)
        assert len(neighbors) == 2

        claims = graph.find_connected_claims("lib_fastapi")
        assert len(claims) == 1
        assert claims[0].id == "claim_pydantic"
