"""Unit tests for LangGraph HTTP client.

These tests verify the client's HTTP communication with the LangGraph Dev Server,
including request formatting, error handling, and response parsing.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from alim.langgraph.client import LangGraphClient, LangGraphClientError

# ============================================
# FIXTURES
# ============================================


@pytest.fixture
def client():
    """Create LangGraph client instance."""
    return LangGraphClient(
        base_url="http://localhost:2024",
        graph_id="test_graph",
    )


@pytest.fixture
def mock_async_client():
    """Mock httpx.AsyncClient with proper context manager support."""
    mock = AsyncMock(spec=httpx.AsyncClient)
    return mock


# ============================================
# CLIENT INITIALIZATION TESTS
# ============================================


def test_client_init_default():
    """Test client initialization with defaults."""
    client = LangGraphClient()

    assert client.base_url == "http://localhost:2024"
    assert client.graph_id == "alim_agent"
    assert client.timeout == 120.0


def test_client_init_custom():
    """Test client initialization with custom values."""
    client = LangGraphClient(
        base_url="http://custom:3000",
        graph_id="custom_graph",
        timeout=60.0,
    )

    assert client.base_url == "http://custom:3000"
    assert client.graph_id == "custom_graph"
    assert client.timeout == 60.0


def test_client_strips_trailing_slash():
    """Test client strips trailing slash from base URL."""
    client = LangGraphClient(base_url="http://localhost:2024/")

    assert client.base_url == "http://localhost:2024"


def test_generate_thread_id():
    """Test thread ID generation."""
    thread_id = LangGraphClient.generate_thread_id()
    assert thread_id.startswith("thread_")
    assert len(thread_id) == 19  # "thread_" + 12 hex chars


# ============================================
# CONTEXT MANAGER TESTS
# ============================================


@pytest.mark.asyncio
async def test_context_manager_creates_client():
    """Test async context manager initializes HTTP client."""
    client = LangGraphClient()
    assert client._client is None

    async with client:
        assert client._client is not None


@pytest.mark.asyncio
async def test_context_manager_closes_client():
    """Test async context manager closes HTTP client on exit."""
    client = LangGraphClient()
    async with client:
        pass  # HTTP client was created
    assert client._client is None


def test_client_property_raises_without_context():
    """Test accessing client property without context raises error."""
    client = LangGraphClient()
    with pytest.raises(RuntimeError, match="not initialized"):
        _ = client.client


# ============================================
# HEALTH CHECK TESTS
# ============================================


@pytest.mark.asyncio
async def test_health_success(client, mock_async_client):
    """Test successful health check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_response.raise_for_status = MagicMock()
    mock_async_client.get = AsyncMock(return_value=mock_response)

    client._client = mock_async_client

    result = await client.health()
    assert result == {"status": "ok"}
    mock_async_client.get.assert_called_once_with("/health")


@pytest.mark.asyncio
async def test_is_healthy_returns_true(client, mock_async_client):
    """Test is_healthy returns True when status is ok."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "ok"}
    mock_response.raise_for_status = MagicMock()
    mock_async_client.get = AsyncMock(return_value=mock_response)

    client._client = mock_async_client

    result = await client.is_healthy()
    assert result is True


@pytest.mark.asyncio
async def test_is_healthy_returns_false_on_error(client, mock_async_client):
    """Test is_healthy returns False on connection error."""
    mock_async_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    client._client = mock_async_client

    result = await client.is_healthy()
    assert result is False


@pytest.mark.asyncio
async def test_health_raises_on_http_error(client, mock_async_client):
    """Test health() raises LangGraphClientError on HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error",
        request=MagicMock(),
        response=MagicMock(status_code=500),
    )
    mock_async_client.get = AsyncMock(return_value=mock_response)
    client._client = mock_async_client

    with pytest.raises(LangGraphClientError, match="Health check failed"):
        await client.health()


# ============================================
# THREAD MANAGEMENT TESTS
# ============================================


@pytest.mark.asyncio
async def test_create_thread_success(client, mock_async_client):
    """Test successful thread creation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"thread_id": "new-thread-123"}
    mock_response.raise_for_status = MagicMock()
    mock_async_client.post = AsyncMock(return_value=mock_response)

    client._client = mock_async_client

    thread_id = await client.create_thread()
    assert thread_id == "new-thread-123"
    mock_async_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_create_thread_with_metadata(client, mock_async_client):
    """Test thread creation with metadata."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "thread-with-meta"}
    mock_response.raise_for_status = MagicMock()
    mock_async_client.post = AsyncMock(return_value=mock_response)

    client._client = mock_async_client

    thread_id = await client.create_thread(metadata={"user_id": "test-user"})
    assert thread_id == "thread-with-meta"

    # Verify metadata was passed
    call_args = mock_async_client.post.call_args
    assert call_args[1]["json"]["metadata"]["user_id"] == "test-user"


@pytest.mark.asyncio
async def test_ensure_thread_returns_existing(client, mock_async_client):
    """Test ensure_thread returns existing thread ID without API call."""
    client._client = mock_async_client

    thread_id = await client.ensure_thread("existing-thread-123")
    assert thread_id == "existing-thread-123"
    mock_async_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_thread_creates_new_when_none(client, mock_async_client):
    """Test ensure_thread creates new thread when None."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "new-thread-456"}
    mock_response.raise_for_status = MagicMock()
    mock_async_client.post = AsyncMock(return_value=mock_response)

    client._client = mock_async_client

    thread_id = await client.ensure_thread(None)
    assert thread_id == "new-thread-456"
    mock_async_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_thread_state_success(client, mock_async_client):
    """Test getting thread state."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"messages": [], "user_id": "test"}
    mock_response.raise_for_status = MagicMock()
    mock_async_client.get = AsyncMock(return_value=mock_response)

    client._client = mock_async_client

    state = await client.get_thread_state("thread-123")
    assert state == {"messages": [], "user_id": "test"}
    mock_async_client.get.assert_called_once_with("/threads/thread-123/state")


@pytest.mark.asyncio
async def test_get_thread_state_not_found(client, mock_async_client):
    """Test getting state for non-existent thread."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=MagicMock(status_code=404)
    )
    mock_async_client.get = AsyncMock(return_value=mock_response)

    client._client = mock_async_client

    with pytest.raises(LangGraphClientError, match="Thread not found"):
        await client.get_thread_state("nonexistent-thread")


@pytest.mark.asyncio
async def test_delete_thread_success(client, mock_async_client):
    """Test successful thread deletion."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_async_client.delete = AsyncMock(return_value=mock_response)

    client._client = mock_async_client

    result = await client.delete_thread("thread-to-delete")
    assert result is True
    mock_async_client.delete.assert_called_once_with("/threads/thread-to-delete")


@pytest.mark.asyncio
async def test_delete_thread_not_found_returns_false(client, mock_async_client):
    """Test deleting non-existent thread returns False."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=MagicMock(status_code=404)
    )
    mock_async_client.delete = AsyncMock(return_value=mock_response)

    client._client = mock_async_client

    result = await client.delete_thread("nonexistent")
    assert result is False


# ============================================
# INVOKE TESTS
# ============================================


@pytest.mark.asyncio
async def test_invoke_success(client, mock_async_client):
    """Test successful graph invocation."""
    # Mock create_thread response
    create_thread_response = MagicMock()
    create_thread_response.json.return_value = {"id": "test-thread"}
    create_thread_response.raise_for_status = MagicMock()

    # Mock invoke response
    invoke_response = MagicMock()
    invoke_response.json.return_value = {
        "messages": [{"role": "assistant", "content": "Hello!"}],
        "current_response": "Hello!",
    }
    invoke_response.raise_for_status = MagicMock()

    mock_async_client.post = AsyncMock(side_effect=[create_thread_response, invoke_response])
    client._client = mock_async_client

    result = await client.invoke(
        input_state={"messages": [{"role": "user", "content": "Hi"}]},
        thread_id=None,
    )

    assert result["current_response"] == "Hello!"


@pytest.mark.asyncio
async def test_invoke_with_existing_thread(client, mock_async_client):
    """Test invoke with existing thread ID."""
    invoke_response = MagicMock()
    invoke_response.json.return_value = {"current_response": "Response text"}
    invoke_response.raise_for_status = MagicMock()

    mock_async_client.post = AsyncMock(return_value=invoke_response)
    client._client = mock_async_client

    result = await client.invoke(
        input_state={"messages": []},
        thread_id="existing-thread",
    )

    assert result["current_response"] == "Response text"
    # Only one POST call (invoke), no thread creation
    assert mock_async_client.post.call_count == 1


@pytest.mark.asyncio
async def test_invoke_with_config(client, mock_async_client):
    """Test invoke passes config correctly."""
    invoke_response = MagicMock()
    invoke_response.json.return_value = {}
    invoke_response.raise_for_status = MagicMock()

    mock_async_client.post = AsyncMock(return_value=invoke_response)
    client._client = mock_async_client

    await client.invoke(
        input_state={"messages": []},
        thread_id="thread-123",
        config={"metadata": {"user_id": "test-user"}},
    )

    call_args = mock_async_client.post.call_args
    assert call_args[1]["json"]["config"]["metadata"]["user_id"] == "test-user"


@pytest.mark.asyncio
async def test_invoke_http_error(client, mock_async_client):
    """Test invoke raises LangGraphClientError on HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error",
        request=MagicMock(),
        response=mock_response,
    )
    mock_async_client.post = AsyncMock(return_value=mock_response)
    client._client = mock_async_client

    with pytest.raises(LangGraphClientError, match="Graph invocation failed"):
        await client.invoke(
            input_state={"messages": []},
            thread_id="thread-123",
        )


# ============================================
# CHAT CONVENIENCE METHODS TESTS
# ============================================


@pytest.mark.asyncio
async def test_chat_convenience_method(client, mock_async_client):
    """Test high-level chat method."""
    create_thread_response = MagicMock()
    create_thread_response.json.return_value = {"id": "chat-thread"}
    create_thread_response.raise_for_status = MagicMock()

    invoke_response = MagicMock()
    invoke_response.json.return_value = {"current_response": "Chat response"}
    invoke_response.raise_for_status = MagicMock()

    mock_async_client.post = AsyncMock(side_effect=[create_thread_response, invoke_response])
    client._client = mock_async_client

    result = await client.chat(
        message="Hello, ALİM!",
        user_id="farmer-123",
    )

    assert result["current_response"] == "Chat response"


# ============================================
# THREAD ID EXTRACTION TESTS
# ============================================


class TestExtractThreadId:
    """Test thread ID extraction from various response formats."""

    def test_extract_from_thread_id_key(self):
        """Test extraction from thread_id key."""
        data = {"thread_id": "abc123"}
        assert LangGraphClient._extract_thread_id(data) == "abc123"

    def test_extract_from_id_key(self):
        """Test extraction from id key."""
        data = {"id": "xyz789"}
        assert LangGraphClient._extract_thread_id(data) == "xyz789"

    def test_extract_from_nested_thread_object(self):
        """Test extraction from nested thread object."""
        data = {"thread": {"id": "nested-id"}}
        assert LangGraphClient._extract_thread_id(data) == "nested-id"

    def test_extract_from_nested_thread_id(self):
        """Test extraction from nested thread_id."""
        data = {"thread": {"thread_id": "nested-thread-id"}}
        assert LangGraphClient._extract_thread_id(data) == "nested-thread-id"

    def test_raises_on_missing_id(self):
        """Test raises error when no ID found."""
        data = {"other": "data"}
        with pytest.raises(LangGraphClientError, match="Could not extract"):
            LangGraphClient._extract_thread_id(data)


# ============================================
# URL CONSTRUCTION TESTS
# ============================================


def test_url_construction_default():
    """Test default URL construction."""
    client = LangGraphClient()
    assert client.base_url == "http://localhost:2024"
    assert client.graph_id == "alim_agent"


def test_url_construction_custom():
    """Test custom URL construction."""
    client = LangGraphClient(
        base_url="https://langgraph.example.com:8080",
        graph_id="custom_agent",
    )
    assert client.base_url == "https://langgraph.example.com:8080"
    assert client.graph_id == "custom_agent"
