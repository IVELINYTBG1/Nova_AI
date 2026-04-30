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
from nova.providers.anthropic_provider import AnthropicProvider
from nova.providers.base_provider import ProviderConfigError
from nova.providers.fish_speech_api_provider import FishSpeechApiProvider
from nova.providers.groq_gpt_turbo_stt_provider import GroqGptTurboSttProvider
from nova.providers.groq_llama_scout_vision_provider import GroqLlamaScoutVisionProvider
from nova.providers.groq_oss_120b_provider import GroqOss120BProvider
from nova.providers.registry import ProviderRegistry
from nova.providers.stub_provider import StubProvider


@dataclass
class NovaApp:
    orchestrator: Orchestrator
    io_membrane: IOMembrane
    registry: AgentRegistry
    execution_service: ExecutionService
    queue: TaskQueue
    model_router: ModelRouter
    provider_registry: ProviderRegistry


def build_nova(settings: Settings) -> NovaApp:
    memory = SimpleMemoryStore(settings.memory_file)
    provider_registry = ProviderRegistry()

    try:
        provider_registry.register_primary_llm(AnthropicProvider())
    except ProviderConfigError:
        pass

    try:
        provider_registry.register_fallback_llm(GroqOss120BProvider())
    except ProviderConfigError:
        pass

    try:
        provider_registry.register_stt(GroqGptTurboSttProvider())
    except ProviderConfigError:
        pass

    try:
        provider_registry.register_tts(FishSpeechApiProvider())
    except ProviderConfigError:
        pass

    try:
        provider_registry.register_vision(GroqLlamaScoutVisionProvider())
    except ProviderConfigError:
        pass

    provider_registry.ensure_llm_pairing()

    if not provider_registry.has_primary_llm() and not provider_registry.has_fallback_llm():
        stub = StubProvider()
        provider_registry.register_primary_llm(stub)
        provider_registry.register_fallback_llm(stub)

    model_router = ModelRouter(registry=provider_registry)
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
        model_router=model_router,
        provider_registry=provider_registry,
    )