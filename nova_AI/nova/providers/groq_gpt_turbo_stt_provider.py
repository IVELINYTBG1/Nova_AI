from __future__ import annotations

import httpx

from nova.config.python_files.api_loader import ApiKeyLoadError, load_key
from nova.providers.base_provider import BaseSttProvider, ProviderConfigError, ProviderExecutionError


class GroqGptTurboSttProvider(BaseSttProvider):
    name = "groq_gpt_turbo_stt"
    model = "whisper-large-v3-turbo"

    def __init__(self, timeout: float = 60.0) -> None:
        try:
            self._api_key = load_key("groq_stt")
        except ApiKeyLoadError as exc:
            raise ProviderConfigError(str(exc)) from exc
        self._base_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        self._timeout = timeout

    async def transcribe(self, audio_bytes: bytes, language: str | None = None) -> str:
        if not audio_bytes:
            raise ProviderExecutionError("Groq STT received empty audio input.")

        headers = {
            "authorization": f"Bearer {self._api_key}",
        }
        data = {"model": self.model, "response_format": "json"}
        if language:
            data["language"] = language
        files = {"file": ("nova_audio.wav", audio_bytes, "audio/wav")}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._base_url, headers=headers, data=data, files=files)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text if exc.response is not None else ""
            raise ProviderExecutionError(f"Groq STT HTTP error: {exc}. Response body: {body}") from exc
        except httpx.HTTPError as exc:
            raise ProviderExecutionError(f"Groq STT transport error: {exc}") from exc
        except ValueError as exc:
            raise ProviderExecutionError(f"Groq STT returned invalid JSON: {exc}") from exc

        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ProviderExecutionError("Groq STT response contained no transcribed text.")
        return text.strip()