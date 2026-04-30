from __future__ import annotations

from pathlib import Path


class ApiKeyLoadError(RuntimeError):
    """Raised when an API key file is missing or empty."""


def load_key(name: str) -> str:
    """
    Load an API key from nova/config/api_keys/<name>_api.txt.

    Example:
        load_key("anthropic") -> reads nova/config/api_keys/anthropic_api.txt
        load_key("groq_oss") -> reads nova/config/api_keys/groq_oss_api.txt
    """
    normalized = name.strip().lower()
    if not normalized:
        raise ApiKeyLoadError("API key name must be a non-empty string.")

    current_dir = Path(__file__).resolve().parent
    config_dir = current_dir.parent
    key_path = config_dir / "api_keys" / f"{normalized}_api.txt"

    if not key_path.exists():
        raise ApiKeyLoadError(
            f"API key file not found for '{normalized}': expected '{key_path.name}' in '{key_path.parent}'."
        )

    value = key_path.read_text(encoding="utf-8").strip()
    if not value:
        raise ApiKeyLoadError(
            f"API key file for '{normalized}' is empty: '{key_path.name}'."
        )

    return value