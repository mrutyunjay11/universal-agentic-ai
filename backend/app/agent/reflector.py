from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.agent.state import AgentState, PlanStep, StepStatus
from app.agent.events import agent_event_bus, AgentEvent, EventType


class ReflectionAction(str, Enum):
    CONTINUE = "CONTINUE"
    REPLAN = "REPLAN"
    ASK_USER = "ASK_USER"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"


class ReflectionResult(BaseModel):
    action: ReflectionAction
    reason: str
    missing_information: list[str] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    confidence: float = 1.0


class ReflectionEngine:
    """Evaluates agent execution state against goal requirements, detecting failures, contradictions, and completion."""

    async def reflect(
        self,
        current_step: Optional[PlanStep],
        state: AgentState,
    ) -> ReflectionResult:
        # Check budget limits first
        if state.budget.is_exhausted:
            res = ReflectionResult(
                action=ReflectionAction.FAIL,
                reason="Task budget exhausted (iterations, execution time, tool calls, or token quota reached).",
                recommended_action="Abort or request budget increase",
                confidence=1.0,
            )
            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.REFLECTION_COMPLETED,
                payload=res.model_dump(),
            ))
            return res

        # 1. Did the current step fail?
        if current_step and current_step.status == StepStatus.FAILED:
            res = ReflectionResult(
                action=ReflectionAction.REPLAN,
                reason=f"Step '{current_step.id}' failed with error: {current_step.error}",
                recommended_action=f"Apply failure strategy: {current_step.failure_strategy.value}",
                confidence=0.85,
            )
            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.REFLECTION_COMPLETED,
                payload=res.model_dump(),
            ))
            return res

        # 2. Check if all plan steps are completed
        if state.plan and all(s.status == StepStatus.COMPLETED for s in state.plan.steps):
            # Check verification outcomes
            has_refuted = any(v.status == "refuted" for v in state.verification_results)
            if has_refuted:
                res = ReflectionResult(
                    action=ReflectionAction.REPLAN,
                    reason="A verification check refuted a step assertion. Replanning required to resolve contradiction.",
                    recommended_action="Insert diagnostic and corrective step",
                    confidence=0.90,
                )
            else:
                res = ReflectionResult(
                    action=ReflectionAction.COMPLETE,
                    reason="All plan steps successfully executed and verified against criteria.",
                    confidence=0.95,
                )

            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.REFLECTION_COMPLETED,
                payload=res.model_dump(),
            ))
            return res

        # 3. Normal continuation
        res = ReflectionResult(
            action=ReflectionAction.CONTINUE,
            reason="Step completed successfully. Proceed to next scheduled step in plan.",
            confidence=0.95,
        )
        await agent_event_bus.emit(AgentEvent(
            task_id=state.task_id,
            event_type=EventType.REFLECTION_COMPLETED,
            payload=res.model_dump(),
        ))
        return res


reflection_engine = ReflectionEngine()
