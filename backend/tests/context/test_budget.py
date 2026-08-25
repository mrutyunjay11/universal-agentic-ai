import pytest
from app.context.budget import ContextBudgetManager
from app.context.policies import ContextSlotType


class TestContextBudget:
    def test_budget_allocation_and_redistribution(self):
        bm = ContextBudgetManager(default_model_context_limit=32768)

        allocations = bm.calculate_budget_allocation(
            model_context_limit=32768,
            system_overhead_tokens=1500,
            task_complexity="HIGH",
        )

        assert ContextSlotType.PRIMARY_EVIDENCE in allocations
        assert ContextSlotType.SYSTEM_POLICY in allocations
        assert allocations[ContextSlotType.PRIMARY_EVIDENCE].allocated_tokens > 2000

        # Redistribution
        allocations[ContextSlotType.SECONDARY_EVIDENCE].used_tokens = 200
        bm.redistribute_unused_budget(
            allocations,
            source_slot=ContextSlotType.SECONDARY_EVIDENCE,
            target_slot=ContextSlotType.PRIMARY_EVIDENCE,
        )
        assert allocations[ContextSlotType.PRIMARY_EVIDENCE].allocated_tokens > 2000
