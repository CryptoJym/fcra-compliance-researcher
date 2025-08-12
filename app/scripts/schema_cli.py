from __future__ import annotations

import json
from pathlib import Path
import typer

from app.core.schema_versioning import (
    CURRENT_SCHEMA_VERSION,
    validate_version,
    migrate_patch_file,
    migrate_patch_dict,
)


app = typer.Typer(add_completion=False)


@app.command()
def version() -> None:
    typer.echo(CURRENT_SCHEMA_VERSION)


@app.command()
def validate(file: str) -> None:
    p = Path(file)
    data = json.loads(p.read_text())
    ok, msg = validate_version(data)
    typer.echo(json.dumps({"ok": ok, "message": msg}))


@app.command()
def migrate(file: str) -> None:
    p = Path(file)
    notes = migrate_patch_file(p)
    typer.echo(json.dumps({"migrated": True if notes else False, "notes": notes}))


if __name__ == "__main__":
    app()


