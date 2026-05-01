from __future__ import annotations

import asyncio

from nova.core.camera_gate import CameraGate
from nova.core.camera_service import CameraServiceError
from nova.core.identity_gate import IdentityDecision


class FakeCameraService:
    def __init__(self, frame: bytes | None = None, error: Exception | None = None) -> None:
        self._frame = frame
        self._error = error

    def capture_frame_bytes(self) -> bytes | None:
        if self._error:
            raise self._error
        return self._frame


class FakeIdentityGate:
    def __init__(self, decision: IdentityDecision) -> None:
        self._decision = decision
        self._enrolled_reference_image = b"ref"

    async def verify_candidate(self, candidate_image: bytes) -> IdentityDecision:
        return self._decision

    def set_reference_image(self, image_bytes: bytes) -> None:
        self._enrolled_reference_image = image_bytes


def test_camera_gate_allows_when_camera_unavailable() -> None:
    async def run_test() -> None:
        gate = CameraGate(
            identity_gate=FakeIdentityGate(IdentityDecision(True, 1.0, False, "ok")),
            camera_service=FakeCameraService(error=CameraServiceError("no camera")),
            debounce_delay_seconds=0.01,
        )
        assert await gate.verify() is True

    asyncio.run(run_test())


def test_camera_gate_denies_when_identity_not_confirmed() -> None:
    async def run_test() -> None:
        gate = CameraGate(
            identity_gate=FakeIdentityGate(IdentityDecision(False, 0.2, False, "not same person")),
            camera_service=FakeCameraService(frame=b"frame"),
            debounce_delay_seconds=0.01,
        )
        assert await gate.verify() is False

    asyncio.run(run_test())


def test_camera_gate_allows_when_vision_not_configured() -> None:
    async def run_test() -> None:
        gate = CameraGate(
            identity_gate=None,
            camera_service=FakeCameraService(frame=b"frame"),
            debounce_delay_seconds=0.01,
        )
        assert await gate.verify() is True

    asyncio.run(run_test())