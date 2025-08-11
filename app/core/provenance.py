from __future__ import annotations

from typing import Dict, Any

from sqlalchemy import Table, Column, Integer, String, JSON, MetaData
from sqlalchemy.orm import Session

from .db import get_engine
from ..config.settings import settings

metadata = MetaData()

provenance_table = Table(
    "provenance",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("jurisdiction_path", String, index=True),
    Column("field_path", String),
    Column("source_url", String),
    Column("snippet", String),
    Column("extra", JSON),
)


def init_provenance() -> None:
    engine = get_engine(settings.database_url)
    # Reset table to ensure a clean slate for tests/tools
    metadata.drop_all(engine, tables=[provenance_table])
    metadata.create_all(engine, tables=[provenance_table])


def record_provenance(
    jurisdiction_path: str,
    field_path: str,
    source_url: str,
    snippet: str,
    extra: Dict[str, Any] | None = None,
) -> None:
    engine = get_engine(settings.database_url)
    with Session(engine) as session:
        session.execute(
            provenance_table.insert().values(
                jurisdiction_path=jurisdiction_path,
                field_path=field_path,
                source_url=source_url,
                snippet=snippet,
                extra=extra or {},
            )
        )
        session.commit()
