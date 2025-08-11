from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

# Fallback constants. Replace/augment by reading schema docs if provided.
FALLBACK_ENUMS: Dict[str, List[str]] = {
    "ban_the_box.timing.stage": ["application", "interview", "conditional_offer", "post_offer"],
    "notice_requirements.pre_adverse.required": ["always", "sometimes", "never"],
    "notice_requirements.adverse.required": ["always", "sometimes", "never"],
}


def get_allowed_enums() -> Dict[str, List[str]]:
    """
    Returns allowed enum values mapping by field path.
    If SCHEMA_ENUMS_PATH is set to a JSON file, load from there; otherwise fallback constants.
    JSON format: { "field.path": ["val1", "val2"] }
    """
    path = os.getenv("SCHEMA_ENUMS_PATH")
    if path:
        try:
            data = json.loads(Path(path).read_text())
            if isinstance(data, dict):
                # Basic validation: ensure values are lists of strings
                valid: Dict[str, List[str]] = {}
                for k, v in data.items():
                    if isinstance(v, list) and all(isinstance(x, str) for x in v):
                        valid[k] = v
                if valid:
                    return valid
        except Exception:
            pass
    return FALLBACK_ENUMS
