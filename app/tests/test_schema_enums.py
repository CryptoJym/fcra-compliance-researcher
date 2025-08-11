from __future__ import annotations

import json
import os
from pathlib import Path

from app.core.schema_enums import get_allowed_enums


def test_schema_enums_fallback():
    os.environ.pop("SCHEMA_ENUMS_PATH", None)
    enums = get_allowed_enums()
    assert "ban_the_box.timing.stage" in enums
    assert isinstance(enums["ban_the_box.timing.stage"], list)


def test_schema_enums_override(tmp_path: Path):
    data = {"notice_requirements.adverse.required": ["always", "never"]}
    f = tmp_path / "enums.json"
    f.write_text(json.dumps(data))
    os.environ["SCHEMA_ENUMS_PATH"] = str(f)
    enums = get_allowed_enums()
    assert enums == data
