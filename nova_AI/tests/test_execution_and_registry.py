from __future__ import annotations

from typing import Any

from nova.agents.base_agent import BaseAgent
from nova.core.execution import ExecutionService
from nova.core.execution_types import ExecutionRequest
from nova.core.registry import AgentRegistry
from nova.core.result_types import AgentMetadata, AgentResult


class DummyAgent(BaseAgent):
    metadata = AgentMetadata(
        name="dummy",
        version="0.1.0",
        description="Dummy test agent.",
        capabilities=["dummy.run"],
        input_schema="{'value': str}",
        output_schema="{'echo': str}",
        safety_level="safe",
        undoable=False,
    )

    def execute(self, input_data: dict[str, Any]) -> AgentResult:
        try:
            return AgentResult(success=True, data={"echo": input_data.get("value", "")})
        except Exception as exc:
            return self._safe_failure(exc)



def test_execution_service_runs_registered_agent_without_leaking_exceptions() -> None:
    registry = AgentRegistry()
    registry.register(DummyAgent())
    service = ExecutionService(registry)
    request = ExecutionRequest(
        agent_name="dummy",
        input_data={"value": "hello"},
        reason="test",
        requested_by="pytest",
    )

    record = service.execute_agent(request)

    assert record.success is True
    assert record.result.success is True
    assert record.result.data == {"echo": "hello"}