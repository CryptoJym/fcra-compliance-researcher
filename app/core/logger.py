from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .paths import ensure_directories


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    ensure_directories()
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(log_dir / f"{name}.log", maxBytes=2_000_000, backupCount=5)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
