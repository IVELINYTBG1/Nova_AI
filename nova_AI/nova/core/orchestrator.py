from __future__ import annotations

from datetime import datetime

from nova.core.execution import ExecutionService
from nova.core.execution_types import ExecutionRequest, HonestyFacts, MemoryProvenance
from nova.core.honesty import HonestyValidator
from nova.core.language.polish import LanguagePolisher
from nova.core.memory.memory_interface import MemoryStore
from nova.core.model_router import ModelRouter
from nova.core.personality.system_prompt import build_system_prompt
from nova.core.result_types import InputTurn, MemoryItem, ModelRequest, ResponseTurn
from nova.core.time_context import describe_elapsed_time, get_current_time_context, maybe_time_acknowledgment

_MAX_HISTORY_PAIRS = 10   # 10 user+assistant pairs = 20 messages max


class Orchestrator:
    def __init__(
        self,
        memory: MemoryStore,
        model_router: ModelRouter,
        honesty: HonestyValidator,
        polisher: LanguagePolisher,
        execution_service: ExecutionService,
        vector_memory: object | None = None,
        nova_state: object | None = None,
    ) -> None:
        self._memory = memory
        self._model_router = model_router
        self._honesty = honesty
        self._polisher = polisher
        self._execution = execution_service
        self._vector_memory = vector_memory
        self._nova_state = nova_state
        self._history: list[dict[str, str]] = []   # ← rolling session buffer

    def handle_turn(self, turn: InputTurn) -> ResponseTurn:
        now = datetime.now().astimezone()
        time_context = get_current_time_context(now)
        memories = self._memory.search(turn.text, limit=3)
        context = self._build_memory_context(memories, now)
        vector_context = self._build_vector_memory_context(turn.text)
        merged_context = self._merge_contexts(context, vector_context)
        lowered = turn.text.lower()

        state_context = ""
        if self._nova_state is not None and hasattr(self._nova_state, "to_context_string"):
            state_context = str(self._nova_state.to_context_string()).strip()

        system_prompt = build_system_prompt(time_context)
        if state_context:
            system_prompt = f"{system_prompt}\n\nInternal state:\n{state_context}"

        # Snapshot history BEFORE appending current turn —
        # model_router receives only prior turns, then appends user_text itself.
        prior_history = list(self._history)

        # Record the user turn now so it exists for the next round.
        self._history.append({"role": "user", "content": turn.text})
        self._trim_history()

        if any(kw in lowered for kw in ["plan", "steps", "how should i approach"]):
            planning_prompt = (
                f"{system_prompt}\n"
                "You are a planning specialist. Given a goal and optional context, "
                "return a short numbered list of concrete steps."
            )
            request = ExecutionRequest(
                agent_name="planner",
                input_data={"goal": turn.text, "context": merged_context, "planning_prompt": planning_prompt},
                reason="user-goal-planning",
                requested_by=turn.user_id,
            )
            execution_record = self._execution.execute_agent(request)
            result = execution_record.result
            if result.success:
                lines = ["Here is a possible plan:"]
                for i, step in enumerate(result.data.get("steps", []), start=1):
                    lines.append(f"{i}. {step}")
                draft = ResponseTurn(
                    text="\n".join(lines),
                    language=turn.language or "en",
                    success=True,
                    source="agent:planner",
                    notes=[],
                )
            else:
                draft = ResponseTurn(
                    text=result.error or "Planning failed.",
                    language=turn.language or "en",
                    success=False,
                    source="agent:planner",
                    notes=[],
                )
            facts = HonestyFacts(
                agent_result=result,
                task_state=None,
                undo_state=None,
                memory_provenance=MemoryProvenance(
                    memory_ids=[item.id for item in memories],
                    sources=[item.source for item in memories] + self._vector_memory_sources(vector_context),
                    latest_user_override=True,
                ),
                executed=True,
                queued=False,
            )
            validated = self._honesty.validate(draft, facts)
            final_response = self._polisher.polish(validated)
            if final_response.success and final_response.text:
                self._history.append({"role": "assistant", "content": final_response.text})
                self._trim_history()
            self._store_memory_if_relevant(turn)
            return final_response

        model_request = ModelRequest(
            task_type="chat",
            system_prompt=system_prompt,
            user_text=turn.text,
            context=merged_context,
            history=prior_history,       # ← history now flows through
        )
        model_response = self._model_router.generate(model_request)
        draft = ResponseTurn(
            text=model_response.text if model_response.success else (model_response.error or "Model request failed."),
            language=turn.language or "en",
            success=model_response.success,
            source="direct",
            notes=[],
        )
        facts = HonestyFacts(
            agent_result=None,
            task_state=None,
            undo_state=None,
            memory_provenance=MemoryProvenance(
                memory_ids=[item.id for item in memories],
                sources=[item.source for item in memories] + self._vector_memory_sources(vector_context),
                latest_user_override=True,
            ),
            executed=False,
            queued=False,
        )
        validated = self._honesty.validate(draft, facts)
        final_response = self._polisher.polish(validated)
        final_response = self._maybe_prepend_time_acknowledgment(final_response, now)

        if final_response.success and final_response.text:
            self._history.append({"role": "assistant", "content": final_response.text})
            self._trim_history()

        self._store_memory_if_relevant(turn)
        return final_response

    def _trim_history(self) -> None:
        max_messages = _MAX_HISTORY_PAIRS * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

    def _build_memory_context(self, memories: list[MemoryItem], now: datetime) -> str:
        parts: list[str] = []
        for item in memories:
            reference_time = item.updated_at or item.created_at
            elapsed = describe_elapsed_time(reference_time, now)
            parts.append(f"{item.content} (stored {elapsed})")
        return " | ".join(parts)

    def _build_vector_memory_context(self, query: str) -> str:
        if self._vector_memory is None:
            return ""
        parts: list[str] = []
        if hasattr(self._vector_memory, "search_facts"):
            try:
                facts = self._vector_memory.search_facts(query, n=3)
            except Exception:
                facts = []
            for item in facts:
                content = str(item.get("content", "")).strip()
                if content:
                    parts.append(f"Known fact: {content}")
        if hasattr(self._vector_memory, "recall"):
            try:
                turns = self._vector_memory.recall(query, n=3)
            except Exception:
                turns = []
            for item in turns:
                content = str(item.get("content", "")).strip()
                role = str(item.get("role", "")).strip()
                if content:
                    parts.append(f"Prior {role} turn: {content}" if role else f"Prior turn: {content}")
        return " | ".join(parts)

    def _merge_contexts(self, base_context: str, vector_context: str) -> str:
        if base_context and vector_context:
            return f"{base_context} | {vector_context}"
        return base_context or vector_context or ""

    def _vector_memory_sources(self, vector_context: str) -> list[str]:
        return ["vector_memory"] if vector_context else []

    def _maybe_prepend_time_acknowledgment(self, response: ResponseTurn, now: datetime) -> ResponseTurn:
        # Only on the very first reply of the session — not on every short message.
        if len(self._history) > 2:
            return response
        phrase = maybe_time_acknowledgment(now)
        if (
            phrase
            and response.source == "direct"
            and response.success is True
            and len(response.text) < 160
        ):
            return ResponseTurn(
                text=f"{phrase} {response.text}",
                language=response.language,
                success=response.success,
                source=response.source,
                notes=response.notes,
            )
        return response

    def _store_memory_if_relevant(self, turn: InputTurn) -> None:
        lowered = turn.text.lower()
        triggers = [
            "remember", "my project", "i am building", "i'm building",
            "i like", "i prefer", "don't forget", "dont forget", "my name is",
        ]
        if any(trigger in lowered for trigger in triggers):
            item = MemoryItem.create(
                topic="user_context",
                content=turn.text,
                tags=["user", "context"],
                source="conversation",
            )
            self._memory.store(item)