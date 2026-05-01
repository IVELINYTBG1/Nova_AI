from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from nova.core.result_types import AgentResult


@dataclass(frozen=True)
class ExecutionRequest:
    agent_name: str
    input_data: dict[str, Any]
    reason: str
    requested_by: str
    task_id: str | None = None


@dataclass(frozen=True)
class ExecutionRecord:
    execution_id: str
    agent_name: str
    success: bool
    result: AgentResult
    started_at: datetime
    finished_at: datetime
    task_id: str | None = None


@dataclass(frozen=True)
class MemoryProvenance:
    memory_ids: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    latest_user_override: bool = True


@dataclass(frozen=True)
class HonestyFacts:
    agent_result: AgentResult | None
    task_state: str | None
    undo_state: str | None
    memory_provenance: MemoryProvenance
    executed: bool
    queued: bool


@dataclass
class TaskState:
    task_id: str
    status: str
    request: ExecutionRequest
    created_at: datetime
    updated_at: datetime
    result: AgentResult | None = None

    @classmethod
    def create(cls, task_id: str, request: ExecutionRequest) -> "TaskState":
        now = datetime.now(timezone.utc).astimezone()
        return cls(
            task_id=task_id,
            status="pending",
            request=request,
            created_at=now,
            updated_at=now,
        )