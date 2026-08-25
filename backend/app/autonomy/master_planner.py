from __future__ import annotations
from typing import Any, Optional
from app.autonomy.policies import ExecutionMode
from app.autonomy.task_graph import TaskGraph
from app.autonomy.task_decomposer import task_decomposer


class MasterPlanner:
    """
    High-level master planner. Determines whether a goal warrants single-agent or multi-agent execution,
    and produces hierarchical execution blueprints.
    """

    def decide_execution_mode(self, goal: str, context: Optional[dict[str, Any]] = None) -> ExecutionMode:
        g_lower = goal.lower()

        # Multi-domain or parallel research keywords
        multi_domain_keywords = (
            "compare", "multi-source", "research and implement", "code and verify",
            "full stack", "analyze and build", "parallel", "independent verification",
        )
        if any(kw in g_lower for kw in multi_domain_keywords):
            return ExecutionMode.SPECIALIZED_MULTI_AGENT

        # Complex workflows
        if any(kw in g_lower for kw in ("workflow", "pipeline", "end to end")):
            return ExecutionMode.HIERARCHICAL_MULTI_AGENT

        # Simple or single-turn calculations/lookups
        if len(goal.split()) < 8 and ("calculate" in g_lower or "list" in g_lower or "what is" in g_lower):
            return ExecutionMode.SINGLE_AGENT

        # Default to specialized multi-agent for non-trivial tasks
        return ExecutionMode.SPECIALIZED_MULTI_AGENT

    def plan_master_task(
        self,
        task_id: str,
        goal: str,
        mode: ExecutionMode,
        context: Optional[dict[str, Any]] = None,
    ) -> TaskGraph:
        return task_decomposer.decompose(
            master_task_id=task_id,
            goal=goal,
            context=context,
        )


master_planner = MasterPlanner()
