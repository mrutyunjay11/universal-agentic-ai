# Universal Agentic AI — Memory Architecture (Phase 3)

## 1. Architectural Overview

Phase 3 introduces a robust, decay-aware, and security-isolated **Memory, Knowledge, Context, Retrieval, and Learning Infrastructure** that seamlessly connects with Phase 1 (Universal Tool Ecosystem) and Phase 2 (Agent State Machine & Orchestration).

```text
                               Agent Task / Request
                                        │
                                        ▼
                              ┌───────────────────┐
                              │  Query Enriched   │
                              │   Understanding   │
                              └─────────┬─────────┘
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │        Hybrid Retrieval Engine          │
                   │  (Semantic + Keyword + Scope + Filter)  │
                   └────────────────────┬────────────────────┘
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │         Multi-Factor Ranker             │
                   │ (Relevance, Importance, Freshness, Ver) │
                   └────────────────────┬────────────────────┘
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │    Hierarchical Context Builder         │
                   │   (Token Budgets + Dynamic Compression) │
                   └────────────────────┬────────────────────┘
                                        │
                                        ▼
                          Phase 2 Execution & Verification
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │      Post-Task Consolidation            │
                   │  (Noise Filter + Provenance + Promotion)│
                   └────────────────────┬────────────────────┘
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │  Memory Stores (SQLite / Vector / RAG)  │
                   └─────────────────────────────────────────┘
```

---

## 2. Memory Types

The memory architecture distinguishes between 9 standard memory types:

| Memory Type | Purpose | Lifetime & Scope |
| :--- | :--- | :--- |
| `WORKING` | Ephemeral scratchpad information for the current task | Task-scoped, fast decay (~2.4h) |
| `EPISODIC` | Past interactions, conversations, and events | Multi-turn, medium decay (14d) |
| `SEMANTIC` | General verified technical concepts and definitions | Long-lived (180d) |
| `PROCEDURAL` | Successful multi-step workflows, scripts, and commands | Project/Global (90d) |
| `PROJECT` | Workspace-specific configuration, dependencies, conventions | Project-scoped (60d) |
| `USER_PREFERENCE` | Stable user coding/response preferences | User-scoped (365d) |
| `FACT` | Concrete factual claims backed by provenance | Verified facts (120d) |
| `TASK_HISTORY` | Past task outcomes, lessons, and step counts | Retrospective history (30d) |
| `SOURCE_MEMORY` | Authority ratings and trust scores of external sources | Domain/Source-scoped (90d) |

---

## 3. Core Subsystems

1. **`models.py`**: Strongly-typed `MemoryRecord`, `InvalidationRecord`, `MemoryType`, `VerificationStatus`, and `FreshnessStatus`.
2. **`stores/`**: Pluggable storage abstractions (`SQLiteMemoryStore`, `VectorMemoryStore`, `HybridMemoryStore`).
3. **`embeddings.py`**: Provider-agnostic embedding interface with `DeterministicMockEmbedder` and `OllamaEmbedder`.
4. **`retrieval.py` & `ranking.py`**: Multi-factor scoring combining semantic similarity, keyword matching, task/project relevance, freshness decay, and contradiction penalties.
5. **`decay.py` & `invalidation.py`**: Exponential half-life decay, stale knowledge detection, and non-destructive contradiction superseding.
6. **`consolidation.py`**: Post-task review of working memory promoting verified facts, conventions, and procedures.
7. **`context_builder.py`**: Multi-slot token budgeting and dynamic compression (`TRUNCATE`, `SUMMARIZE`, `DEDUPLICATE`).
8. **`manager.py`**: Central `MemoryManager` facade ensuring tenant/project isolation.
