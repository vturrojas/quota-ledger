import os

import pytest

from app.infra.db.session import engine
from app.infra.event_store.models import Base as EventStoreBase
from app.infra.projections.models import Base as ProjectionBase


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> None:
    """
    Ensure DB schema exists for integration tests.
    CI starts with an empty Postgres database.
    """
    assert os.getenv("DATABASE_URL"), "DATABASE_URL must be set for integration tests"

    # Create both sets of tables (event store + projections) on the same engine.
    EventStoreBase.metadata.create_all(bind=engine)
    ProjectionBase.metadata.create_all(bind=engine)
