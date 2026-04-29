from __future__ import annotations

from nova.core.execution_types import HonestyFacts
from nova.core.result_types import ResponseTurn


class HonestyValidator:
    def validate(self, draft: ResponseTurn, facts: HonestyFacts) -> ResponseTurn:
        if facts.agent_result is not None:
            if facts.agent_result.success and not draft.success:
                return ResponseTurn(
                    text=draft.text,
                    language=draft.language,
                    success=True,
                    source=draft.source,
                    notes=draft.notes,
                )
            if not facts.agent_result.success:
                return ResponseTurn(
                    text=facts.agent_result.error or draft.text,
                    language=draft.language,
                    success=False,
                    source=draft.source,
                    notes=draft.notes,
                )
        return draft