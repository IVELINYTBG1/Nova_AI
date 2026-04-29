from __future__ import annotations

import httpx

from nova.config.python_files.api_loader import ApiKeyLoadError, load_key
from nova.providers.base_provider import BaseTtsProvider, ProviderConfigError, ProviderExecutionError


class FishSpeechApiProvider(BaseTtsProvider):
    name = "fish_speech_api"

    def __init__(self, timeout: float = 120.0) -> None:
        try:
            self._api_key = load_key("fish_speech")
        except ApiKeyLoadError as exc:
            raise ProviderConfigError(str(exc)) from exc
        self._base_url = "https://api.fish.audio"
        self._timeout = timeout

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        language: str | None = None,
    ) -> bytes:
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ProviderExecutionError("Fish Speech received empty text input.")

        headers = {
            "authorization": f"Bearer {self._api_key}",
            "content-type": "application/json",
        }
        payload = {
            "text": cleaned_text,
        }
        if voice:
            payload["voice"] = voice
        if language:
            payload["language"] = language

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                # TODO:
                # Replace this placeholder endpoint and payload with the exact Fish Speech
                # cloud REST contract once the final API spec is confirmed for your account.
                response = await client.post(
                    f"{self._base_url}/v1/tts",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text if exc.response is not None else ""
            raise ProviderExecutionError(f"Fish Speech HTTP error: {exc}. Response body: {body}") from exc
        except httpx.HTTPError as exc:
            raise ProviderExecutionError(f"Fish Speech transport error: {exc}") from exc

        audio_bytes = response.content
        if not audio_bytes:
            raise ProviderExecutionError("Fish Speech response contained no audio bytes.")
        return audio_bytes