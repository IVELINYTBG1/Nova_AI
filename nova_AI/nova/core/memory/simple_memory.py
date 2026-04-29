from __future__ import annotations

import json
from pathlib import Path

from nova.core.memory.memory_interface import MemoryStore
from nova.core.result_types import MemoryItem


class SimpleMemoryStore(MemoryStore):
    def __init__(self, file_path: str) -> None:
        self._file_path = Path(file_path)
        self._items: list[MemoryItem] = []
        self._load()

    def store(self, item: MemoryItem) -> None:
        self._items.append(item)
        self._save()

    def search(self, query: str, limit: int = 5) -> list[MemoryItem]:
        lowered = query.lower()
        matches = [
            item
            for item in self._items
            if lowered in item.content.lower() or lowered in item.topic.lower() or any(lowered in tag.lower() for tag in item.tags)
        ]
        return matches[:limit]

    def list_topics(self) -> list[str]:
        return sorted({item.topic for item in self._items})

    def _load(self) -> None:
        if not self._file_path.exists():
            return
        raw = json.loads(self._file_path.read_text(encoding="utf-8"))
        self._items = [
            MemoryItem(
                id=item["id"],
                topic=item["topic"],
                content=item["content"],
                tags=item["tags"],
                source=item["source"],
                created_at=self._parse_datetime(item["created_at"]),
                updated_at=self._parse_datetime(item["updated_at"]),
            )
            for item in raw
        ]

    def _save(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "id": item.id,
                "topic": item.topic,
                "content": item.content,
                "tags": item.tags,
                "source": item.source,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }
            for item in self._items
        ]
        self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _parse_datetime(value: str):
        from datetime import datetime

        return datetime.fromisoformat(value)