from __future__ import annotations
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.context.policies import ContextStrategy


class InformationRequirement(BaseModel):
    id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:6]}")
    description: str
    requirement_type: str = "FACT"  # "FACT", "CODE", "VERSION", "COMPATIBILITY", "SPECIFICATION"
    is_mandatory: bool = True
    coverage_status: str = "MISSING"  # "COVERED", "PARTIAL", "MISSING"


class ContextPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"cplan_{uuid.uuid4().hex[:8]}")
    task: str
    strategy: ContextStrategy = ContextStrategy.HYBRID
    required_information: list[InformationRequirement] = Field(default_factory=list)
    verification_requirements: list[str] = Field(default_factory=list)
    estimated_complexity: str = "MEDIUM"


class ContextPlanner:
    """
    Context Planner.
    Analyzes the current reasoning step to determine exact information requirements,
    verification requirements, and selects the appropriate dynamic context strategy.
    Does NOT replace the Phase 2 Agent task planner.
    """

    def create_context_plan(
        self,
        task: str,
        constraints: Optional[list[str]] = None,
        strategy_override: Optional[ContextStrategy] = None,
    ) -> ContextPlan:
        task_lower = task.lower()

        # Strategy selection heuristics
        if strategy_override:
            strategy = strategy_override
        elif "compare" in task_lower or "conflict" in task_lower or "research" in task_lower:
            strategy = ContextStrategy.ITERATIVE_RAG
        elif "dataset" in task_lower or "calculate" in task_lower or "rows" in task_lower:
            strategy = ContextStrategy.TOOL_COMPUTATION
        elif "large document" in task_lower or "pdf" in task_lower or "spec" in task_lower:
            strategy = ContextStrategy.HIERARCHICAL_RETRIEVAL
        elif len(task) < 100 and not any(k in task_lower for k in ["version", "v1", "v2", "v3", "v4", "framework", "library", "compatibility", "support", "migration", "refactor"]):
            strategy = ContextStrategy.DIRECT_CONTEXT
        else:
            strategy = ContextStrategy.HYBRID

        # Extract information requirements
        reqs: list[InformationRequirement] = []

        if any(k in task_lower for k in ["version", "v1", "v2", "v3", "v4", "compatibility", "support", "migration", "pydantic", "fastapi"]):
            reqs.append(InformationRequirement(description="Current library framework versions", requirement_type="VERSION"))
            reqs.append(InformationRequirement(description="Official compatibility documentation release notes", requirement_type="COMPATIBILITY"))
            reqs.append(InformationRequirement(description="Breaking changes or migration guides", requirement_type="SPECIFICATION"))
        elif "security" in task_lower or "vulnerability" in task_lower:
            reqs.append(InformationRequirement(description="Advisory records CVE details", requirement_type="FACT"))
            reqs.append(InformationRequirement(description="Remediation steps patched versions", requirement_type="SPECIFICATION"))
        elif any(k in task_lower for k in ["code", "function", "module", "class", "refactor", "method"]):
            reqs.append(InformationRequirement(description="Symbol definition and implementation", requirement_type="CODE"))
            reqs.append(InformationRequirement(description="Callers and usage references", requirement_type="CODE"))
        else:
            reqs.append(InformationRequirement(description=f"Primary evidence supporting task: {task[:60]}", requirement_type="FACT"))

        verif_reqs = ["primary_source_attribution"]
        if any(k in task_lower for k in ["version", "v1", "v2", "v3", "v4", "compatibility", "migration", "support"]):
            verif_reqs.append("version_validation")
        if any(k in task_lower for k in ["code", "function", "module", "class", "refactor", "method", "test"]):
            verif_reqs.append("syntax_and_test_validation")

        return ContextPlan(
            task=task,
            strategy=strategy,
            required_information=reqs,
            verification_requirements=verif_reqs,
            estimated_complexity="HIGH" if len(reqs) > 2 else "MEDIUM",
        )


context_planner = ContextPlanner()
