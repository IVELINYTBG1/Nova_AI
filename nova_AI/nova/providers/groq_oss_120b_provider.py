from __future__ import annotations

from typing import Any

import httpx

from nova.config.python_files.api_loader import ApiKeyLoadError, load_key
from nova.providers.base_provider import (
    BaseLlmProvider,
    ChatMessage,
    ProviderConfigError,
    ProviderExecutionError,
    ProviderResult,
)


class GroqOss120BProvider(BaseLlmProvider):
    name = "groq_oss_120b"
    model = "openai/gpt-oss-120b"

    def __init__(self, timeout: float = 30.0) -> None:
        try:
            self._api_key = load_key("groq_oss")
        except ApiKeyLoadError as exc:
            raise ProviderConfigError(str(exc)) from exc
        self._base_url = "https://api.groq.com/openai/v1/chat/completions"
        self._timeout = timeout

    async def chat(
        self,
        messages: list[ChatMessage],
        meta: dict[str, Any] | None = None,
    ) -> ProviderResult:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": (meta or {}).get("temperature", 0.2),
            "max_tokens": (meta or {}).get("max_tokens", 1024),
        }
        return await self._post_chat(payload)

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ProviderResult:
        messages: list[ChatMessage] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self.chat(messages=messages, meta=meta)

    async def _post_chat(self, payload: dict[str, Any]) -> ProviderResult:
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
            raise ProviderExecutionError(f"Groq HTTP error: {exc}. Response body: {body}") from exc
        except httpx.HTTPError as exc:
            raise ProviderExecutionError(f"Groq transport error: {exc}") from exc
        except ValueError as exc:
            raise ProviderExecutionError(f"Groq returned invalid JSON: {exc}") from exc

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderExecutionError("Groq response missing 'choices'.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ProviderExecutionError("Groq response choice was malformed.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ProviderExecutionError("Groq response missing message object.")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProviderExecutionError("Groq response contained no message content.")

        usage_block = data.get("usage")
        usage: dict[str, int] | None = None
        if isinstance(usage_block, dict):
            usage = {}
            for source_key, target_key in (
                ("prompt_tokens", "input_tokens"),
                ("completion_tokens", "output_tokens"),
                ("total_tokens", "total_tokens"),
            ):
                value = usage_block.get(source_key)
                if isinstance(value, int):
                    usage[target_key] = value
            if not usage:
                usage = None

        return ProviderResult(
            success=True,
            text=content.strip(),
            provider_name=self.name,
            model_name=self.model,
            error=None,
            raw=data,
            usage=usage,
        )