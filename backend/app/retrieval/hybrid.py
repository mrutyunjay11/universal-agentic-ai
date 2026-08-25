from __future__ import annotations
import math
from typing import Any, Optional
from enum import Enum

from app.retrieval.candidate import RetrievalCandidate
from app.retrieval.bm25 import BM25Retriever, bm25_retriever
from app.models.qwen_embedding import QwenEmbeddingProvider
from app.models.qwen_reranker import QwenRerankerProvider
from app.models.registry import model_registry


class FusionStrategy(str, Enum):
    WEIGHTED = "WEIGHTED"
    RRF = "RRF"  # Reciprocal Rank Fusion


class HybridRetriever:
    """
    Two-Stage Hybrid Retrieval & Fusion Engine.
    Stage 1: Multi-candidate parallel retrieval (Qwen3-Embedding-8B dense vectors + BM25 exact matching).
    Stage 2: Reciprocal Rank Fusion (RRF) / Weighted Fusion + Qwen3-Reranker-8B cross-attention reranking.
    """

    def __init__(
        self,
        embedding_provider: Optional[QwenEmbeddingProvider] = None,
        reranker_provider: Optional[QwenRerankerProvider] = None,
        bm25: Optional[BM25Retriever] = None,
    ):
        self.embedding_provider = embedding_provider or model_registry.get_embedding_provider("Qwen/Qwen3-Embedding-8B")
        self.reranker_provider = reranker_provider or model_registry.get_reranker_provider("Qwen/Qwen3-Reranker-8B")
        self.bm25 = bm25 or bm25_retriever
        self.corpus: list[RetrievalCandidate] = []

    def set_corpus(self, documents: list[RetrievalCandidate]) -> None:
        self.corpus = list(documents)
        self.bm25.index_documents(self.corpus)

    async def search(
        self,
        query: str,
        semantic_top_k: int = 50,
        keyword_top_k: int = 50,
        fused_top_k: int = 50,
        reranked_top_k: int = 12,
        fusion_strategy: FusionStrategy = FusionStrategy.RRF,
    ) -> list[RetrievalCandidate]:
        if not self.corpus or not query:
            return []

        # 1. Exact Lexical Retrieval (BM25)
        bm25_candidates = self.bm25.search(query, top_k=keyword_top_k)

        # 2. Semantic Embedding Retrieval (Qwen3-Embedding-8B)
        query_vec = await self.embedding_provider.embed_query(query)
        doc_texts = [d.content for d in self.corpus]
        doc_vecs = await self.embedding_provider.embed_documents(doc_texts)

        semantic_candidates: list[tuple[int, float]] = []
        for idx, dvec in enumerate(doc_vecs):
            # Cosine similarity
            dot = sum(q * d for q, d in zip(query_vec, dvec))
            semantic_candidates.append((idx, dot))

        semantic_candidates.sort(key=lambda x: x[1], reverse=True)

        # 3. Candidate Fusion (RRF or Weighted)
        fused_scores: dict[str, RetrievalCandidate] = {}

        if fusion_strategy == FusionStrategy.RRF:
            rrf_k = 60
            # Rank from BM25
            for rank, c in enumerate(bm25_candidates):
                cid = c.candidate_id
                fused_scores[cid] = c.model_copy()
                fused_scores[cid].fusion_score += 1.0 / (rrf_k + rank + 1)

            # Rank from Semantic
            for rank, (idx, sim) in enumerate(semantic_candidates[:semantic_top_k]):
                doc_orig = self.corpus[idx]
                cid = doc_orig.candidate_id
                if cid not in fused_scores:
                    fused_scores[cid] = doc_orig.model_copy()
                fused_scores[cid].semantic_score = round(sim, 4)
                fused_scores[cid].fusion_score += 1.0 / (rrf_k + rank + 1)
        else:
            # Weighted Fusion
            for c in bm25_candidates:
                cid = c.candidate_id
                fused_scores[cid] = c.model_copy()
                fused_scores[cid].fusion_score += c.keyword_score * 0.4

            for idx, sim in semantic_candidates[:semantic_top_k]:
                doc_orig = self.corpus[idx]
                cid = doc_orig.candidate_id
                if cid not in fused_scores:
                    fused_scores[cid] = doc_orig.model_copy()
                fused_scores[cid].semantic_score = round(sim, 4)
                fused_scores[cid].fusion_score += sim * 0.6

        candidate_pool = list(fused_scores.values())
        candidate_pool.sort(key=lambda x: x.fusion_score, reverse=True)
        candidate_pool = candidate_pool[:fused_top_k]

        # 4. Stage 2: Cross-Attention Reranking (Qwen3-Reranker-8B)
        if self.reranker_provider:
            texts = [c.content for c in candidate_pool]
            ranked_results = await self.reranker_provider.rerank(query, texts, top_k=reranked_top_k)

            final_ranked: list[RetrievalCandidate] = []
            for item in ranked_results:
                orig_cand = candidate_pool[item["index"]].model_copy()
                orig_cand.reranker_score = item["reranker_score"]
                final_ranked.append(orig_cand)
            return final_ranked

        return candidate_pool[:reranked_top_k]


hybrid_retriever = HybridRetriever()
