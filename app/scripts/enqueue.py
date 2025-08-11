from __future__ import annotations

import json
from pathlib import Path
import typer

from app.core.paths import project_root
from app.agents.tasks import process_jurisdiction

app = typer.Typer(add_completion=False)


@app.command()
def file(jurisdiction_path: str, skip_validation: bool = False, skip_merge: bool = False):
    res = process_jurisdiction.delay(jurisdiction_path, skip_validation=skip_validation, skip_merge=skip_merge)
    typer.echo(f"queued: {res.id}")


@app.command()
def queue(queue_path: str = str(project_root() / "tools" / "research_queue.json"), skip_validation: bool = False, skip_merge: bool = False):
    data = json.loads(Path(queue_path).read_text())
    for item in data:
        jid = item.get("jurisdiction_path")
        if not jid:
            continue
        res = process_jurisdiction.delay(jid, skip_validation=skip_validation, skip_merge=skip_merge)
        typer.echo(f"queued {jid}: {res.id}")


if __name__ == "__main__":
    app()
