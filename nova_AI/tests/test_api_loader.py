from __future__ import annotations

from pathlib import Path

import pytest

from nova.config.python_files import api_loader
from nova.config.python_files.api_loader import ApiKeyLoadError, load_key


def test_load_key_reads_from_api_keys_folder(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_root = tmp_path / "config"
    python_files = config_root / "python_files"
    api_keys = config_root / "api_keys"
    python_files.mkdir(parents=True)
    api_keys.mkdir(parents=True)
    fake_loader = python_files / "api_loader.py"
    fake_loader.write_text("# placeholder", encoding="utf-8")
    (api_keys / "anthropic_api.txt").write_text("test-key", encoding="utf-8")

    monkeypatch.setattr(api_loader, "__file__", str(fake_loader))

    assert load_key("anthropic") == "test-key"


def test_load_key_raises_for_missing_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_root = tmp_path / "config"
    python_files = config_root / "python_files"
    api_keys = config_root / "api_keys"
    python_files.mkdir(parents=True)
    api_keys.mkdir(parents=True)
    fake_loader = python_files / "api_loader.py"
    fake_loader.write_text("# placeholder", encoding="utf-8")

    monkeypatch.setattr(api_loader, "__file__", str(fake_loader))

    with pytest.raises(ApiKeyLoadError):
        load_key("groq_oss")