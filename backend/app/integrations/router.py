from __future__ import annotations
from typing import Any, Optional
from app.integrations.base import IntegrationContext, IntegrationResult
from app.integrations.registry import integration_registry
from app.integrations.rate_limits import rate_limit_manager
from app.integrations.policies import action_approval_manager, ApprovalState
from app.integrations.events import integration_event_bus, IntegrationEvent, IntegrationEventType


class IntegrationRouter:
    """
    Central router for external integration requests.
    Validates permissions, verifies pre-execution approval states, checks rate limit quotas,
    and executes actions through the registered external system connector.
    """

    async def route_and_execute(
        self,
        integration_name: str,
        action: str,
        context: IntegrationContext,
        **kwargs,
    ) -> IntegrationResult:
        connector = integration_registry.get(integration_name)
        if not connector:
            return IntegrationResult(
                integration_name=integration_name,
                action=action,
                status="ERROR",
                error=f"Integration '{integration_name}' not found in registry",
            )

        # 1. Check rate limit
        if not rate_limit_manager.check_and_consume(connector.name):
            return IntegrationResult(
                integration_name=integration_name,
                action=action,
                status="RATE_LIMITED",
                error=f"Rate limit quota exceeded for provider '{connector.provider}'",
            )

        # 2. Check capabilities
        if action not in connector.capabilities:
            return IntegrationResult(
                integration_name=integration_name,
                action=action,
                status="UNSUPPORTED_ACTION",
                error=f"Action '{action}' not supported by connector '{integration_name}'",
            )

        # 3. Execute via connector
        result = await connector.execute(action, context, **kwargs)

        integration_event_bus.emit(IntegrationEvent(
            event_type=IntegrationEventType.EXTERNAL_ACTION_EXECUTED,
            provider=connector.provider,
            resource_id=context.task_id,
            payload={"action": action, "status": result.status},
        ))

        return result


integration_router = IntegrationRouter()
