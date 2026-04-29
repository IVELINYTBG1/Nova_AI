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


class AnthropicProvider(BaseLlmProvider):
    name = "anthropic"
    model = "claude-3-5-haiku-latest"

    def __init__(self, timeout: float = 30.0) -> None:
        try:
            self._api_key = load_key("anthropic")
        except ApiKeyLoadError as exc:
            raise ProviderConfigError(str(exc)) from exc
        self._base_url = "https://api.anthropic.com/v1/messages"
        self._timeout = timeout

    async def chat(
        self,
        messages: list[ChatMessage],
        meta: dict[str, Any] | None = None,
    ) -> ProviderResult:
        system_messages = [msg["content"] for msg in messages if msg["role"] == "system"]
        non_system_messages = [msg for msg in messages if msg["role"] != "system"]
        payload = {
            "model": self.model,
            "max_tokens": (meta or {}).get("max_tokens", 1024),
            "system": "\n\n".join(system_messages).strip(),
            "messages": non_system_messages,
        }
        if not payload["messages"]:
            payload["messages"] = [{"role": "user", "content": ""}]
        return await self._post_messages(payload)

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ProviderResult:
        payload = {
            "model": self.model,
            "max_tokens": (meta or {}).get("max_tokens", 1024),
            "system": system or "",
            "messages": [{"role": "user", "content": prompt}],
        }
        return await self._post_messages(payload)

    async def _post_messages(self, payload: dict[str, Any]) -> ProviderResult:
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._base_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text if exc.response is not None else ""
            raise ProviderExecutionError(f"Anthropic HTTP error: {exc}. Response body: {body}") from exc
        except httpx.HTTPError as exc:
            raise ProviderExecutionError(f"Anthropic transport error: {exc}") from exc
        except ValueError as exc:
            raise ProviderExecutionError(f"Anthropic returned invalid JSON: {exc}") from exc

        content = data.get("content")
        if not isinstance(content, list):
            raise ProviderExecutionError("Anthropic response missing 'content' list.")

        text_parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_value = block.get("text")
                if isinstance(text_value, str) and text_value:
                    text_parts.append(text_value)
        text = "\n".join(text_parts).strip()
        if not text:
            raise ProviderExecutionError("Anthropic response contained no text blocks.")

        usage_block = data.get("usage")
        usage: dict[str, int] | None = None
        if isinstance(usage_block, dict):
            usage = {}
            for source_key, target_key in (("input_tokens", "input_tokens"), ("output_tokens", "output_tokens")):
                value = usage_block.get(source_key)
                if isinstance(value, int):
                    usage[target_key] = value
            if not usage:
                usage = None

        return ProviderResult(
            success=True,
            text=text,
            provider_name=self.name,
            model_name=self.model,
            error=None,
            raw=data,
            usage=usage,
        )