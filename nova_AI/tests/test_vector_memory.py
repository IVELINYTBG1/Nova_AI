from __future__ import annotations

from nova.core.memory.vector_memory import VectorMemoryStore


def test_vector_memory_stores_and_recalls_turn(tmp_path) -> None:
    store = VectorMemoryStore(storage_path=str(tmp_path / "vector_memory.json"))
    store.store_turn("user", "We are rebuilding Nova from scratch.")
    store.store_turn("nova", "Understood. We are rebuilding her cleanly.")

    results = store.recall("rebuilding Nova", n=2)

    assert len(results) >= 1
    assert any("Nova" in item["content"] for item in results)


def test_vector_memory_stores_and_searches_facts(tmp_path) -> None:
    store = VectorMemoryStore(storage_path=str(tmp_path / "vector_memory.json"))
    store.store_fact("The user prefers modular Python architecture.", topic="preferences")

    results = store.search_facts("modular python", n=2)

    assert len(results) == 1
    assert results[0]["topic"] == "preferences"
    assert "modular Python architecture" in results[0]["content"]


def test_vector_memory_stats_returns_correct_counts(tmp_path) -> None:
    store = VectorMemoryStore(storage_path=str(tmp_path / "vector_memory.json"))
    store.store_turn("user", "One")
    store.store_turn("nova", "Two")
    store.store_fact("Three")

    stats = store.stats()

    assert stats["conversation_turns"] == 2
    assert stats["stored_facts"] == 1