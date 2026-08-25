from __future__ import annotations
from typing import Any
from app.context.policies import OrderingStrategy, ContextSlotType
from app.context.evidence import EvidenceItem


class PositionAwareContextOrdering:
    """
    Position-Aware Context Ordering Engine.
    Mitigates position sensitivity degradation by strategically placing high-value evidence
    at prime attention anchors (beginning and end of reasoning blocks) while clustering supporting detail.
    """

    def order_evidence(
        self,
        items: list[EvidenceItem],
        strategy: OrderingStrategy = OrderingStrategy.POSITION_AWARE,
    ) -> list[EvidenceItem]:
        if not items or len(items) <= 2:
            return list(items)

        if strategy == OrderingStrategy.RELEVANCE_FIRST:
            return sorted(items, key=lambda x: x.authoritative_score * x.confidence, reverse=True)

        if strategy == OrderingStrategy.POSITION_AWARE:
            # Sandwiching: Place highest scoring at the very beginning (index 0)
            # and second highest at the very end (index -1), filling intermediate in the middle.
            sorted_items = sorted(items, key=lambda x: x.authoritative_score * x.confidence, reverse=True)
            head = [sorted_items[0]]
            tail = [sorted_items[1]] if len(sorted_items) > 1 else []
            middle = sorted_items[2:]
            return head + middle + tail

        # Default fallback
        return list(items)


position_ordering = PositionAwareContextOrdering()
