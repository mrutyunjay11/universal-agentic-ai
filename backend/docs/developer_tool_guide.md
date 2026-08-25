# Universal Agentic AI Tool Ecosystem — Developer Guide

Welcome to the Developer Guide for adding and extending tools in the Universal Agentic AI ecosystem.

---

## 1. Tool Architecture

Every tool in the system is managed by the central `ToolRegistry` (`app/tools/registry.py`) and satisfies the `BaseTool` contract (`app/tools/base.py`).

### Standard Execution Pipeline
```text
Agent / API Request
   ↓
Tool Registry
   ↓
Permission Check (7-Tier Gate)
   ↓
Dependency & Availability Check
   ↓
Input Validation (Pydantic / Type Inference)
   ↓
Timeout & Cancellation Wrapper
   ↓
Tool Execution
   ↓
Secret Redaction & Audit Logger
   ↓
Provenance Attribution
   ↓
Structured ToolResult
```

---

## 2. Adding a New Tool

### Option A: Using the `@tool_registry.register` Decorator (Recommended)

```python
from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.provenance import create_provenance, SourceType

@tool_registry.register(
    name="my_custom_tool",
    category=ToolCategory.DATA,
    description="Analyzes input data and returns structured metrics.",
    permission=PermissionTier.READ,
    timeout=15,
    requires=["pkg:numpy"],  # Optional dependency check (pkg: or cli:)
    tags=["analytics", "math"],
)
async def tool_my_custom_tool(data_points: list[float], metric: str = "mean") -> dict:
    if not data_points:
        return {"error": "data_points cannot be empty"}
    
    val = sum(data_points) / len(data_points)
    
    prov = create_provenance(
        source_type=SourceType.CALCULATION,
        uri="calc://custom_metric",
        content=str(val),
        title="Custom Metric Calculation",
    )
    
    return {
        "metric": metric,
        "value": val,
        "_provenance": prov,  # Automatically attached to ToolResult.provenance
    }
```

### Option B: Subclassing `BaseTool`

For stateful or complex multi-step tools, subclass `BaseTool`:

```python
from app.tools.base import BaseTool, ToolMetadata, ToolCategory, ToolContext
from app.tools.permissions import PermissionTier

class CustomAnalyzerTool(BaseTool):
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="custom_analyzer",
            category=ToolCategory.CODE,
            description="Performs deep structural code analysis.",
            permission=PermissionTier.READ,
            timeout=30,
            required_parameters=["file_path"],
        )

    async def execute_impl(self, context: ToolContext, file_path: str, **kwargs):
        # Implementation logic here
        return {"file_path": file_path, "status": "analyzed"}

# Register instance
tool_registry.register_tool(CustomAnalyzerTool())
```

---

## 3. Permission Tiers

Always assign the lowest necessary privilege level to your tool:

| Tier | Enum | When to use |
|---|---|---|
| `READ` | `PermissionTier.READ` | Read-only inspection, file reading, static analysis, system info |
| `READ_WRITE` | `PermissionTier.READ_WRITE` | Non-destructive edits with automatic `.agent-backups/` snapshot |
| `EXECUTE` | `PermissionTier.EXECUTE` | Sandboxed command execution, running test suites, compilation |
| `NETWORK` | `PermissionTier.NETWORK` | Web search, HTTP GET requests, documentation fetching |
| `EXTERNAL_SYSTEM` | `PermissionTier.EXTERNAL_SYSTEM` | External mutations (HTTP POST/PUT, database writes, cloud APIs) |
| `DESTRUCTIVE` | `PermissionTier.DESTRUCTIVE` | Destructive operations (file deletion, drop table, git restore) |
| `SYSTEM` | `PermissionTier.SYSTEM` | Privileged operations (process kill, OS config, git commit) |

---

## 4. Error Handling & Structured Errors

Never silently swallow exceptions. Either raise custom `ToolError` subclasses (`ToolValidationError`, `ToolTimeoutError`, `ToolSecurityError`, `ToolDependencyError`) or let standard exceptions raise; the base tool runner automatically wraps them into a `StructuredError`:

```json
{
  "success": false,
  "error": {
    "type": "validation_error",
    "message": "File not found: main.py",
    "retryable": false,
    "details": {}
  }
}
```

---

## 5. Testing Your Tool

Add unit tests under `backend/tests/` and ensure your tool passes the conformance suite:

```bash
python -m pytest backend/tests/test_tool_conformance.py -v
```
