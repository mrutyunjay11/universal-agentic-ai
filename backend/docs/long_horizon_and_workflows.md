# Universal Agentic AI — Long-Horizon Execution & Persistent Workflows

## 1. Checkpoint Snapshots & Recovery

The `LongHorizonManager` creates persistent snapshots of the subtask DAG state at major transition boundaries:

- `INITIAL_DECOMPOSITION`
- `POST_EXECUTION`
- `ERROR_RECOVERY`

If an agent or host process is interrupted, the state machine can restore the exact graph from the latest checkpoint and resume unfinished subtasks without re-executing completed work.

---

## 2. Stateful Conditional Workflows

The `PersistentWorkflowEngine` supports multi-stage workflows with dynamic fallback branching:

```text
Research
   ↓
Implementation
   ↓
Testing ──(Fail)──→ Debugging ──→ Testing
   ↓ (Pass)
Final Verification
   ↓
Report
```
