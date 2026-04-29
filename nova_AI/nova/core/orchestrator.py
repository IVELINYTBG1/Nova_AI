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


class Orchestrator:
    def __init__(
        self,
        memory: MemoryStore,
        model_router: ModelRouter,
        honesty: HonestyValidator,
        polisher: LanguagePolisher,
        execution_service: ExecutionService,
    ) -> None:
        self._memory = memory
        self._model_router = model_router
        self._honesty = honesty
        self._polisher = polisher
        self._execution = execution_service

    def handle_turn(self, turn: InputTurn) -> ResponseTurn:
        now = datetime.now().astimezone()
        time_context = get_current_time_context(now)
        memories = self._memory.search(turn.text, limit=3)
        context = self._build_memory_context(memories, now)
        lowered = turn.text.lower()

        if any(kw in lowered for kw in ["plan", "steps", "how should i approach"]):
            planning_prompt = (
                f"{build_system_prompt(time_context)}\n"
                "You are a planning specialist. Given a goal and optional context, "
                "return a short numbered list of concrete steps."
            )
            request = ExecutionRequest(
                agent_name="planner",
                input_data={"goal": turn.text, "context": context, "planning_prompt": planning_prompt},
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
                    sources=[item.source for item in memories],
                    latest_user_override=True,
                ),
                executed=True,
                queued=False,
            )
            validated = self._honesty.validate(draft, facts)
            final_response = self._polisher.polish(validated)
            self._store_memory_if_relevant(turn)
            return final_response

        model_request = ModelRequest(
            task_type="chat",
            system_prompt=build_system_prompt(time_context),
            user_text=turn.text,
            context=context,
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
                sources=[item.source for item in memories],
                latest_user_override=True,
            ),
            executed=False,
            queued=False,
        )
        validated = self._honesty.validate(draft, facts)
        final_response = self._polisher.polish(validated)
        final_response = self._maybe_prepend_time_acknowledgment(final_response, now)
        self._store_memory_if_relevant(turn)
        return final_response

    def _build_memory_context(self, memories: list[MemoryItem], now: datetime) -> str:
        parts: list[str] = []
        for item in memories:
            reference_time = item.updated_at or item.created_at
            elapsed = describe_elapsed_time(reference_time, now)
            parts.append(f"{item.content} (stored {elapsed})")
        return " | ".join(parts)

    def _maybe_prepend_time_acknowledgment(self, response: ResponseTurn, now: datetime) -> ResponseTurn:
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
            "remember",
            "my project",
            "i am building",
            "i'm building",
            "i like",
            "i prefer",
            "don't forget",
            "dont forget",
            "my name is",
        ]
        if any(trigger in lowered for trigger in triggers):
            item = MemoryItem.create(
                topic="user_context",
                content=turn.text,
                tags=["user", "context"],
                source="conversation",
            )
            self._memory.store(item)