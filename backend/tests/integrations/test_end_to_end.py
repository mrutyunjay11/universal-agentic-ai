import pytest
from app.integrations.router import integration_router
from app.integrations.base import IntegrationContext
from app.integrations.webhooks import webhook_manager
from app.integrations.policies import action_approval_manager, ApprovalState
from app.integrations.deployment import deployment_pipeline
from app.integrations.incident import incident_workflow


class TestIntegrationsEndToEnd:
    @pytest.mark.asyncio
    async def test_scenario_a_github_pr_workflow(self):
        """Scenario A: GitHub PR opened -> Webhook verified -> Review posted."""
        payload = b'{"action": "opened", "pull_request": {"number": 42}}'
        secret = "gh_secret_key"
        sig = webhook_manager.generate_signature(payload, secret)

        valid, _ = webhook_manager.verify_webhook_event(payload, sig, secret, delivery_id="gh_deliv_001")
        assert valid is True

        ctx = IntegrationContext(task_id="task_gh_scen")
        res = await integration_router.route_and_execute("github", "review_pull_request", ctx, pr_number=42)
        assert res.status == "SUCCESS"
        assert res.data["review_status"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_scenario_b_email_draft_preview_approval_and_send(self):
        """Scenario B: Draft email -> External action preview -> Approval -> Send -> Verified delivery."""
        ctx = IntegrationContext(task_id="task_email_scen")
        draft = await integration_router.route_and_execute(
            "email",
            "draft_message",
            ctx,
            to="partner@acme.com",
            subject="Strategic Partnership",
        )
        assert draft.status == "SUCCESS"

        # Generate action preview
        preview = action_approval_manager.create_preview(
            action_type="send_email",
            provider="EmailGateway",
            target_resource="partner@acme.com",
            parameters={"draft_id": draft.data["draft_id"]},
            requires_approval=True,
        )
        assert preview.approval_state == ApprovalState.PENDING

        # User approves action
        action_approval_manager.approve_action(preview.id)

        # Send email
        sent = await integration_router.route_and_execute(
            "email",
            "send_message",
            ctx,
            to="partner@acme.com",
            subject="Strategic Partnership",
        )
        assert sent.status == "SUCCESS"
        assert sent.data["verified_delivery"] is True

    @pytest.mark.asyncio
    async def test_scenario_c_calendar_scheduling(self):
        """Scenario C: Find free time -> Create event -> Verify."""
        ctx = IntegrationContext(task_id="task_cal_scen")
        slots = await integration_router.route_and_execute("calendar", "find_free_time", ctx)
        assert slots.status == "SUCCESS"

        event = await integration_router.route_and_execute(
            "calendar",
            "create_event",
            ctx,
            title="Q3 Review",
            start_time=slots.data["available_slots"][0],
        )
        assert event.status == "SUCCESS"
        assert event.reconciliation_state["calendar_synced"] is True

    @pytest.mark.asyncio
    async def test_scenario_d_deployment_staging_prod_and_rollback(self):
        """Scenario D: Staging deploy -> Health check -> Production gate -> Rollback."""
        dep = deployment_pipeline.create_deployment("order-api", "v1.2.0", previous_version="v1.1.0")

        # Staging validation
        assert deployment_pipeline.run_staging_validation(dep.deployment_id) is True

        # Production promotion with approval
        promoted, msg = deployment_pipeline.promote_to_production(dep.deployment_id, approved=True)
        assert promoted is True
        assert "Successfully" in msg

        # Rollback
        rolled_back, rb_msg = deployment_pipeline.rollback(dep.deployment_id)
        assert rolled_back is True
        assert "v1.1.0" in rb_msg

    @pytest.mark.asyncio
    async def test_scenario_e_monitoring_incident_response(self):
        """Scenario E: Alert -> Incident -> Log collection -> Diagnosis -> Remediation -> Recovery."""
        inc = incident_workflow.trigger_incident(
            title="500 Errors in Payment API",
            severity="HIGH",
            alert_source="ObservabilityGateway",
        )

        assert inc.status == "TRIGGERED"

        # Collect logs and diagnose
        incident_workflow.collect_logs_and_diagnose(
            inc.incident_id,
            logs=["Timeout connecting to upstream bank gateway"],
            hypothesis="Connection pool exhaustion",
        )

        # Propose remediation
        incident_workflow.propose_remediation(inc.incident_id, "Increase connection pool size to 50")

        # Apply remediation
        resolved, _ = incident_workflow.apply_remediation_and_verify(inc.incident_id, approved=True)
        assert resolved is True
        assert inc.recovery_verified is True
        assert inc.status == "RESOLVED"

    @pytest.mark.asyncio
    async def test_scenario_f_remote_execution_lifecycle(self):
        """Scenario F: Remote host authentication -> Execute -> Collect result -> Disconnect."""
        ctx = IntegrationContext(task_id="task_remote_scen")
        connected = await integration_router.route_and_execute("remote_exec", "connect_host", ctx)
        assert connected.status == "SUCCESS"

        exec_res = await integration_router.route_and_execute("remote_exec", "execute_command", ctx, command="df -h")
        assert exec_res.status == "SUCCESS"
        assert exec_res.data["exit_code"] == 0

        disconnected = await integration_router.route_and_execute("remote_exec", "disconnect_host", ctx)
        assert disconnected.status == "SUCCESS"
