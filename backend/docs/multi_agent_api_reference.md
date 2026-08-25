# Universal Agentic AI — Autonomy & Multi-Agent API Reference

## 1. REST API Endpoints

The Autonomy API exposes complete control over single and multi-agent workflows under `/api/autonomy/`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/autonomy/tasks` | Submit complex task for autonomous multi-agent execution |
| `GET` | `/api/autonomy/tasks/{task_id}` | Fetch master task status and aggregated results |
| `POST` | `/api/autonomy/tasks/{task_id}/pause` | Pause long-horizon execution |
| `POST` | `/api/autonomy/tasks/{task_id}/resume` | Resume paused task from checkpoint |
| `POST` | `/api/autonomy/tasks/{task_id}/cancel` | Safely cascade cancel all subtasks |
| `GET` | `/api/autonomy/tasks/{task_id}/graph` | Retrieve SubTask DAG representation |
| `GET` | `/api/autonomy/tasks/{task_id}/agents` | List active specialized sub-agents |
| `GET` | `/api/autonomy/tasks/{task_id}/events` | Fetch audit trail of autonomy events |
| `GET` | `/api/autonomy/tasks/{task_id}/artifacts` | Fetch shared artifacts produced during execution |
| `GET` | `/api/autonomy/agents` | List all registered specialized agent profiles |
| `GET` | `/api/autonomy/agents/{agent_id}` | Fetch details of a specific agent profile |
| `GET` | `/api/autonomy/workflows` | List registered persistent workflows |
