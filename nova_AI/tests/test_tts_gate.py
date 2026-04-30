from __future__ import annotations

import asyncio

from nova.core.tts_gate import TtsExhaustionGuard, TtsGate, TtsInterruptHandler
from nova.providers.base_provider import ProviderExecutionError, ProviderResult


class FakeRouter:
    def __init__(self, text: str) -> None:
        self._text = text

    async def route_generate(self, prompt: str, system: str | None = None):
        return ProviderResult(success=True, text=self._text, provider_name="fake", model_name="fake")


def test_tts_gate_mute_on_quiet_context() -> None:
    async def run_test() -> None:
        gate = TtsGate(FakeRouter('{"quiet_mode": true, "reason": "Sleeping nearby."}'))
        should_speak = await gate.should_speak("keep it down", ["someone is sleeping"])
        assert should_speak is False
        assert gate.is_muted() is True

    asyncio.run(run_test())


def test_tts_gate_unmute_on_explicit_lift() -> None:
    async def run_test() -> None:
        gate = TtsGate(FakeRouter('{"quiet_mode": false, "reason": "Quiet mode lifted."}'))
        gate.enable()
        should_speak = await gate.should_speak("you can speak now", ["be quiet earlier"])
        assert should_speak is True
        assert gate.is_muted() is False

    asyncio.run(run_test())


def test_tts_interrupt_fires_on_user_speech() -> None:
    handler = TtsInterruptHandler()
    handler.signal_user_speaking()
    assert handler.is_interrupted() is True


def test_tts_interrupt_ignores_other_speaker() -> None:
    handler = TtsInterruptHandler()
    handler.signal_other_speaking()
    assert handler.is_interrupted() is False


def test_tts_exhaustion_guard_notifies_once() -> None:
    guard = TtsExhaustionGuard()
    handled = guard.handle_tts_error(ProviderExecutionError("Fish Speech HTTP error: 429 quota exceeded"))
    assert handled is True
    assert guard.has_notified() is True


def test_tts_exhaustion_guard_suppresses_second_notification() -> None:
    guard = TtsExhaustionGuard()
    first = guard.handle_tts_error(ProviderExecutionError("402 insufficient credit"))
    second = guard.handle_tts_error(ProviderExecutionError("402 insufficient credit"))
    assert first is True
    assert second is True
    assert guard.has_notified() is True