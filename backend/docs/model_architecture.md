# Approved Universal Agentic AI Model Architecture

This document defines the production model architecture, retrieval pipelines, reranking layers, fallback mechanisms, and deterministic verification integration for the Universal Agentic AI.

---

## 1. Primary Architecture Overview

```text
                                  USER
                                    ↓
                        Qwen3.8-Max / Qwen3.8-2.4T
                         Main Agent & Brain (LLM)
                                    ↓
                         DYNAMIC CONTEXT PLANNER
                                    ↓
                     ┌──────────────┴──────────────┐
                     ↓                             ↓
            Qwen3-Embedding-8B                BM25 / Keyword
            (Dense Semantic Retrieval)        (Exact Technical Retrieval)
                     ↓                             ↓
                     └──────────────┬──────────────┘
                                    ↓
                              Candidate Pool
                                    ↓
                           Qwen3-Reranker-8B
                       (Cross-Attention Reranking)
                                    ↓
                           Evidence Selection
                                    ↓
                         Deduplication & Diversity
                                    ↓
                        Coverage & Freshness Check
                                    ↓
                           Conflict Detection
                                    ↓
                         Dynamic Context Bundle
                                    ↓
                        Qwen3.8-Max / Qwen3.8-2.4T
                              Final Reasoning
                                    ↓
                         Deterministic Verifiers
                         (AST, Pytest, SymPy, Pandas)
                                    ↓
                               Final Result
```

---

## 2. Approved Model Specifications & Roles

| Tier / Role | Primary Model | Open-Weight / Local Variant | Hardware Requirement | Fallback Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Main Reasoning** | `Qwen3.8-Max` | `Qwen/Qwen3.8-2.4T-A95B` | 480 GB+ VRAM (Multi-GPU cluster) | `qwen2.5-coder:32b` / `14b` / `7b` |
| **Semantic Retrieval** | `Qwen/Qwen3-Embedding-8B` | `Qwen/Qwen3-Embedding-8B` | 16 GB VRAM | BM25 Lexical Matching |
| **Exact Lexical Search** | `BM25` | `BM25` | CPU / RAM | In-memory keyword match |
| **Reranking** | `Qwen/Qwen3-Reranker-8B` | `Qwen/Qwen3-Reranker-8B` | 16 GB VRAM | 4-Tier Hybrid Deterministic Rerank |
| **Verification** | Deterministic Tool Suite | Local AST, Pytest, SymPy | CPU | Static Analysis |

---

## 3. Two-Stage Hybrid Retrieval & Fusion

1. **Stage 1 (Parallel Candidate Gathering)**:
   - **Semantic Candidates**: `Qwen/Qwen3-Embedding-8B` encodes queries and documents into normalized 4096-dimensional vectors.
   - **Exact Candidates**: `BM25` tokenizes and scores exact identifiers, error codes (`ERR_MODULE_NOT_FOUND`), package versions (`v4.2.0`), function names, and file paths.
   - **Fusion**: Uses Reciprocal Rank Fusion (RRF, $k=60$) or Weighted Fusion ($0.6 \times \text{Semantic} + 0.4 \times \text{Keyword}$) to assemble the candidate pool.
2. **Stage 2 (Cross-Attention Reranking)**:
   - `Qwen/Qwen3-Reranker-8B` cross-scores top candidates to filter out noisy context chunks.
   - Supports 4-tier graceful fallback (`Qwen3-Reranker-8B` $\to$ Deterministic Hybrid Scoring $\to$ Semantic + BM25 Score $\to$ Metadata Rank).
3. **Dynamic Context Intelligence Integration**:
   - Selected evidence is deduplicated, checked for temporal/version conflicts, position-ordered, and budgeted into structured slots for `Qwen3.8-Max` reasoning.
4. **Deterministic Verification**:
   - The reasoning model never verifies its own claims. Phase 1 tools (AST analysis, test execution, deterministic math solvers) provide verifiable ground-truth validation.
