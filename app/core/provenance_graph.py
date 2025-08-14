from __future__ import annotations

from typing import Any
from datetime import datetime, UTC

from sqlalchemy import Table, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.orm import Session

from .db import get_engine
from ..config.settings import settings


metadata = MetaData()

provenance_edges = Table(
    "provenance_edges",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("jurisdiction_path", String, index=True),
    Column("claim", String),
    Column("source_url", String, index=True),
    Column("weight", Float, default=1.0),
    Column("created_at", DateTime, default=datetime.now(UTC)),
)


def init_provenance_graph() -> None:
    engine = get_engine(settings.database_url)
    metadata.drop_all(engine, tables=[provenance_edges])
    metadata.create_all(engine, tables=[provenance_edges])


def record_provenance_edge(jurisdiction_path: str, claim: str, source_url: str, weight: float = 1.0) -> None:
    engine = get_engine(settings.database_url)
    with Session(engine) as session:
        session.execute(
            provenance_edges.insert().values(
                jurisdiction_path=jurisdiction_path,
                claim=claim,
                source_url=source_url,
                weight=weight,
                created_at=datetime.now(UTC),
            )
        )
        session.commit()


