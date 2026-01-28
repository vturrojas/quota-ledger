from fastapi import APIRouter

from app.api.v1.routes import accounts

router = APIRouter()
router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
