from __future__ import annotations

import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Basic auth with optional bypass for tests
security = HTTPBasic(auto_error=False)


def require_basic_auth(credentials: HTTPBasicCredentials | None = Depends(security)) -> bool:
    # Test bypass
    if os.getenv("DASH_AUTH_DISABLED") == "1":
        return True

    # Support legacy env var names and new ones
    user = os.getenv("DASH_USER") or os.getenv("DASHBOARD_USER")
    pwd = os.getenv("DASH_PASS") or os.getenv("DASHBOARD_PASS")

    # If not configured, allow access (dev default)
    if not user and not pwd:
        return True

    if not credentials or credentials.username != (user or "") or credentials.password != (pwd or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic realm=dashboard"},
        )
    return True
