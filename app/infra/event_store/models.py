from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)

from app.infra.db.base import Base


class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True)
    stream_id = Column(String, nullable=False, index=True)
    stream_version = Column(BigInteger, nullable=False)
    event_type = Column(String, nullable=False)
    event_schema_version = Column(Integer, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    idempotency_key = Column(String, nullable=True)
    payload = Column(JSON, nullable=False)
    meta = Column("metadata", JSON, nullable=False, default=dict)

    __table_args__ = (
        UniqueConstraint("stream_id", "stream_version", name="uq_events_stream_version"),
        UniqueConstraint("stream_id", "idempotency_key", name="uq_events_idempotency"),
    )
