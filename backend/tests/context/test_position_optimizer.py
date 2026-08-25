import pytest
from app.context.attention import PositionAwareContextOrdering
from app.context.evidence import EvidenceItem, EvidenceReference
from app.context.policies import OrderingStrategy


class TestPositionOptimizer:
    def test_position_aware_sandwich_ordering(self):
        pao = PositionAwareContextOrdering()

        items = [
            EvidenceItem(content="Item C", reference=EvidenceReference(document_id="d3", chunk_id="c3"), authoritative_score=0.4),
            EvidenceItem(content="Item A", reference=EvidenceReference(document_id="d1", chunk_id="c1"), authoritative_score=0.9),
            EvidenceItem(content="Item B", reference=EvidenceReference(document_id="d2", chunk_id="c2"), authoritative_score=0.8),
        ]

        ordered = pao.order_evidence(items, strategy=OrderingStrategy.POSITION_AWARE)
        assert len(ordered) == 3
        # Highest authoritative (Item A) at index 0
        assert ordered[0].content == "Item A"
        # Second highest (Item B) at index -1
        assert ordered[-1].content == "Item B"
