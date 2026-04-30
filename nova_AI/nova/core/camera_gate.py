from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from nova.core.camera_service import CameraService, CameraServiceError
from nova.core.identity_gate import IdentityGate, IdentityVerificationError, VerificationDebouncer

logger = logging.getLogger(__name__)


@dataclass
class CameraGate:
    identity_gate: IdentityGate | None
    camera_service: CameraService
    cache_ttl_seconds: float = 60.0
    debounce_delay_seconds: float = 3.0

    def __post_init__(self) -> None:
        # Internal cache for the last verification decision and when it was made.
        self._last_verified_at: float | None = None
        self._last_verified_ok: bool | None = None
        # Debouncer so she does not re-verify on every keystroke.
        self._debouncer = VerificationDebouncer(self.debounce_delay_seconds, self._debounced_verify)

    async def verify(self) -> bool:
        if self.identity_gate is None:
            # No vision configured: fail open.
            return True

        if self._cache_valid() and self._last_verified_ok is True:
            return True

        self._debouncer.submit_event()
        await self._debouncer.flush()
        # Deny only on a clear negative; any failure or missing data is treated as allow.
        return self._last_verified_ok is not False

    async def capture_frame(self) -> bytes | None:
        try:
            return await asyncio.to_thread(self.camera_service.capture_frame_bytes)
        except CameraServiceError as exc:
            logger.warning("Nova camera capture unavailable: %s", exc)
            return None
        except Exception as exc:
            logger.warning("Nova camera capture failed unexpectedly: %s", exc)
            return None

    def invalidate_cache(self) -> None:
        self._last_verified_at = None
        self._last_verified_ok = None

    async def enroll_from_camera(self) -> bool:
        if self.identity_gate is None:
            return False

        frame = await self.capture_frame()
        if not frame:
            return False

        self.identity_gate.set_reference_image(frame)
        self._last_verified_at = time.monotonic()
        self._last_verified_ok = True
        return True

    def is_enrolled(self) -> bool:
        return bool(
            self.identity_gate is not None
            and getattr(self.identity_gate, "_enrolled_reference_image", None)
        )

    async def _debounced_verify(self) -> None:
        if self.identity_gate is None:
            self._last_verified_ok = True
            self._last_verified_at = time.monotonic()
            return

        frame = await self.capture_frame()
        if not frame:
            # Camera problems should not lock her completely; fail open.
            self._last_verified_ok = True
            self._last_verified_at = time.monotonic()
            return

        try:
            decision = await self.identity_gate.verify_candidate(frame)
        except IdentityVerificationError as exc:
            logger.warning("Nova identity verification failed open: %s", exc)
            self._last_verified_ok = True
            self._last_verified_at = time.monotonic()
            return

        self._last_verified_ok = bool(decision.same_person and not decision.spoof_suspected)
        self._last_verified_at = time.monotonic()

    def _cache_valid(self) -> bool:
        return (
            self._last_verified_at is not None
            and (time.monotonic() - self._last_verified_at) < self.cache_ttl_seconds
        )