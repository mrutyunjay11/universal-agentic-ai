# Universal Agentic AI — Security Hardening & Zero-Trust Architecture

## 1. Identity Attributions

Every sensitive action is attributed to a strongly typed principal:
- `HUMAN_USER`
- `SERVICE_ACCOUNT`
- `AGENT_IDENTITY`
- `WORKER_IDENTITY`
- `ADMINISTRATOR`

---

## 2. Tool Trust Tiers & Supply-Chain Security

Tools registered into the platform must possess trust metadata:
- `OFFICIAL`: Signed core platform tools
- `VERIFIED`: Audited partner/ecosystem plugins
- `USER_INSTALLED`: Sandboxed user scripts
- `UNTRUSTED`: Strictly rejected in production mode
- `DISABLED`: Emergency kill-switch disabled

---

## 3. Network Egress Security

All outbound network requests are validated against domain allowlists with SSRF protection.
