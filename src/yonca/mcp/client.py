# src/yonca/mcp/client.py
"""MCP Client factory and base class for calling MCP servers.

This is the main entry point for LangGraph nodes to call external MCP servers.

Architecture:
--------------
MCPClient (singleton)
    ├─► HTTPClient (httpx.AsyncClient for network calls)
    ├─► Tool Cache (recent tool calls for deduplication)
    └─► Metrics (latency, success rate for Langfuse)

Design Patterns:
1. Singleton Pattern: One MCPClient instance per server
2. Factory Pattern: get_mcp_client() returns configured instance
3. Decorator Pattern: Logging/metrics wrapped around actual calls
4. Timeout Pattern: All calls have configurable timeouts

Testing:
-------
Unit tests mock MCPClient with AsyncMock to avoid network calls.
Integration tests use docker-compose with real mock servers.

See: tests/unit/test_mcp_client.py
See: tests/integration/test_mcp_integration.py (todo)
"""

import inspect
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from yonca.mcp.config import get_server_config

logger = structlog.get_logger(__name__)


# ============================================================
# Data Models
# ============================================================


@dataclass
class MCPCallResult:
    """Result of an MCP server call."""

    success: bool
    data: Any = None
    error: str | None = None
    latency_ms: float = 0.0
    server: str = ""
    tool_name: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)

    def to_langfuse_metadata(self) -> dict[str, Any]:
        """Convert to Langfuse metadata for logging."""
        return {
            "mcp_server": self.server,
            "mcp_tool": self.tool_name,
            "mcp_success": self.success,
            "mcp_latency_ms": self.latency_ms,
            "mcp_timestamp": self.timestamp.isoformat(),
            **({"mcp_error": self.error} if self.error else {}),
        }


@dataclass
class MCPToolCall:
    """Configuration for an MCP tool call."""

    server: str  # "openweather", "zekalab", "ektis", "cbar"
    tool: str  # Tool name on the server
    args: dict[str, Any]  # Arguments to pass
    cache_seconds: int = 0  # 0 = no caching


# ============================================================
# Base MCP Client
# ============================================================


class MCPClient:
    """Client for calling MCP servers.

    Responsibilities:
    - Authentication & credential management
    - HTTP request/response handling
    - Timeout & retry logic
    - Logging & observability
    - Caching (optional)

    NOT responsible for:
    - Business logic (that stays in LangGraph nodes)
    - Data transformation (that's node responsibility)
    - State management (that's LangGraph's job)
    """

    def __init__(self, server_name: str):
        """Initialize MCP client for a specific server.

        Args:
            server_name: Server identifier (e.g., "openweather", "zekalab")
        """
        self.server_name = server_name
        self.config = get_server_config(server_name)

        if not self.config:
            logger.warning(f"MCP server '{server_name}' not configured or disabled")
            self.enabled = False
        else:
            self.enabled = self.config.enabled

        self._http_client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Context manager entry."""
        if self.enabled and self.config:
            self._http_client = httpx.AsyncClient(timeout=self.config.timeout_ms / 1000.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._http_client:
            await self._http_client.aclose()

    async def call_tool(self, call: MCPToolCall) -> MCPCallResult:
        """Call a tool on the MCP server.

        Args:
            call: MCPToolCall with server, tool name, and args

        Returns:
            MCPCallResult with success/data/error/latency

        Raises:
            ValueError: If server not configured
            httpx.TimeoutException: If request times out
        """
        # Re-evaluate enabled state based on current config (supports test injection)
        if not self.config or not getattr(self.config, "enabled", False):
            return MCPCallResult(
                success=False,
                error=f"MCP server '{self.server_name}' is disabled",
                server=self.server_name,
                tool_name=call.tool,
            )

        if not self._http_client:
            return MCPCallResult(
                success=False,
                error=f"MCP server '{self.server_name}' not initialized",
                server=self.server_name,
                tool_name=call.tool,
            )

        start_time = datetime.now(UTC)

        try:
            logger.info(
                "mcp_call_start",
                server=self.server_name,
                tool=call.tool,
                args_keys=list(call.args.keys()),
            )

            # Make the request
            response = await self._http_client.post(
                f"{self.config.url}/tools/{call.tool}",
                json={"args": call.args},
                headers=self._build_headers(),
            )

            latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

            rs = response.raise_for_status()
            if inspect.iscoroutine(rs):
                await rs

            data_or_coro = response.json()
            data = await data_or_coro if inspect.iscoroutine(data_or_coro) else data_or_coro

            logger.info(
                "mcp_call_success",
                server=self.server_name,
                tool=call.tool,
                latency_ms=latency_ms,
            )

            return MCPCallResult(
                success=True,
                data=data,
                latency_ms=latency_ms,
                server=self.server_name,
                tool_name=call.tool,
            )

        except httpx.TimeoutException:
            latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
            logger.error(
                "mcp_call_timeout",
                server=self.server_name,
                tool=call.tool,
                latency_ms=latency_ms,
            )
            return MCPCallResult(
                success=False,
                error=f"Timeout after {latency_ms:.0f}ms",
                latency_ms=latency_ms,
                server=self.server_name,
                tool_name=call.tool,
            )

        except httpx.HTTPError as e:
            latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
            error_msg = (
                f"HTTP {e.response.status_code if hasattr(e, 'response') else '?'}: {str(e)}"
            )
            logger.error(
                "mcp_call_error",
                server=self.server_name,
                tool=call.tool,
                error=error_msg,
                latency_ms=latency_ms,
            )
            return MCPCallResult(
                success=False,
                error=error_msg,
                latency_ms=latency_ms,
                server=self.server_name,
                tool_name=call.tool,
            )

        except Exception as e:
            latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(
                "mcp_call_exception",
                server=self.server_name,
                tool=call.tool,
                error=error_msg,
                latency_ms=latency_ms,
            )
            return MCPCallResult(
                success=False,
                error=error_msg,
                latency_ms=latency_ms,
                server=self.server_name,
                tool_name=call.tool,
            )

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers including authentication.

        Returns:
            dict: HTTP headers with auth credentials
        """
        headers = {"Content-Type": "application/json"}

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        if self.config.secret:
            headers["X-Secret"] = self.config.secret

        return headers


# ============================================================
# Singleton Factory
# ============================================================

_clients: dict[str, MCPClient] = {}


async def get_mcp_client(server_name: str = "zekalab") -> MCPClient:
    """Get or create an MCP client for a server.

    Uses singleton pattern to avoid creating multiple clients.

    Args:
        server_name: Server identifier (default: "zekalab" for internal rules)

    Returns:
        MCPClient instance

    Example:
        client = await get_mcp_client("openweather")
        result = await client.call_tool(
            MCPToolCall(
                server="openweather",
                tool="get_forecast",
                args={"latitude": 40.4, "longitude": 49.9}
            )
        )
    """
    if server_name not in _clients:
        _clients[server_name] = MCPClient(server_name)
        await _clients[server_name].__aenter__()
        logger.info("mcp_client_created", server=server_name)

    return _clients[server_name]


async def close_all_mcp_clients():
    """Close all MCP clients.

    Call this during application shutdown.
    """
    for server_name, client in _clients.items():
        try:
            await client.__aexit__(None, None, None)
            logger.info("mcp_client_closed", server=server_name)
        except Exception as e:
            logger.error("mcp_client_close_error", server=server_name, error=str(e))

    _clients.clear()
