from __future__ import annotations

from nova.core.result_types import ModelRequest, ModelResponse
from nova.providers.base_provider import BaseProvider


class StubProvider(BaseProvider):
    name = "stub"

    def generate(self, request: ModelRequest) -> ModelResponse:
        if request.task_type == "plan":
            return ModelResponse(
                success=True,
                text="1. Clarify the goal\n2. Break the work into phases\n3. Execute one phase at a time",
                provider_name=self.name,
                model_name="stub-planner",
                error=None,
            )
        return ModelResponse(
            success=True,
            text="Understood.",
            provider_name=self.name,
            model_name="stub-chat",
            error=None,
        )