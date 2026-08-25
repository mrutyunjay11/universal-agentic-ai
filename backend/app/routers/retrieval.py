from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.retrieval.candidate import RetrievalCandidate
from app.retrieval.hybrid import hybrid_retriever, FusionStrategy
from app.models.registry import model_registry

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])


class SearchRequest(BaseModel):
    query: str
    documents: list[dict[str, Any]] = Field(default_factory=list)
    semantic_top_k: int = 50
    keyword_top_k: int = 50
    fused_top_k: int = 50
    reranked_top_k: int = 12
    fusion_strategy: str = "RRF"


class RerankRequest(BaseModel):
    query: str
    documents: list[str] = Field(default_factory=list)
    top_k: int = 10


@router.post("/search")
async def search_hybrid(req: SearchRequest):
    """Executes Stage 1 Hybrid (Qwen3-Embedding-8B + BM25) and Stage 2 Reranking (Qwen3-Reranker-8B)."""
    candidates = []
    for d in req.documents:
        candidates.append(RetrievalCandidate(
            candidate_id=d.get("id", f"doc_{len(candidates)}"),
            document_id=d.get("document_id", "doc_main"),
            chunk_id=d.get("chunk_id", "chunk_1"),
            source_id=d.get("source_id", "source_1"),
            content=d.get("content", ""),
            source_type=d.get("source_type", "OFFICIAL_DOCS"),
        ))

    if candidates:
        hybrid_retriever.set_corpus(candidates)

    strat = FusionStrategy.RRF if req.fusion_strategy == "RRF" else FusionStrategy.WEIGHTED
    results = await hybrid_retriever.search(
        query=req.query,
        semantic_top_k=req.semantic_top_k,
        keyword_top_k=req.keyword_top_k,
        fused_top_k=req.fused_top_k,
        reranked_top_k=req.reranked_top_k,
        fusion_strategy=strat,
    )
    return {
        "query": req.query,
        "results_count": len(results),
        "results": [r.model_dump() for r in results],
    }


@router.post("/rerank")
async def rerank_documents(req: RerankRequest):
    """Direct cross-attention reranking using Qwen3-Reranker-8B."""
    reranker = model_registry.get_reranker_provider("Qwen/Qwen3-Reranker-8B")
    if not reranker:
        raise HTTPException(status_code=503, detail="Reranker provider unavailable")

    ranked = await reranker.rerank(query=req.query, documents=req.documents, top_k=req.top_k)
    return {"query": req.query, "ranked": ranked}
