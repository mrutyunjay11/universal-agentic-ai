# Universal Agentic AI — Platform REST API Reference

## 1. Health & Probe Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Basic application health |
| `GET` | `/health/live` | Kubernetes / Cloud liveness probe |
| `GET` | `/health/ready` | Readiness probe (is system accepting tasks) |
| `GET` | `/health/dependencies` | Deep dependency health check (DB, queue, vector, models) |

---

## 2. Platform Management Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/platform/diagnostics` | Comprehensive system self-diagnostics |
| `GET` | `/api/platform/queue` | Task queue depth and dead-letter count |
| `POST` | `/api/platform/queue/enqueue` | Asynchronously enqueue a prioritized task |
| `GET` | `/api/platform/workers` | List active worker nodes and heartbeats |
| `GET` | `/api/platform/costs` | Retrieve operational cost summary |
| `POST` | `/api/platform/budgets` | Set spend budget limits |
| `GET` | `/api/platform/traces/{trace_id}` | Retrieve distributed trace span tree |
| `GET` | `/api/platform/metrics` | Telemetry performance and latency metrics |
| `GET` | `/api/platform/alerts` | Query active and historical platform alerts |
| `POST` | `/api/platform/backups/create` | Trigger automated backup snapshot |
| `POST` | `/api/platform/backups/restore-test` | Execute automated restoration verification drill |
| `GET` | `/api/platform/feature-flags` | List feature flags and rollouts |
| `POST` | `/api/platform/feature-flags` | Update or toggle feature flag |
| `POST` | `/api/platform/privacy/forget` | GDPR privacy forget and purge user memories |
