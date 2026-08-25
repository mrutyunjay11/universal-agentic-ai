from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field
from app.agent.state import AgentState, TaskState
from app.tools.permissions import PermissionTier


class RegressionCase(BaseModel):
    id: str = Field(default_factory=lambda: f"reg_{uuid.uuid4().hex[:8]}")
    title: str
    original_failure_reason: str
    request: str
    permission_granted: PermissionTier = PermissionTier.SYSTEM
    expected_task_status: TaskState = TaskState.COMPLETED
    expected_substrings: list[str] = Field(default_factory=list)
    forbidden_substrings: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_run_at: Optional[str] = None
    last_run_passed: Optional[bool] = None


class RegressionSuite:
    """
    Persistent regression test manager.
    Converts previously discovered failures into permanent regression cases and validates
    that candidate updates do not introduce unacceptable regressions.
    """

    def __init__(self):
        self._cases: dict[str, RegressionCase] = {}

    def add_case(
        self,
        title: str,
        original_failure_reason: str,
        request: str,
        expected_substrings: Optional[list[str]] = None,
        forbidden_substrings: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
    ) -> RegressionCase:
        case = RegressionCase(
            title=title,
            original_failure_reason=original_failure_reason,
            request=request,
            expected_substrings=expected_substrings or [],
            forbidden_substrings=forbidden_substrings or [],
            tags=tags or [],
        )
        self._cases[case.id] = case
        return case

    def create_case_from_failed_state(self, state: AgentState, failure_reason: str) -> RegressionCase:
        """Converts an observed failed agent task state into a permanent regression test case."""
        return self.add_case(
            title=f"Regression for: {state.normalized_goal or state.original_request[:50]}",
            original_failure_reason=failure_reason,
            request=state.original_request,
            expected_substrings=[],
            tags=["auto_generated_from_failure"],
        )

    def get_case(self, case_id: str) -> Optional[RegressionCase]:
        return self._cases.get(case_id)

    def list_cases(self) -> list[RegressionCase]:
        return list(self._cases.values())

    async def run_case(self, case: RegressionCase, agent_runner: Any) -> tuple[bool, str]:
        """Runs a single regression test case against the agent engine."""
        case.last_run_at = datetime.now(timezone.utc).isoformat()
        try:
            state = agent_runner.create_task(case.request, permission_granted=case.permission_granted)
            completed_state = await agent_runner.run_task(state)

            if completed_state.task_status != case.expected_task_status:
                case.last_run_passed = False
                return False, f"Expected status {case.expected_task_status.value}, got {completed_state.task_status.value}"

            summary_text = ""
            if completed_state.final_result and isinstance(completed_state.final_result, dict):
                summary_text = str(completed_state.final_result.get("summary", ""))

            for expected in case.expected_substrings:
                if expected.lower() not in summary_text.lower():
                    case.last_run_passed = False
                    return False, f"Missing expected substring '{expected}' in final response"

            for forbidden in case.forbidden_substrings:
                if forbidden.lower() in summary_text.lower():
                    case.last_run_passed = False
                    return False, f"Forbidden substring '{forbidden}' found in final response"

            case.last_run_passed = True
            return True, "Passed"

        except Exception as e:
            case.last_run_passed = False
            return False, f"Execution exception: {str(e)}"

    async def run_all(self, agent_runner: Any) -> dict[str, Any]:
        """Runs entire regression suite and computes pass rate."""
        results = []
        for case in self._cases.values():
            passed, reason = await self.run_case(case, agent_runner)
            results.append({"case_id": case.id, "title": case.title, "passed": passed, "reason": reason})

        passed_count = sum(1 for r in results if r["passed"])
        total = len(results)
        return {
            "total_cases": total,
            "passed_count": passed_count,
            "failed_count": total - passed_count,
            "pass_rate": round(passed_count / max(1, total), 4),
            "results": results,
        }


regression_suite = RegressionSuite()
