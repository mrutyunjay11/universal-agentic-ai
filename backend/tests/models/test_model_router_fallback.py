import pytest
from app.models.router import ModelRouter
from app.models.registry import ModelRegistry


class TestModelRouterFallback:
    @pytest.mark.asyncio
    async def test_router_flagship_and_hardware_fallback(self):
        registry = ModelRegistry()
        router = ModelRouter(registry=registry)

        # 1. Default Flagship Routing
        provider, model_id = await router.route_reasoning(task_type="CODING", prefer_local=False)
        assert model_id == "Qwen3.8-Max"
        assert provider is not None

        # 2. Local Fallback Routing
        fb_provider, fb_id = await router.route_reasoning(task_type="GENERAL", prefer_local=True)
        assert fb_provider is not None
        assert "qwen" in fb_id.lower()
