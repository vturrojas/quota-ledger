import pytest

from app.domain.aggregate import apply_event, decide
from app.domain.commands import CreateAccount, RecordUsage, SuspendAccount
from app.domain.errors import InvariantViolation, NotFound
from app.domain.types import AccountQuotaState


def test_cannot_record_usage_before_create() -> None:
    state = AccountQuotaState()
    with pytest.raises(NotFound):
        decide(state, RecordUsage("a1", "api_calls", 1, "2026-01-01T00:00:00Z", "k1"))


def test_usage_units_must_be_positive() -> None:
    state = AccountQuotaState()
    events = decide(state, CreateAccount("a1", "basic", "2026-01"))
    for e in events:
        state = apply_event(state, e)

    with pytest.raises(InvariantViolation):
        decide(state, RecordUsage("a1", "api_calls", 0, "2026-01-01T00:00:00Z", "k1"))


def test_cannot_record_usage_when_suspended() -> None:
    state = AccountQuotaState()
    for e in decide(state, CreateAccount("a1", "basic", "2026-01")):
        state = apply_event(state, e)
    for e in decide(state, SuspendAccount("a1", "fraud")):
        state = apply_event(state, e)

    with pytest.raises(InvariantViolation):
        decide(state, RecordUsage("a1", "api_calls", 1, "2026-01-01T00:00:00Z", "k1"))
