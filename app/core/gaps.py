from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

# Minimal required fields placeholder to estimate gaps without the full schema
REQUIRED_FIELDS: List[str] = [
    "jurisdiction",
    "last_updated",
    # add more as needed; full schema integration will replace this
]


def estimate_gaps(base_dir: Path, jurisdiction_path: str) -> int:
    """
    Estimate number of missing required fields for a jurisdiction file.
    If file does not exist, return a high number to prioritize.
    """
    file_path = base_dir / jurisdiction_path
    if not file_path.exists():
        return len(REQUIRED_FIELDS) * 10
    try:
        data = json.loads(file_path.read_text())
    except Exception:
        return len(REQUIRED_FIELDS) * 10
    missing = 0
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] in (None, ""):
            missing += 1
    return missing
