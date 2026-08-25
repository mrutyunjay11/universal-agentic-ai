from __future__ import annotations
from typing import Any, Optional
from app.tools.registry import tool_registry
from app.tools.base import BaseTool, ToolCategory
from app.tools.permissions import check_permission, PermissionTier


# Capability mappings to primary tools in Phase 1
CAPABILITY_TOOL_MAP: dict[str, list[str]] = {
    # File & Workspace
    "file.read": ["read_file", "file_exists", "get_file_metadata"],
    "file.write": ["write_file", "create_directory"],
    "file.edit": ["edit_file", "apply_diff", "multi_replace_file"],
    "file.delete": ["delete_file"],
    "file.list": ["list_directory", "search_files"],
    "file.rollback": ["rollback_file"],

    # Code Intelligence
    "code.symbols": ["find_symbols", "find_definition"],
    "code.references": ["find_references", "find_callers"],
    "code.analyze": ["analyze_code", "detect_language"],
    "code.format": ["format_code", "run_linter", "type_check"],

    # Terminal & Processes
    "terminal.run": ["execute_terminal"],
    "terminal.background": ["run_background_process", "get_process_status", "kill_process"],

    # Testing
    "testing.run": ["run_tests", "run_test_file", "run_test_pattern"],
    "testing.debug": ["debug_command", "analyze_failure"],

    # Git
    "git.status": ["git_status", "git_diff", "git_log"],
    "git.branch": ["git_branch", "git_checkout", "git_create_branch"],
    "git.commit": ["git_commit", "git_stash", "git_restore"],

    # Web & Research
    "web.search": ["search_web", "search_documentation", "search_academic_sources", "search_news", "search_code_repositories"],
    "web.extract": ["extract_web_content", "fetch_web_page", "extract_links", "download_resource"],

    # Browser
    "browser.navigate": ["open_browser", "navigate", "wait"],
    "browser.interact": ["click", "type_text", "press_key", "scroll"],
    "browser.inspect": ["extract_page_text", "get_page_elements", "take_screenshot"],

    # Documents
    "doc.read": ["read_document", "extract_text", "extract_metadata"],
    "doc.tables": ["extract_tables"],
    "doc.compare": ["compare_documents", "summarize_document"],

    # Data
    "data.read": ["read_csv", "read_json"],
    "data.write": ["write_csv", "write_json"],
    "data.analyze": ["analyze_dataset", "detect_missing_values", "detect_outliers"],
    "data.statistics": ["calculate_statistics", "filter_data", "sort_data", "group_data"],
    "data.chart": ["create_chart"],

    # Database
    "db.query": ["read_query", "list_tables", "describe_table"],
    "db.execute": ["execute_sql", "validate_sql", "analyze_query"],

    # API
    "api.request": ["http_get", "http_post", "http_put", "http_delete", "graphql_query"],
    "api.inspect": ["inspect_api", "validate_response"],

    # Math
    "math.calculate": ["calculator", "unit_convert"],
    "math.symbolic": ["symbolic_math", "solve_equation", "matrix_operations"],
    "math.simulation": ["run_simulation", "plot_function"],

    # Vision
    "vision.analyze": ["analyze_image", "extract_image_text", "detect_objects", "describe_image"],

    # Packages & Environment
    "package.list": ["list_dependencies", "detect_project_type", "check_dependencies"],
    "package.manage": ["install_dependency", "remove_dependency", "update_dependency"],

    # Sandbox
    "sandbox.run": ["create_sandbox", "run_in_sandbox", "destroy_sandbox"],

    # System
    "system.info": ["get_system_info", "get_os_info", "get_cpu_info", "get_memory_info", "get_disk_info"],

    # RAG / Knowledge
    "rag.search": ["search_knowledge_base", "search_codebase", "hybrid_search", "semantic_search", "retrieve_chunks"],

    # Verification
    "verify.claim": ["verify_claim", "match_claim_to_evidence"],
    "verify.claims": ["extract_claims", "match_claim_to_evidence"],
    "verify.code": ["verify_code"],
    "verify.calculation": ["verify_calculation"],
    "verify.contradiction": ["detect_contradiction", "compare_sources"],
    "verify.source_authority": ["check_source_authority", "check_source_date", "check_primary_source"],
    "verify.document": ["verify_document", "check_citation"],
}


class ToolRouter:
    """Routes required agent capabilities to the safest, fastest, and lowest-privilege available tool in Phase 1 Registry."""

    def route_capability(
        self,
        capability: str,
        permission_granted: PermissionTier = PermissionTier.SYSTEM,
        preferred_tool: Optional[str] = None,
    ) -> Optional[str]:
        # 1. If preferred tool matches capability and permissions, use it
        if preferred_tool:
            tool = tool_registry.get_tool(preferred_tool)
            if tool and check_permission(tool.metadata.permission, permission_granted):
                return preferred_tool

        # 2. Lookup candidate tools for capability
        candidates = CAPABILITY_TOOL_MAP.get(capability, [])
        for name in candidates:
            tool = tool_registry.get_tool(name)
            if tool and check_permission(tool.metadata.permission, permission_granted):
                return name

        # 3. Direct lookup in registry by tool name
        direct_tool = tool_registry.get_tool(capability)
        if direct_tool and check_permission(direct_tool.metadata.permission, permission_granted):
            return capability

        return None

    def get_tools_for_capabilities(self, capabilities: list[str], permission_granted: PermissionTier = PermissionTier.SYSTEM) -> list[str]:
        selected: list[str] = []
        for cap in capabilities:
            tool_name = self.route_capability(cap, permission_granted)
            if tool_name and tool_name not in selected:
                selected.append(tool_name)
        return selected


tool_router = ToolRouter()
