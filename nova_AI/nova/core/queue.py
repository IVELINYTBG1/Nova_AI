from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from nova.core.execution_types import ExecutionRecord, ExecutionRequest, TaskState


class TaskQueue:
    def __init__(self, executor: Callable[[ExecutionRequest], ExecutionRecord]) -> None:
        self._executor = executor
        self._tasks: dict[str, TaskState] = {}

    def enqueue(self, request: ExecutionRequest) -> str:
        task_id = str(uuid4())
        self._tasks[task_id] = TaskState.create(task_id=task_id, request=request)
        return task_id

    def run_next(self, task_id: str) -> ExecutionRecord:
        task = self._tasks[task_id]
        task.status = "running"
        task.updated_at = datetime.now(timezone.utc).astimezone()
        record = self._executor(task.request)
        task.result = record.result
        task.status = "completed" if record.success else "failed"
        task.updated_at = datetime.now(timezone.utc).astimezone()
        return record

    def get(self, task_id: str) -> TaskState:
        return self._tasks[task_id]