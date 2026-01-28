from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.infra.db.init_db import init_db

app = FastAPI(title="QuotaLedger", version="0.1.0")
app.include_router(v1_router, prefix="/v1")


@app.on_event("startup")
def _startup() -> None:
    init_db()
