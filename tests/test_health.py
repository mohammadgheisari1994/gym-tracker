from fastapi.testclient import TestClient


def test_healthz_reports_ok(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] is True
