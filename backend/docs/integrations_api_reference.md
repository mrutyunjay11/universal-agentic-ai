# Universal Agentic AI — Integrations REST API Reference

## 1. REST Endpoints

The Integration API manages connectors, external action previews, approval gates, and deployments under `/api/`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/integrations` | List all registered external connectors and status |
| `GET` | `/api/integrations/{name}` | Fetch connector details, auth methods, and capabilities |
| `POST` | `/api/integrations/{name}/connect` | Establish connection using opaque credential reference |
| `POST` | `/api/integrations/{name}/disconnect` | Disconnect and purge active connection state |
| `GET` | `/api/integrations/{name}/health` | Query health, latency ms, and rate limit status |
| `GET` | `/api/integrations/{name}/capabilities` | List supported capability actions |
| `GET` | `/api/integrations/{name}/permissions` | List required permission scopes |
| `POST` | `/api/external-actions/preview` | Generate pre-execution action preview |
| `POST` | `/api/external-actions/{id}/approve` | Explicitly approve pending external action |
| `POST` | `/api/external-actions/{id}/deny` | Deny pending external action |
| `GET` | `/api/external-actions/{id}` | Fetch approval state and preview details |
| `GET` | `/api/deployments` | List tracked deployments across environments |
| `GET` | `/api/deployments/{id}` | Get deployment details and verification state |
| `POST` | `/api/deployments/{id}/rollback` | Trigger automated rollback to previous version |
| `GET` | `/api/integrations/events` | Fetch audit trail of external system events |
