from __future__ import annotations

from typing import Any

from nova.providers.base_provider import ProviderResult


class StubProvider:
    name = "stub"
    model = "stub-model"

    async def chat(self, messages: list[dict[str, str]], meta: dict[str, Any] | None = None) -> ProviderResult:
        return ProviderResult(
            success=True,
            text="Stub response.",
            provider_name=self.name,
            model_name=self.model,
            error=None,
            raw=None,
            usage=None,
        )

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ProviderResult:
        return ProviderResult(
            success=True,
            text="Stub response.",
            provider_name=self.name,
            model_name=self.model,
            error=None,
            raw=None,
            usage=None,
        )
