from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class Settings:
    memory_file: Path
    default_language: str = "en"


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]
    memory_dir = project_root / "nova" / "data"
    memory_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        memory_file=memory_dir / "memory.json",
        default_language="en",
    )
