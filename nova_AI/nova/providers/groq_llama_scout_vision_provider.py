from __future__ import annotations

import base64

import httpx

from nova.config.python_files.api_loader import ApiKeyLoadError, load_key
from nova.providers.base_provider import ProviderConfigError, ProviderExecutionError


class GroqLlamaScoutVisionProvider:
    name = "groq_llama_scout_vision"
    model = "meta-llama/llama-4-scout-17b-16e-instruct"

    def __init__(self, timeout: float = 60.0) -> None:
        try:
            self._api_key = load_key("groq_vision")
        except ApiKeyLoadError as exc:
            raise ProviderConfigError(str(exc)) from exc
        self._base_url = "https://api.groq.com/openai/v1/chat/completions"
        self._timeout = timeout

    async def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        if not image_bytes:
            raise ProviderExecutionError("Groq vision received empty image input.")
        cleaned_prompt = prompt.strip()
        if not cleaned_prompt:
            raise ProviderExecutionError("Groq vision received an empty prompt.")

        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/jpeg;base64,{image_b64}"
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": cleaned_prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
        }
        headers = {
            "authorization": f"Bearer {self._api_key}",
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._base_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text if exc.response is not None else ""
            raise ProviderExecutionError(f"Groq vision HTTP error: {exc}. Response body: {body}") from exc
        except httpx.HTTPError as exc:
            raise ProviderExecutionError(f"Groq vision transport error: {exc}") from exc
        except ValueError as exc:
            raise ProviderExecutionError(f"Groq vision returned invalid JSON: {exc}") from exc

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderExecutionError("Groq vision response missing 'choices'.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ProviderExecutionError("Groq vision response choice was malformed.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ProviderExecutionError("Groq vision response missing message object.")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProviderExecutionError("Groq vision response contained no message content.")

        return content.strip()