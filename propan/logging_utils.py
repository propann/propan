"""Logging helpers for Propan."""

from __future__ import annotations

import logging

from .settings import get_settings


def configure_logging() -> None:
    """Configure root logging with env-driven level."""

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
