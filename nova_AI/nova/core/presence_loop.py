from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


class PresenceLoop:
    def __init__(self, state, output_callback, interval_seconds: float = 300.0) -> None:
        self._state = state
        self._output_callback = output_callback
        self._interval_seconds = interval_seconds
        self._running = False

    async def run(self) -> None:
        self._running = True
        while self._running:
            await asyncio.sleep(self._interval_seconds)
            minutes_elapsed = self._interval_seconds / 60.0
            self._state.drift(minutes_elapsed)
            logger.debug("Nova presence drifted by %.2f minutes.", minutes_elapsed)

            if self._state.should_initiate():
                message = self._state.get_initiation_message()
                logger.debug("Nova presence initiated contact: %s", message)
                result = self._output_callback(message)
                if asyncio.iscoroutine(result):
                    await result

    def stop(self) -> None:
        self._running = False