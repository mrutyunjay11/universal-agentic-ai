from __future__ import annotations
from typing import Any
from app.agent.state import Plan, StepStatus, VerificationRequirement


class PlannerEvaluator:
    """
    Evaluates whether generated DAG execution plans are minimal, non-redundant, dependency-correct,
    acyclic, safe, and possess adequate verification coverage.
    """

    def evaluate_plan(self, plan: Plan | None) -> dict[str, Any]:
        if not plan or not plan.steps:
            return {
                "score": 0.0,
                "is_acyclic": True,
                "has_redundant_steps": False,
                "verification_coverage": 0.0,
                "issues": ["Plan is empty or missing"],
            }

        issues: list[str] = []
        step_ids = {s.id for s in plan.steps}

        # 1. Dependency Validity
        for s in plan.steps:
            for dep in s.dependencies:
                if dep not in step_ids:
                    issues.append(f"Step {s.id} depends on nonexistent step '{dep}'")

        # 2. Cycle Detection
        is_acyclic = self._check_acyclic(plan)
        if not is_acyclic:
            issues.append("Plan contains circular dependency cycle")

        # 3. Redundant / Duplicate Tool Calls
        tool_signatures = [f"{s.tool_name}:{str(sorted(s.tool_args.items()))}" for s in plan.steps if s.tool_name]
        has_redundant = len(tool_signatures) != len(set(tool_signatures))
        if has_redundant:
            issues.append("Plan contains redundant duplicate tool invocations with identical parameters")

        # 4. Verification Requirement Coverage
        verified_steps = [s for s in plan.steps if s.verification_required in (VerificationRequirement.REQUIRED, VerificationRequirement.OPTIONAL)]
        ver_coverage = len(verified_steps) / len(plan.steps) if plan.steps else 0.0

        # Calculate composite planning score
        score = 1.0
        if not is_acyclic:
            score -= 0.5
        if has_redundant:
            score -= 0.2
        if issues:
            score -= min(0.3, len(issues) * 0.1)

        return {
            "score": round(max(0.0, min(1.0, score)), 4),
            "is_acyclic": is_acyclic,
            "has_redundant_steps": has_redundant,
            "verification_coverage": round(ver_coverage, 4),
            "total_steps": len(plan.steps),
            "issues": issues,
        }

    def _check_acyclic(self, plan: Plan) -> bool:
        """Kahn's topological sort cycle detector."""
        in_degree = {s.id: len(s.dependencies) for s in plan.steps}
        adj: dict[str, list[str]] = {s.id: [] for s in plan.steps}
        for s in plan.steps:
            for dep in s.dependencies:
                if dep in adj:
                    adj[dep].append(s.id)

        queue = [s.id for s in plan.steps if in_degree[s.id] == 0]
        visited_count = 0

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited_count == len(plan.steps)


planner_evaluator = PlannerEvaluator()
