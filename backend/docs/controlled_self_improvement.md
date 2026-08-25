# Universal Agentic AI — Controlled Evidence-Based Self-Improvement

## 1. Core Principle: Anti-Degradation Governance

The agent **does not perform uncontrolled runtime self-modification**. Improvements must follow an evidence-backed qualification pipeline:

```text
               Observed Failure / Latency
                            │
                            ▼
                   Root Cause Analysis
                            │
                            ▼
                   Improvement Proposal
              (Prompt, Weight, Routing diff)
                            │
                            ▼
                   Sandbox Evaluation
                            │
                            ▼
              ├── Safety Scanner Check (Zero tolerance)
              ├── Benchmark Suite ($\ge 60\%$ Pass Rate)
              └── Regression Suite (100% Pass Rate)
                            │
                            ▼
                  Approved Candidate Version
                            │
                            ▼
                Canary / Production Promotion
```

---

## 2. Improvement Proposal Types

- `PROMPT_OPTIMIZATION`: Prompt template tuning or system instruction clarification.
- `ROUTING_WEIGHT_TUNING`: Capability router priority adjustments based on tool reliability health.
- `RETRIEVAL_WEIGHT_TUNING`: Multi-factor ranker weights (`project_relevance`, `freshness`, `importance`).
- `PLANNER_STRATEGY_TUNING`: DAG decomposition heuristics and verification requirements.
- `VERIFICATION_RULE_UPDATE`: Specialized claim extraction patterns.
