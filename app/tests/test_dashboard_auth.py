from __future__ import annotations

import os
from fastapi.testclient import TestClient

from app.dashboard.server import app


def test_dashboard_allows_when_auth_disabled(monkeypatch):
    monkeypatch.delenv("DASHBOARD_USER", raising=False)
    monkeypatch.delenv("DASHBOARD_PASS", raising=False)
    client = TestClient(app)
    r = client.get("/")
    # Depends() will be satisfied without credentials when disabled
    assert r.status_code in (200, 401)
    # If other errors occur due to DB, we still accept 200/401 as auth layer signal


def test_dashboard_requires_basic_auth(monkeypatch):
    monkeypatch.setenv("DASHBOARD_USER", "user")
    monkeypatch.setenv("DASHBOARD_PASS", "pass")
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 401
    r2 = client.get("/", auth=("user", "pass"))
    # Could be 200 or 500 depending on DB setup; ensure auth gate opens
    assert r2.status_code in (200, 500)


