from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    default_provider: str = "stub"
    default_language: str = "en"
    memory_file: str = ".nova_memory.json"


def load_settings() -> Settings:
    return Settings(
        default_provider=os.getenv("NOVA_DEFAULT_PROVIDER", "stub"),
        default_language=os.getenv("NOVA_DEFAULT_LANGUAGE", "en"),
        memory_file=os.getenv("NOVA_MEMORY_FILE", ".nova_memory.json"),
    )