import pytest
from app.platform.task_queue import task_queue, TaskPriority, TaskStatus
from app.platform.worker_pool import worker_pool, WorkerPoolType
from app.platform.distributed_lock import lock_manager
from app.platform.tracing import tracer
from app.platform.tool_trust import tool_trust_manager, ToolTrustTier
from app.platform.resource_limiter import resource_limiter
from app.platform.cost_governance import cost_governance
from app.platform.database import platform_database
from app.platform.caching import platform_cache
from app.platform.telemetry import telemetry
from app.platform.sla_manager import sla_manager


class TestEndToEndProduction:
    def test_complete_production_platform_lifecycle(self):
        # 1. Enqueue task
        q_item = task_queue.enqueue(
            task_id="prod_task_881",
            payload={"goal": "Analyze dataset and publish report"},
            priority=TaskPriority.HIGH,
            pool_type="GENERAL_WORKERS",
        )
        assert q_item.status == TaskStatus.PENDING

        # 2. Worker leases task
        worker = worker_pool.register_worker(WorkerPoolType.GENERAL_WORKERS)
        leased_item = task_queue.lease_next_task(worker.worker_id, pool_type="GENERAL_WORKERS")
        assert leased_item is not None
        assert leased_item.task_id == "prod_task_881"
        worker_pool.assign_task_to_worker(worker.worker_id, leased_item.task_id)

        # 3. Distributed lock acquired
        lock_acquired = lock_manager.acquire_lock(f"task_lock_{leased_item.task_id}", worker.worker_id)
        assert lock_acquired is True

        # 4. Start distributed trace
        trace_id = tracer.start_trace(leased_item.task_id)
        root_span = tracer.start_span(trace_id, name="ProductionWorker.Execute")

        # 5. Check tool trust
        tool_trust_manager.register_tool_trust("data_analyzer", ToolTrustTier.OFFICIAL)
        assert tool_trust_manager.is_tool_allowed("data_analyzer", is_production=True) is True

        # 6. Enforce resource limits
        resource_limiter.initialize_task(leased_item.task_id, max_llm_tokens=50000, max_tool_calls=20)
        within_limits, _ = resource_limiter.record_usage(leased_item.task_id, tokens=1200, tool_calls=3)
        assert within_limits is True

        # 7. Record cost expense
        cost_ok, _, cost_rec = cost_governance.record_expense(
            leased_item.task_id,
            user_id="user_prod_corp",
            llm_tokens=1200,
            tool_calls=3,
        )
        assert cost_ok is True
        assert cost_rec.total_cost_usd > 0

        # 8. Store state in authoritative database
        db_entity = platform_database.save_entity(
            entity_type="task_state",
            data={"status": "COMPLETED", "summary": "Dataset analysis complete"},
            tenant_id="tenant_corp",
            user_id="user_prod_corp",
            custom_id=f"state_{leased_item.task_id}",
        )
        assert db_entity.version == 1

        # 9. Cache result
        platform_cache.set(f"task_cache_{leased_item.task_id}", {"report_id": "rep_991"})
        assert platform_cache.get(f"task_cache_{leased_item.task_id}") == {"report_id": "rep_991"}

        # 10. End trace span and complete task
        tracer.end_span(root_span, status="OK")
        task_queue.acknowledge_complete(leased_item.id, worker.worker_id)
        worker_pool.complete_worker_task(worker.worker_id, success=True)
        lock_manager.release_lock(f"task_lock_{leased_item.task_id}", worker.worker_id)

        # 11. Record telemetry and verify SLA
        telemetry.record_task_outcome(success=True, duration_ms=root_span.duration_ms or 50)
        sla_report = sla_manager.compute_slo_status(availability_pct=99.95, verification_accuracy_pct=99.8)
        assert sla_report["overall_compliant"] is True
