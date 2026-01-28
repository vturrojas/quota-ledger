from __future__ import annotations

from sqlalchemy import JSON, Column, Integer, String

from app.infra.event_store.models import Base


class AccountCurrent(Base):
    __tablename__ = "account_current"

    account_id = Column(String, primary_key=True)
    stream_version = Column(Integer, nullable=False)

    status = Column(String, nullable=False)
    plan_id = Column(String, nullable=True)
    period = Column(String, nullable=True)
    used = Column(JSON, nullable=False, default=dict)
