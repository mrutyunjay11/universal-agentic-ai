# Universal Agentic AI — Distributed Task Queues & Worker Pools

## 1. Durable Task Queue

The `DurableTaskQueue` provides provider-independent priority dispatching, visibility timeouts, and dead-letter queue (DLQ) routing:

```text
Enqueue Task (Priority 1-10)
            │
            ▼
      Pending Queue
            │
            ▼
Lease to Worker (Visibility Timeout: 30s)
            │
      ┌─────┴─────┐
      ▼           ▼
  Heartbeat    Execution
  (Renewal)        │
            ┌─────┴─────┐
            ▼           ▼
        Complete      Fail
            │           │
            ▼           ▼
       Acknowledge   Retry Count < 3 ?
                     ├── Yes ──► Requeue
                     └── No  ──► Dead-Letter Queue (DLQ)
```

---

## 2. Specialized Worker Pools

Workers are segregated by workload demands:
- `GENERAL_WORKERS`: Standard planning and light reasoning
- `CODING_WORKERS`: Code execution, AST analysis, sandboxed compilation
- `BROWSER_WORKERS`: Playwright/Puppeteer rendering and web navigation
- `GPU_WORKERS`: Multimodal, vision, and local inference
- `DATA_WORKERS`: Pandas/Polars large dataset transformations
- `SANDBOX_WORKERS`: Isolated untrusted external command execution
