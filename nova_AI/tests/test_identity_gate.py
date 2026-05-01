from __future__ import annotations

import asyncio

import pytest

from nova.core.identity_gate import (
    IdentityDecisionSource,
    IdentityGate,
    IdentityVerificationError,
    VerificationDebouncer,
)


class FakeVisionProvider:
    def __init__(self, response: str) -> None:
        self._response = response
        self.calls: list[tuple[bytes, str]] = []

    async def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        self.calls.append((image_bytes, prompt))
        return self._response


class FakeCameraService:
    def __init__(self, frame: bytes | None) -> None:
        self._frame = frame

    def capture_frame_bytes(self) -> bytes | None:
        return self._frame


def test_identity_gate_parses_valid_structured_model_response() -> None:
    async def run_test() -> None:
        provider = FakeVisionProvider(
            '{"same_person": true, "confidence": 0.82, "spoof_suspected": false, "reason": "Facial features look consistent."}'
        )
        gate = IdentityGate(provider, enrolled_reference_image=b"reference")

        decision = await gate.verify_candidate(b"candidate")

        assert decision.same_person is True
        assert decision.confidence == 0.82
        assert decision.spoof_suspected is False
        assert decision.reason == "Facial features look consistent."

    asyncio.run(run_test())


def test_identity_gate_coerces_string_boolean_values() -> None:
    async def run_test() -> None:
        provider = FakeVisionProvider(
            '{"same_person": "true", "confidence": 0.91, "spoof_suspected": "false", "reason": "Looks like the same person."}'
        )
        gate = IdentityGate(provider, enrolled_reference_image=b"reference")

        decision = await gate.verify_candidate(b"candidate")

        assert decision.same_person is True
        assert decision.spoof_suspected is False

    asyncio.run(run_test())


def test_identity_gate_rejects_invalid_string_boolean_value() -> None:
    async def run_test() -> None:
        provider = FakeVisionProvider(
            '{"same_person": "yes", "confidence": 0.82, "spoof_suspected": false, "reason": "unclear"}'
        )
        gate = IdentityGate(provider, enrolled_reference_image=b"reference")

        with pytest.raises(IdentityVerificationError):
            await gate.verify_candidate(b"candidate")

    asyncio.run(run_test())


def test_identity_gate_rejects_malformed_model_output() -> None:
    async def run_test() -> None:
        provider = FakeVisionProvider("not valid json")
        gate = IdentityGate(provider, enrolled_reference_image=b"reference")

        with pytest.raises(IdentityVerificationError):
            await gate.verify_candidate(b"candidate")

    asyncio.run(run_test())


def test_identity_check_skipped_when_no_frame_is_available() -> None:
    async def run_test() -> None:
        provider = FakeVisionProvider(
            '{"same_person": true, "confidence": 0.82, "spoof_suspected": false, "reason": "unused"}'
        )
        gate = IdentityGate(provider, enrolled_reference_image=b"reference")
        camera = FakeCameraService(frame=None)

        decision = await gate.verify_candidate_from_camera(camera)

        assert decision.source is IdentityDecisionSource.SKIPPED
        assert decision.reason == "Camera feed is not available for verification."
        assert provider.calls == []

    asyncio.run(run_test())


def test_verification_debouncer_only_fires_once_after_inactivity() -> None:
    async def run_test() -> None:
        fired: list[str] = []

        async def callback() -> None:
            fired.append("called")

        debouncer = VerificationDebouncer(delay_seconds=0.05, callback=callback)
        debouncer.submit_event()
        debouncer.submit_event()
        debouncer.submit_event()

        await asyncio.sleep(0.08)
        await debouncer.flush()

        assert fired == ["called"]

    asyncio.run(run_test())


def test_verification_debouncer_reset_delays_trigger() -> None:
    async def run_test() -> None:
        fired: list[str] = []

        async def callback() -> None:
            fired.append("called")

        debouncer = VerificationDebouncer(delay_seconds=0.05, callback=callback)
        debouncer.submit_event()
        await asyncio.sleep(0.03)
        debouncer.submit_event()
        await asyncio.sleep(0.03)
        assert fired == []
        await asyncio.sleep(0.04)
        await debouncer.flush()

        assert fired == ["called"]

    asyncio.run(run_test())