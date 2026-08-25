# Universal Agentic AI — Multi-Agent Architecture (Phase 5)

## 1. Architectural Overview

Phase 5 introduces advanced autonomy, task delegation, parallel execution, specialized sub-agents, and multi-agent coordination while maintaining deterministic control, model diversity, and least privilege.

```text
                                 User Goal
                                     │
                                     ▼
                          ┌───────────────────────┐
                          │  Master Orchestrator  │
                          │ (Mode Determination)  │
                          └──────────┬────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
            Single-Agent Mode                Multi-Agent Mode
                    │                                 │
                    │                                 ▼
                    │                     ┌───────────────────────┐
                    │                     │    Task Decomposer    │
                    │                     │  (SubTask Graph / DAG)│
                    │                     └──────────┬────────────┘
                    │                                │
                    │                                ▼
                    │                     ┌───────────────────────┐
                    │                     │ Advanced Scheduler    │
                    │                     │ (Dependency & Batch)  │
                    │                     └──────────┬────────────┘
                    │                                │
                    │               ┌────────────────┼────────────────┐
                    │               ▼                ▼                ▼
                    │         Researcher           Coder            Data
                    │            Agent             Agent            Agent
                    │               │                │                │
                    │               └────────────────┼────────────────┘
                    │                                │
                    │                                ▼
                    │                     ┌───────────────────────┐
                    │                     │    Result Contracts   │
                    │                     │   & Shared Artifacts  │
                    │                     └──────────┬────────────┘
                    │                                │
                    │                                ▼
                    │                     ┌───────────────────────┐
                    │                     │   Conflict Resolver   │
                    │                     │  (Evidence Dominance) │
                    │                     └──────────┬────────────┘
                    │                                │
                    │                                ▼
                    │                     ┌───────────────────────┐
                    │                     │   Result Aggregator   │
                    │                     │ (Unified Ground Truth)│
                    │                     └──────────┬────────────┘
                    │                                │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
                       Unified Final Grounded Output
```

---

## 2. Core Operational Modes

| Mode | Trigger Condition | Execution Strategy |
| :--- | :--- | :--- |
| `SINGLE_AGENT` | Focused single-turn tasks (simple math, single-file lookups) | Linear execution via single agent loop |
| `PARALLEL_SUBTASKS` | Independent partition queries or multi-source fetching | Concurrent batch execution without inter-task dependencies |
| `SPECIALIZED_MULTI_AGENT` | Multi-domain requirements (research + coding + testing) | Capability-based agent assignment & topological DAG |
| `HIERARCHICAL_MULTI_AGENT` | Complex, long-horizon workflows with verification gates | Supervisor-directed execution with checkpoints & recovery |

---

## 3. Guiding Principles

1. **Optimization, Not Substitute for Verification**: Multi-agent consensus is an optimization for parallelism and domain specialization. Empirical evidence and deterministic verification strictly dominate agent consensus.
2. **Provider-Agnostic Model Diversity**: Different specialized agents can operate on different models without requiring homogeneous LLM backends.
3. **Least Privilege & Scoped Context**: Sub-agents receive only the context, memory items, and permission tiers necessary for their specific subtask.
