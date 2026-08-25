import pytest
from app.context.attention import PositionAwareContextOrdering
from app.context.evidence import EvidenceItem, EvidenceReference
from app.context.policies import OrderingStrategy


class TestPositionRobustness:
    def test_relevance_first_and_position_aware_invariance(self):
        pao = PositionAwareContextOrdering()

        items = [
            EvidenceItem(content="Low relevance note", reference=EvidenceReference(document_id="d1", chunk_id="c1"), authoritative_score=0.2),
            EvidenceItem(content="Crucial technical fact", reference=EvidenceReference(document_id="d2", chunk_id="c2"), authoritative_score=0.98),
            EvidenceItem(content="Medium supporting context", reference=EvidenceReference(document_id="d3", chunk_id="c3"), authoritative_score=0.6),
        ]

        ordered_rel = pao.order_evidence(items, strategy=OrderingStrategy.RELEVANCE_FIRST)
        assert ordered_rel[0].content == "Crucial technical fact"

        ordered_sand = pao.order_evidence(items, strategy=OrderingStrategy.POSITION_AWARE)
        assert ordered_sand[0].content == "Crucial technical fact"
