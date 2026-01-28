from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.domain.errors import ConcurrencyConflict
from app.domain.events import EventEnvelope
from app.domain.aggregate import apply_event
from app.domain.types import AccountQuotaState

from app.infra.db.session import SessionLocal
from app.infra.event_store.models import Event
from app.infra.projections.models import AccountCurrent


def _parse_occurred_at(value: str) -> datetime:
    """
    Accepts:
      - "now" (special marker)
      - ISO8601 like "2026-01-01T00:00:00Z"
      - ISO8601 with offset
    """
    if value == "now":
        return datetime.now(timezone.utc)

    # Handle trailing Z
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _to_envelope(row: Event) -> EventEnvelope:
    occurred_at = row.occurred_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return EventEnvelope(
        event_type=row.event_type,  # type: ignore[arg-type]
        schema_version=row.event_schema_version,
        occurred_at=occurred_at,
        payload=row.payload,
        idempotency_key=row.idempotency_key,
    )


class SqlAlchemyEventStore:
    def append(self, stream_id: str, expected_version: int, events: list[EventEnvelope]) -> int:
        """
        Append with optimistic concurrency.
        expected_version is the caller's view of the current stream version.
        Returns the new stream version after append.
        """
        if not events:
            return expected_version

        with SessionLocal() as session:
            # Determine current version in DB
            current_version = session.execute(
                select(func.coalesce(func.max(Event.stream_version), 0)).where(Event.stream_id == stream_id)
            ).scalar_one()

            # Idempotency: if the first new event has an idempotency_key, and we already have it,
            # return the existing stream_version (safe retry).
            key = events[0].idempotency_key
            if key:
                existing = session.execute(
                    select(Event).where(Event.stream_id == stream_id, Event.idempotency_key == key)
                ).scalar_one_or_none()
                if existing is not None:
                    # Return current stream version as of now
                    return current_version

            if current_version != expected_version:
                raise ConcurrencyConflict(
                    f"Concurrency conflict for stream '{stream_id}': expected {expected_version}, found {current_version}"
                )

            next_version = current_version
            for e in events:
                next_version += 1
                row = Event(
                    event_id=str(uuid4()),
                    stream_id=stream_id,
                    stream_version=next_version,
                    event_type=e.event_type,
                    event_schema_version=e.schema_version,
                    occurred_at=_parse_occurred_at(e.occurred_at),
                    idempotency_key=e.idempotency_key,
                    payload=e.payload,
                    meta={},  # fill later with correlation_id, actor, etc.
                )
                session.add(row)
                session.flush()

            # load existing events in this tx (cheap for now)
            rows = session.execute(
                select(Event)
                .where(Event.stream_id == stream_id)
                .order_by(Event.stream_version.asc())
            ).scalars().all()

            state = AccountQuotaState()
            for r in rows:
                state = apply_event(state, _to_envelope(r))

            proj = session.get(AccountCurrent, stream_id)
            if proj is None:
                session.add(
                    AccountCurrent(
                        account_id=stream_id,
                        stream_version=next_version,
                        status=state.status,
                        plan_id=state.plan_id,
                        period=state.period,
                        used=state.used or {},
                    )
                )
            else:
                proj.stream_version = next_version
                proj.status = state.status
                proj.plan_id = state.plan_id
                proj.period = state.period
                proj.used = state.used or {}

            try:
                session.commit()

            except IntegrityError as exc:
                session.rollback()
                # Could be idempotency unique violation or stream_version unique violation
                # We'll treat it as concurrency for now; later we’ll make idempotency return prior result.
                raise ConcurrencyConflict("Integrity conflict while appending events") from exc

            return next_version

    def load_stream(self, stream_id: str) -> list[EventEnvelope]:
        with SessionLocal() as session:
            rows = session.execute(
                select(Event).where(Event.stream_id == stream_id).order_by(Event.stream_version.asc())
            ).scalars().all()
            return [_to_envelope(r) for r in rows]

    def load_stream_since(self, stream_id: str, since_version: int) -> list[EventEnvelope]:
        with SessionLocal() as session:
            rows = session.execute(
                select(Event)
                .where(Event.stream_id == stream_id, Event.stream_version > since_version)
                .order_by(Event.stream_version.asc())
            ).scalars().all()
            return [_to_envelope(r) for r in rows]
