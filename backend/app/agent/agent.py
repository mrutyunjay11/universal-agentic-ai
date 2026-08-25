from __future__ import annotations
import time
import uuid
import datetime
from typing import Any, Optional

from app.agent.state import (
    AgentState,
    TaskState,
    Plan,
    PlanStep,
    StepStatus,
    RiskLevel,
    VerificationRequirement,
    FailureStrategy,
)
from app.agent.events import agent_event_bus, AgentEvent, EventType
from app.agent.understanding import task_understander, GoalUnderstanding
from app.agent.classifier import task_classifier
from app.agent.planner import planner
from app.agent.plan_validator import plan_validator
from app.agent.router import tool_router
from app.agent.executor import execution_engine, StepExecutionResult
from app.agent.observer import observation_manager
from app.agent.verifier import verification_coordinator
from app.agent.reflector import reflection_engine, ReflectionAction
from app.agent.replanner import replanner
from app.agent.context import context_manager
from app.agent.budget import budget_manager
from app.agent.checkpoint import checkpoint_manager
from app.agent.models.router import model_router, ModelRole
from app.agent.prompts.templates import get_prompt
from app.tools.permissions import PermissionTier


class UniversalAgent:
    """Master orchestrator implementing the complete goal-driven Agentic AI lifecycle."""

    def __init__(self, project_root: str = "./projects"):
        self.project_root = project_root
        self._tasks: dict[str, AgentState] = {}

    def create_task(
        self,
        request: str,
        session_id: Optional[str] = None,
        permission_granted: PermissionTier = PermissionTier.READ_WRITE,
    ) -> AgentState:
        state = AgentState(
            session_id=session_id or f"sess_{uuid.uuid4().hex[:8]}",
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            original_request=request,
            permission_granted=permission_granted,
        )
        budget_manager.init_budget(state)
        self._tasks[state.task_id] = state
        checkpoint_manager.save_checkpoint(state)

        return state

    def get_task(self, task_id: str) -> Optional[AgentState]:
        if task_id in self._tasks:
            return self._tasks[task_id]
        return checkpoint_manager.load_latest_checkpoint(task_id)

    async def run_task(self, state: AgentState) -> AgentState:
        start_time = time.time()

        # Emit task created
        await agent_event_bus.emit(AgentEvent(
            task_id=state.task_id,
            event_type=EventType.TASK_CREATED,
            payload={"request": state.original_request},
        ))

        try:
            # Stage 1: Task Understanding
            state.transition_to(TaskState.UNDERSTANDING)
            await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
            understanding: GoalUnderstanding = task_understander.understand(state.original_request)
            state.normalized_goal = understanding.normalized_goal
            state.context["understanding"] = understanding.model_dump()

            # Retrieve relevant long-term & project memories
            try:
                from app.memory.manager import memory_manager
                retrieved_mems = await memory_manager.retrieve(
                    query=state.original_request,
                    limit=5,
                    project_id=self.project_root,
                )
                state.context["retrieved_memories"] = [m.to_dict() for _, m in retrieved_mems]
            except Exception as mem_err:
                logger.debug("Memory retrieval skipped: %s", mem_err)

            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.TASK_UNDERSTOOD,
                payload=understanding.model_dump(),
            ))

            # Stage 2: Task Classification & Planning
            state.transition_to(TaskState.PLANNING)
            await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
            state.task_type = task_classifier.classify(state.original_request)
            plan: Plan = planner.plan(understanding, state.task_type)
            state.plan = plan
            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.PLAN_CREATED,
                payload=plan.model_dump(),
            ))

            # Stage 3: Plan Validation
            state.transition_to(TaskState.PLAN_VALIDATION)
            await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
            val_res = plan_validator.validate(state.plan, state.permission_granted)
            if not val_res.valid:
                state.warnings.extend(val_res.warnings)
                state.errors.append({"stage": "validation", "errors": val_res.errors})
                state.transition_to(TaskState.FAILED)
                await agent_event_bus.emit(AgentEvent(
                    task_id=state.task_id,
                    event_type=EventType.TASK_FAILED,
                    payload={"errors": val_res.errors},
                ))
                return state

            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.PLAN_VALIDATED,
                payload=val_res.to_dict(),
            ))

            # Stage 4: Controlled Execution Loop
            while state.plan and not all(s.status == StepStatus.COMPLETED for s in state.plan.steps):
                budget_manager.record_iteration(state)
                budget_manager.record_elapsed_time(state, start_time)

                within_budget, budget_err = budget_manager.check_budget(state)
                if not within_budget:
                    state.errors.append({"error": budget_err})
                    state.transition_to(TaskState.FAILED)
                    await agent_event_bus.emit(AgentEvent(
                        task_id=state.task_id,
                        event_type=EventType.TASK_FAILED,
                        payload={"error": budget_err},
                    ))
                    return state

                # Find next executable pending step
                executable_steps = [
                    s for s in state.plan.steps
                    if s.status == StepStatus.PENDING
                    and all(any(prev.id == d and prev.status == StepStatus.COMPLETED for prev in state.plan.steps) for d in s.dependencies)
                ]
                if not executable_steps:
                    pending = [s for s in state.plan.steps if s.status == StepStatus.PENDING]
                    if not pending:
                        break
                    step = pending[0]
                else:
                    step = executable_steps[0]

                # 4a. Execute
                state.transition_to(TaskState.EXECUTING)
                await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
                exec_res: StepExecutionResult = await execution_engine.execute_step(step, state, self.project_root)

                if exec_res.needs_approval:
                    state.transition_to(TaskState.WAITING_FOR_APPROVAL)
                    await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
                    checkpoint_manager.save_checkpoint(state)
                    return state

                # 4b. Observe
                state.transition_to(TaskState.OBSERVING)
                await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
                obs = observation_manager.observe(step, exec_res, state)
                await agent_event_bus.emit(AgentEvent(
                    task_id=state.task_id,
                    event_type=EventType.OBSERVATION_CREATED,
                    payload=obs.model_dump(),
                ))

                # 4c. Verify
                state.transition_to(TaskState.VERIFYING)
                await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
                await verification_coordinator.verify_step(step, state, self.project_root)

                # 4d. Reflect
                state.transition_to(TaskState.REFLECTING)
                await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
                reflection = await reflection_engine.reflect(step, state)

                if reflection.action == ReflectionAction.FAIL:
                    state.transition_to(TaskState.FAILED)
                    await agent_event_bus.emit(AgentEvent(
                        task_id=state.task_id,
                        event_type=EventType.TASK_FAILED,
                        payload={"reason": reflection.reason},
                    ))
                    return state

                elif reflection.action == ReflectionAction.REPLAN:
                    state.transition_to(TaskState.REPLANNING)
                    await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
                    state.plan = replanner.replan(state.plan, reflection, step)
                    await agent_event_bus.emit(AgentEvent(
                        task_id=state.task_id,
                        event_type=EventType.REPLAN_CREATED,
                        payload=state.plan.model_dump(),
                    ))
                    # Validate replanned plan
                    state.transition_to(TaskState.PLAN_VALIDATION)
                    await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))
                    val_res = plan_validator.validate(state.plan, state.permission_granted)
                    if not val_res.valid:
                        state.transition_to(TaskState.FAILED)
                        return state

                elif reflection.action == ReflectionAction.COMPLETE:
                    break

                checkpoint_manager.save_checkpoint(state)

            # Stage 5: Final Synthesis & Completion
            state.transition_to(TaskState.COMPLETED)
            await agent_event_bus.emit(AgentEvent(task_id=state.task_id, event_type=EventType.STATE_CHANGED, payload={"state": state.task_status.value}))

            # Build grounded summary
            summary_points = []
            if state.plan:
                summary_points.append(f"Completed {len([s for s in state.plan.steps if s.status == StepStatus.COMPLETED])} execution steps.")
            if state.verification_results:
                summary_points.append(f"Performed {len(state.verification_results)} verification checks.")
            if state.evidence:
                summary_points.append(f"Collected {len(state.evidence)} evidence references.")

            final_answer = f"Task completed successfully: '{state.normalized_goal}'.\n" + "\n".join(f"- {p}" for p in summary_points)
            if state.observations:
                final_answer += f"\n\nKey Finding: {state.observations[-1].summary}"

            state.confidence = 0.95 if not state.errors else 0.70
            state.final_result = {
                "goal": state.normalized_goal,
                "summary": final_answer,
                "confidence": state.confidence,
                "steps_completed": [s.id for s in state.plan.steps if s.status == StepStatus.COMPLETED] if state.plan else [],
                "evidence_count": len(state.evidence),
                "verifications_passed": len([v for v in state.verification_results if v.status == "verified"]),
            }

            checkpoint_manager.save_checkpoint(state)

            # Consolidate completed task into persistent memory
            try:
                from app.memory.manager import memory_manager
                await memory_manager.consolidate_task(state, project_id=self.project_root)
            except Exception as cons_err:
                logger.debug("Memory consolidation error: %s", cons_err)

            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.TASK_COMPLETED,
                payload=state.final_result,
            ))

            return state

        except Exception as e:
            state.errors.append({"fatal_exception": str(e)})
            try:
                state.transition_to(TaskState.FAILED)
            except Exception:
                state.task_status = TaskState.FAILED
            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.TASK_FAILED,
                payload={"error": str(e)},
            ))
            return state

    async def resume_task(self, task_id: str, approved: bool = True) -> Optional[AgentState]:
        state = self.get_task(task_id)
        if not state:
            return None

        if state.task_status != TaskState.WAITING_FOR_APPROVAL:
            return state

        if approved:
            # Grant approval
            if state.pending_approval:
                state.user_approvals.append({**state.pending_approval, "approved": True})
                state.pending_approval = None
            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.APPROVAL_GRANTED,
                payload={"task_id": task_id},
            ))
            return await self.run_task(state)
        else:
            state.user_approvals.append({**(state.pending_approval or {}), "approved": False})
            state.pending_approval = None
            await agent_event_bus.emit(AgentEvent(
                task_id=state.task_id,
                event_type=EventType.APPROVAL_DENIED,
                payload={"task_id": task_id},
            ))
            state.transition_to(TaskState.CANCELLED)
            return state

    async def cancel_task(self, task_id: str) -> Optional[AgentState]:
        state = self.get_task(task_id)
        if not state:
            return None
        state.task_status = TaskState.CANCELLED
        await agent_event_bus.emit(AgentEvent(
            task_id=state.task_id,
            event_type=EventType.TASK_CANCELLED,
            payload={"task_id": task_id},
        ))
        checkpoint_manager.save_checkpoint(state)
        return state


universal_agent = UniversalAgent()
