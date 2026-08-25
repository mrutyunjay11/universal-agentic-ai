# Universal Agentic AI — Memory Lifecycle & Consolidation

## 1. Lifecycle States & Transitions

```text
       [ Task Execution ]
               │
               ▼ (Observation / Evidence)
       [ Working Memory ]
               │
               ▼ (Consolidation Pipeline)
       [ Candidate Memory ]
               │
               ├── Verified? ────> [ Persistent Fact / Project Memory ]
               │
               └── Ephemeral? ───> [ Discarded ]
```

---

## 2. Decay, Stale Knowledge, and Invalidation

1. **Exponential Half-Life Decay**:
   - `WORKING`: $t_{1/2} = 0.1$ days (~2.4 hours)
   - `EPISODIC`: $t_{1/2} = 14$ days
   - `PROJECT`: $t_{1/2} = 60$ days
   - `USER_PREFERENCE`: $t_{1/2} = 365$ days

2. **Non-Destructive Superseding**:
   When new official documentation or empirical tests contradict an existing memory:
   - Old memory is marked `SUPERSEDED` / `CONTRADICTED` with `superseded_by` linked to the new record ID.
   - An `InvalidationRecord` is appended to the audit log.
   - Old record remains in storage for auditability but receives ranking penalties during active queries.
