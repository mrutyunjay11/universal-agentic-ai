from __future__ import annotations
import re
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.agent.state import RiskLevel


class GoalUnderstanding(BaseModel):
    normalized_goal: str
    constraints: list[str] = Field(default_factory=list)
    known_facts: list[str] = Field(default_factory=list)
    unknown_information: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    potential_risks: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_code_execution: bool = False
    requires_web_research: bool = False
    requires_filesystem_write: bool = False
    requires_verification: bool = False


class TaskUnderstander:
    """Extracts explicit goals, constraints, required evidence, risks, and success criteria."""

    def understand(self, request: str, context: Optional[dict[str, Any]] = None) -> GoalUnderstanding:
        req_clean = request.strip()
        req_lower = req_clean.lower()

        constraints: list[str] = []
        known_facts: list[str] = []
        unknown_info: list[str] = []
        required_evidence: list[str] = []
        success_criteria: list[str] = []
        potential_risks: list[str] = []

        # 1. Detect capabilities needed
        req_code = any(k in req_lower for k in ("code", "python", "script", "function", "class", "test", "debug", "refactor", "bug", "implement"))
        req_web = any(k in req_lower for k in ("search", "find out", "research", "browse", "website", "documentation", "latest", "news", "google", "arxiv"))
        req_write = any(k in req_lower for k in ("write", "create file", "save", "modify", "edit", "update file", "delete", "remove"))
        req_verify = any(k in req_lower for k in ("verify", "check", "fact-check", "is it true", "compatible", "test it", "validate", "confirm"))
        req_math = any(k in req_lower for k in ("calculate", "solve", "matrix", "equation", "formula", "convert", "unit"))
        req_data = any(k in req_lower for k in ("csv", "json", "dataset", "dataframe", "columns", "average", "statistics"))

        # 2. Extract constraints
        if "without" in req_lower:
            m = re.findall(r"without\s+([^,.]+)", req_clean, re.IGNORECASE)
            for c in m:
                constraints.append(f"Must proceed without: {c.strip()}")

        if "only" in req_lower:
            m = re.findall(r"only\s+([^,.]+)", req_clean, re.IGNORECASE)
            for c in m:
                constraints.append(f"Restricted to only: {c.strip()}")

        # 3. Required evidence & Success criteria
        if req_verify or "compatible" in req_lower:
            required_evidence.append("Primary official documentation or direct execution test result")
            success_criteria.append("Claim verified or disproven with verifiable evidence")

        if req_web:
            required_evidence.append("Authoritative web or documentation sources with URLs")
            success_criteria.append("Synthesized findings with source citations")

        if req_code:
            required_evidence.append("Syntax check and unit test assertions")
            success_criteria.append("Code implemented, inspected, and verified via test execution")

        if req_math:
            required_evidence.append("Deterministic calculation or symbolic math proof")
            success_criteria.append("Computed numerical/symbolic result matching mathematical precision")

        if req_data:
            required_evidence.append("Descriptive statistics and schema validation of target dataset")
            success_criteria.append("Structured data analysis summary produced")

        if not success_criteria:
            success_criteria.append("Complete answer addressing all points of the user request")

        # 4. Risks & Risk Level
        risk_level = RiskLevel.LOW
        if any(k in req_lower for k in ("rm -rf", "delete", "destroy", "drop database", "overwrite", "kill")):
            potential_risks.append("Potential permanent data deletion or process termination")
            risk_level = RiskLevel.HIGH
        elif req_write:
            potential_risks.append("Filesystem modification")
            risk_level = RiskLevel.MEDIUM

        if any(k in req_lower for k in ("system", "sudo", "execute", "install", "pip install", "npm install")):
            potential_risks.append("Environment dependency or system execution mutation")
            if risk_level != RiskLevel.HIGH:
                risk_level = RiskLevel.MEDIUM

        # 5. Normalized goal
        normalized_goal = req_clean.rstrip(".")
        if len(normalized_goal) > 200:
            # First sentence or summary
            first_sent = req_clean.split(".")[0]
            normalized_goal = first_sent.strip()

        return GoalUnderstanding(
            normalized_goal=normalized_goal,
            constraints=constraints,
            known_facts=known_facts,
            unknown_information=unknown_info,
            required_evidence=required_evidence,
            success_criteria=success_criteria,
            potential_risks=potential_risks,
            risk_level=risk_level,
            requires_code_execution=req_code,
            requires_web_research=req_web,
            requires_filesystem_write=req_write,
            requires_verification=req_verify or req_code,
        )


task_understander = TaskUnderstander()
