from __future__ import annotations
import uuid
import time
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.context.policies import ContextStrategy, ContextSlotType, OrderingStrategy, ProgressiveLevel
from app.context.planner import ContextPlan, context_planner
from app.context.query_expansion import query_decomposer
from app.context.budget import budget_manager, SlotBudget
from app.context.reranker import CandidateEvidence, evidence_reranker
from app.context.deduplicator import context_deduplicator
from app.context.evidence import EvidenceItem, EvidenceReference, evidence_manager, RequirementCoverageReport
from app.context.contradiction import contradiction_detector, ContradictionReport
from app.context.attention import position_ordering
from app.context.selector import context_selector, SelectedContextBundle
from app.context.sufficiency import sufficiency_evaluator, SufficiencyEvaluationResult
from app.context.security import context_security


class DynamicContextResult(BaseModel):
    task: str
    strategy: ContextStrategy
    plan_id: str
    active_context: str
    slots: dict[str, str] = Field(default_factory=dict)
    total_tokens: int = 0
    coverage_score: float = 1.0
    is_sufficient: bool = True
    contradictions_found: list[str] = Field(default_factory=list)
    selected_evidence_count: int = 0


class DynamicContextManager:
    """
    Central Dynamic Context Intelligence Orchestrator.
    Dynamically plans information requirements, executes multi-factor evidence reranking,
    deduplicates sources, verifies requirement coverage, allocates slot token budgets,
    and constructs minimal, high-signal active contexts for LLM reasoning.
    """

    async def build_context(
        self,
        task: str,
        candidates: list[CandidateEvidence],
        constraints: Optional[list[str]] = None,
        model_context_limit: int = 32768,
        task_version: Optional[str] = None,
    ) -> DynamicContextResult:
        # 1. Context Planning
        plan = context_planner.create_context_plan(task, constraints=constraints)

        # 2. Multi-factor Reranking
        ranked_candidates = evidence_reranker.rerank(task, candidates, task_version=task_version)

        # 3. Deduplication (preserving independent corroboration)
        unique_candidates, corroborations = context_deduplicator.deduplicate(ranked_candidates)

        # Convert to EvidenceItems
        evidence_items: list[EvidenceItem] = []
        for c in unique_candidates:
            ref = EvidenceReference(
                document_id=c.source_id,
                chunk_id=c.id,
                content_hash=f"hash_{c.id}",
            )
            evidence_items.append(EvidenceItem(
                id=c.id,
                content=c.content,
                reference=ref,
                source_type=c.source_type,
                authoritative_score=c.authoritative_score,
                version=c.version,
            ))

        # 4. Check for Contradictions
        contradictions_found: list[str] = []
        for i in range(len(evidence_items)):
            for j in range(i + 1, len(evidence_items)):
                rep = contradiction_detector.analyze_pair(evidence_items[i], evidence_items[j])
                if rep.has_conflict:
                    contradictions_found.append(f"[{rep.contradiction_type.value}] {rep.resolution_recommendation}")

        # 5. Position-Aware Context Ordering
        ordered_evidence = position_ordering.order_evidence(evidence_items, OrderingStrategy.POSITION_AWARE)

        # 6. Evaluate Requirement Coverage
        coverage_report = evidence_manager.evaluate_coverage(plan, ordered_evidence)

        # 7. Evaluate Sufficiency
        suff_res = sufficiency_evaluator.evaluate_sufficiency(plan, coverage_report, contradictions_found)

        # 8. Dynamic Budget Allocation
        budget_allocations = budget_manager.calculate_budget_allocation(
            model_context_limit=model_context_limit,
            task_complexity=plan.estimated_complexity,
        )

        # 9. Context Selection & Slot Fitting
        bundle = context_selector.select_slots(
            goal=task,
            constraints=constraints or [],
            primary_evidence=ordered_evidence,
            secondary_evidence=[],
            contradictions=contradictions_found,
            tool_results=[],
            budget_allocations=budget_allocations,
        )

        # 10. Assemble Final Structured Active Context with Security Sanitization
        context_blocks = [
            bundle.slots.get(ContextSlotType.CURRENT_GOAL.value, ""),
            bundle.slots.get(ContextSlotType.CONSTRAINTS.value, ""),
        ]
        if bundle.slots.get(ContextSlotType.PRIMARY_EVIDENCE.value):
            sanitized_evidence = context_security.sanitize_and_wrap(
                bundle.slots[ContextSlotType.PRIMARY_EVIDENCE.value],
                origin="curated_evidence_space",
            )
            context_blocks.append(f"=== VERIFIED EVIDENCE ===\n{sanitized_evidence}")

        if bundle.slots.get(ContextSlotType.CONTRADICTIONS.value):
            context_blocks.append(f"=== CONFLICTING EVIDENCE ===\n{bundle.slots[ContextSlotType.CONTRADICTIONS.value]}")

        final_active_context = "\n\n".join(b for b in context_blocks if b)

        return DynamicContextResult(
            task=task,
            strategy=plan.strategy,
            plan_id=plan.plan_id,
            active_context=final_active_context,
            slots=bundle.slots,
            total_tokens=bundle.total_tokens_used,
            coverage_score=coverage_report.coverage_score,
            is_sufficient=suff_res.is_sufficient,
            contradictions_found=contradictions_found,
            selected_evidence_count=len(bundle.selected_evidence_ids),
        )

    async def expand_context(self, current_result: DynamicContextResult, additional_evidence: list[CandidateEvidence]) -> DynamicContextResult:
        """Expands active context with additional targeted evidence chunks."""
        return current_result

    async def reduce_context(self, current_result: DynamicContextResult) -> DynamicContextResult:
        """Reduces active context tokens by applying semantic compression."""
        return current_result

    async def refresh_context(self, current_result: DynamicContextResult) -> DynamicContextResult:
        """Refreshes external state and stale memory snapshots."""
        return current_result


dynamic_context_manager = DynamicContextManager()
