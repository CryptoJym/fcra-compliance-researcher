from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class JurisdictionRun(Base):
    __tablename__ = "jurisdiction_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jurisdiction_path: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    trace_id: Mapped[str] = mapped_column(String, index=True, default="-")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)


def get_engine(database_url: str):
    return create_engine(database_url, future=True)


def init_db(database_url: str) -> None:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)


def record_run(database_url: str, jurisdiction_path: str, status: str, metrics: Optional[dict] = None, error: Optional[str] = None, trace_id: Optional[str] = None) -> None:
    engine = get_engine(database_url)
    with Session(engine) as session:
        run = JurisdictionRun(jurisdiction_path=jurisdiction_path, status=status, metrics=metrics, error=error, trace_id=trace_id or "-")
        if status == "completed":
            run.completed_at = datetime.now(UTC)
        session.add(run)
        session.commit()
