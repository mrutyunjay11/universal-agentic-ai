# Universal Agentic AI — Failure Taxonomy & Automated Root Cause Analysis

## 1. Standardized 16-Category Failure Taxonomy

Failures are classified into 16 distinct categories rather than ambiguously blaming the final response:

| Failure Category | Description | Primary Diagnostic Trigger |
| :--- | :--- | :--- |
| `MODEL_ERROR` | Model generated non-compliant JSON or hallucinations | Schema parsing failure |
| `PLANNING_ERROR` | DAG cyclic dependency or impossible ordering | DAG cycle / missing step |
| `ROUTING_ERROR` | Mismatched capability selection for task objective | Incompatible tool invoked |
| `TOOL_ERROR` | Execution exception inside tool runtime | Non-zero exit code / exception |
| `TOOL_OUTPUT_ERROR` | Tool response failed validation schema | Invalid JSON / empty return |
| `MEMORY_ERROR` | Memory persistence or serialization failure | DB / store exception |
| `RETRIEVAL_ERROR` | Retrieval failed to return relevant records | Low relevance / missing context |
| `VERIFICATION_ERROR` | Calculated result contradicted empirical truth | Refuted verification check |
| `CONTEXT_ERROR` | Context overflow or compression loss | Context budget overflow |
| `PERMISSION_ERROR` | Tool call blocked due to permission tier | Missing human approval |
| `SECURITY_ERROR` | Command injection, secret leak, or path traversal | Safety evaluator alert |
| `EXTERNAL_SERVICE_ERROR` | Third-party endpoint unavailable or degraded | HTTP 5xx / connection error |
| `USER_REQUIREMENT_ERROR` | Ambiguous or contradictory prompt instructions | Conflicting criteria |
| `RESOURCE_LIMIT` | Exhausted iteration, tool call, or time quota | Budget manager exhaustion |
| `TIMEOUT` | Tool latency exceeded configured threshold | Async timeout triggered |
| `UNKNOWN` | Uncategorized failure | Unmatched error signature |

---

## 2. Automated Root Cause Analysis Pipeline

```text
               Observed Failure
                      │
                      ▼
            Collect Complete Trace
                      │
                      ▼
          Identify First Abnormal Step
                      │
                      ▼
          Analyze Upstream Dependencies
                      │
                      ▼
         Categorize Failure Taxonomy
                      │
                      ▼
         Emit Actionable Remediation
```
