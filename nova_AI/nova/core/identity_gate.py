from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable

from nova.providers.base_provider import ProviderExecutionError

logger = logging.getLogger(__name__)


class IdentityVerificationError(RuntimeError):
    """Raised when the identity gate cannot produce a valid verification decision."""


class IdentityDecisionSource(str, Enum):
    MODEL = "model"
    SKIPPED = "skipped"


@dataclass(slots=True, frozen=True)
class IdentityDecision:
    same_person: bool
    confidence: float | None
    spoof_suspected: bool
    reason: str
    source: IdentityDecisionSource = IdentityDecisionSource.MODEL


class IdentityGate:
    def __init__(self, vision_provider, enrolled_reference_image: bytes | None = None) -> None:
        self._vision_provider = vision_provider
        self._enrolled_reference_image = enrolled_reference_image

    def set_reference_image(self, image_bytes: bytes) -> None:
        if not image_bytes:
            raise IdentityVerificationError("Reference image cannot be empty.")
        self._enrolled_reference_image = image_bytes

    async def verify_candidate(self, candidate_image: bytes) -> IdentityDecision:
        if not self._enrolled_reference_image:
            raise IdentityVerificationError("No enrolled reference image is set.")
        if not candidate_image:
            raise IdentityVerificationError("Candidate image cannot be empty.")

        prompt = (
            "You are performing a best-effort owner presence comparison, not strong authentication. "
            "Compare the enrolled owner reference image against the current candidate image. "
            "Respond with strict JSON only in this exact shape: "
            '{"same_person": true|false, "confidence": number|null, "spoof_suspected": true|false, "reason": "short explanation"}. '
            "Keep confidence between 0 and 1. Do not include markdown fences or extra text.\n\n"
            "The enrolled owner reference image is the image provided in this request. "
            "Judge whether the candidate likely appears to be the same visible person, and whether spoofing is suspected."
        )
        combined_bytes = self._enrolled_reference_image + b"\n--candidate-boundary--\n" + candidate_image

        try:
            raw_response = await self._vision_provider.analyze_image(combined_bytes, prompt)
        except ProviderExecutionError:
            raise
        except Exception as exc:
            raise IdentityVerificationError(f"Identity verification call failed: {exc}") from exc

        return self._parse_decision(raw_response)

    async def verify_candidate_from_camera(self, camera_service) -> IdentityDecision:
        frame = camera_service.capture_frame_bytes()
        if not frame:
            return IdentityDecision(
                same_person=False,
                confidence=None,
                spoof_suspected=False,
                reason="Camera feed is not available for verification.",
                source=IdentityDecisionSource.SKIPPED,
            )
        return await self.verify_candidate(frame)

    def _coerce_bool(self, value: object, field_name: str) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
        raise IdentityVerificationError(f"Identity gate response field '{field_name}' must be a boolean.")

    def _parse_decision(self, raw_response: str) -> IdentityDecision:
        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            logger.warning("Malformed identity provider output: %s", raw_response)
            raise IdentityVerificationError(f"Identity gate expected strict JSON but received invalid output: {exc}") from exc

        if not isinstance(payload, dict):
            logger.warning("Identity provider returned non-object payload: %r", payload)
            raise IdentityVerificationError("Identity gate expected a JSON object.")

        same_person = self._coerce_bool(payload.get("same_person"), "same_person")
        spoof_suspected = self._coerce_bool(payload.get("spoof_suspected"), "spoof_suspected")
        reason = payload.get("reason")
        confidence = payload.get("confidence")

        if not isinstance(reason, str) or not reason.strip():
            logger.warning("Identity provider returned invalid reason field: %r", reason)
            raise IdentityVerificationError("Identity gate response field 'reason' must be a non-empty string.")
        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                logger.warning("Identity provider returned invalid confidence field: %r", confidence)
                raise IdentityVerificationError("Identity gate response field 'confidence' must be numeric or null.")
            confidence = float(confidence)
            if confidence < 0.0 or confidence > 1.0:
                logger.warning("Identity provider returned out-of-range confidence: %r", confidence)
                raise IdentityVerificationError("Identity gate confidence must be between 0 and 1.")

        return IdentityDecision(
            same_person=same_person,
            confidence=confidence,
            spoof_suspected=spoof_suspected,
            reason=reason.strip(),
        )


class VerificationDebouncer:
    def __init__(
        self,
        delay_seconds: float,
        callback: Callable[[], Awaitable[None]],
    ) -> None:
        self._delay_seconds = delay_seconds
        self._callback = callback
        self._task: asyncio.Task[None] | None = None

    def submit_event(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()
        self._task = asyncio.create_task(self._run())

    async def flush(self) -> None:
        if self._task is None:
            return
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def _run(self) -> None:
        try:
            await asyncio.sleep(self._delay_seconds)
            await self._callback()
        except asyncio.CancelledError:
            raise