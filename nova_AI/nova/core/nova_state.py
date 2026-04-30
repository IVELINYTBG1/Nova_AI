from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass
class NovaInternalState:
    storage_path: str = "nova/data/nova_state.json"
    energy: float = 1.0
    engagement: float = 0.5
    patience: float = 1.0
    mood: float = 0.7
    last_interaction: str | None = None
    last_initiation: str | None = None

    def __post_init__(self) -> None:
        self._path = Path(self.storage_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def update_on_interaction(self, message_length: int) -> None:
        now = datetime.now(timezone.utc)
        self.last_interaction = now.isoformat()

        self.engagement = _clamp(self.engagement + 0.08)
        self.energy = _clamp(self.energy - (0.06 if message_length >= 240 else 0.02))
        self.patience = _clamp(self.patience - (0.03 if message_length <= 3 else 0.005))
        self.mood = _clamp(self.mood + ((self.engagement - 0.5) * 0.04))
        self._save()

    def drift(self, minutes_elapsed: float) -> None:
        self.energy = _clamp(self.energy + 0.01 * (minutes_elapsed / 5.0))

        if minutes_elapsed >= 30.0:
            self.engagement = _clamp(self.engagement - 0.05 * (minutes_elapsed / 30.0))

        if minutes_elapsed >= 60.0:
            self.patience = _clamp(self.patience - 0.03 * (minutes_elapsed / 60.0))

        baseline = 0.6
        self.mood = _clamp(self.mood + ((baseline - self.mood) * 0.1))
        self._save()

    def to_context_string(self) -> str:
        if self.energy < 0.4:
            return (
                "You are running a little low on energy right now. "
                "Keep responses measured and do not overextend."
            )
        if self.engagement >= 0.65 and self.energy >= 0.7:
            return (
                "You are currently well-rested and engaged. "
                "You feel sharp and present."
            )
        if self.engagement < 0.35:
            return (
                "You feel slightly distant after too much silence. "
                "Stay attentive, grounded, and gently present."
            )
        if self.patience < 0.4:
            return (
                "You feel a little worn thin. "
                "Stay calm, direct, and controlled."
            )
        return (
            "You feel steady, present, and attentive. "
            "Keep your tone calm and natural."
        )

    def should_initiate(self) -> bool:
        if self.last_interaction is None:
            return False

        now = datetime.now(timezone.utc)
        last_interaction = datetime.fromisoformat(self.last_interaction)
        if now - last_interaction < timedelta(minutes=60):
            return False

        if self.engagement >= 0.45:
            return False

        if self.last_initiation is None:
            return True

        last_initiation = datetime.fromisoformat(self.last_initiation)
        return (now - last_initiation) >= timedelta(minutes=60)

    def get_initiation_message(self) -> str:
        self.last_initiation = datetime.now(timezone.utc).isoformat()
        self._save()

        if self.engagement < 0.2:
            return "Back whenever you're ready."
        if self.mood < 0.45:
            return "Still here."
        return "You've been quiet. Everything okay?"

    def _load(self) -> None:
        if not self._path.exists():
            self.last_interaction = datetime.now(timezone.utc).isoformat()
            self._save()
            return

        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            self.last_interaction = datetime.now(timezone.utc).isoformat()
            self._save()
            return

        self.energy = float(payload.get("energy", self.energy))
        self.engagement = float(payload.get("engagement", self.engagement))
        self.patience = float(payload.get("patience", self.patience))
        self.mood = float(payload.get("mood", self.mood))
        self.last_interaction = payload.get("last_interaction") or datetime.now(timezone.utc).isoformat()
        self.last_initiation = payload.get("last_initiation")

    def _save(self) -> None:
        payload = {
            "energy": self.energy,
            "engagement": self.engagement,
            "patience": self.patience,
            "mood": self.mood,
            "last_interaction": self.last_interaction,
            "last_initiation": self.last_initiation,
        }
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")