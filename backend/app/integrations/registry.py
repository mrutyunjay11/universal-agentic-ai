from __future__ import annotations
from typing import Any, Optional
from app.integrations.base import Integration
from app.integrations.connectors import ALL_CONNECTORS


class IntegrationRegistry:
    """
    Registry for discovering, listing, and accessing all available external system connectors.
    """

    def __init__(self):
        self._connectors: dict[str, Integration] = {c.name: c for c in ALL_CONNECTORS}

    def register(self, connector: Integration) -> None:
        self._connectors[connector.name] = connector

    def get(self, name: str) -> Optional[Integration]:
        return self._connectors.get(name)

    def list_connectors(self) -> list[Integration]:
        return list(self._connectors.values())

    def find_connector_for_capability(self, capability: str) -> Optional[Integration]:
        for conn in self._connectors.values():
            if capability in conn.capabilities:
                return conn
        return None


integration_registry = IntegrationRegistry()
