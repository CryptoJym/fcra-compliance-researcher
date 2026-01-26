from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator
except Exception as e:  # pragma: no cover
    raise SystemExit(f"jsonschema is required to validate: {e}")


def schema_path() -> Path:
    env_path = os.getenv("SCHEMA_PATH")
    if env_path:
        return Path(env_path)
    scope = os.getenv("RESEARCH_SCOPE", "CRA").strip().upper()
    base = Path(__file__).resolve().parents[1] / "schema"
    if scope == "CRA":
        return base / "cra-matrix.schema.json"
    return base / "cra-matrix.schema.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validate(schema_file: Path, payload: dict) -> list[str]:
    schema = load_json(schema_file)
    validator = Draft7Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(payload), key=lambda e: e.path):
        loc = ".".join(str(p) for p in err.path) or "$"
        errors.append(f"{loc}: {err.message}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CRA compliance patch against schema")
    parser.add_argument("--file", required=False, help="Jurisdiction file (unused for CRA-only scope)")
    parser.add_argument("--input", required=True, help="Patch JSON file")
    args = parser.parse_args()

    patch_path = Path(args.input)
    if not patch_path.exists():
        print(f"Patch not found: {patch_path}", file=sys.stderr)
        return 2

    schema_file = schema_path()
    if not schema_file.exists():
        print(f"Schema not found: {schema_file}", file=sys.stderr)
        return 2

    payload = load_json(patch_path)
    errors = validate(schema_file, payload)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
