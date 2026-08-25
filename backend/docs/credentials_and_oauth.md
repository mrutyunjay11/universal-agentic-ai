# Universal Agentic AI — Credentials & OAuth 2.0 Management

## 1. Opaque Credential References

To prevent credentials from leaking into agent prompt contexts or untrusted execution traces, raw secrets are never passed to the model. The agent references credentials via opaque identifiers:

```json
{
  "ref_id": "cred_github_4f92a1",
  "provider": "GitHub",
  "credential_type": "oauth2",
  "scopes": ["github.read", "github.write"],
  "tenant_id": "tenant_acme"
}
```

---

## 2. Vault Security & Multi-Tenant Isolation

- **Encrypted In-Memory Vault (`SecretStore`)**: Raw tokens reside in memory-isolated storage.
- **Tenant & Project Fencing**: Attempting to resolve a credential across different `user_id` or `tenant_id` boundaries is strictly blocked.
- **Secret Redaction**: Outbound network requests, tool results, and logs automatically redact matching patterns (`[REDACTED_SECRET]`).

---

## 3. OAuth 2.0 Lifecycle

The `OAuthFramework` handles:
1. **Authorization URL Generation with PKCE & State Protection**.
2. **Callback Code Verification & Token Exchange**.
3. **Automated Access Token Refresh**.
4. **Token Revocation**.
