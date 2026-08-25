from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.context.policies import ContextSlotType
from app.context.tokenizer import tokenizer_provider


class SlotBudget(BaseModel):
    slot_type: ContextSlotType
    min_tokens: int = 100
    max_tokens: int = 4000
    allocated_tokens: int = 1000
    used_tokens: int = 0
    priority: int = 5  # 1 (lowest) to 10 (highest)


class ContextBudgetManager:
    """
    Dynamic context budget allocator.
    Accounts for prompt overhead (system instructions, tool schemas, user input, output reserve),
    computes available evidence budget, and adaptively distributes tokens across slots based on priority.
    """

    def __init__(self, default_model_context_limit: int = 32768, safety_margin_tokens: int = 1024):
        self.default_model_limit = default_model_context_limit
        self.safety_margin = safety_margin_tokens

    def calculate_budget_allocation(
        self,
        model_context_limit: Optional[int] = None,
        system_overhead_tokens: int = 1500,
        tool_schema_tokens: int = 1200,
        user_input_tokens: int = 500,
        output_reserve_tokens: int = 2048,
        task_complexity: str = "MEDIUM",  # "LOW", "MEDIUM", "HIGH"
    ) -> dict[ContextSlotType, SlotBudget]:
        limit = model_context_limit or self.default_model_limit
        fixed_overhead = system_overhead_tokens + tool_schema_tokens + user_input_tokens + output_reserve_tokens + self.safety_margin
        available_budget = max(2000, limit - fixed_overhead)

        # Baseline slot configurations
        allocations: dict[ContextSlotType, SlotBudget] = {
            ContextSlotType.SYSTEM_POLICY: SlotBudget(
                slot_type=ContextSlotType.SYSTEM_POLICY,
                allocated_tokens=system_overhead_tokens,
                priority=10,
            ),
            ContextSlotType.CURRENT_GOAL: SlotBudget(
                slot_type=ContextSlotType.CURRENT_GOAL,
                allocated_tokens=min(500, user_input_tokens),
                priority=10,
            ),
            ContextSlotType.CONSTRAINTS: SlotBudget(
                slot_type=ContextSlotType.CONSTRAINTS,
                allocated_tokens=400,
                priority=9,
            ),
            ContextSlotType.PRIMARY_EVIDENCE: SlotBudget(
                slot_type=ContextSlotType.PRIMARY_EVIDENCE,
                allocated_tokens=int(available_budget * (0.45 if task_complexity == "HIGH" else 0.35)),
                max_tokens=int(available_budget * 0.7),
                priority=9,
            ),
            ContextSlotType.SECONDARY_EVIDENCE: SlotBudget(
                slot_type=ContextSlotType.SECONDARY_EVIDENCE,
                allocated_tokens=int(available_budget * 0.15),
                priority=6,
            ),
            ContextSlotType.CONTRADICTIONS: SlotBudget(
                slot_type=ContextSlotType.CONTRADICTIONS,
                allocated_tokens=int(available_budget * 0.10),
                priority=8,
            ),
            ContextSlotType.TOOL_RESULTS: SlotBudget(
                slot_type=ContextSlotType.TOOL_RESULTS,
                allocated_tokens=int(available_budget * 0.15),
                priority=7,
            ),
            ContextSlotType.MEMORY: SlotBudget(
                slot_type=ContextSlotType.MEMORY,
                allocated_tokens=int(available_budget * 0.10),
                priority=6,
            ),
            ContextSlotType.WORKSPACE: SlotBudget(
                slot_type=ContextSlotType.WORKSPACE,
                allocated_tokens=int(available_budget * 0.10),
                priority=7,
            ),
            ContextSlotType.OUTPUT_RESERVE: SlotBudget(
                slot_type=ContextSlotType.OUTPUT_RESERVE,
                allocated_tokens=output_reserve_tokens,
                priority=10,
            ),
        }
        return allocations

    def redistribute_unused_budget(
        self,
        allocations: dict[ContextSlotType, SlotBudget],
        source_slot: ContextSlotType,
        target_slot: ContextSlotType,
    ) -> None:
        src = allocations.get(source_slot)
        tgt = allocations.get(target_slot)
        if src and tgt:
            unused = max(0, src.allocated_tokens - src.used_tokens)
            if unused > 0:
                src.allocated_tokens -= unused
                tgt.allocated_tokens += unused


budget_manager = ContextBudgetManager()
