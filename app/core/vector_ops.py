from __future__ import annotations

import hashlib
from typing import Dict, Iterable


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def should_ingest(meta: Dict) -> bool:
    # Skip if marked
    if meta.get("skip"):
        return False
    return True
