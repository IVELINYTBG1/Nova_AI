from __future__ import annotations

from datetime import datetime, timezone

from nova.bootstrap import build_nova
from nova.config.settings import load_settings
from nova.core.execution import ExecutionService
from nova.core.honesty import HonestyValidator
from nova.core.iomembrane import IOMembrane
from nova.core.language.polish import LanguagePolisher
from nova.core.memory.memory_interface import MemoryStore
from nova.core.model_router import ModelRouter
from nova.core.orchestrator import Orchestrator
from nova.core.personality.system_prompt import build_system_prompt
from nova.core.queue import TaskQueue
from nova.core.registry import AgentRegistry
from nova.core.result_types import InputTurn, MemoryItem, ResponseTurn
from nova.providers.stub_provider import StubProvider


class FakeMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self._items: list[MemoryItem] = []

    def store(self, item: MemoryItem) -> None:
        self._items.append(item)

    def search(self, query: str, limit: int = 5) -> list[MemoryItem]:
        return self._items[:limit]

    def list_topics(self) -> list[str]:
        return sorted({item.topic for item in self._items})



def test_build_nova_returns_expected_components() -> None:
    app = build_nova(load_settings())
    assert app.orchestrator is not None
    assert app.io_membrane is not None
    assert app.registry is not None
    assert app.execution_service is not None
    assert app.queue is not None
    assert isinstance(app.orchestrator, Orchestrator)
    assert isinstance(app.io_membrane, IOMembrane)
    assert isinstance(app.registry, AgentRegistry)
    assert isinstance(app.execution_service, ExecutionService)
    assert isinstance(app.queue, TaskQueue)



def test_build_system_prompt_includes_time_context_section() -> None:
    prompt = build_system_prompt(
        {
            "date": "2026-04-29",
            "time": "21:00",
            "weekday": "Wednesday",
            "part_of_day": "night",
        }
    )
    assert "CURRENT TIME CONTEXT:" in prompt
    assert "Local date: 2026-04-29" in prompt
    assert "Part of day: night" in prompt



def test_orchestrator_handle_turn_returns_direct_success_response() -> None:
    memory = FakeMemoryStore()
    memory.store(MemoryItem.create(topic="project", content="Nova is under active rebuild.", tags=["nova"], source="test"))
    provider = StubProvider()
    router = ModelRouter(providers={provider.name: provider}, default_provider=provider.name)
    execution_service = ExecutionService(AgentRegistry())
    orchestrator = Orchestrator(
        memory=memory,
        model_router=router,
        honesty=HonestyValidator(),
        polisher=LanguagePolisher(),
        execution_service=execution_service,
    )
    turn = InputTurn(
        text="Hello Nova",
        raw_text="Hello Nova",
        language="en",
        user_id="boss",
        session_id="test-session",
    )

    response = orchestrator.handle_turn(turn)

    assert isinstance(response, ResponseTurn)
    assert response.success is True
    assert response.source == "direct"
    assert response.text.strip() != ""



def test_orchestrator_handle_turn_uses_planner_agent_path() -> None:
    app = build_nova(load_settings())
    turn = InputTurn(
        text="Plan steps to rebuild Nova in clear phases.",
        raw_text="Plan steps to rebuild Nova in clear phases.",
        language="en",
        user_id="boss",
        session_id="test-session",
    )

    response = app.orchestrator.handle_turn(turn)

    assert response.success is True
    assert response.source == "agent:planner"
    assert "1." in response.text or "1)" in response.text



def test_orchestrator_stores_memory_for_remember_style_input() -> None:
    memory = FakeMemoryStore()
    provider = StubProvider()
    router = ModelRouter(providers={provider.name: provider}, default_provider=provider.name)
    execution_service = ExecutionService(AgentRegistry())
    orchestrator = Orchestrator(
        memory=memory,
        model_router=router,
        honesty=HonestyValidator(),
        polisher=LanguagePolisher(),
        execution_service=execution_service,
    )
    turn = InputTurn(
        text="Remember that my project is Nova rebuild.",
        raw_text="Remember that my project is Nova rebuild.",
        language="en",
        user_id="boss",
        session_id="test-session",
    )

    orchestrator.handle_turn(turn)

    assert len(memory._items) == 1
    assert memory._items[0].topic == "user_context"
    assert memory._items[0].source == "conversation"
    assert memory._items[0].content == turn.text



def test_orchestrator_does_not_store_memory_for_simple_greeting() -> None:
    memory = FakeMemoryStore()
    provider = StubProvider()
    router = ModelRouter(providers={provider.name: provider}, default_provider=provider.name)
    execution_service = ExecutionService(AgentRegistry())
    orchestrator = Orchestrator(
        memory=memory,
        model_router=router,
        honesty=HonestyValidator(),
        polisher=LanguagePolisher(),
        execution_service=execution_service,
    )
    turn = InputTurn(
        text="Hello Nova",
        raw_text="Hello Nova",
        language="en",
        user_id="boss",
        session_id="test-session",
    )

    orchestrator.handle_turn(turn)

    assert len(memory._items) == 0



def test_orchestrator_builds_memory_context_with_relative_time_phrase() -> None:
    memory = FakeMemoryStore()
    item = MemoryItem.create(
        topic="project",
        content="Nova is under active rebuild.",
        tags=["nova"],
        source="test",
    )
    old_item = MemoryItem(
        id=item.id,
        topic=item.topic,
        content=item.content,
        tags=item.tags,
        source=item.source,
        created_at=datetime(2026, 4, 27, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 27, 12, 0, tzinfo=timezone.utc),
    )
    provider = StubProvider()
    router = ModelRouter(providers={provider.name: provider}, default_provider=provider.name)
    orchestrator = Orchestrator(
        memory=memory,
        model_router=router,
        honesty=HonestyValidator(),
        polisher=LanguagePolisher(),
        execution_service=ExecutionService(AgentRegistry()),
    )

    context = orchestrator._build_memory_context([old_item], datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc))

    assert "stored about 2 days ago" in context



def test_orchestrator_maybe_prepends_late_hour_acknowledgment() -> None:
    provider = StubProvider()
    router = ModelRouter(providers={provider.name: provider}, default_provider=provider.name)
    orchestrator = Orchestrator(
        memory=FakeMemoryStore(),
        model_router=router,
        honesty=HonestyValidator(),
        polisher=LanguagePolisher(),
        execution_service=ExecutionService(AgentRegistry()),
    )
    response = ResponseTurn(
        text="Nova here.",
        language="en",
        success=True,
        source="direct",
        notes=[],
    )

    updated = orchestrator._maybe_prepend_time_acknowledgment(
        response,
        datetime(2026, 4, 29, 23, 30, tzinfo=timezone.utc),
    )

    assert updated.text.startswith("It’s")