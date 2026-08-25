from __future__ import annotations
from typing import Any, Optional
from app.autonomy.task_graph import SubTask, TaskGraph, SubTaskStatus
from app.tools.permissions import PermissionTier


class TaskDecomposer:
    """
    Decomposes complex user tasks into a structured, dependency-ordered SubTask DAG
    with explicit capability requirements and permission tiers.
    """

    def decompose(
        self,
        master_task_id: str,
        goal: str,
        context: Optional[dict[str, Any]] = None,
    ) -> TaskGraph:
        graph = TaskGraph(master_task_id=master_task_id)
        g_lower = goal.lower()

        # 1. Research & Verification Task
        if any(w in g_lower for w in ("research", "find", "investigate", "compare", "fact", "verify claim")):
            sub1 = SubTask(
                id=f"{master_task_id}_research_primary",
                title="Primary Web and Source Research",
                objective="Search official documentation, web sources, and collect initial evidence",
                parent_task_id=master_task_id,
                required_capabilities=["web.search", "web.fetch"],
                preferred_tools=["search_web", "fetch_web_page"],
                permission_tier=PermissionTier.NETWORK,
                priority=3,
            )
            sub2 = SubTask(
                id=f"{master_task_id}_research_secondary",
                title="Secondary Source Comparison",
                objective="Search secondary technical references and release notes for corroboration",
                parent_task_id=master_task_id,
                dependencies=[],
                required_capabilities=["web.search"],
                preferred_tools=["search_web"],
                permission_tier=PermissionTier.NETWORK,
                priority=2,
            )
            sub3 = SubTask(
                id=f"{master_task_id}_verifier",
                title="Independent Evidence Verification",
                objective="Compare sources, check contradictions, and establish ground truth verdict",
                parent_task_id=master_task_id,
                dependencies=[sub1.id, sub2.id],
                required_capabilities=["verify.claim"],
                preferred_tools=["verify_claim", "verify_source_authority"],
                permission_tier=PermissionTier.READ,
                priority=5,
            )
            graph.add_subtask(sub1)
            graph.add_subtask(sub2)
            graph.add_subtask(sub3)

        # 2. Coding / Implementation / Debugging Task
        elif any(w in g_lower for w in ("code", "implement", "fix", "debug", "refactor", "build", "script")):
            sub1 = SubTask(
                id=f"{master_task_id}_analysis",
                title="Repository and Codebase Analysis",
                objective="Inspect existing files, symbol definitions, and dependencies",
                parent_task_id=master_task_id,
                required_capabilities=["file.read", "code.analyze"],
                preferred_tools=["list_directory", "read_file", "analyze_code"],
                permission_tier=PermissionTier.READ,
                priority=3,
            )
            sub2 = SubTask(
                id=f"{master_task_id}_coder",
                title="Code Implementation",
                objective="Write or update source code implementation",
                parent_task_id=master_task_id,
                dependencies=[sub1.id],
                required_capabilities=["file.write", "code.edit"],
                preferred_tools=["write_file", "edit_file"],
                permission_tier=PermissionTier.READ_WRITE,
                priority=4,
            )
            sub3 = SubTask(
                id=f"{master_task_id}_tester",
                title="Unit and Integration Testing",
                objective="Run test suite and verify implementation behavior",
                parent_task_id=master_task_id,
                dependencies=[sub2.id],
                required_capabilities=["code.verify", "terminal.run"],
                preferred_tools=["verify_code", "execute_command"],
                permission_tier=PermissionTier.SYSTEM,
                priority=5,
            )
            graph.add_subtask(sub1)
            graph.add_subtask(sub2)
            graph.add_subtask(sub3)

        # 3. Data Analysis Task
        elif any(w in g_lower for w in ("data", "csv", "sql", "statistics", "dataset", "analytics")):
            sub1 = SubTask(
                id=f"{master_task_id}_data_inspection",
                title="Data Loading and Schema Inspection",
                objective="Load dataset, inspect schema, and validate column datatypes",
                parent_task_id=master_task_id,
                required_capabilities=["data.inspect", "file.read"],
                preferred_tools=["read_file", "calculate_statistics"],
                permission_tier=PermissionTier.READ,
                priority=3,
            )
            sub2 = SubTask(
                id=f"{master_task_id}_data_stats",
                title="Statistical Computation and Validation",
                objective="Compute descriptive statistics and verify numerical assertions",
                parent_task_id=master_task_id,
                dependencies=[sub1.id],
                required_capabilities=["data.statistics", "math.calculate"],
                preferred_tools=["calculate_statistics", "calculator", "verify_calculation"],
                permission_tier=PermissionTier.READ,
                priority=4,
            )
            graph.add_subtask(sub1)
            graph.add_subtask(sub2)

        # 4. Default General Decomposition
        else:
            sub1 = SubTask(
                id=f"{master_task_id}_step_1",
                title="Information Gathering",
                objective="Collect necessary tools and data for task goal",
                parent_task_id=master_task_id,
                required_capabilities=["file.read"],
                permission_tier=PermissionTier.READ,
                priority=2,
            )
            sub2 = SubTask(
                id=f"{master_task_id}_step_2",
                title="Execution and Synthesis",
                objective="Execute core actions and synthesize final result",
                parent_task_id=master_task_id,
                dependencies=[sub1.id],
                required_capabilities=["file.write"],
                permission_tier=PermissionTier.READ_WRITE,
                priority=3,
            )
            graph.add_subtask(sub1)
            graph.add_subtask(sub2)

        return graph


task_decomposer = TaskDecomposer()
