from __future__ import annotations

import pytest

from nova.config.python_files.api_loader import ApiKeyLoadError
from nova.providers.base_provider import ProviderConfigError
from nova.providers.fish_speech_api_provider import FishSpeechApiProvider
from nova.providers.groq_gpt_turbo_stt_provider import GroqGptTurboSttProvider
from nova.providers.registry import ProviderRegistry


class FakeSttProvider:
    name = "fake-stt"

    async def transcribe(self, audio_bytes: bytes, language: str | None = None) -> str:
        return "ok"


class FakeTtsProvider:
    name = "fake-tts"

    async def synthesize(self, text: str, voice: str | None = None, language: str | None = None) -> bytes:
        return b"audio"


def test_groq_stt_missing_key_raises_provider_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "nova.providers.groq_gpt_turbo_stt_provider.load_key",
        lambda name: (_ for _ in ()).throw(ApiKeyLoadError("missing groq stt key")),
    )

    with pytest.raises(ProviderConfigError):
        GroqGptTurboSttProvider()


def test_fish_speech_missing_key_raises_provider_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "nova.providers.fish_speech_api_provider.load_key",
        lambda name: (_ for _ in ()).throw(ApiKeyLoadError("missing fish speech key")),
    )

    with pytest.raises(ProviderConfigError):
        FishSpeechApiProvider()


def test_provider_registry_can_register_and_get_stt_tts() -> None:
    registry = ProviderRegistry()
    stt = FakeSttProvider()
    tts = FakeTtsProvider()

    registry.register_stt(stt)
    registry.register_tts(tts)

    assert registry.get_stt() is stt
    assert registry.get_tts() is tts