from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

from nova.core.nova_state import NovaInternalState
from nova.core.presence_loop import PresenceLoop


def test_nova_state_loads_from_json_on_startup(tmp_path) -> None:
    path = tmp_path / "nova_state.json"
    path.write_text(
        json.dumps(
            {
                "energy": 0.4,
                "engagement": 0.3,
                "patience": 0.9,
                "mood": 0.5,
                "last_interaction": datetime.now(timezone.utc).isoformat(),
            }
        ),
        encoding="utf-8",
    )

    state = NovaInternalState(storage_path=str(path))

    assert state.energy == 0.4
    assert state.engagement == 0.3
    assert state.patience == 0.9
    assert state.mood == 0.5


def test_nova_state_saves_after_update(tmp_path) -> None:
    path = tmp_path / "nova_state.json"
    state = NovaInternalState(storage_path=str(path))

    state.update_on_interaction(250)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "energy" in payload
    assert "last_interaction" in payload


def test_nova_state_engagement_drops_with_silence(tmp_path) -> None:
    state = NovaInternalState(storage_path=str(tmp_path / "nova_state.json"))
    before = state.engagement

    state.drift(35)

    assert state.engagement < before


def test_nova_state_energy_drops_with_long_messages(tmp_path) -> None:
    state = NovaInternalState(storage_path=str(tmp_path / "nova_state.json"))
    before = state.energy

    state.update_on_interaction(300)

    assert state.energy < before


def test_nova_state_to_context_string_returns_natural_language(tmp_path) -> None:
    state = NovaInternalState(storage_path=str(tmp_path / "nova_state.json"))

    text = state.to_context_string()

    assert isinstance(text, str)
    assert len(text) > 10


def test_nova_state_to_context_string_never_exposes_raw_floats(tmp_path) -> None:
    state = NovaInternalState(storage_path=str(tmp_path / "nova_state.json"))

    text = state.to_context_string()

    assert "0." not in text
    assert "1.0" not in text


def test_presence_loop_initiates_after_long_silence(tmp_path, monkeypatch) -> None:
    state = NovaInternalState(storage_path=str(tmp_path / "nova_state.json"))
    state.engagement = 0.2
    state.last_interaction = (datetime.now(timezone.utc) - timedelta(minutes=65)).isoformat()
    messages: list[str] = []

    async def fake_sleep(seconds: float) -> None:
        loop.stop()

    loop = PresenceLoop(state=state, output_callback=lambda message: messages.append(message), interval_seconds=300.0)
    monkeypatch.setattr("nova.core.presence_loop.asyncio.sleep", fake_sleep)

    asyncio.run(loop.run())

    assert len(messages) == 1


def test_presence_loop_does_not_spam(tmp_path, monkeypatch) -> None:
    state = NovaInternalState(storage_path=str(tmp_path / "nova_state.json"))
    state.engagement = 0.2
    state.last_interaction = (datetime.now(timezone.utc) - timedelta(minutes=130)).isoformat()
    state.last_initiation = datetime.now(timezone.utc).isoformat()
    messages: list[str] = []

    async def fake_sleep(seconds: float) -> None:
        loop.stop()

    loop = PresenceLoop(state=state, output_callback=lambda message: messages.append(message), interval_seconds=300.0)
    monkeypatch.setattr("nova.core.presence_loop.asyncio.sleep", fake_sleep)

    asyncio.run(loop.run())

    assert messages == []