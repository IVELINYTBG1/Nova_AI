from __future__ import annotations

import logging


def configure_logging(level: str = "INFO", app_name: str | None = None) -> None:
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    if app_name:
        logging.getLogger(app_name).setLevel(resolved_level)