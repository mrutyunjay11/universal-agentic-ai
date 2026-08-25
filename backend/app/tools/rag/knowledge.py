from __future__ import annotations
import os
import re
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError
from app.services.memory_service import memory_service


@tool_registry.register(
    name="search_knowledge_base",
    category=ToolCategory.RAG,
    description="Search indexed documents and knowledge base using semantic search.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_search_knowledge_base(query: str, project_id: str = "default", limit: int = 5) -> dict[str, Any]:
    try:
        results = await memory_service.search_semantic(project_id=project_id, query=query, limit=limit)
        return {"query": query, "results_count": len(results), "results": results}
    except Exception as e:
        return {"query": query, "results_count": 0, "results": [], "note": str(e)}


@tool_registry.register(
    name="search_codebase",
    category=ToolCategory.RAG,
    description="Search the codebase using semantic + keyword hybrid search. Returns ranked relevant code chunks.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_search_codebase(
    query: str,
    project_id: str = "default",
    limit: int = 10,
    file_pattern: Optional[str] = None,
) -> dict[str, Any]:
    try:
        results = await memory_service.hybrid_search(
            project_id=project_id,
            query=query,
            limit=limit,
            file_pattern=file_pattern,
        )
        return {"query": query, "results_count": len(results), "chunks": results}
    except Exception as e:
        return {"query": query, "results_count": 0, "chunks": [], "note": str(e)}


@tool_registry.register(
    name="semantic_search",
    category=ToolCategory.RAG,
    description="Search vectors using embedding similarity.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_semantic_search(query: str, project_id: str = "default", limit: int = 5) -> dict[str, Any]:
    return await tool_search_knowledge_base(query=query, project_id=project_id, limit=limit)


@tool_registry.register(
    name="keyword_search",
    category=ToolCategory.RAG,
    description="Search documents using BM25 keyword matching.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_keyword_search(query: str, project_id: str = "default", limit: int = 10) -> dict[str, Any]:
    try:
        results = memory_service.search_keyword(project_id=project_id, query=query, limit=limit)
        return {"query": query, "match_count": len(results), "results": results}
    except Exception as e:
        return {"query": query, "match_count": 0, "results": [], "note": str(e)}


@tool_registry.register(
    name="hybrid_search",
    category=ToolCategory.RAG,
    description="Execute hybrid search (Vector embeddings + BM25 keyword + Reranking) across the repository.",
    permission=PermissionTier.READ,
    timeout=20,
)
async def tool_hybrid_search(query: str, project_id: str = "default", limit: int = 10) -> dict[str, Any]:
    return await tool_search_codebase(query=query, project_id=project_id, limit=limit)


@tool_registry.register(
    name="retrieve_chunks",
    category=ToolCategory.RAG,
    description="Retrieve specific indexed code or document chunks by chunk ID or file path.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_retrieve_chunks(file_path: str, project_id: str = "default") -> dict[str, Any]:
    chunks = await memory_service.get_file_chunks(project_id=project_id, file_path=file_path)
    return {"file_path": file_path, "chunks_count": len(chunks), "chunks": chunks}


@tool_registry.register(
    name="index_documents",
    category=ToolCategory.RAG,
    description="Trigger indexing of documents or codebase files into the vector database.",
    permission=PermissionTier.READ_WRITE,
    timeout=120,
)
async def tool_index_documents(project_root: str = "./projects", project_id: str = "default") -> dict[str, Any]:
    from app.services.indexing_service import indexing_service
    status = await indexing_service.index_project(project_id=project_id, project_root=project_root)
    return {"project_id": project_id, "status": status}


@tool_registry.register(
    name="update_index",
    category=ToolCategory.RAG,
    description="Update index for a single modified file.",
    permission=PermissionTier.READ_WRITE,
    timeout=30,
)
async def tool_update_index(file_path: str, project_id: str = "default", project_root: str = "./projects") -> dict[str, Any]:
    from app.services.indexing_service import indexing_service
    await indexing_service.reindex_file(project_id=project_id, file_path=file_path, project_root=project_root)
    return {"file_path": file_path, "status": "reindexed"}


@tool_registry.register(
    name="delete_index_entry",
    category=ToolCategory.RAG,
    description="Delete indexed vectors and chunks for a deleted file.",
    permission=PermissionTier.DESTRUCTIVE,
    timeout=15,
)
async def tool_delete_index_entry(file_path: str, project_id: str = "default") -> dict[str, Any]:
    await memory_service.delete_file_chunks(project_id=project_id, file_path=file_path)
    return {"file_path": file_path, "status": "deleted_from_index"}
