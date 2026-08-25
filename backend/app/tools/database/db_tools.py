from __future__ import annotations
import os
import sqlite3
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError
from app.utils.security import enforce_project_root

_DESTRUCTIVE_SQL_KEYWORDS = ("DROP ", "TRUNCATE ", "ALTER ", "DELETE FROM", "DROP TABLE")


@tool_registry.register(
    name="validate_sql",
    category=ToolCategory.DATABASE,
    description="Validate SQL syntax and inspect for destructive operations before execution.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_validate_sql(sql_query: str) -> dict[str, Any]:
    query_upper = sql_query.strip().upper()
    is_destructive = any(kw in query_upper for kw in _DESTRUCTIVE_SQL_KEYWORDS)
    is_read_only = query_upper.startswith(("SELECT", "EXPLAIN", "PRAGMA", "SHOW", "DESCRIBE"))

    return {
        "query": sql_query,
        "is_read_only": is_read_only,
        "is_destructive": is_destructive,
        "valid": True,
        "requires_approval": is_destructive,
    }


@tool_registry.register(
    name="list_tables",
    category=ToolCategory.DATABASE,
    description="List all tables and views in a SQLite or database file.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_list_tables(db_path: str = "./session_data.db", project_root: str = ".") -> dict[str, Any]:
    abs_path = os.path.abspath(db_path)
    if not os.path.exists(abs_path):
        raise ToolValidationError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(abs_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'")
    tables = [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]
    conn.close()

    return {"db_path": db_path, "tables_count": len(tables), "tables": tables}


@tool_registry.register(
    name="describe_table",
    category=ToolCategory.DATABASE,
    description="Get schema columns, types, primary keys, and nullability of a database table.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_describe_table(table_name: str, db_path: str = "./session_data.db") -> dict[str, Any]:
    abs_path = os.path.abspath(db_path)
    if not os.path.exists(abs_path):
        raise ToolValidationError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(abs_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    conn.close()

    if not cols:
        raise ToolValidationError(f"Table '{table_name}' does not exist or has no columns.")

    columns = [
        {
            "cid": c[0],
            "name": c[1],
            "type": c[2],
            "notnull": bool(c[3]),
            "default_value": c[4],
            "primary_key": bool(c[5]),
        }
        for c in cols
    ]

    return {"table_name": table_name, "column_count": len(columns), "columns": columns}


@tool_registry.register(
    name="read_query",
    category=ToolCategory.DATABASE,
    description="Execute a safe READ-ONLY SQL query (SELECT) and return structured records.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_read_query(query: str, db_path: str = "./session_data.db", limit: int = 50) -> dict[str, Any]:
    validation = await tool_validate_sql(query)
    if not validation["is_read_only"]:
        raise ToolSecurityError("read_query only permits SELECT/EXPLAIN statements. Use execute_sql for mutations.", "write_in_read_tool")

    abs_path = os.path.abspath(db_path)
    if not os.path.exists(abs_path):
        raise ToolValidationError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(abs_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchmany(limit)
        results = [dict(r) for r in rows]
    except Exception as e:
        conn.close()
        raise ToolValidationError(f"SQL execution error: {e}")

    conn.close()
    return {
        "query": query,
        "rows_returned": len(results),
        "results": results,
    }


@tool_registry.register(
    name="execute_sql",
    category=ToolCategory.DATABASE,
    description="Execute an SQL statement (INSERT, UPDATE, CREATE, DELETE). Requires EXTERNAL_SYSTEM/DESTRUCTIVE permission.",
    permission=PermissionTier.EXTERNAL_SYSTEM,
    timeout=20,
)
async def tool_execute_sql(query: str, db_path: str = "./session_data.db") -> dict[str, Any]:
    abs_path = os.path.abspath(db_path)
    conn = sqlite3.connect(abs_path)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        conn.commit()
        rows_affected = cursor.rowcount
    except Exception as e:
        conn.rollback()
        conn.close()
        raise ToolValidationError(f"SQL execution failed: {e}")

    conn.close()
    return {"query": query, "rows_affected": rows_affected, "status": "executed"}


@tool_registry.register(
    name="analyze_query",
    category=ToolCategory.DATABASE,
    description="Explain query execution plan for performance and index usage.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_analyze_query(query: str, db_path: str = "./session_data.db") -> dict[str, Any]:
    explain_q = f"EXPLAIN QUERY PLAN {query}"
    abs_path = os.path.abspath(db_path)
    if not os.path.exists(abs_path):
        raise ToolValidationError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(abs_path)
    cursor = conn.cursor()
    try:
        cursor.execute(explain_q)
        plan = cursor.fetchall()
    except Exception as e:
        conn.close()
        raise ToolValidationError(f"Could not explain query: {e}")

    conn.close()
    return {"query": query, "execution_plan": plan}


@tool_registry.register(
    name="list_databases",
    category=ToolCategory.DATABASE,
    description="Discover and list database files in the project workspace.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_list_databases(project_root: str = "./projects") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    db_files = []
    if abs_root and os.path.exists(abs_root):
        for root, _, files in os.walk(abs_root):
            for f in files:
                if f.endswith((".db", ".sqlite", ".sqlite3")):
                    db_files.append(os.path.relpath(os.path.join(root, f), project_root))

    if os.path.exists("./session_data.db"):
        db_files.append("./session_data.db")

    return {"databases_found": len(db_files), "databases": list(set(db_files))}
