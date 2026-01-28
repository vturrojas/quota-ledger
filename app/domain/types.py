from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Meter = Literal["api_calls", "storage_mb"]

@dataclass(frozen=True)
class Plan:
    plan_id: str
    limits: dict[Meter, int]


@dataclass(frozen=True)
class AccountQuotaState:
    exists: bool = False
    status: Literal["active", "suspended"] = "active"
    plan_id: str | None = None
    period: str | None = None  # e.g. "2026-01"
    used: dict[Meter, int] | None = None
