from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "Nova"
    user_id: str = "boss"
    session_id: str = "terminal-session"
    default_language: str = "en"
    log_level: str = "INFO"
    memory_backend: str = "simple"
    memory_file: str = ".nova_memory.json"
    default_provider: str = "stub"
    terminal_prompt: str = "You> "
    camera_index: int = 0


def load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("NOVA_APP_NAME", "Nova"),
        user_id=os.getenv("NOVA_USER_ID", "boss"),
        session_id=os.getenv("NOVA_SESSION_ID", "terminal-session"),
        default_language=os.getenv("NOVA_DEFAULT_LANGUAGE", "en"),
        log_level=os.getenv("NOVA_LOG_LEVEL", "INFO").upper(),
        memory_backend=os.getenv("NOVA_MEMORY_BACKEND", "simple"),
        memory_file=os.getenv("NOVA_MEMORY_FILE", str(Path(".nova_memory.json"))),
        default_provider=os.getenv("NOVA_DEFAULT_PROVIDER", "stub"),
        terminal_prompt=os.getenv("NOVA_TERMINAL_PROMPT", "You> "),
        camera_index=int(os.getenv("NOVA_CAMERA_INDEX", "0")),
    )