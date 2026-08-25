import pytest
from app.platform.database import PlatformDatabase


class TestPlatformDatabase:
    def test_entity_crud_and_tenant_partitioning(self):
        db = PlatformDatabase()

        # Save entity in tenant_alpha
        ent = db.save_entity(
            entity_type="workflow_state",
            data={"current_step": 3, "status": "RUNNING"},
            tenant_id="tenant_alpha",
            user_id="user_alice",
            custom_id="wf_state_101",
        )

        assert ent.id == "wf_state_101"
        assert ent.version == 1

        # Query in tenant_alpha -> Found
        res = db.get_entity("wf_state_101", tenant_id="tenant_alpha")
        assert res is not None
        assert res.data["current_step"] == 3

        # Cross-tenant query in tenant_beta -> Blocked (None)
        cross_res = db.get_entity("wf_state_101", tenant_id="tenant_beta")
        assert cross_res is None
