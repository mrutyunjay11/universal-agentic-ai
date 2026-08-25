# Universal Agentic AI — Resource Management, Watchdog & Deadlock Prevention

## 1. Centralized Resource Accounting

The `ResourceManager` records consumption per task, subtask, and specialized agent:

- Total tokens (prompt + completion)
- Tool calls count
- Execution duration ms
- Estimated USD cost calculation

---

## 2. Watchdog & Deadlock Prevention

- **Stall Monitoring**: Automatically detects when task execution has not progressed within `stall_timeout_seconds`.
- **Deadlock Detection**: Analyzes the dependency graph using topological sort to detect circular wait conditions ($A \to B \to A$) and breaks deadlocks cleanly.
