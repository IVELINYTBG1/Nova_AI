from __future__ import annotations

import asyncio

import pytest

from nova.config.python_files.api_loader import ApiKeyLoadError
from nova.providers.base_provider import ProviderConfigError
from nova.providers.groq_llama_scout_vision_provider import GroqLlamaScoutVisionProvider


def test_groq_vision_missing_key_raises_provider_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "nova.providers.groq_llama_scout_vision_provider.load_key",
        lambda name: (_ for _ in ()).throw(ApiKeyLoadError("missing groq vision key")),
    )

    with pytest.raises(ProviderConfigError):
        GroqLlamaScoutVisionProvider()


def test_groq_vision_sends_two_labeled_images_when_boundary_present(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"same_person": true, "confidence": 0.9, "spoof_suspected": false, "reason": "match"}'
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr("nova.providers.groq_llama_scout_vision_provider.load_key", lambda name: "test-key")
    monkeypatch.setattr("nova.providers.groq_llama_scout_vision_provider.httpx.AsyncClient", FakeClient)

    async def run_test() -> None:
        provider = GroqLlamaScoutVisionProvider()
        output = await provider.analyze_image(b"ref\n--candidate-boundary--\ncandidate", "compare them")
        assert "same_person" in output

    asyncio.run(run_test())

    content = captured["json"]["messages"][0]["content"]
    assert captured["json"]["response_format"] == {"type": "json_object"}
    assert content[1]["text"] == "Reference image:"
    assert content[2]["type"] == "image_url"
    assert content[3]["text"] == "Candidate image:"
    assert content[4]["type"] == "image_url"