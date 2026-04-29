from __future__ import annotations

from nova.core.result_types import ModelRequest, ModelResponse
from nova.providers.base_provider import BaseProvider


class ModelRouter:
    def __init__(self, providers: dict[str, BaseProvider], default_provider: str) -> None:
        self._providers = providers
        self._default_provider = default_provider

    def generate(self, request: ModelRequest) -> ModelResponse:
        provider = self._providers[self._default_provider]
        return provider.generate(request)