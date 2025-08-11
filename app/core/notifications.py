from __future__ import annotations

import os
import json
from typing import Optional

import httpx

from .logger import setup_logger

logger = setup_logger("notify")


def notify_slack(message: str) -> bool:
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        logger.info(f"Slack disabled: {message}")
        return False
    try:
        resp = httpx.post(url, json={"text": message}, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        logger.error(f"Slack notify failed: {e}")
        return False
