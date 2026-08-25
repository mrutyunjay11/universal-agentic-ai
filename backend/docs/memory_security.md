# Universal Agentic AI — Memory Security & Isolation

## 1. Multi-Tenant & Project Isolation

Memory access enforces strict isolation boundaries across:
- **`user_id`**: User preferences, private history, and conversation summaries are isolated to the specific user.
- **`project_id`**: Project conventions, build scripts, and local facts are restricted to the relevant workspace.
- **`GLOBAL` Scope**: General scientific and language facts without secret tokens or workspace specifics.

---

## 2. Anti-Hallucination & Secret Filtering

1. **Selective Promotion**: Raw unverified LLM output is never automatically saved as a permanent fact. Only evidence-backed or deterministically verified items are promoted to `VERIFIED`.
2. **Secret Redaction**: When memories are created from tool executions, Phase 1 secret filters sanitize API keys, passwords, and tokens before persistence.
