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
    """Return a tuple of (migrated_data, note). For now, v1 is latest so no-op."""
    version = get_version(data)
    if version is None:
        # Assume legacy v1 when missing; set explicitly
        out = dict(data)
        out["schema_version"] = LATEST_VERSION
        return out, "Set default schema_version=v1 for legacy document"
    # Future: implement vN -> vN+1 migrations
    return data, "no-op"


def _migrate_missing_version_to_v1(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    notes: List[str] = []
    out = dict(data)
    # Example normalization: lastUpdated -> last_updated
    if "lastUpdated" in out and "last_updated" not in out:
        out["last_updated"] = out.pop("lastUpdated")
        notes.append("Renamed lastUpdated -> last_updated")
    # Ensure required top-level keys are present if obvious
    if "jurisdiction" not in out and "jurisdiction_path" in out:
        out["jurisdiction"] = out["jurisdiction_path"]
        notes.append("Filled jurisdiction from jurisdiction_path")
    # Stamp schema version
    out["schema_version"] = CURRENT_SCHEMA_VERSION
    notes.append(f"Stamped schema_version={CURRENT_SCHEMA_VERSION}")
    return out, notes


def migrate_patch_dict(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Migrate a patch dict to CURRENT_SCHEMA_VERSION. Returns (migrated, notes)."""
    if not isinstance(data, dict):
        return data, []
    version = data.get("schema_version")
    if version in (None, "", "v0"):
        return _migrate_missing_version_to_v1(data)
    # Already current or newer (unknown): no-op
    return data, []


def migrate_patch_file(patch_path: Path) -> List[str]:
    """Migrate a patch file in-place. Returns notes of applied migrations."""
    try:
        obj = json.loads(patch_path.read_text())
    except Exception:
        return []
    migrated, notes = migrate_patch_dict(obj)
    if notes:
        patch_path.write_text(json.dumps(migrated, indent=2))
    return notes
