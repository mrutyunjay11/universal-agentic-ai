from __future__ import annotations
import os
import shutil
import tempfile
import pytest
from app.tools.registry import tool_registry
from app.tools.base import ToolContext
from app.tools.permissions import PermissionTier


@pytest.fixture
def temp_data_dir():
    d = tempfile.mkdtemp(prefix="test_data_math_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.mark.asyncio
class TestDataAndMathTools:
    async def test_calculator_deterministic(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        res = await tool_registry.execute("calculator", {"expression": "(15 * 4) + (100 / 2) - 10"}, ctx)
        assert res.success
        assert res.output["result"] == 100.0
        assert res.provenance is not None

        # Trigo & pow
        res2 = await tool_registry.execute("calculator", {"expression": "2 ** 8 + sqrt(144)"}, ctx)
        assert res2.success
        assert res2.output["result"] == 268.0

    async def test_unit_converter(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        res1 = await tool_registry.execute("unit_convert", {"value": 100.0, "from_unit": "celsius", "to_unit": "fahrenheit"}, ctx)
        assert res1.success
        assert res1.output["converted_value"] == 212.0

        res2 = await tool_registry.execute("unit_convert", {"value": 1024.0, "from_unit": "megabytes", "to_unit": "gigabytes"}, ctx)
        assert res2.success
        assert res2.output["converted_value"] == 1.0

    async def test_data_analysis_csv_lifecycle(self, temp_data_dir):
        ctx = ToolContext(project_root=temp_data_dir, permission_granted=PermissionTier.SYSTEM)
        data = [
            {"name": "Alice", "age": 30, "salary": 95000},
            {"name": "Bob", "age": 25, "salary": 70000},
            {"name": "Charlie", "age": 35, "salary": 120000},
            {"name": "David", "age": 28, "salary": 80000},
        ]

        # Write CSV
        w_res = await tool_registry.execute("write_csv", {"file_path": "employees.csv", "data": data}, ctx)
        assert w_res.success

        # Read CSV
        r_res = await tool_registry.execute("read_csv", {"file_path": "employees.csv"}, ctx)
        assert r_res.success
        assert r_res.output["total_rows"] == 4

        # Analyze dataset
        analysis = await tool_registry.execute("analyze_dataset", {"file_path": "employees.csv"}, ctx)
        assert analysis.success
        assert "salary" in analysis.output["columns"]
        assert analysis.output["columns"]["salary"]["min"] == 70000.0

        # Filter data
        filt = await tool_registry.execute("filter_data", {"file_path": "employees.csv", "column": "age", "operator": "gt", "value": "29"}, ctx)
        assert filt.success
        assert filt.output["matched_rows"] == 2

    async def test_statistics_calculation(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        nums = [10.0, 20.0, 30.0, 40.0, 50.0]
        res = await tool_registry.execute("calculate_statistics", {"numbers": nums}, ctx)
        assert res.success
        assert res.output["mean"] == 30.0
        assert res.output["median"] == 30.0
