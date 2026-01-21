"""Unit tests for LangGraph HTTP client.

These tests verify the client's HTTP communication with the LangGraph Dev Server,
including request formatting, error handling, and response parsing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from yonca.langgraph.client import LangGraphClient

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
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    mock = AsyncMock(spec=httpx.AsyncClient)
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock()
    return mock


# ============================================
# CLIENT INITIALIZATION TESTS
# ============================================


def test_client_init_default():
    """Test client initialization with defaults."""
    client = LangGraphClient()

    assert client.base_url == "http://localhost:2024"
    assert client.graph_id == "yonca_agent"
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


# ============================================
# INVOKE TESTS
# ============================================


@pytest.mark.asyncio
async def test_invoke_success(client, mock_httpx_client):
    """Test successful graph invocation."""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={"messages": [{"content": "Response text", "role": "assistant"}]}
    )
    mock_httpx_client.post.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await client.invoke(
            message="Test message",
            thread_id="test-thread",
            user_id="test-user",
        )

    assert isinstance(result, dict)
    assert "messages" in result
    assert result["messages"][0]["content"] == "Response text"
    assert result["messages"][0]["role"] == "assistant"


@pytest.mark.asyncio
async def test_invoke_with_all_parameters(client, mock_httpx_client):
    """Test graph invocation with all optional parameters."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"messages": [{"role": "assistant", "content": "Response"}]}
    mock_httpx_client.post.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await client.invoke(
            message="Test message",
            thread_id="test-thread",
            user_id="test-user",
            session_id="test-session",
            language="az",
        )

    assert result["messages"][0]["content"] == "Response"

    # Verify all parameters were passed
    call_args = mock_httpx_client.post.call_args
    payload = call_args[1]["json"]["input"]
    assert payload["current_input"] == "Test message"
    assert payload["user_id"] == "test-user"
    assert payload["session_id"] == "test-session"
    assert payload["language"] == "az"


@pytest.mark.asyncio
async def test_invoke_http_error(client, mock_httpx_client):
    """Test graph invocation HTTP error handling."""
    # Create a proper HTTP error response
    error_response = httpx.Response(
        status_code=500,
        request=httpx.Request("POST", "http://localhost:2024/runs/stream"),
    )
    mock_httpx_client.post.return_value = error_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        # The client should raise HTTPStatusError for 500 status
        response = httpx.Response(
            status_code=500,
            request=httpx.Request("POST", "http://localhost:2024/runs/stream"),
        )
        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=response.request,
            response=response,
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.invoke(
                message="Test",
                thread_id="test-thread",
                user_id="test-user",
            )


@pytest.mark.asyncio
async def test_invoke_connection_error(client, mock_httpx_client):
    """Test graph invocation with connection error."""
    mock_httpx_client.post.side_effect = httpx.ConnectError("Connection failed")

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        with pytest.raises(httpx.ConnectError):
            await client.invoke(
                message="Test",
                thread_id="test-thread",
                user_id="test-user",
            )


@pytest.mark.asyncio
async def test_invoke_no_messages(client, mock_httpx_client):
    """Test graph invocation when response has no messages."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"messages": []}
    mock_httpx_client.post.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await client.invoke(
            message="Test",
            thread_id="test-thread",
            user_id="test-user",
        )

    assert result == ""


# ============================================
# STREAM TESTS
# ============================================


@pytest.mark.asyncio
async def test_stream_success(client, mock_httpx_client):
    """Test successful graph streaming."""

    # Mock streaming response
    async def mock_stream_iter():
        yield b'data: {"messages": [{"content": "Chunk 1"}]}\n\n'
        yield b'data: {"messages": [{"content": "Chunk 2"}]}\n\n'

    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    mock_response.aiter_bytes = mock_stream_iter

    mock_httpx_client.stream.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        chunks = []
        async for chunk in client.stream(
            message="Test",
            thread_id="test-thread",
            user_id="test-user",
        ):
            chunks.append(chunk)

    assert len(chunks) == 2
    assert "Chunk 1" in chunks[0]
    assert "Chunk 2" in chunks[1]


@pytest.mark.asyncio
async def test_stream_empty_response(client, mock_httpx_client):
    """Test graph streaming with empty response."""

    async def mock_stream_iter():
        return
        yield  # Make it a generator

    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    mock_response.aiter_bytes = mock_stream_iter

    mock_httpx_client.stream.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        chunks = []
        async for chunk in client.stream(
            message="Test",
            thread_id="test-thread",
            user_id="test-user",
        ):
            chunks.append(chunk)

    assert len(chunks) == 0


# ============================================
# THREAD MANAGEMENT TESTS
# ============================================


@pytest.mark.asyncio
async def test_ensure_thread_success(client, mock_httpx_client):
    """Test successful thread creation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"thread_id": "new-thread-123"}
    mock_httpx_client.post.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        thread_id = await client.ensure_thread(
            user_id="test-user",
            farm_id="test-farm",
        )

    assert thread_id == "new-thread-123"


@pytest.mark.asyncio
async def test_ensure_thread_minimal(client, mock_httpx_client):
    """Test thread creation with minimal parameters."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"thread_id": "new-thread-456"}
    mock_httpx_client.post.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        thread_id = await client.ensure_thread(user_id="test-user")

    assert thread_id == "new-thread-456"


# ============================================
# HEALTH CHECK TESTS
# ============================================


@pytest.mark.asyncio
async def test_health_success(client, mock_httpx_client):
    """Test successful health check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "healthy"}
    mock_httpx_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        is_healthy = await client.health()

    assert is_healthy is True


@pytest.mark.asyncio
async def test_health_unhealthy(client, mock_httpx_client):
    """Test health check when server is unhealthy."""
    mock_httpx_client.get.side_effect = httpx.ConnectError("Connection failed")

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        is_healthy = await client.health()

    assert is_healthy is False


@pytest.mark.asyncio
async def test_health_http_error(client, mock_httpx_client):
    """Test health check with HTTP error."""
    mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
        message="Server error",
        request=MagicMock(),
        response=MagicMock(status_code=500),
    )

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        is_healthy = await client.health()

    assert is_healthy is False


# ============================================
# URL CONSTRUCTION TESTS
# ============================================


def test_graph_url_construction(client):
    """Test graph endpoint URL construction."""
    # Test with default values
    client = LangGraphClient()
    assert client.base_url == "http://localhost:2024"
    assert client.graph_id == "yonca_agent"

    # Verify URL would be: http://localhost:2024/runs/stream


def test_custom_base_url_construction():
    """Test URL construction with custom base URL."""
    client = LangGraphClient(base_url="https://api.example.com:8080")
    assert client.base_url == "https://api.example.com:8080"


# ============================================
# TIMEOUT TESTS
# ============================================


@pytest.mark.asyncio
async def test_invoke_timeout(client, mock_httpx_client):
    """Test graph invocation timeout."""
    mock_httpx_client.post.side_effect = httpx.TimeoutException("Request timeout")

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        with pytest.raises(httpx.TimeoutException):
            await client.invoke(
                message="Test",
                thread_id="test-thread",
                user_id="test-user",
            )


# ============================================
# PAYLOAD CONSTRUCTION TESTS
# ============================================


@pytest.mark.asyncio
async def test_invoke_payload_structure(client, mock_httpx_client):
    """Test that invoke constructs correct payload structure."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"messages": [{"role": "assistant", "content": "Response"}]}
    mock_httpx_client.post.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        await client.invoke(
            message="Test message",
            thread_id="test-thread",
            user_id="test-user",
            language="az",
        )

    # Get the call arguments
    call_args = mock_httpx_client.post.call_args
    payload = call_args[1]["json"]

    # Verify payload structure
    assert "input" in payload
    assert "config" in payload
    assert "stream_mode" in payload

    # Verify input structure
    assert payload["input"]["user_input"] == "Test message"
    assert payload["input"]["user_id"] == "test-user"
    assert payload["input"]["language"] == "az"

    # Verify config structure
    assert "configurable" in payload["config"]
    assert payload["config"]["configurable"]["thread_id"] == "test-thread"
