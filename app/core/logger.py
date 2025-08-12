from __future__ import annotations

import json
import logging
import re
from logging import LogRecord
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict
import contextvars

from .paths import ensure_directories


# Context variable for per-run trace ID
TRACE_ID: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")


def set_trace_id(trace_id: str) -> None:
    TRACE_ID.set(trace_id)


class TraceIdFilter(logging.Filter):
    def filter(self, record: LogRecord) -> bool:  # noqa: A003 - name dictated by logging
        try:
            record.trace_id = TRACE_ID.get()
        except Exception:
            record.trace_id = "-"
        return True


class JSONFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        payload: Dict[str, Any] = {
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", "-"),
        }
        return json.dumps(payload, ensure_ascii=False)


_REDACT_KEYS = re.compile(r"(api_key|token|secret|password)", re.IGNORECASE)


def redact_secrets(message: str) -> str:
    try:
        return re.sub(r"(api_key|token|secret|password)=[^\s]+", r"\1=***", message, flags=re.IGNORECASE)
    except Exception:
        return message


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    ensure_directories()
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Human-readable file handler
        text_file_handler = RotatingFileHandler(log_dir / f"{name}.log", maxBytes=2_000_000, backupCount=5)
        text_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | trace_id=%(trace_id)s | %(message)s")
        text_file_handler.setFormatter(text_formatter)

        # JSON file handler
        json_file_handler = RotatingFileHandler(log_dir / f"{name}.jsonl", maxBytes=2_000_000, backupCount=5)
        json_file_handler.setFormatter(JSONFormatter())

        # Stream handler (console)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(text_formatter)

        # Attach filter to inject trace_id
        trace_filter = TraceIdFilter()
        text_file_handler.addFilter(trace_filter)
        json_file_handler.addFilter(trace_filter)
        stream_handler.addFilter(trace_filter)

        logger.addHandler(text_file_handler)
        logger.addHandler(json_file_handler)
        logger.addHandler(stream_handler)

    return logger
