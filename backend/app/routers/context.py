from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.context.planner import context_planner, ContextPlan
from app.context.manager import dynamic_context_manager, DynamicContextResult
from app.context.reranker import CandidateEvidence
from app.context.evidence import evidence_manager, EvidenceItem, EvidenceReference
from app.context.sufficiency import sufficiency_evaluator
from app.context.iterative_retrieval import iterative_retrieval_engine
from app.context.compressor import semantic_compressor
from app.context.benchmarks import context_benchmark_suite
from app.context.context_graph import context_graph

router = APIRouter(prefix="/api/context", tags=["context"])


class CreatePlanRequest(BaseModel):
    task: str
    constraints: Optional[list[str]] = None


class BuildContextRequest(BaseModel):
    task: str
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    constraints: Optional[list[str]] = None
    model_context_limit: int = 32768
    task_version: Optional[str] = None


class CompressRequest(BaseModel):
    content: str
    document_id: str = "doc_compress_target"
    target_token_budget: int = 200


class BenchmarkRequest(BaseModel):
    task: str = "Evaluate library compatibility across versions"
    corpus_size_docs: int = 50


@router.post("/plan")
async def create_context_plan(req: CreatePlanRequest):
    """Creates a structured ContextPlan detailing information requirements and strategy."""
    plan = context_planner.create_context_plan(req.task, constraints=req.constraints)
    return plan.model_dump()


@router.post("/build")
async def build_context(req: BuildContextRequest):
    """Constructs a minimal, high-signal active reasoning context."""
    candidates_list: list[CandidateEvidence] = []
    for c in req.candidates:
        candidates_list.append(CandidateEvidence(
            id=c.get("id", "cand_1"),
            content=c.get("content", ""),
            source_id=c.get("source_id", "source_doc"),
            source_type=c.get("source_type", "OFFICIAL_DOCS"),
            authoritative_score=c.get("authoritative_score", 0.8),
            version=c.get("version"),
        ))

    result = await dynamic_context_manager.build_context(
        task=req.task,
        candidates=candidates_list,
        constraints=req.constraints,
        model_context_limit=req.model_context_limit,
        task_version=req.task_version,
    )
    return result.model_dump()


@router.post("/compress")
async def compress_context(req: CompressRequest):
    """Fact-preserving semantic compression of large text."""
    item = EvidenceItem(
        content=req.content,
        reference=EvidenceReference(
            document_id=req.document_id,
            chunk_id=f"{req.document_id}_raw",
        ),
    )
    chunk = semantic_compressor.compress(item, target_token_budget=req.target_token_budget)
    return chunk.model_dump()


@router.get("/graph")
async def get_context_graph():
    """Returns nodes and edges from the bounded context relationship graph."""
    return {
        "nodes_count": len(context_graph._nodes),
        "edges_count": len(context_graph._edges),
        "nodes": [n.model_dump() for n in context_graph._nodes.values()],
    }


@router.post("/benchmark")
async def run_context_benchmark(req: BenchmarkRequest):
    """Runs empirical context management architecture comparison benchmark."""
    results = context_benchmark_suite.run_comparison(req.task, corpus_size_docs=req.corpus_size_docs)
    return {
        "task": req.task,
        "results": [r.model_dump() for r in results],
    }
