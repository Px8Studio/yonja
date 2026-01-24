# tests/unit/test_mcp_client.py
"""Unit tests for MCP client layer.

Tests cover:
- Configuration loading
- HTTP communication
- Error handling
- Logging/metrics
- Timeout behavior
- Authentication headers

All tests use mocked HTTP clients to avoid network calls.
"""

from unittest.mock import AsyncMock, patch

import pytest
from alim.mcp.client import (
    MCPCallResult,
    MCPClient,
    MCPToolCall,
    close_all_mcp_clients,
    get_mcp_client,
)
from alim.mcp.config import MCPServerConfig
from httpx import AsyncClient

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
async def mock_http_client():
    """Create a mock httpx.AsyncClient."""
    mock = AsyncMock(spec=AsyncClient)
    return mock


@pytest.fixture
def mcp_tool_call():
    """Create a sample MCP tool call."""
    return MCPToolCall(
        server="openweather",
        tool="get_forecast",
        args={"latitude": 40.4, "longitude": 49.9, "days": 7},
    )


# ============================================================
# Tests: MCPCallResult
# ============================================================


class TestMCPCallResult:
    """Tests for MCPCallResult data class."""

    def test_result_success(self):
        """Test successful result creation."""
        result = MCPCallResult(
            success=True,
            data={"temperature": 25.0},
            server="openweather",
            tool_name="get_forecast",
        )

        assert result.success is True
        assert result.data["temperature"] == 25.0
        assert result.error is None
        assert result.timestamp is not None

    def test_result_error(self):
        """Test error result creation."""
        result = MCPCallResult(
            success=False,
            error="Connection timeout",
            server="openweather",
            tool_name="get_forecast",
            latency_ms=5000.0,
        )

        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.latency_ms == 5000.0

    def test_langfuse_metadata_success(self):
        """Test Langfuse metadata for successful call."""
        result = MCPCallResult(
            success=True,
            data={"temp": 25},
            server="openweather",
            tool_name="get_forecast",
            latency_ms=250.0,
        )

        metadata = result.to_langfuse_metadata()

        assert metadata["mcp_server"] == "openweather"
        assert metadata["mcp_tool"] == "get_forecast"
        assert metadata["mcp_success"] is True
        assert metadata["mcp_latency_ms"] == 250.0
        assert "mcp_error" not in metadata

    def test_langfuse_metadata_error(self):
        """Test Langfuse metadata for failed call."""
        result = MCPCallResult(
            success=False,
            error="Timeout",
            server="zekalab",
            tool_name="evaluate_irrigation_rules",
            latency_ms=2000.0,
        )

        metadata = result.to_langfuse_metadata()

        assert metadata["mcp_success"] is False
        assert metadata["mcp_error"] == "Timeout"


# ============================================================
# Tests: MCPClient
# ============================================================


class TestMCPClient:
    """Tests for MCPClient class."""

    @pytest.mark.asyncio
    async def test_client_disabled_server(self):
        """Test client behavior when server is disabled."""
        with patch("yonca.mcp.client.get_server_config", return_value=None):
            client = MCPClient("disabled_server")
            assert client.enabled is False

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with config."""
        config = MCPServerConfig(
            enabled=True,
            url="http://localhost:7777",
            timeout_ms=2000,
        )

        with patch("yonca.mcp.client.get_server_config", return_value=config):
            client = MCPClient("zekalab")
            assert client.enabled is True
            assert client.server_name == "zekalab"

    @pytest.mark.asyncio
    async def test_build_headers_with_api_key(self):
        """Test header construction with API key."""
        config = MCPServerConfig(
            enabled=True,
            url="https://openweather.example.com",
            api_key="test_key_12345",  # pragma: allowlist secret
        )

        client = MCPClient("openweather")
        client.config = config

        headers = client._build_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test_key_12345"

    @pytest.mark.asyncio
    async def test_build_headers_with_secret(self):
        """Test header construction with shared secret."""
        config = MCPServerConfig(
            enabled=True,
            url="http://localhost:7777",
            secret="dev_secret",  # pragma: allowlist secret
        )

        client = MCPClient("zekalab")
        client.config = config

        headers = client._build_headers()

        assert headers["X-Secret"] == "dev_secret"  # pragma: allowlist secret

    @pytest.mark.asyncio
    async def test_call_tool_disabled_server(self):
        """Test tool call on disabled server."""
        client = MCPClient("disabled_server")
        client.enabled = False

        call = MCPToolCall(
            server="disabled_server",
            tool="some_tool",
            args={"test": "value"},
        )

        result = await client.call_tool(call)

        assert result.success is False
        assert "disabled" in result.error.lower()

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mock_http_client):
        """Test successful tool call."""
        config = MCPServerConfig(
            enabled=True,
            url="http://localhost:7777",
            timeout_ms=2000,
        )

        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "temperature": 25.0,
            "humidity": 60,
        }

        mock_http_client.post = AsyncMock(return_value=mock_response)

        client = MCPClient("zekalab")
        client.config = config
        client._http_client = mock_http_client

        call = MCPToolCall(
            server="zekalab",
            tool="evaluate_irrigation_rules",
            args={"farm_id": "farm_123"},
        )

        result = await client.call_tool(call)

        assert result.success is True
        assert result.data["temperature"] == 25.0
        assert result.latency_ms >= 0

        # Verify HTTP call
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert "/tools/evaluate_irrigation_rules" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_call_tool_http_error(self, mock_http_client):
        """Test tool call with HTTP error."""
        import httpx

        config = MCPServerConfig(
            enabled=True,
            url="http://localhost:7777",
            timeout_ms=2000,
        )

        # Mock HTTP error
        error_response = AsyncMock()
        error_response.status_code = 500
        mock_http_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server error",
                request=None,
                response=error_response,
            )
        )

        client = MCPClient("zekalab")
        client.config = config
        client._http_client = mock_http_client

        call = MCPToolCall(server="zekalab", tool="test", args={})
        result = await client.call_tool(call)

        assert result.success is False
        assert "Server error" in result.error or "HTTP" in result.error

    @pytest.mark.asyncio
    async def test_call_tool_timeout(self, mock_http_client):
        """Test tool call with timeout."""
        import httpx

        config = MCPServerConfig(
            enabled=True,
            url="http://localhost:7777",
            timeout_ms=500,
        )

        mock_http_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))

        client = MCPClient("zekalab")
        client.config = config
        client._http_client = mock_http_client

        call = MCPToolCall(server="zekalab", tool="test", args={})
        result = await client.call_tool(call)

        assert result.success is False
        assert "Timeout" in result.error


# ============================================================
# Tests: Factory Functions
# ============================================================


class TestMCPFactory:
    """Tests for factory functions."""

    @pytest.mark.asyncio
    async def test_get_mcp_client_singleton(self):
        """Test that get_mcp_client returns singleton."""
        await close_all_mcp_clients()

        config = MCPServerConfig(
            enabled=True,
            url="http://localhost:7777",
        )

        with patch("yonca.mcp.client.get_server_config", return_value=config):
            client1 = await get_mcp_client("zekalab")
            client2 = await get_mcp_client("zekalab")

            assert client1 is client2

        await close_all_mcp_clients()

    @pytest.mark.asyncio
    async def test_get_mcp_client_different_servers(self):
        """Test getting clients for different servers."""
        await close_all_mcp_clients()

        config = MCPServerConfig(
            enabled=True,
            url="http://localhost:7777",
        )

        with patch("yonca.mcp.client.get_server_config", return_value=config):
            zekalab_client = await get_mcp_client("zekalab")
            openweather_client = await get_mcp_client("openweather")

            assert zekalab_client.server_name == "zekalab"
            assert openweather_client.server_name == "openweather"
            assert zekalab_client is not openweather_client

        await close_all_mcp_clients()

    @pytest.mark.asyncio
    async def test_close_all_clients(self):
        """Test closing all MCP clients."""
        await close_all_mcp_clients()

        config = MCPServerConfig(
            enabled=True,
            url="http://localhost:7777",
        )

        with patch("yonca.mcp.client.get_server_config", return_value=config):
            client = await get_mcp_client("zekalab")
            assert client._http_client is not None

            await close_all_mcp_clients()

            # After closing, should be removed from cache
            assert len(__import__("yonca.mcp.client", fromlist=["_clients"])._clients) == 0
