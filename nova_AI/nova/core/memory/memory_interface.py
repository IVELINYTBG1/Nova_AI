from __future__ import annotations

from abc import ABC, abstractmethod

from nova.core.result_types import MemoryItem


class MemoryStore(ABC):
    @abstractmethod
    def store(self, item: MemoryItem) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[MemoryItem]:
        raise NotImplementedError

    @abstractmethod
    def list_topics(self) -> list[str]:
        raise NotImplementedError