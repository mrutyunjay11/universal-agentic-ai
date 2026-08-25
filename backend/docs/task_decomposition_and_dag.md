# Universal Agentic AI — Task Decomposition & Dependency Graph (DAG)

## 1. Task Decomposition Architecture

The `TaskDecomposer` breaks unstructured complex user goals into structured subtasks with explicit dependencies and required capabilities:

```json
{
  "root_task": "mtask_101",
  "subtasks": [
    {
      "id": "mtask_101_research_primary",
      "objective": "Search official documentation and collect initial evidence",
      "dependencies": [],
      "required_capabilities": ["web.search", "web.fetch"],
      "permission_tier": "network"
    },
    {
      "id": "mtask_101_research_secondary",
      "objective": "Search secondary technical references and release notes",
      "dependencies": [],
      "required_capabilities": ["web.search"],
      "permission_tier": "network"
    },
    {
      "id": "mtask_101_verifier",
      "objective": "Compare sources, check contradictions, and establish ground truth verdict",
      "dependencies": ["mtask_101_research_primary", "mtask_101_research_secondary"],
      "required_capabilities": ["verify.claim"],
      "permission_tier": "read"
    }
  ]
}
```

---

## 2. Dependency Graph & Cycle Detection

The `TaskGraph` manages subtasks as a directed acyclic graph:

- **Ready Task Discovery (`get_ready_subtasks`)**: Resolves tasks whose prerequisite dependencies have transitioned to `COMPLETED`.
- **Topological Cycle Prevention (`is_acyclic`)**: Kahn's algorithm validates acyclicity and prevents circular wait deadlocks.
- **Priority-Based Dispatch**: Subtasks are scheduled according to priority levels [1-10].
