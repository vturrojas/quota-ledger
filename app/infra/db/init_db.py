from __future__ import annotations

import app.infra.projections.models  # noqa: F401
from app.infra.db.session import engine
from app.infra.event_store.models import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
