from __future__ import annotations

from nova.config.settings import Settings
from nova.core.language.language_layer import LanguageLayer
from nova.core.result_types import InputTurn, ResponseTurn


class IOMembrane:
    def __init__(self, settings: Settings, language_layer: LanguageLayer) -> None:
        self._settings = settings
        self._language_layer = language_layer

    def read_terminal_turn(self) -> InputTurn:
        while True:
            raw_text = input(self._settings.terminal_prompt)
            if raw_text.strip():
                language = self._language_layer.detect(raw_text)
                return InputTurn(
                    text=raw_text.strip(),
                    raw_text=raw_text,
                    language=language,
                    user_id=self._settings.user_id,
                    session_id=self._settings.session_id,
                )

    def write_terminal_response(self, response: ResponseTurn) -> None:
        text = response.text if response.text else ""
        print(f"Nova> {text}")