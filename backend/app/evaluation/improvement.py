from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.evaluation.regression import regression_suite, RegressionSuite
from app.evaluation.benchmarks import benchmark_framework, BenchmarkFramework


class ImprovementType(str, Enum):
    PROMPT_OPTIMIZATION = "PROMPT_OPTIMIZATION"
    ROUTING_WEIGHT_TUNING = "ROUTING_WEIGHT_TUNING"
    RETRIEVAL_WEIGHT_TUNING = "RETRIEVAL_WEIGHT_TUNING"
    PLANNER_STRATEGY_TUNING = "PLANNER_STRATEGY_TUNING"
    VERIFICATION_RULE_UPDATE = "VERIFICATION_RULE_UPDATE"


class ImprovementStatus(str, Enum):
    PROPOSED = "PROPOSED"
    SANDBOX_VALIDATING = "SANDBOX_VALIDATING"
    BENCHMARKS_PASSED = "BENCHMARKS_PASSED"
    REJECTED_SAFETY = "REJECTED_SAFETY"
    REJECTED_REGRESSION = "REJECTED_REGRESSION"
    APPROVED_CANDIDATE = "APPROVED_CANDIDATE"
    PROMOTED_TO_PRODUCTION = "PROMOTED_TO_PRODUCTION"


class ImprovementProposal(BaseModel):
    id: str = Field(default_factory=lambda: f"imp_{uuid.uuid4().hex[:8]}")
    title: str
    improvement_type: ImprovementType
    target_component: str
    proposed_diff: dict[str, Any]
    rationale: str
    status: ImprovementStatus = ImprovementStatus.PROPOSED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validation_report: Optional[dict[str, Any]] = None


class ControlledSelfImprovementPipeline:
    """
    Evidence-based, controlled self-improvement framework.
    Evaluates candidate improvements in a sandboxed validation environment against
    benchmarks, regression suites, and safety gates before candidate promotion.
    """

    def __init__(
        self,
        reg_suite: Optional[RegressionSuite] = None,
        bench_framework: Optional[BenchmarkFramework] = None,
    ):
        self._proposals: dict[str, ImprovementProposal] = {}
        self.reg_suite = reg_suite or regression_suite
        self.bench_framework = bench_framework or benchmark_framework

    def propose_improvement(
        self,
        title: str,
        improvement_type: ImprovementType,
        target_component: str,
        proposed_diff: dict[str, Any],
        rationale: str,
    ) -> ImprovementProposal:
        proposal = ImprovementProposal(
            title=title,
            improvement_type=improvement_type,
            target_component=target_component,
            proposed_diff=proposed_diff,
            rationale=rationale,
        )
        self._proposals[proposal.id] = proposal
        return proposal

    async def validate_proposal(
        self,
        proposal_id: str,
        agent_runner: Any,
    ) -> tuple[bool, ImprovementProposal]:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal '{proposal_id}' not found")

        proposal.status = ImprovementStatus.SANDBOX_VALIDATING

        # 1. Safety Scan on proposed diff
        if any("ignore" in str(v).lower() or "exec" in str(v).lower() for v in proposal.proposed_diff.values()):
            proposal.status = ImprovementStatus.REJECTED_SAFETY
            proposal.validation_report = {"error": "Safety violation: proposed diff contains dangerous instructions"}
            return False, proposal

        # 2. Run Benchmarks in Sandbox
        bench_res = await self.bench_framework.run_benchmarks(agent_runner)
        if bench_res["pass_rate"] < 0.60:
            proposal.status = ImprovementStatus.REJECTED_REGRESSION
            proposal.validation_report = {"benchmark_results": bench_res, "error": "Benchmark pass rate below threshold"}
            return False, proposal

        # 3. Run Regression Suite
        reg_res = await self.reg_suite.run_all(agent_runner)
        if reg_res["failed_count"] > 0:
            proposal.status = ImprovementStatus.REJECTED_REGRESSION
            proposal.validation_report = {"regression_results": reg_res, "error": "Regression test failure detected"}
            return False, proposal

        proposal.status = ImprovementStatus.APPROVED_CANDIDATE
        proposal.validation_report = {
            "benchmark_pass_rate": bench_res["pass_rate"],
            "regression_pass_rate": reg_res["pass_rate"],
            "safety_passed": True,
        }
        return True, proposal

    def promote_to_production(self, proposal_id: str) -> bool:
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal.status != ImprovementStatus.APPROVED_CANDIDATE:
            return False
        proposal.status = ImprovementStatus.PROMOTED_TO_PRODUCTION
        return True

    def list_proposals(self) -> list[ImprovementProposal]:
        return list(self._proposals.values())


self_improvement_pipeline = ControlledSelfImprovementPipeline()
