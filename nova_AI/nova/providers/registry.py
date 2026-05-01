from __future__ import annotations

from dataclasses import dataclass

from nova.providers.base_provider import (
    BaseLlmProvider,
    BaseSttProvider,
    BaseTtsProvider,
    BaseWebResearchProvider,
)


@dataclass(slots=True)
class ProviderRegistry:
    _primary_llm: BaseLlmProvider | None = None
    _fallback_llm: BaseLlmProvider | None = None
    _stt: BaseSttProvider | None = None
    _tts: BaseTtsProvider | None = None
    _vision: object | None = None
    _web_research: BaseWebResearchProvider | None = None

    def register_primary_llm(self, provider: BaseLlmProvider) -> None:
        self._primary_llm = provider

    def register_fallback_llm(self, provider: BaseLlmProvider) -> None:
        self._fallback_llm = provider

    def register_stt(self, provider: BaseSttProvider) -> None:
        self._stt = provider

    def register_tts(self, provider: BaseTtsProvider) -> None:
        self._tts = provider

    def register_vision(self, provider: object) -> None:
        self._vision = provider

    def register_web_research(self, provider: BaseWebResearchProvider) -> None:
        self._web_research = provider

    def has_primary_llm(self) -> bool:
        return self._primary_llm is not None

    def has_fallback_llm(self) -> bool:
        return self._fallback_llm is not None

    def has_stt(self) -> bool:
        return self._stt is not None

    def has_tts(self) -> bool:
        return self._tts is not None

    def has_vision(self) -> bool:
        return self._vision is not None

    def has_web_research(self) -> bool:
        return self._web_research is not None

    def ensure_llm_pairing(self) -> None:
        if self.has_primary_llm() and not self.has_fallback_llm():
            self._fallback_llm = self._primary_llm
        elif self.has_fallback_llm() and not self.has_primary_llm():
            self._primary_llm = self._fallback_llm

    def get_primary_llm(self) -> BaseLlmProvider:
        if self._primary_llm is None:
            raise LookupError("Primary LLM provider is not registered.")
        return self._primary_llm

    def get_fallback_llm(self) -> BaseLlmProvider:
        if self._fallback_llm is None:
            raise LookupError("Fallback LLM provider is not registered.")
        return self._fallback_llm

    def get_stt(self) -> BaseSttProvider:
        if self._stt is None:
            raise LookupError("STT provider is not registered.")
        return self._stt

    def get_tts(self) -> BaseTtsProvider:
        if self._tts is None:
            raise LookupError("TTS provider is not registered.")
        return self._tts

    def get_vision(self) -> object:
        if self._vision is None:
            raise LookupError("Vision provider is not registered.")
        return self._vision

    def get_web_research(self) -> BaseWebResearchProvider:
        if self._web_research is None:
            raise LookupError("Web research provider is not registered.")
        return self._web_research