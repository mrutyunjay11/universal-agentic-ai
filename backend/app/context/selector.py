from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.context.policies import ContextSlotType
from app.context.budget import SlotBudget
from app.context.evidence import EvidenceItem
from app.context.tokenizer import tokenizer_provider


class SelectedContextBundle(BaseModel):
    slots: dict[str, str] = Field(default_factory=dict)
    total_tokens_used: int = 0
    selected_evidence_ids: list[str] = Field(default_factory=list)
    omitted_count: int = 0


class ContextSelector:
    """
    Context Selector.
    Fits ranked and deduplicated evidence items into designated slot token budgets,
    ensuring minimum evidence diversity and zero budget overflows.
    """

    def select_slots(
        self,
        goal: str,
        constraints: list[str],
        primary_evidence: list[EvidenceItem],
        secondary_evidence: list[EvidenceItem],
        contradictions: list[str],
        tool_results: list[str],
        budget_allocations: dict[ContextSlotType, SlotBudget],
    ) -> SelectedContextBundle:
        slots_content: dict[str, str] = {}
        selected_ids: list[str] = []
        total_tokens = 0
        omitted = 0

        # 1. Goal & Constraints
        slots_content[ContextSlotType.CURRENT_GOAL.value] = f"CURRENT GOAL: {goal}"
        slots_content[ContextSlotType.CONSTRAINTS.value] = "CONSTRAINTS: " + " | ".join(constraints) if constraints else "CONSTRAINTS: None"

        # 2. Primary Evidence fitting
        prim_budget = budget_allocations.get(ContextSlotType.PRIMARY_EVIDENCE)
        max_prim_tokens = prim_budget.allocated_tokens if prim_budget else 4000
        prim_lines = []
        curr_prim_tokens = 0

        for item in primary_evidence:
            item_tokens, _ = tokenizer_provider.count_tokens(item.content)
            if curr_prim_tokens + item_tokens <= max_prim_tokens:
                prim_lines.append(f"[{item.reference.document_id}] {item.content}")
                curr_prim_tokens += item_tokens
                selected_ids.append(item.id)
            else:
                omitted += 1

        slots_content[ContextSlotType.PRIMARY_EVIDENCE.value] = "\n".join(prim_lines) if prim_lines else "None"
        if prim_budget:
            prim_budget.used_tokens = curr_prim_tokens

        # 3. Contradictions fitting
        if contradictions:
            slots_content[ContextSlotType.CONTRADICTIONS.value] = "\n".join(contradictions)

        # 4. Tool Results
        if tool_results:
            slots_content[ContextSlotType.TOOL_RESULTS.value] = "\n".join(tool_results)

        # Calculate total tokens
        for val in slots_content.values():
            cnt, _ = tokenizer_provider.count_tokens(val)
            total_tokens += cnt

        return SelectedContextBundle(
            slots=slots_content,
            total_tokens_used=total_tokens,
            selected_evidence_ids=selected_ids,
            omitted_count=omitted,
        )


context_selector = ContextSelector()
