import os

from fastapi.testclient import TestClient

from app.main import app


def test_projection_updates_on_append() -> None:
    assert os.getenv("DATABASE_URL"), "DATABASE_URL must be set for integration tests"
    client = TestClient(app)

    client.post(
        "/v1/accounts", json={"account_id": "p1", "initial_plan_id": "basic", "period": "2026-01"}
    )

    r = client.post(
        "/v1/accounts/p1/usage",
        headers={"Idempotency-Key": "p1-u1"},
        json={"meter": "api_calls", "units": 3, "occurred_at": "2026-01-28T01:30:00Z"},
    )
    assert r.status_code == 200, r.text

    s = client.get("/v1/accounts/p1").json()
    assert s["source"] == "projection"
    assert s["used"]["api_calls"] == 3
