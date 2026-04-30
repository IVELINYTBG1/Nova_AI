from __future__ import annotations

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