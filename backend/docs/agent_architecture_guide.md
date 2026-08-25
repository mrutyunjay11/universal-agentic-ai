# Universal Agentic AI — Phase 2 Architecture Guide

## 1. Overview

Phase 2 builds the cognitive intelligence, task understanding, DAG planning, capability routing, verification, and reflective orchestration layer on top of the Phase 1 Universal Tool Ecosystem.

```text
User / API Request
        ↓
Goal Understanding (Goals, Constraints, Evidence, Risks)
        ↓
Task Classification (14 Canonical Task Types)
        ↓
DAG Planning & Layering (Topological execution sequence)
        ↓
Plan Validation (Acyclicity, Permissions, Capability availability)
        ↓
Capability-Based Tool Routing (Metadata & Safety selection)
        ↓
Execution Engine (Sandboxing, Auditing, Timeouts, Provenance)
        ↓
Observation Management (Evidence extraction, Context budgeting)
        ↓
Verification Subsystem (Math, Code, Claim, Source authority)
        ↓
Reflection Engine (Evaluation, Contradiction detection, Replanning)
        ↓
Completion & Grounded Synthesis
```

---

## 2. Component Architecture

### `AgentState` (`app/agent/state.py`)
- Strongly typed Pydantic V2 state tracking:
  - `task_id`, `session_id`, `original_request`, `normalized_goal`
  - `task_type`, `task_status` (13 explicit lifecycle states with transition validation)
  - `plan` (List of `PlanStep` with dependencies, capabilities, verification requirements, failure strategies)
  - `observations`, `evidence`, `verification_results`
  - `budget` (iteration count, tool calls, elapsed time, token quota)
  - `user_approvals`, `pending_approval`

### `TaskUnderstander` (`app/agent/understanding.py`)
- Extracts constraints, known facts, missing info, required evidence types, success criteria, and risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

### `TaskClassifier` (`app/agent/classifier.py`)
- Categorizes tasks into: `RESEARCH`, `CODING`, `DEBUGGING`, `FACT_CHECK`, `DATA_ANALYSIS`, `MATHEMATICAL`, `SCIENTIFIC`, `BROWSER_TASK`, `DOCUMENT_ANALYSIS`, `SYSTEM_TASK`, `MULTI_DOMAIN`, `GENERAL_QUESTION`, `UNKNOWN`.

### `DAGPlanner` & `PlanValidator` (`app/agent/planner.py`, `app/agent/plan_validator.py`)
- Constructs structured DAG plans.
- Groups independent steps into parallel execution layers.
- Detects dependency cycles, missing dependencies, permission mismatches, and safety policy violations.

### `ToolRouter` (`app/agent/router.py`)
- Decouples planner from hardcoded tool names.
- Maps abstract capabilities (`file.read`, `web.search`, `code.analyze`, `verify.claim`, `math.calculate`) to Phase 1 tools.

### `ExecutionEngine` (`app/agent/executor.py`)
- Executes steps via Phase 1 `tool_registry.execute()`.
- Enforces human approval gating for sensitive operations (`WAITING_FOR_APPROVAL`).
- Records call logs, durations, and output formats.

### `ObservationManager` & `AgentContextManager` (`app/agent/observer.py`, `app/agent/context.py`)
- Extracts evidence and summaries from raw tool outputs.
- Budgets multi-slot context (`Goal`, `Plan`, `Observations`, `Evidence`, `Verifications`) to prevent context window explosion.

### `VerificationCoordinator` (`app/agent/verifier.py`)
- Directly interfaces with Phase 1 verification tools:
  - Numerical / symbolic math claims -> `verify_calculation`
  - Code assertions -> `verify_code`
  - Factual / web claims -> `verify_claim`, `detect_contradiction`, `check_source_authority`

### `ReflectionEngine` & `Replanner` (`app/agent/reflector.py`, `app/agent/replanner.py`)
- Evaluates step outcomes and triggers state transitions (`CONTINUE`, `REPLAN`, `COMPLETE`, `FAIL`, `ASK_USER`).
- Adapts plans on failure without discarding successful prior work.

### `CheckpointManager` & `BudgetManager` (`app/agent/checkpoint.py`, `app/agent/budget.py`)
- Checkpoints state snapshots for crash recovery and pause/resume.
- Enforces strict iteration, time, token, and tool call resource budgets.

---

## 3. FastAPI API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/agent/tasks` | Create and start a goal-driven task |
| `GET` | `/api/agent/tasks/{id}` | Inspect task status and progress |
| `GET` | `/api/agent/tasks/{id}/state` | Retrieve full serialized `AgentState` |
| `GET` | `/api/agent/tasks/{id}/events` | Retrieve complete event log |
| `POST` | `/api/agent/tasks/{id}/resume` | Resume paused task or grant approval |
| `POST` | `/api/agent/tasks/{id}/cancel` | Cancel active task |
| `POST` | `/api/agent/tasks/{id}/approval` | Submit human approval decision |
