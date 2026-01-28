from __future__ import annotations

from app.domain.events import EventEnvelope

def upcast(event: EventEnvelope) -> EventEnvelope:
    """
    Upcast older event schema versions to the latest in-memory shape.

    Example:
      UsageRecorded v1 -> v2 by adding 'source'
    """
    if event.event_type == "UsageRecorded" and event.schema_version == 1:
        payload = dict(event.payload)
        payload["source"] = "unknown"
        return EventEnvelope(
            event_type=event.event_type,
            schema_version=2,
            occurred_at=event.occurred_at,
            payload=payload,
            idempotency_key=event.idempotency_key,
        )
    return event
