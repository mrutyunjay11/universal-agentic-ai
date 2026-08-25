# Universal Agentic AI — Hybrid Knowledge Retrieval & Ranking

## 1. Hybrid Retrieval Pipeline

The retrieval engine combines keyword pattern matching, scope filtering, and vector semantic similarity:

```text
Normalized User Query
          │
          ├──> SQLite Indexed Search (Keywords, Tags, Project/User Scopes)
          │
          └──> Vector Store (Cosine Similarity on 768-dim Embeddings)
          │
          ▼
Candidate Pool Deduplication
          │
          ▼
Multi-Factor Ranker Scoring
          │
          ▼
Threshold Filtering & Access Count Update
```

---

## 2. Multi-Factor Ranking Formula

Composite Score calculation in `ranking.py`:

$$\text{Score} = w_{\text{sem}} \cdot S_{\text{sem}} + w_{\text{kw}} \cdot S_{\text{kw}} + w_{\text{task}} \cdot S_{\text{task}} + w_{\text{scope}} \cdot S_{\text{scope}} + w_{\text{imp}} \cdot S_{\text{imp}} + w_{\text{ver}} \cdot S_{\text{ver}} + w_{\text{fresh}} \cdot S_{\text{fresh}} - P_{\text{contradiction}} - P_{\text{stale}}$$

### Weight Configuration (`RankingWeights`):
- `semantic_similarity`: `0.30`
- `keyword_match`: `0.15`
- `task_relevance`: `0.15`
- `project_relevance`: `0.10`
- `importance`: `0.10`
- `verification_quality`: `0.10`
- `freshness`: `0.10`
- `contradiction_penalty`: `-0.50`
- `stale_penalty`: `-0.30`
