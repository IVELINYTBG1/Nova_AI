from __future__ import annotations

from dataclasses import dataclass

from nova.agents.planner.planner_agent import PlannerAgent
from nova.config.settings import Settings
from nova.core.execution import ExecutionService
from nova.core.honesty import HonestyValidator
from nova.core.iomembrane import IOMembrane
from nova.core.language.language_layer import LanguageLayer
from nova.core.language.polish import LanguagePolisher
from nova.core.memory.simple_memory import SimpleMemoryStore
from nova.core.model_router import ModelRouter
from nova.core.orchestrator import Orchestrator
from nova.core.queue import TaskQueue
from nova.core.registry import AgentRegistry
from nova.providers.stub_provider import StubProvider


@dataclass
class NovaApp:
    orchestrator: Orchestrator
    io_membrane: IOMembrane
    registry: AgentRegistry
    execution_service: ExecutionService
    queue: TaskQueue



def build_nova(settings: Settings) -> NovaApp:
    memory = SimpleMemoryStore(settings.memory_file)
    provider = StubProvider()
    model_router = ModelRouter(providers={provider.name: provider}, default_provider=settings.default_provider)
    registry = AgentRegistry()
    planner_agent = PlannerAgent(router=model_router)
    registry.register(planner_agent)
    execution_service = ExecutionService(registry)
    queue = TaskQueue(executor=execution_service.execute_agent)
    language_layer = LanguageLayer(default_language=settings.default_language)
    honesty = HonestyValidator()
    polisher = LanguagePolisher()
    io_membrane = IOMembrane(settings=settings, language_layer=language_layer)
    orchestrator = Orchestrator(
        memory=memory,
        model_router=model_router,
        honesty=honesty,
        polisher=polisher,
        execution_service=execution_service,
    )
    return NovaApp(
        orchestrator=orchestrator,
        io_membrane=io_membrane,
        registry=registry,
        execution_service=execution_service,
        queue=queue,
    )