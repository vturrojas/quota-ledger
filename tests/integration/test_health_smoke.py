from fastapi.testclient import TestClient

from app.main import app


def test_app_starts() -> None:
    client = TestClient(app)
    r = client.get("/docs")
    assert r.status_code == 200
