from __future__ import annotations
from typing import Any
from app.agent.state import Plan, PlanStep, RiskLevel
from app.tools.registry import tool_registry
from app.tools.permissions import check_permission, PermissionTier


class PlanValidationResult:
    def __init__(self, valid: bool, errors: list[str], warnings: list[str]):
        self.valid = valid
        self.errors = errors
        self.warnings = warnings

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class PlanValidator:
    """Validates execution plans for DAG cycles, missing dependencies, tool availability, permissions, and safety policies."""

    def validate(self, plan: Plan, permission_granted: PermissionTier = PermissionTier.SYSTEM) -> PlanValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not plan.steps:
            errors.append("Plan must contain at least one step.")
            return PlanValidationResult(valid=False, errors=errors, warnings=warnings)

        step_ids = {s.id for s in plan.steps}

        # 1. Dependency integrity and cycle detection
        visited: set[str] = set()
        recursion_stack: set[str] = set()
        dep_graph: dict[str, list[str]] = {s.id: s.dependencies for s in plan.steps}

        # Check for unknown dependencies
        for step in plan.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    errors.append(f"Step '{step.id}' declares unknown dependency '{dep}'.")

        def has_cycle(node: str) -> bool:
            visited.add(node)
            recursion_stack.add(node)
            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    return True
            recursion_stack.remove(node)
            return False

        for sid in step_ids:
            if sid not in visited:
                if has_cycle(sid):
                    errors.append(f"Circular dependency detected in plan involving step '{sid}'.")
                    break

        # 2. Tool availability & Permissions
        for step in plan.steps:
            if step.tool_name:
                tool = tool_registry.get_tool(step.tool_name)
                if not tool:
                    # Check if capability can resolve it, else warn/error
                    warnings.append(f"Step '{step.id}' references tool '{step.tool_name}' which is not explicitly registered; capability routing will be used.")
                else:
                    # Check permissions
                    if not check_permission(tool.metadata.permission, permission_granted):
                        errors.append(
                            f"Step '{step.id}' requires tool '{step.tool_name}' with permission '{tool.metadata.permission.value}', but only '{permission_granted.value}' is granted."
                        )

            # 3. High risk verification check
            if step.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) and step.verification_required.value == "NONE":
                warnings.append(f"Step '{step.id}' is high-risk but has verification set to NONE.")

        is_valid = len(errors) == 0
        return PlanValidationResult(valid=is_valid, errors=errors, warnings=warnings)


plan_validator = PlanValidator()
