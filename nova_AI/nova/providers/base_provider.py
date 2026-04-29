from __future__ import annotations

from abc import ABC, abstractmethod

from nova.core.result_types import ModelRequest, ModelResponse


class BaseProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError