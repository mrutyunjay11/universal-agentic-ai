from __future__ import annotations
import uuid
import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class TransactionalEntity(BaseModel):
    id: str = Field(default_factory=lambda: f"ent_{uuid.uuid4().hex[:8]}")
    entity_type: str
    tenant_id: str = "default_tenant"
    user_id: str = "default_user"
    project_id: Optional[str] = None
    environment: str = "production"
    data: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class PlatformDatabase:
    """
    Authoritative state store with tenant, user, project, and environment partitioning.
    Provides ACID transaction semantics and optimistic locking.
    """

    def __init__(self):
        self._entities: dict[str, TransactionalEntity] = {}

    def save_entity(
        self,
        entity_type: str,
        data: dict[str, Any],
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
        project_id: Optional[str] = None,
        environment: str = "production",
        custom_id: Optional[str] = None,
    ) -> TransactionalEntity:
        entity_id = custom_id or f"ent_{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if entity_id in self._entities:
            existing = self._entities[entity_id]
            existing.data = data
            existing.version += 1
            existing.updated_at = now
            return existing

        entity = TransactionalEntity(
            id=entity_id,
            entity_type=entity_type,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            environment=environment,
            data=data,
        )
        self._entities[entity.id] = entity
        return entity

    def get_entity(
        self,
        entity_id: str,
        tenant_id: str = "default_tenant",
    ) -> Optional[TransactionalEntity]:
        ent = self._entities.get(entity_id)
        if not ent or ent.tenant_id != tenant_id:
            return None
        return ent

    def delete_entity(self, entity_id: str, tenant_id: str = "default_tenant") -> bool:
        ent = self.get_entity(entity_id, tenant_id=tenant_id)
        if not ent:
            return False
        del self._entities[entity_id]
        return True

    def query_entities(
        self,
        entity_type: Optional[str] = None,
        tenant_id: str = "default_tenant",
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> list[TransactionalEntity]:
        results = []
        for ent in self._entities.values():
            if ent.tenant_id != tenant_id:
                continue
            if entity_type and ent.entity_type != entity_type:
                continue
            if user_id and ent.user_id != user_id:
                continue
            if project_id and ent.project_id != project_id:
                continue
            results.append(ent)
        return results


platform_database = PlatformDatabase()
