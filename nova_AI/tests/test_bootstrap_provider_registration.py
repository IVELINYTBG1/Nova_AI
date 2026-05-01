from __future__ import annotations

from nova.bootstrap import build_nova
from nova.config.settings import load_settings
from nova.providers.base_provider import ProviderConfigError
from nova.providers.stub_provider import StubProvider


class FakeAnthropicProvider:
    name = "anthropic"
    model = "anthropic-model"

    async def chat(self, messages, meta=None):
        raise NotImplementedError

    async def generate(self, prompt: str, system: str | None = None, meta=None):
        raise NotImplementedError


class FakeGroqProvider:
    name = "groq_oss_120b"
    model = "groq-model"

    async def chat(self, messages, meta=None):
        raise NotImplementedError

    async def generate(self, prompt: str, system: str | None = None, meta=None):
        raise NotImplementedError


def test_bootstrap_uses_stub_provider_when_both_llm_configs_fail(monkeypatch) -> None:
    monkeypatch.setattr(
        "nova.bootstrap.AnthropicProvider",
        lambda: (_ for _ in ()).throw(ProviderConfigError("anthropic missing")),
    )
    monkeypatch.setattr(
        "nova.bootstrap.GroqOss120BProvider",
        lambda: (_ for _ in ()).throw(ProviderConfigError("groq missing")),
    )
    monkeypatch.setattr("nova.bootstrap.GroqGptTurboSttProvider", lambda: (_ for _ in ()).throw(ProviderConfigError("stt missing")))
    monkeypatch.setattr("nova.bootstrap.FishSpeechApiProvider", lambda: (_ for _ in ()).throw(ProviderConfigError("tts missing")))

    app = build_nova(load_settings())

    assert isinstance(app.provider_registry.get_primary_llm(), StubProvider)
    assert isinstance(app.provider_registry.get_fallback_llm(), StubProvider)


def test_bootstrap_ensures_fallback_when_only_primary_exists(monkeypatch) -> None:
    monkeypatch.setattr("nova.bootstrap.AnthropicProvider", FakeAnthropicProvider)
    monkeypatch.setattr(
        "nova.bootstrap.GroqOss120BProvider",
        lambda: (_ for _ in ()).throw(ProviderConfigError("groq missing")),
    )
    monkeypatch.setattr("nova.bootstrap.GroqGptTurboSttProvider", lambda: (_ for _ in ()).throw(ProviderConfigError("stt missing")))
    monkeypatch.setattr("nova.bootstrap.FishSpeechApiProvider", lambda: (_ for _ in ()).throw(ProviderConfigError("tts missing")))

    app = build_nova(load_settings())

    assert app.provider_registry.get_primary_llm() is app.provider_registry.get_fallback_llm()
    assert app.provider_registry.get_primary_llm().__class__ is FakeAnthropicProvider


def test_bootstrap_ensures_primary_when_only_fallback_exists(monkeypatch) -> None:
    monkeypatch.setattr(
        "nova.bootstrap.AnthropicProvider",
        lambda: (_ for _ in ()).throw(ProviderConfigError("anthropic missing")),
    )
    monkeypatch.setattr("nova.bootstrap.GroqOss120BProvider", FakeGroqProvider)
    monkeypatch.setattr("nova.bootstrap.GroqGptTurboSttProvider", lambda: (_ for _ in ()).throw(ProviderConfigError("stt missing")))
    monkeypatch.setattr("nova.bootstrap.FishSpeechApiProvider", lambda: (_ for _ in ()).throw(ProviderConfigError("tts missing")))

    app = build_nova(load_settings())

    assert app.provider_registry.get_primary_llm() is app.provider_registry.get_fallback_llm()
    assert app.provider_registry.get_primary_llm().__class__ is FakeGroqProvider