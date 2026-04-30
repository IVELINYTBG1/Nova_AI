from __future__ import annotations

from nova.core.model_router import ModelRouter
from nova.core.result_types import ModelRequest
from nova.providers.base_provider import ProviderExecutionError, ProviderResult
from nova.providers.registry import ProviderRegistry


class FailingPrimaryProvider:
    name = "primary"
    model = "primary-model"

    async def chat(self, messages, meta=None) -> ProviderResult:
        raise ProviderExecutionError("primary failed")

    async def generate(self, prompt: str, system: str | None = None, meta=None) -> ProviderResult:
        raise ProviderExecutionError("primary failed")


class WorkingFallbackProvider:
    name = "fallback"
    model = "fallback-model"

    async def chat(self, messages, meta=None) -> ProviderResult:
        return ProviderResult(
            success=True,
            text="fallback response",
            provider_name=self.name,
            model_name=self.model,
            error=None,
        )

    async def generate(self, prompt: str, system: str | None = None, meta=None) -> ProviderResult:
        return ProviderResult(
            success=True,
            text="fallback generated",
            provider_name=self.name,
            model_name=self.model,
            error=None,
        )


def test_model_router_falls_back_when_primary_raises_execution_error() -> None:
    registry = ProviderRegistry()
    registry.register_primary_llm(FailingPrimaryProvider())
    registry.register_fallback_llm(WorkingFallbackProvider())
    router = ModelRouter(registry=registry)

    result = router.generate(
        ModelRequest(
            task_type="chat",
            system_prompt="",
            user_text="hello",
            context="",
        )
    )

    assert result.success is True
    assert result.provider_name == "fallback"
    assert result.text == "fallback generated"