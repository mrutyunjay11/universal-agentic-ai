# Universal Agentic AI — Observability & Evaluation Dashboard API

## 1. REST Endpoints

The evaluation layer exposes dedicated observability endpoints:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/evaluation/tasks` | List evaluated task scorecards |
| `GET` | `/api/evaluation/metrics` | Aggregate quality scores, Brier score, ECE |
| `GET` | `/api/evaluation/failures` | 16-category taxonomy distribution & root causes |
| `GET` | `/api/evaluation/regressions` | List persistent regression test cases |
| `GET` | `/api/evaluation/benchmarks` | Run and fetch golden benchmark scores |
| `GET` | `/api/evaluation/tools` | Tool reliability health and latency metrics |
| `GET` | `/api/evaluation/traces/{task_id}` | Complete trajectory with scorecard overlay |
| `POST` | `/api/evaluation/evaluate/{task_id}` | Trigger ad-hoc task evaluation |
| `POST` | `/api/evaluation/feedback` | Record structured human review feedback |
| `POST` | `/api/evaluation/improvement/propose` | Propose controlled modification |
| `POST` | `/api/evaluation/improvement/validate` | Run sandboxed validation on proposal |

---

## 2. Circuit Breaker Protection

- `CLOSED`: Normal tool execution.
- `OPEN`: Repeated failures ($\ge 3$) trip breaker; fast fails requests during cooldown.
- `HALF_OPEN`: Probes tool availability with limited traffic after cooldown before full recovery.
