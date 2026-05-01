from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from nova.agents.planner.planner_agent import PlannerAgent
from nova.config.settings import Settings
from nova.core.camera_gate import CameraGate
from nova.core.camera_service import CameraService
from nova.core.execution import ExecutionService
from nova.core.honesty import HonestyValidator
from nova.core.identity_gate import IdentityDecision, IdentityGate, IdentityVerificationError
from nova.core.iomembrane import IOMembrane
from nova.core.language.language_layer import LanguageLayer
from nova.core.language.polish import LanguagePolisher
from nova.core.memory.simple_memory import SimpleMemoryStore
from nova.core.model_router import ModelRouter
from nova.core.nova_state import NovaInternalState
from nova.core.orchestrator import Orchestrator
from nova.core.presence_loop import PresenceLoop
from nova.core.queue import TaskQueue
from nova.core.registry import AgentRegistry
from nova.core.result_types import InputTurn
from nova.core.tts_gate import TtsExhaustionGuard, TtsGate, TtsInterruptHandler
from nova.providers.base_provider import ProviderConfigError
from nova.providers.fish_speech_api_provider import FishSpeechApiProvider
from nova.providers.groq_gpt_turbo_stt_provider import GroqGptTurboSttProvider
from nova.providers.groq_llama_scout_vision_provider import GroqLlamaScoutVisionProvider
from nova.providers.groq_oss_120b_provider import GroqOss120BProvider
from nova.providers.registry import ProviderRegistry
from nova.providers.stub_provider import StubProvider

try:
    from nova.core.memory.vector_memory import VectorMemoryStore
except Exception:
    VectorMemoryStore = None  # type: ignore[assignment]


RECOGNITION_INTENTS = {
    "can you recognize me",
    "do you recognize me",
    "do you know who i am",
    "is this me",
}


@dataclass
class NovaApp:
    orchestrator: Orchestrator
    io_membrane: IOMembrane
    registry: AgentRegistry
    execution_service: ExecutionService
    queue: TaskQueue
    model_router: ModelRouter
    provider_registry: ProviderRegistry
    camera_service: CameraService
    identity_gate: IdentityGate | None = None
    camera_gate: CameraGate | None = None
    tts_gate: TtsGate | None = None
    tts_interrupt_handler: TtsInterruptHandler | None = None
    tts_exhaustion_guard: TtsExhaustionGuard | None = None
    vector_memory: object | None = None
    nova_state: NovaInternalState | None = None
    presence_loop: PresenceLoop | None = None
    presence_task: asyncio.Task[None] | None = None
    last_live_frame_received: bool = False
    last_identity_status: str | None = None
    recent_user_turns: list[str] = field(default_factory=list)

    def handle_text(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return "Say something real and I’ll respond."

        lowered = cleaned.lower()
        if self._is_recognition_intent(lowered):
            answer = self._answer_identity_question()
            self._remember_turn(cleaned, answer)
            self._update_nova_state(cleaned)
            return answer

        if "can you see me" in lowered or "do you see me" in lowered:
            if not self.camera_service.is_available():
                return "The camera is not available on this runtime. Vision is loaded, but there’s no live camera feed coming through."
            frame = self.camera_service.capture_frame_bytes()
            if frame:
                self.last_live_frame_received = True
                return "Yes. I can take a live frame from the local camera right now."
            return "Vision is loaded, but I didn’t get a live frame from the camera yet."

        remember_prefix = "remember that "
        if lowered.startswith(remember_prefix):
            answer = self._handle_remember_fact(cleaned)
            self._remember_turn(cleaned, answer)
            self._update_nova_state(cleaned)
            return answer

        effective_text = self._expand_follow_up(cleaned)
        if lowered == "what do you remember":
            answer = self._answer_memory_question(effective_text)
            self._remember_turn(cleaned, answer)
            self._update_nova_state(cleaned)
            return answer

        language = self.io_membrane._language_layer.detect(effective_text)
        turn = InputTurn(
            text=effective_text,
            raw_text=text,
            language=language,
            user_id=self.io_membrane._settings.user_id,
            session_id=self.io_membrane._settings.session_id,
        )
        response = self.orchestrator.handle_turn(turn)
        self._remember_turn(cleaned, response.text)
        self._update_nova_state(cleaned)
        return response.text if response.text else "I couldn’t produce a coherent reply for that one."

    def describe_camera_status(self) -> str:
        return "Camera: ready" if self.camera_service.is_available() else "Camera: unavailable"

    def memory_stats_line(self) -> str:
        if self.vector_memory is None or not hasattr(self.vector_memory, "stats"):
            return "Memory: unavailable"
        stats = self.vector_memory.stats()
        return f"Memory: {stats['conversation_turns']} conversation turns, {stats['stored_facts']} stored facts"

    def start_presence_loop(self) -> None:
        if self.presence_loop is None:
            return
        if self.presence_task is not None and not self.presence_task.done():
            return
        self.presence_task = asyncio.create_task(self.presence_loop.run())

    def stop_presence_loop(self) -> None:
        if self.presence_loop is not None:
            self.presence_loop.stop()

    def _remember_turn(self, user_text: str, nova_text: str) -> None:
        self.recent_user_turns.append(user_text)
        self.recent_user_turns = self.recent_user_turns[-6:]
        if self.vector_memory is not None:
            self.vector_memory.store_turn(role="user", content=user_text)
            self.vector_memory.store_turn(role="nova", content=nova_text)

    def _handle_remember_fact(self, cleaned: str) -> str:
        if self.vector_memory is None or not hasattr(self.vector_memory, "store_fact"):
            return "Long-term memory is not available in this runtime."

        fact = cleaned[len("remember that "):].strip()
        if not fact:
            return "Tell me what you want me to remember."

        self.vector_memory.store_fact(fact)
        return "Got it. I’ll remember that."

    def _is_recognition_intent(self, lowered: str) -> bool:
        normalized = " ".join(lowered.split())
        return normalized in RECOGNITION_INTENTS

    def _expand_follow_up(self, cleaned: str) -> str:
        lowered = cleaned.lower().strip()
        if len(lowered.split()) > 3:
            return cleaned
        if not lowered.startswith(("do you", "did you", "can you", "could you", "what about", "and ")):
            return cleaned
        if not self.recent_user_turns:
            return cleaned
        return f"Previous user context: {self.recent_user_turns[-1]}\nCurrent follow-up: {cleaned}"

    def _answer_memory_question(self, query: str) -> str:
        if self.vector_memory is None:
            return "Long-term vector memory is not available in this runtime."

        try:
            facts = self.vector_memory.search_facts(query, n=3) if hasattr(self.vector_memory, "search_facts") else []
            memories = self.vector_memory.recall(query, n=3)
        except Exception as exc:
            return f"Long-term vector memory is configured but unavailable right now: {exc}"

        remembered_bits: list[str] = []
        for item in facts:
            content = str(item.get("content", "")).strip()
            if content:
                remembered_bits.append(content)
        for item in memories:
            content = str(item.get("content", "")).strip()
            if content:
                remembered_bits.append(content)

        if not remembered_bits:
            return "I don’t have anything relevant stored yet."

        if len(remembered_bits) == 1:
            return f"I remember that {remembered_bits[0]}"

        joined = "; ".join(remembered_bits[:3])
        return f"Here’s what stands out to me: {joined}"

    def _answer_identity_question(self) -> str:
        if self.camera_gate is None or self.identity_gate is None:
            return "Identity verification is not available in this runtime."
        if not self.camera_service.is_available():
            return "The camera is unavailable, so I can’t verify your identity right now."
        if not self.camera_gate.is_enrolled():
            return "I don’t have an enrolled reference image yet, so I can’t verify whether this is you."
        try:
            frame = self.camera_service.capture_frame_bytes()
        except Exception as exc:
            return f"The camera is unavailable, so I can’t verify your identity right now: {exc}"
        if not frame:
            return "I couldn’t get a live camera frame, so verification could not be completed."
        try:
            decision = self._run_identity_verification(frame)
        except IdentityVerificationError as exc:
            return f"Identity verification could not be completed: {exc}"
        except Exception as exc:
            return f"Identity verification could not be completed: {exc}"

        self.last_identity_status = decision.reason
        if decision.same_person and not decision.spoof_suspected:
            confidence = f" Confidence: {decision.confidence:.2f}." if decision.confidence is not None else ""
            return f"Yes. I recognize you from the enrolled reference image.{confidence} Reason: {decision.reason}"
        return f"Identity verification could not be completed. Reason: {decision.reason}"

    def _run_identity_verification(self, frame: bytes) -> IdentityDecision:
        import time

        decision = asyncio.run(self.identity_gate.verify_candidate(frame))
        if self.camera_gate is not None:
            self.camera_gate._last_verified_ok = bool(decision.same_person and not decision.spoof_suspected)
            self.camera_gate._last_verified_at = time.monotonic()
        return decision

    def _update_nova_state(self, cleaned: str) -> None:
        if self.nova_state is not None:
            self.nova_state.update_on_interaction(len(cleaned))


def build_nova(settings: Settings) -> NovaApp:
    memory = SimpleMemoryStore(settings.memory_file)
    vector_memory = None
    if VectorMemoryStore is not None:
        try:
            vector_memory = VectorMemoryStore()
        except Exception:
            vector_memory = None

    provider_registry = ProviderRegistry()

    try:
        provider_registry.register_primary_llm(GroqOss120BProvider())
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
    nova_state = NovaInternalState()
    orchestrator = Orchestrator(
        memory=memory,
        model_router=model_router,
        honesty=honesty,
        polisher=polisher,
        execution_service=execution_service,
        vector_memory=vector_memory,
        nova_state=nova_state,
    )
    camera_service = CameraService(camera_index=settings.camera_index)
    identity_gate = IdentityGate(provider_registry.get_vision()) if provider_registry.has_vision() else None
    camera_gate = CameraGate(identity_gate=identity_gate, camera_service=camera_service, debounce_delay_seconds=3.0)
    tts_gate = TtsGate(model_router=model_router)
    tts_interrupt_handler = TtsInterruptHandler()
    tts_exhaustion_guard = TtsExhaustionGuard()
    presence_loop = PresenceLoop(state=nova_state, output_callback=lambda message: print(f"Nova: {message}"))

    return NovaApp(
        orchestrator=orchestrator,
        io_membrane=io_membrane,
        registry=registry,
        execution_service=execution_service,
        queue=queue,
        model_router=model_router,
        provider_registry=provider_registry,
        camera_service=camera_service,
        identity_gate=identity_gate,
        camera_gate=camera_gate,
        tts_gate=tts_gate,
        tts_interrupt_handler=tts_interrupt_handler,
        tts_exhaustion_guard=tts_exhaustion_guard,
        vector_memory=vector_memory,
        nova_state=nova_state,
        presence_loop=presence_loop,
    )