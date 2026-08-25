# Universal Agentic AI — Observability, Tracing & Alerting

## 1. Distributed Tracing (`trace_id` & `span_id`)

Every incoming user request generates an immutable root `trace_id`. Child execution steps create nested spans:

```text
Trace: trc_task_881
├── [Span] MasterOrchestrator.Execute (parent: null)
│   ├── [Span] TaskDecomposer.CreateDAG (parent: span_orch)
│   ├── [Span] CoderAgent.Run (parent: span_orch)
│   │   ├── [Span] Tool.read_file (parent: span_coder)
│   │   └── [Span] Tool.edit_file (parent: span_coder)
│   └── [Span] VerifierAgent.Verify (parent: span_orch)
│       └── [Span] ClaimExtractor.VerifyAST (parent: span_verifier)
```

---

## 2. Telemetry & Metric Aggregation

`PlatformTelemetry` tracks:
- **Task Success / Failure Rate**
- **Tool Execution Success Rate**
- **Average Latency Distributions** (Agent, Tool, LLM, Queue, Memory Retrieval)

---

## 3. Real-Time Alerting

`AlertManager` categorizes anomalies:
- `FAILURE_SPIKE`: Sudden increase in step/task failures
- `SECURITY_VIOLATION`: Unauthorized permission attempts
- `LATENCY_SPIKE`: Latency degradation beyond SLO
- `BUDGET_OVERRUN`: Cost spikes approaching budget caps
