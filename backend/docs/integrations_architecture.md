# Universal Agentic AI — Integrations & External Systems Architecture (Phase 6)

## 1. Architectural Overview

Phase 6 connects the Universal Agentic AI to real-world deployment environments, APIs, databases, containers, cloud providers, and communication channels without sacrificing the security, sandboxing, and evaluation guarantees built in Phases 1–5.

```text
                               Agent Execution
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │  Integration Router   │
                          │ (Capability Matching) │
                          └──────────┬────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │  Credential Manager   │
                          │ (Opaque Ref Isolation)│
                          └──────────┬────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │   Permission Scopes   │
                          │ (Fine-Grained Policy) │
                          └──────────┬────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │  Action Preview Gate  │
                          │(Human Approval Check) │
                          └──────────┬────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │  External Connector   │
                          │ (GitHub, AWS, Email)  │
                          └──────────┬────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │  Real-World Target    │
                          │ (API, Cloud, Machine) │
                          └──────────┬────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │ State Reconciliation  │
                          │  & Verifications      │
                          └──────────┬────────────┘
                                      │
                                      ▼
                             Verified Result
```

---

## 2. Core Security & Isolation Principles

1. **No Raw Secrets in LLM Context**: The agent interacts strictly through opaque identifiers (`cred_github_main`, `cred_aws_prod`). Raw secrets reside in the in-memory `SecretStore` and are injected only at the connector execution boundary.
2. **Fine-Grained Scopes**: External permissions are partitioned by action type (e.g. `email.read` vs `email.send`, `k8s.read` vs `k8s.apply`).
3. **Structured Previews & Approval Gates**: All high-impact external actions (destructive DB mutations, production deployments, outbound emails to external recipients) generate structured previews requiring explicit approval before execution.
4. **State Reconciliation**: Post-execution verification queries the actual external system state rather than blindly trusting local return flags.
