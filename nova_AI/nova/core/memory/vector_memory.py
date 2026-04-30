from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]


def _cosine_overlap(query: str, content: str) -> float:
    query_tokens = _tokenize(query)
    content_tokens = _tokenize(content)
    if not query_tokens or not content_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    content_counts = Counter(content_tokens)

    numerator = sum(query_counts[token] * content_counts.get(token, 0) for token in query_counts)
    if numerator <= 0:
        return 0.0

    query_norm = math.sqrt(sum(value * value for value in query_counts.values()))
    content_norm = math.sqrt(sum(value * value for value in content_counts.values()))
    if query_norm == 0.0 or content_norm == 0.0:
        return 0.0

    return numerator / (query_norm * content_norm)


@dataclass(slots=True)
class VectorMemoryStore:
    storage_path: str = "nova/data/vector_memory.json"

    # Internal attributes must be declared when using slots=True
    _path: Path = field(init=False)
    _payload: dict[str, list[dict[str, Any]]] = field(init=False)

    def __post_init__(self) -> None:
        self._path = Path(self.storage_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._payload = self._load()

    def store_turn(self, role: str, content: str) -> None:
        cleaned = content.strip()
        if not cleaned:
            return

        self._payload["turns"].append(
            {
                "role": role.strip(),
                "content": cleaned,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save()

    def store_fact(self, content: str, topic: str = "user_context") -> None:
        cleaned = content.strip()
        if not cleaned:
            return

        self._payload["facts"].append(
            {
                "topic": topic.strip() or "user_context",
                "content": cleaned,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save()

    def recall(self, query: str, n: int = 3) -> list[dict[str, Any]]:
        ranked: list[tuple[float, dict[str, Any]]] = []
        for item in self._payload["turns"]:
            score = _cosine_overlap(query, str(item.get("content", "")))
            if score > 0.0:
                ranked.append((score, item))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in ranked[:n]]

    def search_facts(self, query: str, n: int = 3) -> list[dict[str, Any]]:
        ranked: list[tuple[float, dict[str, Any]]] = []
        for item in self._payload["facts"]:
            score = _cosine_overlap(query, str(item.get("content", "")))
            if score > 0.0:
                ranked.append((score, item))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in ranked[:n]]

    def stats(self) -> dict[str, int]:
        return {
            "conversation_turns": len(self._payload["turns"]),
            "stored_facts": len(self._payload["facts"]),
        }

    def _load(self) -> dict[str, list[dict[str, Any]]]:
        if not self._path.exists():
            payload: dict[str, list[dict[str, Any]]] = {"turns": [], "facts": []}
            self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return payload

        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            payload = {"turns": [], "facts": []}

        if not isinstance(payload, dict):
            payload = {"turns": [], "facts": []}

        turns = payload.get("turns", [])
        facts = payload.get("facts", [])
        if not isinstance(turns, list):
            turns = []
        if not isinstance(facts, list):
            facts = []

        return {"turns": turns, "facts": facts}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._payload, ensure_ascii=False, indent=2), encoding="utf-8")