from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from nova.core.result_types import ModelRequest, ModelResponse
from nova.providers.base_provider import ChatMessage, ProviderConfigError, ProviderExecutionError, ProviderResult
from nova.providers.registry import ProviderRegistry


@dataclass(slots=True, frozen=True)
class TaskDescription:
    task_type: str
    requires_web: bool = False
    use_fallback_only: bool = False
    meta: dict[str, Any] = field(default_factory=dict)


class ModelRouter:
    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        providers: dict[str, Any] | None = None,
        default_provider: str | None = None,
    ) -> None:
        if registry is not None:
            self._registry = registry
            return

        if not providers or default_provider is None:
            raise ValueError("ModelRouter requires either a ProviderRegistry or providers + default_provider.")
        if default_provider not in providers:
            raise ValueError(f"Default provider '{default_provider}' is not available.")

        built_registry = ProviderRegistry()
        primary = providers[default_provider]
        built_registry.register_primary_llm(primary)
        built_registry.register_fallback_llm(primary)
        self._registry = built_registry

    async def route_chat(
        self,
        task: TaskDescription,
        messages: list[ChatMessage],
    ) -> ProviderResult:
        if task.requires_web:
            # TODO: future hook for web-agent / web research provider flow.
            pass

        if task.use_fallback_only:
            fallback = self._registry.get_fallback_llm()
            return await self._invoke_chat(fallback, messages=messages, meta=task.meta)

        try:
            primary = self._registry.get_primary_llm()
            result = await self._invoke_chat(primary, messages=messages, meta=task.meta)
            if result.success:
                return result
        except (LookupError, ProviderConfigError, ProviderExecutionError):
            pass

        fallback = self._registry.get_fallback_llm()
        return await self._invoke_chat(fallback, messages=messages, meta=task.meta)

    async def route_generate(
        self,
        task: TaskDescription,
        prompt: str,
        system: str | None = None,
    ) -> ProviderResult:
        if task.requires_web:
            # TODO: future hook for web-agent-assisted generation.
            pass

        if task.use_fallback_only:
            fallback = self._registry.get_fallback_llm()
            return await self._invoke_generate(fallback, prompt=prompt, system=system, meta=task.meta)

        try:
            primary = self._registry.get_primary_llm()
            result = await self._invoke_generate(primary, prompt=prompt, system=system, meta=task.meta)
            if result.success:
                return result
        except (LookupError, ProviderConfigError, ProviderExecutionError):
            pass

        fallback = self._registry.get_fallback_llm()
        return await self._invoke_generate(fallback, prompt=prompt, system=system, meta=task.meta)

    def generate(self, request: ModelRequest) -> ModelResponse:
        task = TaskDescription(task_type=request.task_type)
        provider_result = asyncio.run(
            self.route_generate(task=task, prompt=request.user_text, system=request.system_prompt)
        )
        return ModelResponse(
            success=provider_result.success,
            text=provider_result.text,
            provider_name=provider_result.provider_name,
            model_name=provider_result.model_name,
            error=provider_result.error,
        )

    async def _invoke_chat(self, provider: Any, messages: list[ChatMessage], meta: dict[str, Any]) -> ProviderResult:
        if hasattr(provider, "chat"):
            return await provider.chat(messages=messages, meta=meta)

        if hasattr(provider, "generate"):
            prompt = "\n".join(message["content"] for message in messages if message["role"] != "system")
            system = "\n\n".join(message["content"] for message in messages if message["role"] == "system") or None
            return await self._invoke_generate(provider, prompt=prompt, system=system, meta=meta)

        raise ProviderExecutionError(f"Provider '{getattr(provider, 'name', 'unknown')}' does not support chat.")

    async def _invoke_generate(
        self,
        provider: Any,
        prompt: str,
        system: str | None,
        meta: dict[str, Any],
    ) -> ProviderResult:
        generate_method = getattr(provider, "generate", None)
        if generate_method is None:
            raise ProviderExecutionError(f"Provider '{getattr(provider, 'name', 'unknown')}' does not support generate.")

        if asyncio.iscoroutinefunction(generate_method):
            return await generate_method(prompt=prompt, system=system, meta=meta)

        request = ModelRequest(
            task_type=meta.get("task_type", "chat") if meta else "chat",
            system_prompt=system or "",
            user_text=prompt,
            context=(meta or {}).get("context", ""),
        )
        response = generate_method(request)
        return ProviderResult(
            success=response.success,
            text=response.text,
            provider_name=response.provider_name,
            model_name=response.model_name,
            error=response.error,
            raw=None,
            usage=None,
        )