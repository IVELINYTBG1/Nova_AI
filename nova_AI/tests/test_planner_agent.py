from __future__ import annotations

from nova.agents.planner.planner_agent import PlannerAgent
from nova.core.result_types import ModelRequest, ModelResponse


class FakeRouter:
    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            success=True,
            text="1. First step\n2. Second step\n3. Third step",
            provider_name="fake",
            model_name="fake-model",
            error=None,
        )



def test_planner_agent_returns_steps_list() -> None:
    agent = PlannerAgent(router=FakeRouter())
    result = agent.execute({"goal": "test", "context": "ctx"})

    assert result.success is True
    assert "steps" in result.data
    assert result.data["steps"] == ["1. First step", "2. Second step", "3. Third step"]