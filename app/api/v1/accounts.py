from pydantic import BaseModel

from app.domain.commands import CreateAccount
from app.domain.errors import InvariantViolation
from app.infra.event_store.repository import SqlAlchemyEventStore
from app.services.account_service import AccountService

class CreateAccountRequest(BaseModel):
    account_id: str
    initial_plan_id: str
    period: str  # "YYYY-MM"

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
        # already exists etc.
        raise HTTPException(status_code=409, detail=str(e))
    return {"account_id": req.account_id, "stream_version": version}
