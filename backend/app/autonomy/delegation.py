from __future__ import annotations
from typing import Any, Optional
from app.autonomy.task_graph import SubTask
from app.autonomy.agent_profile import AgentProfile
from app.autonomy.policies import DelegationPolicy, default_delegation_policy
from app.autonomy.agent_pool import agent_pool
from app.agents.base import BaseSpecializedAgent, AgentResult


class DelegationEngine:
    """
    Constructs scoped subtask contexts with least privilege permissions,
    dispatches structured tasks to specialized sub-agents, and enforces delegation recursion limits.
    """

    def __init__(self, policy: Optional[DelegationPolicy] = None):
        self.policy = policy or default_delegation_policy

    def build_scoped_context(
        self,
        subtask: SubTask,
        parent_context: Optional[dict[str, Any]] = None,
        depth: int = 1,
    ) -> dict[str, Any]:
        """Enforces least privilege by providing only necessary objective and data."""
        if depth > self.policy.max_delegation_depth:
            raise PermissionError(f"Delegation depth {depth} exceeds maximum allowed ({self.policy.max_delegation_depth})")

        scoped = {
            "subtask_id": subtask.id,
            "objective": subtask.objective,
            "inputs": subtask.inputs,
            "permission_tier": subtask.permission_tier.value,
            "parent_task_id": subtask.parent_task_id,
            "priority": subtask.priority,
        }

        # Inherit only matching project or workspace references
        if parent_context and "project_root" in parent_context:
            scoped["project_root"] = parent_context["project_root"]

        return scoped

    async def delegate_subtask(
        self,
        subtask: SubTask,
        parent_context: Optional[dict[str, Any]] = None,
        depth: int = 1,
    ) -> AgentResult:
        scoped_ctx = self.build_scoped_context(subtask, parent_context, depth=depth)

        # Select agent if not pre-assigned
        if not subtask.assigned_agent:
            profile = agent_pool.select_agent_for_capabilities(
                required_capabilities=subtask.required_capabilities,
                preferred_tools=subtask.preferred_tools,
            )
            subtask.assigned_agent = profile.name

        agent_worker = agent_pool.get_or_spawn_agent(subtask.assigned_agent)
        result = await agent_worker.execute_subtask(subtask, shared_context=scoped_ctx)
        return result


delegation_engine = DelegationEngine()
