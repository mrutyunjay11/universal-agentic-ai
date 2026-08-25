import pytest
from app.integrations.registry import integration_registry


class TestIntegrationRegistry:
    def test_registered_connectors_discovery(self):
        connectors = integration_registry.list_connectors()
        assert len(connectors) >= 15

        names = [c.name for c in connectors]
        assert "github" in names
        assert "email" in names
        assert "calendar" in names
        assert "storage" in names
        assert "cloud" in names
        assert "docker" in names
        assert "kubernetes" in names
        assert "ci_cd" in names
        assert "monitoring" in names

    def test_find_connector_by_capability(self):
        conn = integration_registry.find_connector_for_capability("create_pull_request")
        assert conn is not None
        assert conn.name == "github"

        conn_cal = integration_registry.find_connector_for_capability("find_free_time")
        assert conn_cal is not None
        assert conn_cal.name == "calendar"
