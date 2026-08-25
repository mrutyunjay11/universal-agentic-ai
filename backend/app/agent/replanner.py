from __future__ import annotations
import uuid
from typing import Any, Optional
from app.agent.state import Plan, PlanStep, StepStatus, FailureStrategy, RiskLevel, VerificationRequirement
from app.agent.reflector import ReflectionResult
from app.agent.events import agent_event_bus, AgentEvent, EventType


class Replanner:
    """Adapts an existing plan in response to failures, contradictions, or new discoveries without discarding prior successful work."""

    def replan(
        self,
        plan: Plan,
        reflection: ReflectionResult,
        failed_step: Optional[PlanStep] = None,
    ) -> Plan:
        new_steps: list[PlanStep] = []

        replacement_id = None
        for step in plan.steps:
            if step.status == StepStatus.COMPLETED:
                # Retain completed steps
                new_steps.append(step)
            elif failed_step and step.id == failed_step.id:
                # Handle failed step strategy
                if failed_step.failure_strategy == FailureStrategy.RETRY:
                    retry_step = failed_step.model_copy(deep=True)
                    replacement_id = f"{failed_step.id}_retry"
                    retry_step.id = replacement_id
                    retry_step.status = StepStatus.PENDING
                    retry_step.retry_count += 1
                    new_steps.append(retry_step)

                elif failed_step.failure_strategy == FailureStrategy.ALTERNATIVE_TOOL:
                    # Switch to alternative tool or query
                    alt_step = failed_step.model_copy(deep=True)
                    replacement_id = f"{failed_step.id}_alt"
                    alt_step.id = replacement_id
                    alt_step.status = StepStatus.PENDING
                    if alt_step.tool_name == "search_web":
                        alt_step.tool_name = "search_documentation"
                    elif alt_step.tool_name == "fetch_web_page":
                        alt_step.tool_name = "extract_web_content"
                    new_steps.append(alt_step)

                elif failed_step.failure_strategy == FailureStrategy.RETRY_WITH_MODIFIED_INPUT:
                    mod_step = failed_step.model_copy(deep=True)
                    replacement_id = f"{failed_step.id}_mod"
                    mod_step.id = replacement_id
                    mod_step.status = StepStatus.PENDING
                    new_steps.append(mod_step)

                else:
                    # Generic corrective diagnostic step insertion
                    replacement_id = f"step_diag_{uuid.uuid4().hex[:4]}"
                    diag_step = PlanStep(
                        id=replacement_id,
                        description=f"Diagnose and fix issue: {reflection.reason[:100]}",
                        objective="Investigate root cause and apply workaround",
                        dependencies=[s.id for s in new_steps if s.status == StepStatus.COMPLETED],
                        required_capabilities=["code.analyze", "terminal.run"],
                        tool_name="get_system_info",
                        tool_args={},
                        expected_output="Diagnostic info to unblock plan",
                        verification_required=VerificationRequirement.OPTIONAL,
                        failure_strategy=FailureStrategy.REPLAN,
                        risk_level=RiskLevel.LOW,
                    )
                    new_steps.append(diag_step)
            else:
                # Retain pending future steps
                new_steps.append(step)

        # Update dependencies of downstream steps if replacement occurred
        if failed_step and replacement_id:
            for step in new_steps:
                if failed_step.id in step.dependencies:
                    step.dependencies = [
                        replacement_id if dep == failed_step.id else dep
                        for dep in step.dependencies
                    ]

        updated_plan = Plan(
            plan_id=plan.plan_id,
            goal=plan.goal,
            steps=new_steps,
            version=plan.version + 1,
        )

        return updated_plan


replanner = Replanner()
