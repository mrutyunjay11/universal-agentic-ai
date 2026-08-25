from __future__ import annotations
import uuid
import re
from typing import Any, Optional
from app.agent.state import Plan, PlanStep, TaskType, VerificationRequirement, FailureStrategy, RiskLevel
from app.agent.understanding import GoalUnderstanding


class DAGPlanner:
    """Generates structured DAG plans where each step defines dependencies, required capabilities, verification, and failure strategies."""

    def plan(self, understanding: GoalUnderstanding, task_type: TaskType, context: Optional[dict[str, Any]] = None) -> Plan:
        goal = understanding.normalized_goal
        steps: list[PlanStep] = []

        if task_type == TaskType.RESEARCH:
            steps = [
                PlanStep(
                    id="step_1",
                    description=f"Search authoritative web and documentation sources for '{goal}'",
                    objective="Gather primary information and citations",
                    dependencies=[],
                    required_capabilities=["web.search", "web.extract"],
                    tool_name="search_web",
                    tool_args={"query": goal},
                    expected_output="Relevant search results with URLs and snippets",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.ALTERNATIVE_SOURCE,
                    risk_level=RiskLevel.LOW,
                ),
                PlanStep(
                    id="step_2",
                    description="Verify source authority, dates, and extract core findings",
                    objective="Validate findings against reliable sources",
                    dependencies=["step_1"],
                    required_capabilities=["verify.source_authority", "verify.claims"],
                    tool_name="extract_claims",
                    tool_args={},
                    expected_output="Verified claims with source citations",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.LOW,
                ),
            ]

        elif task_type in (TaskType.CODING, TaskType.DEBUGGING):
            steps = [
                PlanStep(
                    id="step_1",
                    description="Inspect project structure and relevant source files",
                    objective="Understand existing codebase and context",
                    dependencies=[],
                    required_capabilities=["file.list", "file.read"],
                    tool_name="list_directory",
                    tool_args={"dir_path": "."},
                    expected_output="File hierarchy and existing module locations",
                    verification_required=VerificationRequirement.OPTIONAL,
                    failure_strategy=FailureStrategy.RETRY,
                    risk_level=RiskLevel.LOW,
                ),
                PlanStep(
                    id="step_2",
                    description=f"Analyze code symbols or write solution for '{goal}'",
                    objective="Implement code modification or bug fix",
                    dependencies=["step_1"],
                    required_capabilities=["code.analyze", "file.write", "file.edit"],
                    tool_name="write_file",
                    tool_args={},
                    expected_output="Target code written or edited successfully",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.MEDIUM,
                ),
                PlanStep(
                    id="step_3",
                    description="Execute unit tests to verify implementation correctness",
                    objective="Validate syntax and verify test assertions pass",
                    dependencies=["step_2"],
                    required_capabilities=["verify.code", "testing.run"],
                    tool_name="verify_code",
                    tool_args={},
                    expected_output="All unit tests and assertions passing",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.LOW,
                ),
            ]

        elif task_type == TaskType.FACT_CHECK:
            steps = [
                PlanStep(
                    id="step_1",
                    description=f"Search multiple independent sources for claim: '{goal}'",
                    objective="Retrieve evidence from diverse authoritative sources",
                    dependencies=[],
                    required_capabilities=["web.search", "web.extract"],
                    tool_name="search_web",
                    tool_args={"query": goal},
                    expected_output="Search results from multiple domains",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.ALTERNATIVE_SOURCE,
                    risk_level=RiskLevel.LOW,
                ),
                PlanStep(
                    id="step_2",
                    description="Cross-examine sources for contradictions and authority",
                    objective="Detect discrepancies and calculate confidence",
                    dependencies=["step_1"],
                    required_capabilities=["verify.contradiction", "verify.source_authority"],
                    tool_name="check_source_authority",
                    tool_args={},
                    expected_output="Contradiction check and authority evaluation",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.LOW,
                ),
                PlanStep(
                    id="step_3",
                    description="Produce final grounded verification verdict",
                    objective="Synthesize evidence into verified/refuted conclusion",
                    dependencies=["step_2"],
                    required_capabilities=["verify.claim"],
                    tool_name="verify_claim",
                    tool_args={"claim": goal},
                    expected_output="Structured verdict with confidence score and evidence citations",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.LOW,
                ),
            ]

        elif task_type == TaskType.DATA_ANALYSIS:
            steps = [
                PlanStep(
                    id="step_1",
                    description=f"Read and analyze dataset for '{goal}'",
                    objective="Inspect schema, columns, and data distributions",
                    dependencies=[],
                    required_capabilities=["data.read", "data.analyze"],
                    tool_name="read_csv",
                    tool_args={},
                    expected_output="Dataset rows and column summary",
                    verification_required=VerificationRequirement.OPTIONAL,
                    failure_strategy=FailureStrategy.RETRY,
                    risk_level=RiskLevel.LOW,
                ),
                PlanStep(
                    id="step_2",
                    description="Calculate summary statistics and detect outliers",
                    objective="Compute descriptive statistics and anomalies",
                    dependencies=["step_1"],
                    required_capabilities=["data.statistics", "data.outliers"],
                    tool_name="calculate_statistics",
                    tool_args={},
                    expected_output="Statistical analysis metrics",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.LOW,
                ),
            ]

        elif task_type == TaskType.MATHEMATICAL:
            steps = [
                PlanStep(
                    id="step_1",
                    description=f"Compute deterministic numerical/symbolic solution for '{goal}'",
                    objective="Calculate mathematical result with AST verification",
                    dependencies=[],
                    required_capabilities=["math.calculate", "math.symbolic"],
                    tool_name="calculator",
                    tool_args={"expression": goal},
                    expected_output="Exact computed value",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.RETRY_WITH_MODIFIED_INPUT,
                    risk_level=RiskLevel.LOW,
                ),
                PlanStep(
                    id="step_2",
                    description="Verify computed result against mathematical constraints",
                    objective="Confirm accuracy with tolerance bounds",
                    dependencies=["step_1"],
                    required_capabilities=["verify.calculation"],
                    tool_name="verify_calculation",
                    tool_args={"expression": goal},
                    expected_output="Verified mathematical proof/value",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.LOW,
                ),
            ]

        elif task_type == TaskType.MULTI_DOMAIN:
            # e.g., Research + Code + Verification
            steps = [
                PlanStep(
                    id="step_1",
                    description=f"Research documentation and specifications for '{goal}'",
                    objective="Gather official specs and compatibility information",
                    dependencies=[],
                    required_capabilities=["web.search", "web.extract"],
                    tool_name="search_web",
                    tool_args={"query": goal},
                    expected_output="Official documentation and usage examples",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.ALTERNATIVE_SOURCE,
                    risk_level=RiskLevel.LOW,
                ),
                PlanStep(
                    id="step_2",
                    description="Inspect project environment and files",
                    objective="Verify local project readiness",
                    dependencies=[],
                    required_capabilities=["file.list", "system.info"],
                    tool_name="list_directory",
                    tool_args={"dir_path": "."},
                    expected_output="Local environment inventory",
                    verification_required=VerificationRequirement.OPTIONAL,
                    failure_strategy=FailureStrategy.RETRY,
                    risk_level=RiskLevel.LOW,
                ),
                PlanStep(
                    id="step_3",
                    description="Execute technical validation test in sandbox",
                    objective="Empirically verify functionality with test execution",
                    dependencies=["step_1", "step_2"],
                    required_capabilities=["verify.code", "testing.run"],
                    tool_name="verify_code",
                    tool_args={},
                    expected_output="Empirical execution results confirming or refuting support",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.MEDIUM,
                ),
                PlanStep(
                    id="step_4",
                    description="Synthesize verified findings with evidence citations",
                    objective="Formulate grounded conclusion with confidence score",
                    dependencies=["step_3"],
                    required_capabilities=["verify.claim"],
                    tool_name="verify_claim",
                    tool_args={"claim": goal},
                    expected_output="Comprehensive verified conclusion",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.LOW,
                ),
            ]

        else:
            # Generic / System / Other
            steps = [
                PlanStep(
                    id="step_1",
                    description=f"Investigate and gather context for '{goal}'",
                    objective="Collect relevant data and inspect context",
                    dependencies=[],
                    required_capabilities=["system.info", "file.read"],
                    tool_name="get_system_info",
                    tool_args={},
                    expected_output="Initial diagnostic context",
                    verification_required=VerificationRequirement.OPTIONAL,
                    failure_strategy=FailureStrategy.RETRY,
                    risk_level=RiskLevel.LOW,
                ),
                PlanStep(
                    id="step_2",
                    description=f"Execute required actions for '{goal}'",
                    objective="Fulfill user objective",
                    dependencies=["step_1"],
                    required_capabilities=["terminal.run", "file.write"],
                    tool_name="execute_terminal",
                    tool_args={},
                    expected_output="Action execution output",
                    verification_required=VerificationRequirement.REQUIRED,
                    failure_strategy=FailureStrategy.REPLAN,
                    risk_level=RiskLevel.LOW,
                ),
            ]

        return Plan(
            goal=goal,
            steps=steps,
            version=1,
        )

    def get_execution_layers(self, plan: Plan) -> list[list[PlanStep]]:
        """Topological sort grouping independent steps into parallel execution layers."""
        completed: set[str] = set()
        remaining = list(plan.steps)
        layers: list[list[PlanStep]] = []

        while remaining:
            current_layer: list[PlanStep] = []
            for step in remaining:
                if all(dep in completed for dep in step.dependencies):
                    current_layer.append(step)

            if not current_layer:
                # Circular dependency or broken graph - fallback to sequential
                current_layer = [remaining[0]]

            layers.append(current_layer)
            for s in current_layer:
                completed.add(s.id)
                remaining.remove(s)

        return layers


planner = DAGPlanner()
