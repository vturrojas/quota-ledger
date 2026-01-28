from __future__ import annotations

from app.domain.aggregate import apply_event, decide
from app.domain.commands import (
    CreateAccount,
    RecordUsage,
    ReinstateAccount,
    SuspendAccount,
)
from app.domain.errors import InvariantViolation, NotFound
from app.domain.types import AccountQuotaState
from app.infra.db.session import SessionLocal
from app.infra.event_store.repository import SqlAlchemyEventStore
from app.infra.projections.models import AccountCurrent


class AccountService:
    def __init__(self, store: SqlAlchemyEventStore) -> None:
        self.store = store

    def create_account(self, cmd: CreateAccount) -> int:
        history = self.store.load_stream(cmd.account_id)
        state = AccountQuotaState()
        for e in history:
            state = apply_event(state, e)

        new_events = decide(state, cmd)

        return self.store.append(
            stream_id=cmd.account_id,
            expected_version=len(history),
            events=new_events,
        )

    def record_usage(self, cmd: RecordUsage) -> int:
        history = self.store.load_stream(cmd.account_id)
        state = AccountQuotaState()
        for e in history:
            state = apply_event(state, e)

        if not state.exists:
            raise NotFound("Account does not exist")

        new_events = decide(state, cmd)

        return self.store.append(
            stream_id=cmd.account_id,
            expected_version=len(history),
            events=new_events,
        )

    def suspend_account(self, cmd: SuspendAccount) -> int:
        history = self.store.load_stream(cmd.account_id)
        state = AccountQuotaState()
        for e in history:
            state = apply_event(state, e)

        if not state.exists:
            raise NotFound("Account does not exist")

        new_events = decide(state, cmd)

        return self.store.append(
            stream_id=cmd.account_id,
            expected_version=len(history),
            events=new_events,
        )

    def reinstate_account(self, cmd: ReinstateAccount) -> int:
        history = self.store.load_stream(cmd.account_id)
        state = AccountQuotaState()
        for e in history:
            state = apply_event(state, e)

        if not state.exists:
            raise NotFound("Account does not exist")

        new_events = decide(state, cmd)

        return self.store.append(
            stream_id=cmd.account_id,
            expected_version=len(history),
            events=new_events,
        )

    def get_state(self, account_id: str) -> dict:
        # Prefer projection
        with SessionLocal() as session:
            proj = session.get(AccountCurrent, account_id)
            if proj is not None:
                return {
                    "account_id": account_id,
                    "exists": True,
                    "status": proj.status,
                    "plan_id": proj.plan_id,
                    "period": proj.period,
                    "used": proj.used or {},
                    "stream_version": proj.stream_version,
                    "source": "projection",
                }

        # Fallback to replay
        history = self.store.load_stream(account_id)
        state = AccountQuotaState()
        for e in history:
            state = apply_event(state, e)

        if not state.exists:
            raise NotFound("Account does not exist")

        return {
            "account_id": account_id,
            "exists": True,
            "status": state.status,
            "plan_id": state.plan_id,
            "period": state.period,
            "used": state.used or {},
            "stream_version": len(history),
            "source": "replay",
        }

    def list_events(self, account_id: str) -> list[dict]:
        events = self.store.load_stream(account_id)
        return [
            {
                "type": e.event_type,
                "schema_version": e.schema_version,
                "occurred_at": e.occurred_at.isoformat() if hasattr(e.occurred_at, "isoformat") else str(e.occurred_at),
                "idempotency_key": e.idempotency_key,
                "payload": e.payload,
            }
            for e in events
        ]
