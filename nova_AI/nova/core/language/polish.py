from __future__ import annotations

from nova.core.result_types import ResponseTurn


class LanguagePolisher:
    def polish(self, response: ResponseTurn) -> ResponseTurn:
        return response