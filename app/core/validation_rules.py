from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_patch(patch_path: Path) -> Dict[str, Any]:
    return json.loads(patch_path.read_text())


def save_patch(patch_path: Path, data: Dict[str, Any]) -> None:
    patch_path.write_text(json.dumps(data, indent=2))


def check_citations(patch: Dict[str, Any]) -> List[str]:
    """Return list of citation-related errors.
    Minimal rule: if `ban_the_box.applies` is true, require at least one `citations.laws` entry.
    """
    errors: List[str] = []
    btb = (patch or {}).get("ban_the_box", {})
    applies = btb.get("applies")
    citations = (patch or {}).get("citations", {})
    laws = citations.get("laws") if isinstance(citations, dict) else None
    if applies is True:
        if not isinstance(laws, list) or len(laws) == 0:
            errors.append("When ban_the_box.applies is true, citations.laws must contain at least one source")
    return errors


essential_fields = ["jurisdiction", "last_updated"]


def check_required_fields(patch: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    for f in essential_fields:
        if f not in patch or patch[f] in (None, ""):
            errs.append(f"Missing required field: {f}")
    return errs


def maybe_infer_preemption(patch: Dict[str, Any], jurisdiction_path: str) -> Tuple[Dict[str, Any], List[str]]:
    """Heuristic: If city jurisdiction, ban_the_box.applies is false, and citations.laws includes a state URL,
    then add preemptions.preempted_by = ["state"]. Returns (modified_patch, notes)."""
    notes: List[str] = []
    data = dict(patch)
    if "/city/" in jurisdiction_path:
        btb = data.get("ban_the_box", {})
        applies = btb.get("applies")
        citations = (data or {}).get("citations", {})
        laws = citations.get("laws") if isinstance(citations, dict) else []
        has_state_source = any(isinstance(x, str) and (".state." in x or "/codes/" in x or "state." in x) for x in laws)
        if applies is False and has_state_source:
            pre = data.get("preemptions") or {}
            preempted_by = set(pre.get("preempted_by") or [])
            preempted_by.add("state")
            pre["preempted_by"] = sorted(preempted_by)
            data["preemptions"] = pre
            notes.append("Inferred preemption: city preempted by state for ban_the_box")
    return data, notes


def run_internal_checks(patch_path: Path, jurisdiction_path: str, auto_fix_preemption: bool = True) -> Tuple[bool, Dict[str, Any]]:
    data = load_patch(patch_path)
    errors: List[str] = []
    notes: List[str] = []

    errors.extend(check_required_fields(data))
    errors.extend(check_citations(data))

    if auto_fix_preemption:
        new_data, pre_notes = maybe_infer_preemption(data, jurisdiction_path)
        if new_data != data:
            save_patch(patch_path, new_data)
            data = new_data
            notes.extend(pre_notes)

    ok = len(errors) == 0
    details = {"errors": errors, "notes": notes}
    return ok, details
