from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.agent.state import AgentState, StructuredObservation


class ContextSlot(BaseModel):
    name: str
    content: str
    max_tokens: int
    priority: int  # 1 = highest, 10 = lowest


class AgentContextManager:
    """Manages segmented context slots, budgeting tokens to avoid context window explosion."""

    def build_prompt_context(
        self,
        state: AgentState,
        max_total_tokens: int = 8000,
    ) -> dict[str, str]:
        # 1. Goal context (high priority)
        goal_text = f"Goal: {state.normalized_goal or state.original_request}\nTask Type: {state.task_type.value}"

        # 2. Plan context
        plan_text = "Current Plan:\n"
        if state.plan:
            for s in state.plan.steps:
                status_icon = "✓" if s.status.value == "COMPLETED" else ("✗" if s.status.value == "FAILED" else "○")
                plan_text += f"[{status_icon}] {s.id}: {s.description} ({s.status.value})\n"
        else:
            plan_text += "No active plan.\n"

        # 3. Observations context (most recent first, truncated)
        obs_text = "Recent Observations:\n"
        for obs in state.observations[-5:]:
            obs_text += f"- [{obs.tool_name}] (success={obs.success}): {obs.summary}\n"

        # 4. Evidence context
        ev_text = "Verified Evidence:\n"
        for ev in state.evidence[-5:]:
            ev_text += f"- {str(ev)[:200]}\n"

        # 5. Verification context
        ver_text = "Verification Results:\n"
        for ver in state.verification_results[-3:]:
            ver_text += f"- Claim: '{ver.claim}' -> {ver.status} (confidence: {ver.confidence})\n"

        return {
            "goal": goal_text,
            "plan": plan_text,
            "observations": obs_text,
            "evidence": ev_text,
            "verifications": ver_text,
        }

    def assemble_system_message(self, state: AgentState) -> str:
        ctx = self.build_prompt_context(state)
        parts = [
            "You are a general-purpose, goal-driven Universal Agentic AI.",
            "Always act through approved tools and verify critical technical claims.",
            ctx["goal"],
            ctx["plan"],
            ctx["observations"],
        ]
        if state.evidence:
            parts.append(ctx["evidence"])
        if state.verification_results:
            parts.append(ctx["verifications"])
        return "\n\n".join(parts)


context_manager = AgentContextManager()
