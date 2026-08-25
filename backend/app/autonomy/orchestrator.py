from __future__ import annotations
import uuid
import time
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.autonomy.policies import ExecutionMode, DelegationPolicy, default_delegation_policy
from app.autonomy.task_graph import TaskGraph, SubTask, SubTaskStatus
from app.autonomy.master_planner import master_planner
from app.autonomy.scheduler import advanced_scheduler
from app.autonomy.dispatcher import task_dispatcher
from app.autonomy.aggregator import result_aggregator
from app.autonomy.conflict_resolver import conflict_resolver
from app.autonomy.watchdog import watchdog
from app.autonomy.supervisor import hierarchical_supervisor
from app.autonomy.resource_manager import resource_manager
from app.autonomy.long_horizon import long_horizon_manager
from app.autonomy.events import autonomy_event_bus, AutonomyEvent, AutonomyEventType
from app.agent.agent import universal_agent
from app.agent.state import TaskState
from app.tools.permissions import PermissionTier


class MasterTaskRecord(BaseModel):
    task_id: str
    goal: str
    execution_mode: ExecutionMode
    status: str = "PENDING"
    graph: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    evaluation: Optional[dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


import datetime


class MasterOrchestrator:
    """
    Central orchestration coordinator for Phase 5.
    Directs master planning, task decomposition, parallel dependency scheduling,
    sub-agent dispatching, watchdog monitoring, conflict resolution, verification,
    and unified aggregation.
    """

    def __init__(self, policy: Optional[DelegationPolicy] = None):
        self.policy = policy or default_delegation_policy
        self._tasks: dict[str, MasterTaskRecord] = {}
        self._graphs: dict[str, TaskGraph] = {}

    def create_task(
        self,
        goal: str,
        execution_mode: Optional[ExecutionMode] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> MasterTaskRecord:
        task_id = f"mtask_{uuid.uuid4().hex[:8]}"
        mode = execution_mode or master_planner.decide_execution_mode(goal, context)

        record = MasterTaskRecord(
            task_id=task_id,
            goal=goal,
            execution_mode=mode,
        )
        self._tasks[task_id] = record
        return record

    async def execute_task(self, task_id: str) -> MasterTaskRecord:
        record = self._tasks.get(task_id)
        if not record:
            raise ValueError(f"Master task '{task_id}' not found")

        record.status = "RUNNING"
        start_time = time.time()

        await autonomy_event_bus.emit(AutonomyEvent(
            event_type=AutonomyEventType.MASTER_TASK_CREATED,
            task_id=task_id,
            payload={"goal": record.goal, "mode": record.execution_mode.value},
        ))

        # Mode 1: Single Agent Execution
        if record.execution_mode == ExecutionMode.SINGLE_AGENT:
            state = universal_agent.create_task(
                request=record.goal,
                permission_granted=PermissionTier.SYSTEM,
            )
            completed_state = await universal_agent.run_task(state)
            record.status = completed_state.task_status.value
            record.result = {
                "summary": completed_state.final_result.get("summary", "") if completed_state.final_result else "Task finished",
                "observations": [o.summary for o in completed_state.observations],
                "verifications": [v.model_dump() for v in completed_state.verification_results],
            }
            return record

        # Mode 2: Multi-Agent Coordination & DAG Execution
        task_graph = master_planner.plan_master_task(
            task_id=task_id,
            goal=record.goal,
            mode=record.execution_mode,
        )
        self._graphs[task_id] = task_graph
        record.graph = task_graph.to_dict()

        await autonomy_event_bus.emit(AutonomyEvent(
            event_type=AutonomyEventType.TASK_DECOMPOSED,
            task_id=task_id,
            payload={"total_subtasks": len(task_graph.nodes)},
        ))

        # Save initial checkpoint
        long_horizon_manager.save_checkpoint(task_id, "INITIAL_DECOMPOSITION", task_graph)

        # Dispatcher executor hook
        async def execute_subtask_fn(subtask: SubTask):
            watchdog.record_progress()
            res = await task_dispatcher.dispatch(subtask)
            # Track resource usage
            resource_manager.record_usage(
                task_id=task_id,
                agent_name=res.agent_name,
                tokens=150,
                tool_calls=len(res.artifacts),
                duration_ms=res.execution_duration_ms,
            )
            return res

        # Run scheduler across DAG
        agent_results = await advanced_scheduler.schedule_and_execute(task_graph, execute_subtask_fn)

        # Save post-execution checkpoint
        long_horizon_manager.save_checkpoint(task_id, "POST_EXECUTION", task_graph)

        # Aggregate results
        aggregated = result_aggregator.aggregate(
            master_task_id=task_id,
            goal=record.goal,
            task_graph=task_graph,
            agent_results=agent_results,
        )

        record.status = aggregated["status"]
        record.result = aggregated
        record.graph = task_graph.to_dict()

        await autonomy_event_bus.emit(AutonomyEvent(
            event_type=AutonomyEventType.WORKFLOW_COMPLETED if record.status == "COMPLETED" else AutonomyEventType.WORKFLOW_FAILED,
            task_id=task_id,
            payload={"summary": aggregated["summary"]},
        ))

        return record

    def get_task(self, task_id: str) -> Optional[MasterTaskRecord]:
        return self._tasks.get(task_id)

    def get_task_graph(self, task_id: str) -> Optional[TaskGraph]:
        return self._graphs.get(task_id)

    def list_tasks(self) -> list[MasterTaskRecord]:
        return list(self._tasks.values())


master_orchestrator = MasterOrchestrator()
