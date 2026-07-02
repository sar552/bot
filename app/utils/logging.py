"""Logging sozlamasi (TZ §14.10 — xatolar log qilinishi kerak)."""
from __future__ import annotations

import sys

from loguru import logger


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan> - <level>{message}</level>",
    )
    logger.add(
        "logs/bot.log",
        level="INFO",
        rotation="10 MB",
        retention="14 days",
        enqueue=True,
    )
