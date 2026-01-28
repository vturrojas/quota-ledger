from __future__ import annotations

from dataclasses import dataclass

from app.domain.types import Meter


@dataclass(frozen=True)
class CreateAccount:
    account_id: str
    initial_plan_id: str
    period: str  # e.g. "2026-01"


@dataclass(frozen=True)
class ChangePlan:
    account_id: str
    new_plan_id: str


@dataclass(frozen=True)
class RecordUsage:
    account_id: str
    meter: Meter
    units: int
    occurred_at: str
    idempotency_key: str


@dataclass(frozen=True)
class ResetPeriod:
    account_id: str
    new_period: str


@dataclass(frozen=True)
class SuspendAccount:
    account_id: str
    reason: str


@dataclass(frozen=True)
class ReinstateAccount:
    account_id: str
