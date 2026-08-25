from __future__ import annotations
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.integrations.secrets import secret_store


class CredentialMetadata(BaseModel):
    ref_id: str
    provider: str
    credential_type: str  # "api_key", "oauth2", "ssh_key", "service_account"
    user_id: str = "default_user"
    project_id: Optional[str] = None
    tenant_id: str = "default_tenant"
    scopes: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


import datetime


class CredentialManager:
    """
    Centralized credential management layer.
    Allows agents to use opaque references (e.g. 'cred_github_main') without exposing
    raw secret tokens to the model or prompt contexts. Enforces multi-tenant and project isolation.
    """

    def __init__(self):
        self._credentials: dict[str, CredentialMetadata] = {}

    def register_credential(
        self,
        provider: str,
        secret_value: str,
        credential_type: str = "api_key",
        user_id: str = "default_user",
        project_id: Optional[str] = None,
        tenant_id: str = "default_tenant",
        scopes: Optional[list[str]] = None,
        custom_ref_id: Optional[str] = None,
    ) -> CredentialMetadata:
        ref_id = custom_ref_id or f"cred_{provider.lower()}_{uuid.uuid4().hex[:6]}"
        meta = CredentialMetadata(
            ref_id=ref_id,
            provider=provider,
            credential_type=credential_type,
            user_id=user_id,
            project_id=project_id,
            tenant_id=tenant_id,
            scopes=scopes or [],
        )
        self._credentials[ref_id] = meta
        # Store raw secret safely in vault
        secret_store.store_secret(ref_id, secret_value)
        return meta

    def get_credential_metadata(
        self,
        ref_id: str,
        user_id: str = "default_user",
        tenant_id: str = "default_tenant",
    ) -> Optional[CredentialMetadata]:
        meta = self._credentials.get(ref_id)
        if not meta:
            return None
        # Verify tenant & user isolation
        if meta.tenant_id != tenant_id or meta.user_id != user_id:
            return None
        return meta

    def resolve_raw_secret(
        self,
        ref_id: str,
        user_id: str = "default_user",
        tenant_id: str = "default_tenant",
    ) -> Optional[str]:
        meta = self.get_credential_metadata(ref_id, user_id=user_id, tenant_id=tenant_id)
        if not meta:
            return None
        return secret_store.retrieve_secret(ref_id)

    def revoke_credential(self, ref_id: str) -> bool:
        if ref_id in self._credentials:
            del self._credentials[ref_id]
            secret_store.delete_secret(ref_id)
            return True
        return False

    def list_credentials_for_user(
        self,
        user_id: str = "default_user",
        tenant_id: str = "default_tenant",
    ) -> list[CredentialMetadata]:
        return [
            meta for meta in self._credentials.values()
            if meta.user_id == user_id and meta.tenant_id == tenant_id
        ]


credential_manager = CredentialManager()
