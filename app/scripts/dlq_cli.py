from __future__ import annotations

import json
from pathlib import Path
import typer

from app.core.dlq import DLQ_FILE, push_to_dlq


app = typer.Typer(add_completion=False)


@app.command()
def show():
    if not DLQ_FILE.exists():
        typer.echo("[]")
        raise typer.Exit(0)
    typer.echo(DLQ_FILE.read_text())


@app.command()
def clear():
    if DLQ_FILE.exists():
        DLQ_FILE.unlink()
    typer.echo("cleared")


@app.command()
def push(task_json: str):
    data = json.loads(task_json)
    push_to_dlq(data)
    typer.echo("pushed")


if __name__ == "__main__":
    app()


