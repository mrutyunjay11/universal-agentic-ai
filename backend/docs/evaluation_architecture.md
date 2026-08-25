# Universal Agentic AI — Evaluation Architecture (Phase 4)

## 1. Architectural Overview

Phase 4 establishes an independent, multi-dimensional **Evaluation, Reliability, Safety, Quality Assurance, Observability, and Controlled Evidence-Based Self-Improvement Layer** that operates alongside the agent execution engine.

```text
                                User Task / Request
                                         │
                                         ▼
                               Phase 2 & 3 Execution
                        (State Machine, Tools, Memory)
                                         │
                                         ▼
                            Complete Execution Trace
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │     Universal Evaluator Engine       │
                      │  (Correctness, Completeness, Safety) │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    Specialized Evaluation Suite      │
                      │  ├── Factuality & Evidence Mapping   │
                      │  ├── Technical Correctness (AST/Code)│
                      │  ├── Tool Latency & Reliability      │
                      │  ├── Planner Optimality & Acyclicity │
                      │  └── Safety & Prompt Injection Check │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    Quality Scores & RCA Diagnostics  │
                      │ (Taxonomy Categorization & Reporting)│
                      └──────────────────────────────────────┘
```

---

## 2. Standardized Quality Dimensions

Every evaluated task produces independent scores across 8 core dimensions [0.0 - 1.0]:

| Dimension | Description | Minimum Passing Gate |
| :--- | :--- | :--- |
| `CORRECTNESS` | Objective technical accuracy, schema compliance, tests | $\ge 0.75$ |
| `COMPLETENESS` | Satisfaction of user-specified requirements & plan steps | $\ge 0.70$ |
| `RELEVANCE` | Precision and adherence to normalized task goal | $\ge 0.70$ |
| `EVIDENCE_QUALITY` | Provenance citations and non-contradiction | $\ge 0.60$ |
| `VERIFICATION_QUALITY` | Empirical verifier agreement and confidence | $\ge 0.60$ |
| `SAFETY` | Zero tolerance for command/injection/secret leakage | $= 1.00$ |
| `EFFICIENCY` | Execution latency and iteration budget economy | $\ge 0.20$ |
| `REPRODUCIBILITY` | Determinism across identical runs and seed stability | $\ge 0.70$ |

---

## 3. Core Subsystems

1. **`metrics.py` & `rubric.py`**: Strongly-typed `TaskEvaluationResult`, `CriterionEvaluation`, `EvaluationRubric`, `ConfidenceCalibrationTracker`.
2. **`factuality.py`**: `FactualityEvaluator` extracting verifiable claims, mapping to source evidence snippets, and penalizing refutations.
3. **`tool_evaluator.py`**: `ToolReliabilityMonitor` tracking tool latency, timeouts, permission denials, and computing health scores.
4. **`planning_evaluator.py`**: `PlannerEvaluator` analyzing DAG minimality, duplicate tool calls, dependency validity, and topological acyclicity.
5. **`verification_evaluator.py`**: `VerificationEvaluator` measuring verifier performance, agreement, and evidence attribution.
6. **`safety_evaluator.py`**: `SafetyEvaluator` scanning for prompt injection, secret exposure, command injection, and path traversal.
7. **`reports.py`**: `RootCauseAnalyzer` mapping failures to the 16-category standardized taxonomy and generating JSON/Markdown reports.
8. **`regression.py`**: `RegressionSuite` converting observed failures into reproducible regression tests.
9. **`benchmarks.py` & `datasets.py`**: `BenchmarkFramework` testing 14 benchmark domains with golden tasks.
10. **`circuit_breaker.py`**: `CircuitBreakerManager` preventing retry storms on degraded external tools.
11. **`improvement.py`**: `ControlledSelfImprovementPipeline` managing candidate proposals through sandboxed validation gates.
