"""Smoke tests against the FastAPI app via TestClient."""


def test_health_endpoint_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.text == "OK"


def test_landing_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Bottling Line" in response.text


def test_openapi_schema_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["info"]["title"] == "Bottling Line Data Capture"
