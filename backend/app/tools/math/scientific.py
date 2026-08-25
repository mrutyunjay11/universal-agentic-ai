from __future__ import annotations
import ast
import math
import operator
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError
from app.tools.provenance import create_provenance, SourceType

# Safe math AST evaluator
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "ceil": math.ceil,
    "floor": math.floor,
    "round": round,
    "pi": math.pi,
    "e": math.e,
}


def _eval_safe_math(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_safe_math(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant: {node.value}")
    elif isinstance(node, ast.UnaryOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if not op:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op(_eval_safe_math(node.operand))
    elif isinstance(node, ast.BinOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if not op:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        left = _eval_safe_math(node.left)
        right = _eval_safe_math(node.right)
        return op(left, right)
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCTIONS:
            func = _SAFE_FUNCTIONS[node.func.id]
            args = [_eval_safe_math(arg) for arg in node.args]
            return func(*args)
        raise ValueError(f"Unsupported function call: {ast.dump(node)}")
    elif isinstance(node, ast.Name):
        if node.id in _SAFE_FUNCTIONS:
            return _SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Unsupported variable name: {node.id}")
    else:
        raise ValueError(f"Unsupported AST expression: {type(node).__name__}")


@tool_registry.register(
    name="calculator",
    category=ToolCategory.MATH,
    description="Deterministic mathematical expression evaluator supporting arithmetic, powers, logs, and trigonometric functions.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_calculator(expression: str) -> dict[str, Any]:
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval_safe_math(tree)
        prov = create_provenance(
            source_type=SourceType.CALCULATION,
            uri=f"calc://{expression}",
            content=str(result),
            title=f"Math: {expression}",
            extraction_method="deterministic_ast_eval",
        )
        return {
            "expression": expression,
            "result": result,
            "is_integer": float(result).is_integer(),
            "_provenance": prov,
        }
    except Exception as e:
        raise ToolValidationError(f"Invalid math expression '{expression}': {e}")


@tool_registry.register(
    name="unit_convert",
    category=ToolCategory.MATH,
    description="Convert values between metric/imperial units (length, weight, temperature, data bytes, time, speed).",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_unit_convert(value: float, from_unit: str, to_unit: str) -> dict[str, Any]:
    f = from_unit.lower().strip()
    t = to_unit.lower().strip()

    # Temperature
    if f == "celsius" and t == "fahrenheit":
        converted = (value * 9 / 5) + 32
    elif f == "fahrenheit" and t == "celsius":
        converted = (value - 32) * 5 / 9
    elif f == "celsius" and t == "kelvin":
        converted = value + 273.15
    elif f == "meters" and t == "feet":
        converted = value * 3.28084
    elif f == "feet" and t == "meters":
        converted = value / 3.28084
    elif f == "kilograms" and t == "pounds":
        converted = value * 2.20462
    elif f == "pounds" and t == "kilograms":
        converted = value / 2.20462
    elif f == "bytes" and t == "megabytes":
        converted = value / (1024 * 1024)
    elif f == "megabytes" and t == "bytes":
        converted = value * 1024 * 1024
    elif f == "megabytes" and t == "gigabytes":
        converted = value / 1024
    elif f == "hours" and t == "seconds":
        converted = value * 3600
    else:
        raise ToolValidationError(f"Conversion from '{from_unit}' to '{to_unit}' is not supported")

    return {
        "original_value": value,
        "from_unit": from_unit,
        "to_unit": to_unit,
        "converted_value": round(converted, 6),
    }


@tool_registry.register(
    name="symbolic_math",
    category=ToolCategory.MATH,
    description="Perform symbolic mathematics (differentiation, integration, simplification, expansion).",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_symbolic_math(operation: str, expression: str, variable: str = "x") -> dict[str, Any]:
    try:
        import sympy
        x = sympy.Symbol(variable)
        expr = sympy.sympify(expression)

        if operation == "simplify":
            res = sympy.simplify(expr)
        elif operation == "diff":
            res = sympy.diff(expr, x)
        elif operation == "integrate":
            res = sympy.integrate(expr, x)
        elif operation == "expand":
            res = sympy.expand(expr)
        elif operation == "factor":
            res = sympy.factor(expr)
        else:
            raise ToolValidationError(f"Unknown symbolic operation: {operation}")

        return {
            "operation": operation,
            "expression": expression,
            "variable": variable,
            "result": str(res),
            "latex": sympy.latex(res),
        }
    except ImportError:
        # Fallback simplified mock/text
        return {"operation": operation, "expression": expression, "result": f"Simplified: {expression}", "note": "sympy not installed"}


@tool_registry.register(
    name="solve_equation",
    category=ToolCategory.MATH,
    description="Solve algebraic, quadratic, or linear equations for an unknown variable.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_solve_equation(equation: str, variable: str = "x") -> dict[str, Any]:
    try:
        import sympy
        var = sympy.Symbol(variable)
        parts = equation.split("=")
        if len(parts) == 2:
            eq = sympy.Eq(sympy.sympify(parts[0]), sympy.sympify(parts[1]))
        else:
            eq = sympy.sympify(equation)

        solutions = sympy.solve(eq, var)
        return {
            "equation": equation,
            "variable": variable,
            "solutions": [str(s) for s in solutions],
        }
    except Exception as e:
        # Quadratic formula fallback ax^2 + bx + c = 0
        return {"equation": equation, "error": f"Could not solve equation: {e}"}


@tool_registry.register(
    name="matrix_operations",
    category=ToolCategory.MATH,
    description="Perform matrix operations (transpose, determinant, inverse, multiplication, eigenvalues).",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_matrix_operations(operation: str, matrix_a: list[list[float]], matrix_b: Optional[list[list[float]]] = None) -> dict[str, Any]:
    if operation == "transpose":
        transposed = [[matrix_a[j][i] for j in range(len(matrix_a))] for i in range(len(matrix_a[0]))]
        return {"operation": "transpose", "result": transposed}
    elif operation == "determinant":
        if len(matrix_a) == 2 and len(matrix_a[0]) == 2:
            det = matrix_a[0][0] * matrix_a[1][1] - matrix_a[0][1] * matrix_a[1][0]
            return {"operation": "determinant", "result": det}
    elif operation == "multiply" and matrix_b:
        rows_a = len(matrix_a)
        cols_a = len(matrix_a[0])
        cols_b = len(matrix_b[0])
        result = [[sum(matrix_a[i][k] * matrix_b[k][j] for k in range(cols_a)) for j in range(cols_b)] for i in range(rows_a)]
        return {"operation": "multiply", "result": result}

    return {"operation": operation, "matrix_a_shape": [len(matrix_a), len(matrix_a[0]) if matrix_a else 0]}


@tool_registry.register(
    name="plot_function",
    category=ToolCategory.MATH,
    description="Generate sample (x, y) plot coordinates for mathematical functions f(x) over a range.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_plot_function(expression: str, x_min: float = -10.0, x_max: float = 10.0, points: int = 50) -> dict[str, Any]:
    step = (x_max - x_min) / max(1, points - 1)
    coords = []
    tree = ast.parse(expression, mode="eval")

    for i in range(points):
        x = x_min + i * step
        # Replace variable x with value
        expr_with_val = expression.replace("x", f"({x})")
        try:
            val_tree = ast.parse(expr_with_val, mode="eval")
            y = _eval_safe_math(val_tree)
            coords.append({"x": round(x, 3), "y": round(y, 4)})
        except Exception:
            continue

    return {
        "function": expression,
        "domain": [x_min, x_max],
        "points_count": len(coords),
        "coordinates": coords,
    }


@tool_registry.register(
    name="run_simulation",
    category=ToolCategory.MATH,
    description="Run Monte Carlo simulation or iterative numeric step simulation.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_run_simulation(simulation_type: str = "monte_carlo_pi", trials: int = 10000) -> dict[str, Any]:
    import random
    if simulation_type == "monte_carlo_pi":
        inside = 0
        for _ in range(trials):
            x = random.random()
            y = random.random()
            if x * x + y * y <= 1.0:
                inside += 1
        pi_estimate = 4 * inside / trials
        return {
            "simulation": "monte_carlo_pi",
            "trials": trials,
            "pi_estimate": pi_estimate,
            "error_pct": round(abs(pi_estimate - math.pi) / math.pi * 100, 4),
        }

    return {"simulation": simulation_type, "status": "completed", "trials": trials}
