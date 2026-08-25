from __future__ import annotations
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    node_type: str  # "DOCUMENT", "CLAIM", "SOURCE", "MEMORY", "ENTITY", "CODE_FILE", "VERIFICATION_TEST"
    label: str
    canonical_ref_id: Optional[str] = None  # Reference to Phase 3 memory ID or Phase 1 Tool ID
    attributes: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation: str  # "SUPPORTS", "CONTRADICTS", "DEFINED_IN", "CALLS", "VERIFIED_BY", "SUPERSEDES"
    weight: float = 1.0


class ContextGraph:
    """
    Bounded Context Relationship Graph.
    Connects documents, claims, sources, entities, memories, and verification tests.
    Uses lazy traversal and bounded neighborhood queries to prevent graph-size explosion.
    Does NOT act as canonical transactional storage (references canonical stores).
    """

    def __init__(self):
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []

    def add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        canonical_ref_id: Optional[str] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> GraphNode:
        node = GraphNode(
            id=node_id,
            node_type=node_type,
            label=label,
            canonical_ref_id=canonical_ref_id,
            attributes=attributes or {},
        )
        self._nodes[node_id] = node
        return node

    def add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0) -> None:
        edge = GraphEdge(source_id=source_id, target_id=target_id, relation=relation, weight=weight)
        self._edges.append(edge)

    def get_bounded_neighborhood(self, start_node_id: str, max_depth: int = 2) -> list[GraphNode]:
        """Returns adjacent nodes within bounded hop distance."""
        visited: set[str] = {start_node_id}
        current_layer: set[str] = {start_node_id}

        for _ in range(max_depth):
            next_layer: set[str] = set()
            for nid in current_layer:
                for edge in self._edges:
                    if edge.source_id == nid and edge.target_id not in visited:
                        next_layer.add(edge.target_id)
                        visited.add(edge.target_id)
                    elif edge.target_id == nid and edge.source_id not in visited:
                        next_layer.add(edge.source_id)
                        visited.add(edge.source_id)
            current_layer = next_layer
            if not current_layer:
                break

        return [self._nodes[nid] for nid in visited if nid in self._nodes]

    def find_connected_claims(self, entity_id: str) -> list[GraphNode]:
        neighbors = self.get_bounded_neighborhood(entity_id, max_depth=1)
        return [n for n in neighbors if n.node_type == "CLAIM"]


context_graph = ContextGraph()
