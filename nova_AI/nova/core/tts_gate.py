from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

from nova.providers.base_provider import ProviderExecutionError


@dataclass(slots=True, frozen=True)
class TtsDecision:
    quiet_mode: bool
    reason: str


class TtsGate:
    def __init__(self, model_router) -> None:
        self._model_router = model_router
        self._muted = False

    async def should_speak(self, text: str, recent_context: list[str]) -> bool:
        decision = await self._classify(text=text, recent_context=recent_context)
        if decision.quiet_mode:
            self.enable()
        elif self._is_explicit_lift(text):
            self.disable()
        return not self._muted

    def enable(self) -> None:
        self._muted = True

    def disable(self) -> None:
        self._muted = False

    def is_muted(self) -> bool:
        return self._muted

    async def _classify(self, text: str, recent_context: list[str]) -> TtsDecision:
        system = (
            'You are classifying whether Nova should enter or stay in quiet mode. '
            'Return strict JSON only: {"quiet_mode": true|false, "reason": "..."}. '
            'quiet_mode=true if the user is asking for silence, lower volume, whispering, muting, '
            'or the environment implies noise sensitivity. '
            'quiet_mode=false only if the text does not imply quiet mode, or the user explicitly lifts quiet mode.'
        )
        prompt = (
            f"Current user text: {text}\n"
            f"Recent context: {' | '.join(recent_context) if recent_context else 'none'}\n"
            "Answer with strict JSON only."
        )
        result = await self._model_router.route_generate(prompt=prompt, system=system)
        try:
            payload = json.loads(result.text)
        except json.JSONDecodeError as exc:
            raise ProviderExecutionError(f"TTS quiet-mode classifier returned invalid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise ProviderExecutionError("TTS quiet-mode classifier did not return a JSON object.")

        quiet_mode = payload.get("quiet_mode")
        reason = payload.get("reason")

        if not isinstance(quiet_mode, bool):
            raise ProviderExecutionError("TTS quiet-mode classifier field 'quiet_mode' must be boolean.")
        if not isinstance(reason, str) or not reason.strip():
            raise ProviderExecutionError("TTS quiet-mode classifier field 'reason' must be non-empty string.")

        return TtsDecision(quiet_mode=quiet_mode, reason=reason.strip())

    def _is_explicit_lift(self, text: str) -> bool:
        lowered = text.lower()
        lifts = [
            "you can speak now",
            "unmute",
            "talk normally",
            "speak normally",
            "you can talk now",
            "you can be loud again",
        ]
        return any(phrase in lowered for phrase in lifts)


class TtsInterruptHandler:
    def __init__(self) -> None:
        self._event = asyncio.Event()

    def signal_user_speaking(self) -> None:
        self._event.set()

    def signal_other_speaking(self) -> None:
        return None

    def is_interrupted(self) -> bool:
        return self._event.is_set()

    def reset(self) -> None:
        self._event.clear()


class TtsExhaustionGuard:
    def __init__(self) -> None:
        self._notified = False

    def handle_tts_error(self, error: ProviderExecutionError) -> bool:
        message = str(error).lower()
        exhausted = any(token in message for token in ["402", "429", "quota", "credit", "limit", "insufficient"])
        if exhausted:
            self._notified = True
            return True
        return False

    def has_notified(self) -> bool:
        return self._notified

    def reset(self) -> None:
        self._notified = False