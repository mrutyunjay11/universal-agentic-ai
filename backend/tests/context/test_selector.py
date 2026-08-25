import pytest
from app.context.selector import ContextSelector
from app.context.evidence import EvidenceItem, EvidenceReference
from app.context.budget import ContextBudgetManager


class TestContextSelector:
    def test_slot_selection_and_budget_fitting(self):
        selector = ContextSelector()
        bm = ContextBudgetManager()
        allocations = bm.calculate_budget_allocation(model_context_limit=4096)

        evidence = [
            EvidenceItem(content="Primary evidence point 1.", reference=EvidenceReference(document_id="d1", chunk_id="c1")),
            EvidenceItem(content="Primary evidence point 2.", reference=EvidenceReference(document_id="d2", chunk_id="c2")),
        ]

        bundle = selector.select_slots(
            goal="Test Task Goal",
            constraints=["Constraint 1"],
            primary_evidence=evidence,
            secondary_evidence=[],
            contradictions=[],
            tool_results=[],
            budget_allocations=allocations,
        )

        assert bundle.total_tokens_used > 0
        assert len(bundle.selected_evidence_ids) == 2
        assert "CURRENT GOAL" in bundle.slots["CURRENT_GOAL"]
