from alim.api.main import app
from alim.config import settings
from fastapi.testclient import TestClient

client = TestClient(app)


def test_graph_endpoints_security():
    """Verify that graph endpoints require API Key."""

    # 1. Test without key -> Should be 403 or 401
    # The dependency returns 401 for missing, 403 for invalid

    # Invoke
    response = client.post("/api/v1/graph/invoke", json={"message": "test"})
    assert response.status_code == 401

    # Stream
    response = client.post("/api/v1/graph/stream", json={"message": "test"})
    assert response.status_code == 401

    # Threads
    response = client.post("/api/v1/threads")
    assert response.status_code == 401


def test_graph_endpoints_with_invalid_key():
    """Verify that invalid key returns 403."""
    headers = {settings.api_key_header: "wrong-key"}  # pragma: allowlist secret

    response = client.post("/api/v1/graph/invoke", json={"message": "test"}, headers=headers)
    assert response.status_code == 403


def test_graph_endpoints_with_valid_key():
    """Verify that valid key is accepted (auth pass, even if downstream fails)."""
    headers = {settings.api_key_header: settings.api_key_secret}

    # We expect 422 (validation error) or 500 (downstream conn error)
    # but NOT 401/403. This proves auth layer passed.
    response = client.post("/api/v1/graph/invoke", json={}, headers=headers)

    # If json is empty, Pydantic raises 422
    assert response.status_code == 422
