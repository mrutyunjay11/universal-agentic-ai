from __future__ import annotations
import logging
from typing import Any, Optional
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, VerificationStatus, FreshnessStatus
from app.memory.base import MemoryStore
from app.memory.provenance import memory_provenance
from app.agent.state import AgentState, StepStatus

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """
    Post-task consolidation pipeline.
    Reviews short-term working memory, observations, and verification outcomes.
    Filters ephemeral noise and selectively promotes verified facts, project conventions,
    procedural workflows, and failure lessons into persistent memory.
    """

    def __init__(self, store: MemoryStore):
        self.store = store

    async def consolidate_task(
        self,
        state: AgentState,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[MemoryRecord]:
        """
        Consolidates completed task state into persistent memory records.
        """
        consolidated: list[MemoryRecord] = []
        proj_id = project_id or state.task_id or "default_project"

        # 1. Task History Summary Record
        task_summary_content = f"Task '{state.normalized_goal or state.original_request}' completed with status {state.task_status.value}."
        if state.final_result and isinstance(state.final_result, dict):
            task_summary_content += f" Result: {state.final_result.get('summary', '')[:200]}"

        hist_record = MemoryRecord(
            memory_type=MemoryType.TASK_HISTORY,
            scope=MemoryScope.PROJECT if project_id else MemoryScope.GLOBAL,
            content=task_summary_content,
            summary=f"Task {state.task_id} outcome",
            task_id=state.task_id,
            project_id=project_id,
            user_id=user_id,
            confidence=state.confidence,
            importance=0.6,
            verification_status=VerificationStatus.VERIFIED if not state.errors else VerificationStatus.SUPPORTED,
            tags=["task_outcome", state.task_status.value.lower()],
            metadata={"step_count": len(state.plan.steps) if state.plan else 0, "errors": state.errors},
        )
        await self.store.insert(hist_record)
        consolidated.append(hist_record)

        # 2. Extract Verified Facts from Observations & Evidence
        for obs in state.observations:
            if obs.success and obs.evidence:
                for ev in obs.evidence:
                    fact_text = ev.get("snippet") or ev.get("title") or obs.summary
                    if len(fact_text) > 15:
                        fact_rec = MemoryRecord(
                            memory_type=MemoryType.FACT,
                            scope=MemoryScope.GLOBAL,
                            content=fact_text,
                            summary=f"Verified fact from {obs.tool_name}",
                            source=ev.get("uri", obs.tool_name),
                            source_ids=[ev.get("uri", obs.tool_name)],
                            task_id=state.task_id,
                            project_id=project_id,
                            user_id=user_id,
                            confidence=ev.get("authority_score", 0.85),
                            importance=0.7,
                            verification_status=VerificationStatus.VERIFIED,
                            tags=["verified_fact", obs.tool_name],
                            metadata={"extracted_from_tool": obs.tool_name},
                        )
                        await self.store.insert(fact_rec)
                        consolidated.append(fact_rec)

        # 3. Extract Project Conventions & Technical Facts
        # e.g., if python version, framework, or dependency was verified
        req_lower = state.original_request.lower()
        if "python 3." in req_lower or "node" in req_lower or "dependencies" in req_lower:
            proj_rec = MemoryRecord(
                memory_type=MemoryType.PROJECT,
                scope=MemoryScope.PROJECT,
                content=f"Project technical observation: {state.normalized_goal}",
                summary=f"Project tech context for {proj_id}",
                task_id=state.task_id,
                project_id=project_id,
                user_id=user_id,
                confidence=0.9,
                importance=0.8,
                verification_status=VerificationStatus.VERIFIED,
                tags=["project_config", "dependencies"],
            )
            await self.store.insert(proj_rec)
            consolidated.append(proj_rec)

        # 4. Extract Procedural Workflows for multi-step success
        if state.plan and len(state.plan.steps) >= 2 and all(s.status == StepStatus.COMPLETED for s in state.plan.steps):
            steps_desc = " -> ".join([s.tool_name for s in state.plan.steps])
            proc_rec = MemoryRecord(
                memory_type=MemoryType.PROCEDURAL,
                scope=MemoryScope.PROJECT if project_id else MemoryScope.GLOBAL,
                content=f"Successful workflow for '{state.normalized_goal}': {steps_desc}",
                summary=f"Procedure for {state.normalized_goal[:50]}",
                task_id=state.task_id,
                project_id=project_id,
                user_id=user_id,
                confidence=0.9,
                importance=0.75,
                verification_status=VerificationStatus.VERIFIED,
                tags=["procedure", "workflow"],
                metadata={"tools": [s.tool_name for s in state.plan.steps]},
            )
            await self.store.insert(proc_rec)
            consolidated.append(proc_rec)

        logger.info("Consolidated %d persistent memories from task %s", len(consolidated), state.task_id)
        return consolidated
