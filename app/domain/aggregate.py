from __future__ import annotations

from dataclasses import replace

from app.domain.commands import (
    ChangePlan,
    CreateAccount,
    RecordUsage,
    ReinstateAccount,
    ResetPeriod,
    SuspendAccount,
)
from app.domain.errors import InvariantViolation, NotFound
from app.domain.events import EventEnvelope
from app.domain.types import AccountQuotaState


def apply_event(state: AccountQuotaState, e: EventEnvelope) -> AccountQuotaState:
    t = e.event_type
    p = e.payload

    if t == "AccountCreated":
        return AccountQuotaState(
            exists=True,
            status="active",
            plan_id=p["plan_id"],
            period=p["period"],
            used={},
        )

    if not state.exists:
        return state

    if t == "PlanChanged":
        return replace(state, plan_id=p["plan_id"])

    if t == "UsageRecorded":
        used = dict(state.used or {})
        meter = p["meter"]
        used[meter] = int(used.get(meter, 0)) + int(p["units"])
        return replace(state, used=used)

    if t == "PeriodReset":
        return replace(state, period=p["period"], used={})

    if t == "AccountSuspended":
        return replace(state, status="suspended")

    if t == "AccountReinstated":
        return replace(state, status="active")

    return state


def decide(state: AccountQuotaState, cmd) -> list[EventEnvelope]:
    # NOTE: limits/plan resolution happens in the app/service layer for simplicity.
    if isinstance(cmd, CreateAccount):
        if state.exists:
            raise InvariantViolation("Account already exists")
        return [
            EventEnvelope(
                event_type="AccountCreated",
                schema_version=1,
                occurred_at="now",
                payload={"plan_id": cmd.initial_plan_id, "period": cmd.period},
            )
        ]

    if not state.exists:
        raise NotFound("Account does not exist")

    if isinstance(cmd, ChangePlan):
        if state.status != "active":
            raise InvariantViolation("Cannot change plan when account is suspended")
        return [
            EventEnvelope(
                event_type="PlanChanged",
                schema_version=1,
                occurred_at="now",
                payload={"plan_id": cmd.new_plan_id},
            )
        ]

    if isinstance(cmd, RecordUsage):
        if cmd.units <= 0:
            raise InvariantViolation("Usage units must be > 0")
        if state.status != "active":
            raise InvariantViolation("Cannot record usage when account is suspended")
        return [
            EventEnvelope(
                event_type="UsageRecorded",
                schema_version=2,  # demonstrate versioning early
                occurred_at=cmd.occurred_at,
                payload={"meter": cmd.meter, "units": cmd.units, "source": "api"},
                idempotency_key=cmd.idempotency_key,
            )
        ]

    if isinstance(cmd, ResetPeriod):
        # Keep it simple: lexicographic "YYYY-MM" forward-only
        if state.period and cmd.new_period <= state.period:
            raise InvariantViolation("Period must move forward")
        return [
            EventEnvelope(
                event_type="PeriodReset",
                schema_version=1,
                occurred_at="now",
                payload={"period": cmd.new_period},
            )
        ]

    if isinstance(cmd, SuspendAccount):
        if state.status == "suspended":
            raise InvariantViolation("Already suspended")
        return [
            EventEnvelope(
                event_type="AccountSuspended",
                schema_version=1,
                occurred_at="now",
                payload={"reason": cmd.reason},
            )
        ]

    if isinstance(cmd, ReinstateAccount):
        if state.status == "active":
            raise InvariantViolation("Already active")
        return [
            EventEnvelope(
                event_type="AccountReinstated",
                schema_version=1,
                occurred_at="now",
                payload={},
            )
        ]

    raise InvariantViolation(f"Unknown command: {type(cmd).__name__}")
