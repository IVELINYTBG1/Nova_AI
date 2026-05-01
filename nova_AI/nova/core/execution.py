from __future__ import annotations

"""Orchestrator-owned execution boundary for agent work.

This service is the single runtime path for agent execution and undo execution.
It is owned by Nova core and is intended to be used by the orchestrator and queue.
Agents must never import this module.
"""

from datetime import datetime, timezone
import uuid

from nova.core.execution_types import ExecutionRecord, ExecutionRequest
from nova.core.registry import AgentRegistry
from nova.core.result_types import AgentResult


class ExecutionService:
    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def execute_agent(self, request: ExecutionRequest) -> ExecutionRecord:
        started_at = datetime.now(timezone.utc)
        agent = self._registry.get(request.agent_name)
        if agent is None:
            result = AgentResult(success=False, error=f"Agent '{request.agent_name}' is not registered.")
            finished_at = datetime.now(timezone.utc)
            return ExecutionRecord(
                execution_id=str(uuid.uuid4()),
                agent_name=request.agent_name,
                success=False,
                result=result,
                started_at=started_at,
                finished_at=finished_at,
                task_id=request.task_id,
            )

        result = agent.execute(request.input_data)
        finished_at = datetime.now(timezone.utc)
        return ExecutionRecord(
            execution_id=str(uuid.uuid4()),
            agent_name=request.agent_name,
            success=result.success,
            result=result,
            started_at=started_at,
            finished_at=finished_at,
            task_id=request.task_id,
        )

    def undo_agent(self, agent_name: str, undo_token: str, task_id: str | None = None) -> ExecutionRecord:
        started_at = datetime.now(timezone.utc)
        agent = self._registry.get(agent_name)
        if agent is None:
            result = AgentResult(success=False, error=f"Agent '{agent_name}' is not registered.")
        else:
            result = agent.undo(undo_token)
        finished_at = datetime.now(timezone.utc)
        return ExecutionRecord(
            execution_id=str(uuid.uuid4()),
            agent_name=agent_name,
            success=result.success,
            result=result,
            started_at=started_at,
            finished_at=finished_at,
            task_id=task_id,
        )