from __future__ import annotations

import json
from pathlib import Path
import typer

from app.core.vector_store import VectorStore
from app.config.settings import settings

app = typer.Typer(add_completion=False)


@app.command()
def list_docs():
    vs = VectorStore(index_path=settings.vector_db_path, api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    vs.load()
    # Only supported for SimpleVectorStore; fall back to showing count
    store = getattr(vs, "_store", None)
    if hasattr(store, "list_documents"):
        for i, text, meta in store.list_documents():  # type: ignore[attr-defined]
            typer.echo(json.dumps({"i": i, "url": meta.get("url"), "title": meta.get("title"), "tags": meta.get("jurisdiction_tags")}))
    else:
        typer.echo("Listing not supported in FAISS mode. Use fallback mode or implement listing.")


@app.command()
def purge_by_tag(tag: str):
    vs = VectorStore(index_path=settings.vector_db_path, api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    vs.load()
    store = getattr(vs, "_store", None)
    if hasattr(store, "delete_indices") and hasattr(store, "_metas"):
        indices = [i for i, m in enumerate(store._metas) if tag not in (m.get("jurisdiction_tags") or [])]  # type: ignore[attr-defined]
        store.delete_indices(indices)  # type: ignore[attr-defined]
        vs.save()
        typer.echo(f"Purged to only keep tag={tag}")
    else:
        typer.echo("Purge not supported in FAISS mode.")


@app.command()
def reindex():
    """Rebuild the underlying index, applying dedupe and retention policies."""
    vs = VectorStore(index_path=settings.vector_db_path, api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    vs.reindex()
    typer.echo("Reindexed vector store")


@app.command()
def purge_retention():
    """Purge documents older than retention window (SimpleVectorStore only)."""
    vs = VectorStore(index_path=settings.vector_db_path, api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    vs.load()
    # Leverage reindex which applies retention filtering internally
    vs.reindex()
    typer.echo("Purged per retention policy via reindex")


if __name__ == "__main__":
    app()
