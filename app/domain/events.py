from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

EventType = Literal[
    "AccountCreated",
    "PlanChanged",
    "UsageRecorded",
    "PeriodReset",
    "AccountSuspended",
    "AccountReinstated",
]


@dataclass(frozen=True)
class EventEnvelope:
    event_type: EventType
    schema_version: int
    occurred_at: str  # ISO8601 string for now
    payload: dict[str, Any]
    idempotency_key: str | None = None
