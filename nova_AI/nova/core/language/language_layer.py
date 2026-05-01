from __future__ import annotations


class LanguageLayer:
    def __init__(self, default_language: str = "en") -> None:
        self._default_language = default_language

    def detect(self, text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return self._default_language
        return self._default_language   