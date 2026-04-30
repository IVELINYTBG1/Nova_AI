from __future__ import annotations

from nova.providers.registry import ProviderRegistry


class DummyLlmProvider:
    def __init__(self, name: str) -> None:
        self.name = name
        self.model = f"{name}-model"

    async def chat(self, messages, meta=None):
        raise NotImplementedError

    async def generate(self, prompt: str, system: str | None = None, meta=None):
        raise NotImplementedError


class DummySttProvider:
    name = "dummy-stt"

    async def transcribe(self, audio_bytes: bytes, language: str | None = None) -> str:
        return "text"


class DummyTtsProvider:
    name = "dummy-tts"

    async def synthesize(self, text: str, voice: str | None = None, language: str | None = None) -> bytes:
        return b"audio"


class DummyWebProvider:
    name = "dummy-web"

    async def research(self, query: str, meta=None):
        raise NotImplementedError


def test_provider_registry_has_helpers_report_state() -> None:
    registry = ProviderRegistry()
    assert registry.has_primary_llm() is False
    assert registry.has_fallback_llm() is False
    assert registry.has_stt() is False
    assert registry.has_tts() is False
    assert registry.has_web_research() is False

    registry.register_primary_llm(DummyLlmProvider("primary"))
    registry.register_stt(DummySttProvider())
    registry.register_tts(DummyTtsProvider())
    registry.register_web_research(DummyWebProvider())

    assert registry.has_primary_llm() is True
    assert registry.has_fallback_llm() is False
    assert registry.has_stt() is True
    assert registry.has_tts() is True
    assert registry.has_web_research() is True


def test_ensure_llm_pairing_uses_primary_as_fallback_when_only_primary_exists() -> None:
    registry = ProviderRegistry()
    primary = DummyLlmProvider("primary")
    registry.register_primary_llm(primary)

    registry.ensure_llm_pairing()

    assert registry.get_primary_llm() is primary
    assert registry.get_fallback_llm() is primary


def test_ensure_llm_pairing_uses_fallback_as_primary_when_only_fallback_exists() -> None:
    registry = ProviderRegistry()
    fallback = DummyLlmProvider("fallback")
    registry.register_fallback_llm(fallback)

    registry.ensure_llm_pairing()

    assert registry.get_primary_llm() is fallback
    assert registry.get_fallback_llm() is fallback


def test_ensure_llm_pairing_leaves_existing_pair_unchanged() -> None:
    registry = ProviderRegistry()
    primary = DummyLlmProvider("primary")
    fallback = DummyLlmProvider("fallback")
    registry.register_primary_llm(primary)
    registry.register_fallback_llm(fallback)

    registry.ensure_llm_pairing()

    assert registry.get_primary_llm() is primary
    assert registry.get_fallback_llm() is fallback