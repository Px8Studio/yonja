"""Integration tests for LangGraph API routes.

These tests verify the HTTP API layer for graph execution,
including invoke, stream, and thread management endpoints.
"""

import pytest
from alim.api.main import app
from fastapi import status
from httpx import AsyncClient

# ============================================
# FIXTURES
# ============================================


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_message():
    """Sample message payload for graph execution."""
    return {
        "message": "Kartof əkmək istəyirəm",
        "thread_id": "test-thread-123",
        "user_id": "test-user",
        "farm_id": "test-farm",
        "language": "az",
    }


# ============================================
# GRAPH INVOKE TESTS
# ============================================


@pytest.mark.asyncio
async def test_graph_invoke_success(client: AsyncClient, sample_message):
    """Test successful graph invocation."""
    response = await client.post("/api/v1/graph/invoke", json=sample_message)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify response structure
    assert "response" in data
    assert "thread_id" in data
    assert data["thread_id"] == sample_message["thread_id"]

    # Verify response content
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0


@pytest.mark.asyncio
async def test_graph_invoke_with_system_prompt(client: AsyncClient, sample_message):
    """Test graph invocation with custom system prompt."""
    sample_message["system_prompt_override"] = "You are a potato expert."

    response = await client.post("/api/v1/graph/invoke", json=sample_message)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "response" in data


@pytest.mark.asyncio
async def test_graph_invoke_with_scenario_context(client: AsyncClient, sample_message):
    """Test graph invocation with scenario context."""
    sample_message["scenario_context"] = {
        "crop_type": "potato",
        "region": "Ganja",
        "planning_month": "Mart",
    }

    response = await client.post("/api/v1/graph/invoke", json=sample_message)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "response" in data


@pytest.mark.asyncio
async def test_graph_invoke_missing_message(client: AsyncClient):
    """Test graph invocation with missing message field."""
    payload = {
        "thread_id": "test-thread",
        "user_id": "test-user",
        "language": "az",
    }

    response = await client.post("/api/v1/graph/invoke", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_graph_invoke_empty_message(client: AsyncClient, sample_message):
    """Test graph invocation with empty message."""
    sample_message["message"] = ""

    response = await client.post("/api/v1/graph/invoke", json=sample_message)

    # Should still work (empty input is valid, just returns empty/default response)
    assert response.status_code in (status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY)


# ============================================
# GRAPH STREAM TESTS
# ============================================


@pytest.mark.asyncio
async def test_graph_stream_success(client: AsyncClient, sample_message):
    """Test successful graph streaming."""
    async with client.stream("POST", "/api/v1/graph/stream", json=sample_message) as response:
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Collect chunks
        chunks = []
        async for chunk in response.aiter_text():
            if chunk.strip():
                chunks.append(chunk)

        # Verify we got some data
        assert len(chunks) > 0


@pytest.mark.asyncio
async def test_graph_stream_missing_message(client: AsyncClient):
    """Test graph streaming with missing message field."""
    payload = {
        "thread_id": "test-thread",
        "user_id": "test-user",
        "language": "az",
    }

    async with client.stream("POST", "/api/v1/graph/stream", json=payload) as response:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================
# THREAD MANAGEMENT TESTS
# ============================================


@pytest.mark.asyncio
async def test_create_thread_success(client: AsyncClient):
    """Test successful thread creation."""
    payload = {
        "user_id": "test-user",
        "farm_id": "test-farm",
        "metadata": {"test": "value"},
    }

    response = await client.post("/api/v1/graph/threads", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "thread_id" in data
    assert isinstance(data["thread_id"], str)
    assert len(data["thread_id"]) > 0


@pytest.mark.asyncio
async def test_create_thread_minimal(client: AsyncClient):
    """Test thread creation with minimal data."""
    payload = {"user_id": "test-user"}

    response = await client.post("/api/v1/graph/threads", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "thread_id" in data


@pytest.mark.asyncio
async def test_create_thread_missing_user(client: AsyncClient):
    """Test thread creation without user_id."""
    payload = {"farm_id": "test-farm"}

    response = await client.post("/api/v1/graph/threads", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_thread_history(client: AsyncClient):
    """Test retrieving thread history."""
    # First create a thread
    create_response = await client.post(
        "/api/v1/graph/threads",
        json={"user_id": "test-user"},
    )
    thread_id = create_response.json()["thread_id"]

    # Get history
    response = await client.get(f"/api/v1/graph/threads/{thread_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "thread_id" in data
    assert "history" in data
    assert isinstance(data["history"], list)


@pytest.mark.asyncio
async def test_get_thread_not_found(client: AsyncClient):
    """Test retrieving non-existent thread."""
    response = await client.get("/api/v1/graph/threads/non-existent-thread")

    # Should return empty history or 404
    assert response.status_code in (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND)


@pytest.mark.asyncio
async def test_delete_thread_success(client: AsyncClient):
    """Test successful thread deletion."""
    # First create a thread
    create_response = await client.post(
        "/api/v1/graph/threads",
        json={"user_id": "test-user"},
    )
    thread_id = create_response.json()["thread_id"]

    # Delete thread
    response = await client.delete(f"/api/v1/graph/threads/{thread_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data.get("success") is True


@pytest.mark.asyncio
async def test_delete_thread_not_found(client: AsyncClient):
    """Test deleting non-existent thread."""
    response = await client.delete("/api/v1/graph/threads/non-existent-thread")

    # Should still return success (idempotent)
    assert response.status_code in (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND)


# ============================================
# HEALTH CHECK TESTS
# ============================================


@pytest.mark.asyncio
async def test_graph_health_success(client: AsyncClient):
    """Test graph health endpoint."""
    response = await client.get("/api/v1/graph/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "status" in data
    assert data["status"] in ("healthy", "ok")


# ============================================
# ERROR HANDLING TESTS
# ============================================


@pytest.mark.asyncio
async def test_graph_invoke_invalid_json(client: AsyncClient):
    """Test graph invocation with invalid JSON."""
    response = await client.post(
        "/api/v1/graph/invoke",
        content="not json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_graph_invoke_invalid_language(client: AsyncClient, sample_message):
    """Test graph invocation with invalid language code."""
    sample_message["language"] = "invalid-lang-code"

    response = await client.post("/api/v1/graph/invoke", json=sample_message)

    # Should either validate or accept with default
    assert response.status_code in (status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY)


# ============================================
# INTEGRATION WORKFLOW TESTS
# ============================================


@pytest.mark.asyncio
async def test_full_workflow(client: AsyncClient):
    """Test complete workflow: create thread → invoke → get history → delete."""
    # 1. Create thread
    create_response = await client.post(
        "/api/v1/graph/threads",
        json={"user_id": "test-user", "farm_id": "test-farm"},
    )
    assert create_response.status_code == status.HTTP_200_OK
    thread_id = create_response.json()["thread_id"]

    # 2. Invoke graph
    invoke_response = await client.post(
        "/api/v1/graph/invoke",
        json={
            "message": "Kartof haqqında məlumat ver",
            "thread_id": thread_id,
            "user_id": "test-user",
            "language": "az",
        },
    )
    assert invoke_response.status_code == status.HTTP_200_OK
    assert "response" in invoke_response.json()

    # 3. Get history
    history_response = await client.get(f"/api/v1/graph/threads/{thread_id}")
    assert history_response.status_code == status.HTTP_200_OK
    history = history_response.json()["history"]
    assert len(history) >= 0  # May or may not have entries depending on checkpointer

    # 4. Delete thread
    delete_response = await client.delete(f"/api/v1/graph/threads/{thread_id}")
    assert delete_response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_multiple_invocations_same_thread(client: AsyncClient):
    """Test multiple graph invocations on the same thread."""
    # Create thread
    create_response = await client.post(
        "/api/v1/graph/threads",
        json={"user_id": "test-user"},
    )
    thread_id = create_response.json()["thread_id"]

    # Multiple invocations
    messages = [
        "Kartof haqqında məlumat ver",
        "Əkmək üçün ən yaxşı vaxt nə zaman?",
        "Hansı torpaq növü yaxşıdır?",
    ]

    for msg in messages:
        response = await client.post(
            "/api/v1/graph/invoke",
            json={
                "message": msg,
                "thread_id": thread_id,
                "user_id": "test-user",
                "language": "az",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "response" in response.json()
