from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.registry import model_registry
from app.models.router import model_router

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def list_models():
    """Lists all registered models and their operational metadata."""
    models = model_registry.list_all_models()
    return {"count": len(models), "models": models}


@router.get("/health")
async def get_models_health():
    """Executes live health checks across all reasoning, embedding, and reranking providers."""
    report = await model_registry.run_health_checks()
    return {"timestamp": "2026-08-25", "health_report": report}


@router.get("/capabilities")
async def get_model_capabilities():
    """Returns capabilities of active flagship and fallback models."""
    return {
        "primary_reasoning": {
            "model_id": "Qwen3.8-Max",
            "context_window": 1000000,
            "capabilities": ["chat", "tools", "structured_output", "vision", "long_horizon_planning"],
        },
        "semantic_embedding": {
            "model_id": "Qwen/Qwen3-Embedding-8B",
            "dimension": 4096,
            "capabilities": ["dense_vectors", "code_retrieval", "multilingual"],
        },
        "reranker": {
            "model_id": "Qwen/Qwen3-Reranker-8B",
            "capabilities": ["cross_attention", "4_level_fallback"],
        },
    }
