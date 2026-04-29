from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class AgentMetadata:
    name: str
    version: str
    description: str
    capabilities: list[str]
    input_schema: str
    output_schema: str
    safety_level: str
    undoable: bool


@dataclass
class AgentResult:
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    notes: str | None = None
    undo_token: str | None = None


@dataclass(frozen=True)
class ModelRequest:
    task_type: str
    system_prompt: str
    user_text: str
    context: str = ""


@dataclass(frozen=True)
class ModelResponse:
    success: bool
    text: str
    provider_name: str
    model_name: str
    error: str | None = None


@dataclass(frozen=True)
class InputTurn:
    text: str
    raw_text: str
    language: str | None
    user_id: str
    session_id: str


@dataclass(frozen=True)
class ResponseTurn:
    text: str
    language: str
    success: bool
    source: str
    notes: list[str]


@dataclass(frozen=True)
class MemoryItem:
    id: str
    topic: str
    content: str
    tags: list[str]
    source: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        topic: str,
        content: str,
        tags: list[str] | None = None,
        source: str = "conversation",
    ) -> "MemoryItem":
        now = datetime.now(timezone.utc).astimezone()
        return cls(
            id=str(uuid4()),
            topic=topic,
            content=content,
            tags=list(tags or []),
            source=source,
            created_at=now,
            updated_at=now,
        )