from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.domain.commands import CreateAccount, RecordUsage, ReinstateAccount, SuspendAccount
from app.domain.errors import InvariantViolation, NotFound
from app.infra.event_store.repository import SqlAlchemyEventStore
from app.services.account_service import AccountService

router = APIRouter()


class CreateAccountRequest(BaseModel):
    account_id: str
    initial_plan_id: str
    period: str  # "YYYY-MM"


class RecordUsageRequest(BaseModel):
    meter: str  # keep simple for now
    units: int
    occurred_at: str  # ISO8601, e.g. 2026-01-28T01:00:00Z


class SuspendAccountRequest(BaseModel):
    reason: str


@router.post("", status_code=201)
def create_account(req: CreateAccountRequest) -> dict:
    svc = AccountService(SqlAlchemyEventStore())
    try:
        version = svc.create_account(
            CreateAccount(
                account_id=req.account_id,
                initial_plan_id=req.initial_plan_id,
                period=req.period,
            )
        )
    except InvariantViolation as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
    return {"account_id": req.account_id, "stream_version": version}


@router.get("/{account_id}")
def get_account(account_id: str) -> dict:
    svc = AccountService(SqlAlchemyEventStore())
    try:
        return svc.get_state(account_id)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from None


@router.get("/{account_id}/events")
def list_events(account_id: str) -> dict:
    svc = AccountService(SqlAlchemyEventStore())
    return {"account_id": account_id, "events": svc.list_events(account_id)}


@router.post("/{account_id}/usage")
def record_usage(
    account_id: str,
    req: RecordUsageRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    svc = AccountService(SqlAlchemyEventStore())
    try:
        version = svc.record_usage(
            RecordUsage(
                account_id=account_id,
                meter=req.meter,  # we’ll tighten to Literal later
                units=req.units,
                occurred_at=req.occurred_at,
                idempotency_key=idempotency_key,
            )
        )
        return {"account_id": account_id, "stream_version": version}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except InvariantViolation as e:
        raise HTTPException(status_code=409, detail=str(e)) from None


@router.post("/{account_id}/suspend")
def suspend_account(account_id: str, req: SuspendAccountRequest) -> dict:
    svc = AccountService(SqlAlchemyEventStore())
    try:
        version = svc.suspend_account(SuspendAccount(account_id=account_id, reason=req.reason))
        return {"account_id": account_id, "stream_version": version}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except InvariantViolation as e:
        raise HTTPException(status_code=409, detail=str(e)) from None


@router.post("/{account_id}/reinstate")
def reinstate_account(account_id: str) -> dict:
    svc = AccountService(SqlAlchemyEventStore())
    try:
        version = svc.reinstate_account(ReinstateAccount(account_id=account_id))
        return {"account_id": account_id, "stream_version": version}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except InvariantViolation as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
