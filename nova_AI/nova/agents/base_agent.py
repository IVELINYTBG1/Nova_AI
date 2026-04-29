from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import logging

from nova.core.result_types import AgentMetadata, AgentResult

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base contract for all Nova agents.

    Agents must keep their public execution boundary exception-safe.
    The recommended execute() pattern in concrete agents is:

        def execute(self, input_data: dict[str, Any]) -> AgentResult:
            try:
                ... agent logic ...
                return AgentResult(success=True, data=result)
            except Exception as exc:
                return self._safe_failure(exc)

    Concrete agents must not let exceptions escape past execute() or undo().
    """

    metadata: AgentMetadata

    @abstractmethod
    def execute(self, input_data: dict[str, Any]) -> AgentResult:
        raise NotImplementedError

    def undo(self, undo_token: str) -> AgentResult:
        try:
            return AgentResult(
                success=False,
                error=f"Undo is not supported for agent '{self.metadata.name}'.",
            )
        except Exception as exc:
            return self._safe_failure(exc)

    def _safe_failure(self, exc: Exception) -> AgentResult:
        logger.exception("Agent '%s' failed", self.metadata.name)
        return AgentResult(success=False, error=str(exc))