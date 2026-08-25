# Universal Agentic AI — Context Architecture & Token Budgeting

## 1. Context Slot Hierarchy

To prevent LLM context window explosion, prompts are assembled in distinct, budgeted slots:

```text
=== SYSTEM ===
Agent identity, guidelines, tool constraints

=== CURRENT_TASK ===
Normalized goal, risk level, success criteria

=== CURRENT_PLAN ===
Execution DAG steps, version, and dependencies

=== PROJECT_MEMORY ===
Verified workspace conventions, framework, build commands

=== EXTERNAL_KNOWLEDGE ===
Relevant verified facts and procedural memories

=== EVIDENCE ===
Original sources, citations, and authority scores

=== TOOL_RESULTS ===
Compressed recent observations and diagnostic outputs
```

---

## 2. Token Budgeting Strategy

Default allocations (`ContextBudget`):

| Context Slot | Target Budget (Tokens) | Overflow Strategy |
| :--- | :--- | :--- |
| `SYSTEM` | 2,000 | Immutable |
| `CURRENT_TASK` | 1,500 | Core goal preserved |
| `CURRENT_PLAN` | 1,500 | Step descriptions truncated |
| `PROJECT_MEMORY` | 2,000 | Ranked by relevance |
| `EXTERNAL_KNOWLEDGE` | 2,500 | Summarized & ranked |
| `EVIDENCE` | 2,500 | Middle-truncated with citation intact |
| `TOOL_RESULTS` | 2,000 | Compressed output |
| **Total Target** | **16,000** | Scalable up to 32k/128k |

---

## 3. Dynamic Compression Strategies

1. **`TRUNCATE`**: Middle-truncation preserves head and final conclusion lines while compressing voluminous internal logs.
2. **`SUMMARIZE`**: Extracts key factual sentences and structured result summaries.
3. **`DEDUPLICATE`**: Eliminates repeated error stacks or log lines.
4. **`COMPRESS_TOOL_OUTPUT`**: Converts raw JSON/table payloads into concise summaries without losing numbers, exit codes, or URLs.
