# 🚀 Universal Agentic AI Platform

[![Tests](https://img.shields.io/badge/Tests-251%20Passed%20(100%25)-brightgreen.svg)](file:///Users/mrutyunjayjoshi/Desktop/ai_agent/backend/tests)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org/)
[![Architecture](https://img.shields.io/badge/Model%20Stack-Qwen3.8--Max%20%7C%20Qwen3--Embedding--8B%20%7C%20Qwen3--Reranker--8B-purple.svg)](file:///Users/mrutyunjayjoshi/Desktop/ai_agent/backend/docs/model_architecture.md)

A general-purpose, model-agnostic, production-hardened **Autonomous Agentic AI Platform** powered by the **Qwen3.8-Max Model Stack**, **Dynamic Context Intelligence**, **Multi-Agent Orchestration**, and **Deterministic Tool Verification**.

---

## 🌟 Key Architecture & Capabilities

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

### 🧠 Core Subsystems
1. **Phase 1 — Universal Tool Ecosystem**: 169 tools across system, code, terminal, testing, data, database, browser, documents, web, and arithmetic with security permissions and audit trails.
2. **Phase 2 — Agent Brain & DAG Planning**: Dynamic task understanding, multi-step planning, reflection, checkpoint rollback, and model abstraction.
3. **Phase 3 — Memory & Knowledge Infrastructure**: Hybrid SQLite + Vector memory, exponential time decay, memory consolidation, and semantic retrieval.
4. **Phase 4 — Evaluation & Reliability**: 8 quality dimensions, 16 failure taxonomies, automated Root Cause Analysis (RCA), golden benchmarks, and controlled self-improvement.
5. **Phase 5 — Advanced Autonomy & Multi-Agent**: `MasterOrchestrator`, subtask DAGs, parallel scheduler, 8 specialized agent personas, and consensus voting.
6. **Phase 6 — Real-World Integrations**: 15 connectors (GitHub, GitLab, Email, Calendar, Storage, Cloud, Database, Docker, Kubernetes, CI/CD, Monitoring, Slack, Discord, Remote Exec, Generic API).
7. **Phase 7 — Production Platform**: Durable priority task queue, distributed locks, GPU scheduling, multi-tenant partitioning, cost governance, telemetry, alerts, and disaster recovery.
8. **Dynamic Context Intelligence Upgrade**: Working reasoning surface paradigm, 4-level fallback reranking, progressive disclosure (Levels 0-4), temporal/version conflict detection, and prompt injection sandboxing (`<EXTERNAL_DATA>`).
9. **Approved Model Stack**:
   - **Main Reasoning**: `Qwen3.8-Max` (Remote Managed API) & `Qwen/Qwen3.8-2.4T-A95B` (Open-Weight Cluster)
   - **Semantic Embedding**: `Qwen/Qwen3-Embedding-8B` (4096-dim dense vectors)
   - **Exact Retrieval**: `BM25` deterministic lexical matching
   - **Reranker**: `Qwen/Qwen3-Reranker-8B` (cross-attention scoring with 4-tier graceful fallback)
   - **Verification**: Deterministic verification tools (AST, Pytest, SymPy, Pandas)

---

## 💻 Hardware Requirements Matrix

| Tier | Target Use Case | CPU | RAM / Unified Memory | GPU / VRAM | Storage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Minimum** | **Remote API Mode** (`Qwen3.8-Max` via API + local BM25 + Dynamic Context) | 4 Cores (Intel / AMD / Apple M1) | **8 GB – 16 GB** | None (CPU inference) | 10 GB SSD |
| **Recommended** | **Local Hybrid Mode** (`Qwen2.5-Coder-32B/14B` + `Qwen3-Embedding-8B` + `Qwen3-Reranker-8B`) | 8+ Cores (Apple Silicon Pro/Max or modern x86_64) | **32 GB – 64 GB** | **16 GB – 24 GB VRAM** (RTX 3090/4090 or Apple 36GB+ Unified Memory) | 50 GB NVMe SSD |
| **Best / Enterprise** | **Full Local Flagship** (Full 2.4T open-weight `Qwen/Qwen3.8-2.4T-A95B` cluster) | 32+ Cores (AMD EPYC / Intel Xeon) | **512 GB – 1 TB RAM** | **8× NVIDIA H100 / A100 (80GB)** (480 GB+ VRAM cluster) | 1 TB+ NVMe SSD |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* **Python**: `Python 3.12`
* **Node.js**: `Node.js 18+` or `20+`
* **Git** installed

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run full test suite (251 tests)
pytest tests/ -v

# Start FastAPI backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* **Swagger API Documentation**: `http://localhost:8000/docs`
* **Health Endpoint**: `http://localhost:8000/api/health`

### 3. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install Node packages
npm install

# Start Next.js development server
npm run dev
```
* **Web UI URL**: `http://localhost:3000`

---

## 🐳 Docker Deployment

To launch the complete platform using Docker:
```bash
# Build and run backend container
cd backend
docker-compose up -d
```

---

## 🧪 Testing & Verification

The platform features a 251-test unified test suite across all subsystems:

```bash
cd backend
.venv/bin/pytest tests/ -W error
```

```text
============================= 251 passed in 12.12s =============================
```

- **Phase 1 Tools**: 57 tests passing
- **Phase 2 Agent Brain**: 29 tests passing
- **Phase 3 Memory Infrastructure**: 24 tests passing
- **Phase 4 Evaluation & Reliability**: 27 tests passing
- **Phase 5 Autonomy & Multi-Agent**: 27 tests passing
- **Phase 6 Integrations**: 29 tests passing
- **Phase 7 Platform & Scaling**: 25 tests passing
- **Dynamic Context Intelligence**: 24 tests passing
- **Model Stack & Hybrid Retrieval**: 9 tests passing

---

## 📜 License

This project is licensed under the Apache-2.0 License.
