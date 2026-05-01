from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, TypedDict


class ProviderConfigError(RuntimeError):
    """Raised when a provider is misconfigured, such as a missing API key."""


class ProviderExecutionError(RuntimeError):
    """Raised when a provider request fails during execution."""


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


@dataclass(slots=True, frozen=True)
class ProviderResult:
    success: bool
    text: str
    provider_name: str
    model_name: str
    error: str | None = None
    raw: dict[str, Any] | None = None
    usage: dict[str, int] | None = None


@dataclass(slots=True, frozen=True)
class ResearchResult:
    success: bool
    query: str
    summary: str
    sources: list[str] = field(default_factory=list)
    error: str | None = None
    raw: dict[str, Any] | None = None


class BaseLlmProvider(Protocol):
    name: str
    model: str

    async def chat(
        self,
        messages: list[ChatMessage],
        meta: dict[str, Any] | None = None,
    ) -> ProviderResult:
        ...

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ProviderResult:
        ...


class BaseSttProvider(Protocol):
    name: str

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str | None = None,
    ) -> str:
        ...


class BaseTtsProvider(Protocol):
    name: str

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        language: str | None = None,
    ) -> bytes:
        ...


class BaseWebResearchProvider(Protocol):
    name: str

    async def research(
        self,
        query: str,
        meta: dict[str, Any] | None = None,
    ) -> ResearchResult:
        ...