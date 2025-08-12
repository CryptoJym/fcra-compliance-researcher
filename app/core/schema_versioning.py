from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

SUPPORTED_VERSIONS = {"v1"}
LATEST_VERSION = "v1"
CURRENT_SCHEMA_VERSION = "v1"


def get_version(data: Dict[str, Any]) -> str | None:
    return data.get("schema_version")


def validate_version(data: Dict[str, Any]) -> Tuple[bool, str]:
    version = get_version(data)
    if version is None:
        return False, "Missing required field: schema_version"
    if version not in SUPPORTED_VERSIONS:
        return False, f"Unsupported schema_version: {version}"
    return True, "ok"


def migrate_to_latest(data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    version = get_version(data)
    if version is None:
        out = dict(data)
        out["schema_version"] = LATEST_VERSION
        # Also normalize a couple of legacy fields for convenience
        if "lastUpdated" in out and "last_updated" not in out:
            out["last_updated"] = out.pop("lastUpdated")
        if "jurisdiction" not in out and "jurisdiction_path" in out:
            out["jurisdiction"] = out["jurisdiction_path"]
        return out, "Stamped schema_version=v1 and normalized legacy fields"
    return data, "no-op"


def _migrate_missing_version_to_v1(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    notes: List[str] = []
    out = dict(data)
    if "lastUpdated" in out and "last_updated" not in out:
        out["last_updated"] = out.pop("lastUpdated")
        notes.append("Renamed lastUpdated -> last_updated")
    if "jurisdiction" not in out and "jurisdiction_path" in out:
        out["jurisdiction"] = out["jurisdiction_path"]
        notes.append("Filled jurisdiction from jurisdiction_path")
    out["schema_version"] = CURRENT_SCHEMA_VERSION
    notes.append(f"Stamped schema_version={CURRENT_SCHEMA_VERSION}")
    return out, notes


def migrate_patch_dict(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    if not isinstance(data, dict):
        return data, []
    version = data.get("schema_version")
    if version in (None, "", "v0"):
        return _migrate_missing_version_to_v1(data)
    return data, []


def migrate_patch_file(patch_path: Path) -> List[str]:
    try:
        obj = json.loads(patch_path.read_text())
    except Exception:
        return []
    migrated, notes = migrate_patch_dict(obj)
    if notes:
        patch_path.write_text(json.dumps(migrated, indent=2))
    return notes
