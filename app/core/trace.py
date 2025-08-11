from __future__ import annotations

from contextvars import ContextVar
from contextlib import contextmanager
import uuid

_current_trace_id: ContextVar[str] = ContextVar("trace_id", default="-")


def get_trace_id() -> str:
    return _current_trace_id.get()


@contextmanager
def use_trace_id(trace_id: str | None = None):
    token = None
    try:
        tid = trace_id or uuid.uuid4().hex
        token = _current_trace_id.set(tid)
        yield tid
    finally:
        if token is not None:
            _current_trace_id.reset(token)
