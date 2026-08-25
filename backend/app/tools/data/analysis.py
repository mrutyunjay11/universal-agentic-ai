from __future__ import annotations
import csv
import json
import math
import os
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError
from app.utils.security import enforce_project_root


def _load_csv_data(file_path: str, project_root: str) -> tuple[list[str], list[dict[str, Any]]]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"CSV file not found: {file_path}")

    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return list(headers), rows


@tool_registry.register(
    name="read_csv",
    category=ToolCategory.DATA,
    description="Read a CSV dataset into structured JSON records with headers and row count.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_read_csv(file_path: str, project_root: str = "./projects", limit: int = 50) -> dict[str, Any]:
    headers, rows = _load_csv_data(file_path, project_root)
    return {
        "file_path": file_path,
        "headers": headers,
        "total_rows": len(rows),
        "rows": rows[:limit],
    }


@tool_registry.register(
    name="write_csv",
    category=ToolCategory.DATA,
    description="Write structured list of records to a CSV file.",
    permission=PermissionTier.READ_WRITE,
    timeout=10,
)
async def tool_write_csv(file_path: str, data: list[dict[str, Any]], project_root: str = "./projects") -> dict[str, Any]:
    if not data:
        raise ToolValidationError("Cannot write empty dataset to CSV")

    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        raise ToolSecurityError(f"Path access denied: {file_path}", "path_traversal")

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    keys = list(data[0].keys())

    with open(abs_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    return {"file_path": file_path, "rows_written": len(data), "headers": keys}


@tool_registry.register(
    name="read_json",
    category=ToolCategory.DATA,
    description="Read a JSON file into structured data.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_read_json(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"JSON file not found: {file_path}")

    with open(abs_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"file_path": file_path, "data": data}


@tool_registry.register(
    name="write_json",
    category=ToolCategory.DATA,
    description="Write Python data structure as formatted JSON to a file.",
    permission=PermissionTier.READ_WRITE,
    timeout=10,
)
async def tool_write_json(file_path: str, data: Any, project_root: str = "./projects", indent: int = 2) -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path:
        raise ToolSecurityError("Path access denied", "path_traversal")

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)

    return {"file_path": file_path, "status": "written"}


@tool_registry.register(
    name="analyze_dataset",
    category=ToolCategory.DATA,
    description="Perform comprehensive statistical overview of a dataset (column types, nulls, cardinality, numeric stats).",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_analyze_dataset(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    headers, rows = _load_csv_data(file_path, project_root)
    col_analysis = {}

    for col in headers:
        values = [r[col] for r in rows if r.get(col) is not None and r.get(col) != ""]
        null_count = len(rows) - len(values)
        unique_vals = set(values)

        # Check numeric
        numeric_vals = []
        for v in values:
            try:
                numeric_vals.append(float(v))
            except ValueError:
                pass

        if len(numeric_vals) == len(values) and values:
            mean_val = sum(numeric_vals) / len(numeric_vals)
            sorted_nums = sorted(numeric_vals)
            median_val = sorted_nums[len(sorted_nums) // 2]
            col_analysis[col] = {
                "type": "numeric",
                "count": len(values),
                "null_count": null_count,
                "min": min(numeric_vals),
                "max": max(numeric_vals),
                "mean": round(mean_val, 2),
                "median": round(median_val, 2),
            }
        else:
            col_analysis[col] = {
                "type": "categorical",
                "count": len(values),
                "null_count": null_count,
                "unique_values": len(unique_vals),
                "sample_values": list(unique_vals)[:5],
            }

    return {
        "file_path": file_path,
        "total_rows": len(rows),
        "total_columns": len(headers),
        "columns": col_analysis,
    }


@tool_registry.register(
    name="detect_missing_values",
    category=ToolCategory.DATA,
    description="Scan dataset for null, empty, NaN, or missing values across all columns.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_detect_missing_values(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    headers, rows = _load_csv_data(file_path, project_root)
    missing_by_col = {}

    for col in headers:
        empty_count = sum(1 for r in rows if not r.get(col) or str(r.get(col)).strip().lower() in ("", "null", "none", "nan"))
        if empty_count > 0:
            missing_by_col[col] = {
                "missing_count": empty_count,
                "missing_ratio": round(empty_count / max(1, len(rows)), 4),
            }

    return {
        "file_path": file_path,
        "total_rows": len(rows),
        "has_missing_values": bool(missing_by_col),
        "missing_by_column": missing_by_col,
    }


@tool_registry.register(
    name="detect_outliers",
    category=ToolCategory.DATA,
    description="Detect statistical outliers in numeric columns using IQR (Interquartile Range).",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_detect_outliers(file_path: str, column_name: str, project_root: str = "./projects") -> dict[str, Any]:
    headers, rows = _load_csv_data(file_path, project_root)
    if column_name not in headers:
        raise ToolValidationError(f"Column '{column_name}' not found in dataset. Available: {headers}")

    nums = []
    for r in rows:
        try:
            nums.append(float(r[column_name]))
        except (ValueError, TypeError):
            pass

    if len(nums) < 4:
        return {"column": column_name, "message": "Not enough numeric values for outlier detection"}

    nums.sort()
    q1 = nums[len(nums) // 4]
    q3 = nums[(len(nums) * 3) // 4]
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = [x for x in nums if x < lower_bound or x > upper_bound]
    return {
        "column": column_name,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": len(outliers),
        "sample_outliers": outliers[:20],
    }


@tool_registry.register(
    name="calculate_statistics",
    category=ToolCategory.DATA,
    description="Calculate detailed descriptive statistics (mean, median, variance, std dev, skewness) for numeric data.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_calculate_statistics(numbers: list[float]) -> dict[str, Any]:
    if not numbers:
        raise ToolValidationError("Numbers list cannot be empty")

    n = len(numbers)
    mean_val = sum(numbers) / n
    variance = sum((x - mean_val) ** 2 for x in numbers) / max(1, n - 1)
    std_dev = math.sqrt(variance)
    sorted_n = sorted(numbers)
    median_val = sorted_n[n // 2]

    return {
        "count": n,
        "min": min(numbers),
        "max": max(numbers),
        "mean": round(mean_val, 4),
        "median": round(median_val, 4),
        "variance": round(variance, 4),
        "standard_deviation": round(std_dev, 4),
    }


@tool_registry.register(
    name="filter_data",
    category=ToolCategory.DATA,
    description="Filter rows in a dataset where column matches a condition (eq, ne, gt, lt, contains).",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_filter_data(
    file_path: str,
    column: str,
    operator: str,
    value: str,
    project_root: str = "./projects",
) -> dict[str, Any]:
    headers, rows = _load_csv_data(file_path, project_root)
    filtered = []

    for r in rows:
        val = r.get(column, "")
        match = False
        if operator == "eq":
            match = str(val) == str(value)
        elif operator == "ne":
            match = str(val) != str(value)
        elif operator == "contains":
            match = str(value).lower() in str(val).lower()
        elif operator in ("gt", "lt"):
            try:
                num_val = float(val)
                target = float(value)
                match = (num_val > target) if operator == "gt" else (num_val < target)
            except ValueError:
                pass

        if match:
            filtered.append(r)

    return {
        "file_path": file_path,
        "filter": {"column": column, "operator": operator, "value": value},
        "matched_rows": len(filtered),
        "rows": filtered[:50],
    }


@tool_registry.register(
    name="sort_data",
    category=ToolCategory.DATA,
    description="Sort rows of a CSV dataset by specified column.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_sort_data(file_path: str, column: str, ascending: bool = True, project_root: str = "./projects") -> dict[str, Any]:
    headers, rows = _load_csv_data(file_path, project_root)
    try:
        sorted_rows = sorted(rows, key=lambda x: float(x.get(column, 0)), reverse=not ascending)
    except ValueError:
        sorted_rows = sorted(rows, key=lambda x: str(x.get(column, "")), reverse=not ascending)

    return {"file_path": file_path, "sorted_by": column, "ascending": ascending, "rows": sorted_rows[:50]}


@tool_registry.register(
    name="group_data",
    category=ToolCategory.DATA,
    description="Group records by key column and compute aggregate counts and sums.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_group_data(file_path: str, group_by_column: str, project_root: str = "./projects") -> dict[str, Any]:
    headers, rows = _load_csv_data(file_path, project_root)
    groups: dict[str, int] = {}

    for r in rows:
        key = str(r.get(group_by_column, "Unknown"))
        groups[key] = groups.get(key, 0) + 1

    return {"group_by": group_by_column, "group_counts": groups}


@tool_registry.register(
    name="validate_schema",
    category=ToolCategory.DATA,
    description="Validate that records adhere to expected column types and required fields.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_validate_schema(file_path: str, expected_schema: dict[str, str], project_root: str = "./projects") -> dict[str, Any]:
    headers, rows = _load_csv_data(file_path, project_root)
    missing_cols = [col for col in expected_schema if col not in headers]
    if missing_cols:
        return {"valid": False, "missing_columns": missing_cols}

    type_errors = []
    for row_idx, r in enumerate(rows[:100], 1):
        for col, expected_type in expected_schema.items():
            val = r.get(col)
            if expected_type == "numeric":
                try:
                    float(val)
                except (ValueError, TypeError):
                    type_errors.append({"row": row_idx, "column": col, "value": val, "expected": "numeric"})

    return {
        "valid": len(type_errors) == 0,
        "type_errors_count": len(type_errors),
        "sample_errors": type_errors[:10],
    }


@tool_registry.register(
    name="create_chart",
    category=ToolCategory.DATA,
    description="Generate a chart configuration (bar, line, scatter, pie) from data points.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_create_chart(chart_type: str, title: str, labels: list[str], values: list[float]) -> dict[str, Any]:
    return {
        "chart_type": chart_type,
        "title": title,
        "data": {
            "labels": labels,
            "datasets": [{"label": title, "data": values}],
        },
        "status": "configured",
    }
