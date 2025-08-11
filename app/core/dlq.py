from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .paths import project_root

DLQ_FILE = project_root() / "tools" / "dead_letter_queue.json"


def push_to_dlq(task: Dict) -> None:
    DLQ_FILE.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    if DLQ_FILE.exists():
        try:
            entries = json.loads(DLQ_FILE.read_text())
        except Exception:
            entries = []
    entries.append(task)
    DLQ_FILE.write_text(json.dumps(entries, indent=2))
