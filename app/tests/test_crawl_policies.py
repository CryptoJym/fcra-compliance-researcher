from __future__ import annotations

import os
import time
import builtins
from app.core.crawl import respect_robots, choose_user_agent, polite_delay


def test_choose_user_agent_env(monkeypatch):
    monkeypatch.setenv("CRAWL_USER_AGENT", "TestAgent/1.0")
    assert choose_user_agent() == "TestAgent/1.0"


def test_respect_robots_disabled(monkeypatch):
    monkeypatch.setenv("CRAWL_RESPECT_ROBOTS", "0")
    assert respect_robots("https://example.com/x", "AnyUA") is True


def test_polite_delay(monkeypatch):
    monkeypatch.setenv("CRAWL_DELAY_SECONDS", "0.01")
    start = time.monotonic()
    polite_delay("https://example.com/x")
    polite_delay("https://example.com/x")
    assert time.monotonic() - start >= 0.01


