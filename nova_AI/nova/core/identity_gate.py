from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable

from nova.providers.base_provider import ProviderExecutionError


class IdentityVerificationError(RuntimeError):
    """Raised when the identity gate cannot produce a valid verification decision."""


class IdentityDecisionSource(str, Enum):
    MODEL = "model"


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

    def _parse_decision(self, raw_response: str) -> IdentityDecision:
        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise IdentityVerificationError(f"Identity gate expected strict JSON but received invalid output: {exc}") from exc

        if not isinstance(payload, dict):
            raise IdentityVerificationError("Identity gate expected a JSON object.")

        same_person = payload.get("same_person")
        spoof_suspected = payload.get("spoof_suspected")
        reason = payload.get("reason")
        confidence = payload.get("confidence")

        if not isinstance(same_person, bool):
            raise IdentityVerificationError("Identity gate response field 'same_person' must be a boolean.")
        if not isinstance(spoof_suspected, bool):
            raise IdentityVerificationError("Identity gate response field 'spoof_suspected' must be a boolean.")
        if not isinstance(reason, str) or not reason.strip():
            raise IdentityVerificationError("Identity gate response field 'reason' must be a non-empty string.")
        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                raise IdentityVerificationError("Identity gate response field 'confidence' must be numeric or null.")
            confidence = float(confidence)
            if confidence < 0.0 or confidence > 1.0:
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