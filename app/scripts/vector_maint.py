from __future__ import annotations

import json
from pathlib import Path
import typer

from app.config.settings import settings
from app.core.vector_store import VectorStore


app = typer.Typer(add_completion=False)


@app.command()
def reindex(index_path: str | None = None) -> None:
    vp = index_path or settings.vector_db_path
    vs = VectorStore(index_path=vp, api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    vs.load()
    vs.reindex()
    typer.echo("Reindex complete")


@app.command()
def stats(index_path: str | None = None) -> None:
    vp = index_path or settings.vector_db_path
    vs = VectorStore(index_path=vp, api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    # Use internal doc store to report stats
    texts, metas = vs._read_all_docs_from_store()  # type: ignore[attr-defined]
    uniq = set()
    for m in metas:
        key = (m or {}).get("dedupe_key") or (m or {}).get("url")
        if key:
            uniq.add(key)
    typer.echo(json.dumps({"docs": len(texts), "unique": len(uniq)}, indent=2))


if __name__ == "__main__":
    app()


