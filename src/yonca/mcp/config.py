# src/yonca/mcp/config.py
"""Configuration management for MCP servers.

Centralizes all MCP server configuration (URLs, credentials, timeouts)
to support multi-environment deployment (dev, staging, prod).

Configuration Priority:
1. Environment variables (highest priority)
2. .env file (development)
3. Config file (optional)
4. Defaults (lowest priority)

Example .env:
    ZEKALAB_MCP_ENABLED=true
    ZEKALAB_MCP_URL=http://localhost:7777
    ZEKALAB_MCP_SECRET=dev_secret_key

    OPENWEATHER_MCP_ENABLED=true
    OPENWEATHER_MCP_URL=https://openweather-mcp.example.com
    OPENWEATHER_API_KEY=your_api_key_here
    OPENWEATHER_TIMEOUT_MS=500
"""


import structlog
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logger = structlog.get_logger(__name__)


# ============================================================
# Settings Classes
# ============================================================


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    model_config = {"extra": "ignore"}

    enabled: bool = Field(default=True, description="Enable this MCP server")
    url: str = Field(description="MCP server URL")
    api_key: str | None = Field(default=None, description="API key for authentication")
    secret: str | None = Field(default=None, description="Shared secret for internal servers")
    timeout_ms: int = Field(default=2000, description="Request timeout in milliseconds")
    retries: int = Field(default=3, description="Number of retries on failure")
    retry_backoff_ms: int = Field(default=100, description="Backoff between retries")


class MCPSettings(BaseSettings):
    """Global MCP configuration."""

    model_config = {"extra": "ignore"}

    # Global
    mcp_enabled: bool = Field(
        default=True,
        description="Enable MCP client layer globally",
    )
    log_mcp_calls: bool = Field(
        default=True,
        description="Log all MCP calls to structlog",
    )

    # Weather MCP
    openweather_mcp_enabled: bool = Field(
        default=False,  # Start disabled, enable after Phase 1.1
        description="Enable OpenWeather MCP",
    )
    openweather_mcp_url: str = Field(
        default="https://openweather-mcp.example.com",
        description="OpenWeather MCP server URL",
    )
    openweather_api_key: str | None = Field(
        default=None,
        description="OpenWeather API key",
    )
    openweather_timeout_ms: int = Field(
        default=500,
        description="OpenWeather timeout in milliseconds",
    )

    # ZekaLab Internal MCP (Rules Engine)
    zekalab_mcp_enabled: bool = Field(
        default=False,  # Start disabled, enable after Phase 1.3
        description="Enable ZekaLab internal MCP server",
    )
    zekalab_mcp_url: str = Field(
        default="http://localhost:7777",
        description="ZekaLab MCP server URL",
    )
    zekalab_mcp_secret: str | None = Field(
        default=None,
        description="ZekaLab MCP shared secret",
    )
    zekalab_timeout_ms: int = Field(
        default=2000,
        description="ZekaLab timeout in milliseconds",
    )

    # EKTİS MCP (Phase 3)
    ektis_mcp_enabled: bool = Field(
        default=False,
        description="Enable EKTİS MCP integration",
    )
    ektis_mcp_url: str = Field(
        default="https://ektis-api.example.com",
        description="EKTİS MCP server URL",
    )
    ektis_api_key: str | None = Field(
        default=None,
        description="EKTİS API key",
    )

    # CBAR Banking MCP (Phase 3)
    cbar_mcp_enabled: bool = Field(
        default=False,
        description="Enable CBAR Open Banking MCP",
    )
    cbar_mcp_url: str = Field(
        default="https://cbar-banking-mcp.example.com",
        description="CBAR MCP server URL",
    )
    cbar_api_key: str | None = Field(
        default=None,
        description="CBAR API key",
    )


# ============================================================
# Global Settings Instance
# ============================================================

mcp_settings = MCPSettings()


# ============================================================
# Configuration Validation
# ============================================================


def validate_mcp_config() -> dict[str, str]:
    """Validate MCP configuration and return status.

    Returns:
        dict: Server name → status (enabled/disabled)
    """
    status = {}

    if mcp_settings.openweather_mcp_enabled:
        if mcp_settings.openweather_api_key:
            status["openweather"] = "✅ enabled"
        else:
            logger.warning("openweather_mcp_enabled but OPENWEATHER_API_KEY not set")
            status["openweather"] = "⚠️ missing credentials"
    else:
        status["openweather"] = "⏳ disabled"

    if mcp_settings.zekalab_mcp_enabled:
        status["zekalab"] = "✅ enabled"
    else:
        status["zekalab"] = "⏳ disabled"

    if mcp_settings.ektis_mcp_enabled:
        if mcp_settings.ektis_api_key:
            status["ektis"] = "✅ enabled"
        else:
            logger.warning("ektis_mcp_enabled but EKTIS_API_KEY not set")
            status["ektis"] = "⚠️ missing credentials"
    else:
        status["ektis"] = "⏳ disabled"

    if mcp_settings.cbar_mcp_enabled:
        if mcp_settings.cbar_api_key:
            status["cbar"] = "✅ enabled"
        else:
            logger.warning("cbar_mcp_enabled but CBAR_API_KEY not set")
            status["cbar"] = "⚠️ missing credentials"
    else:
        status["cbar"] = "⏳ disabled"

    return status


def get_server_config(server_name: str) -> MCPServerConfig | None:
    """Get configuration for a specific MCP server.

    Args:
        server_name: Server identifier (e.g., "openweather", "zekalab")

    Returns:
        MCPServerConfig or None if not configured
    """
    if server_name == "openweather":
        if mcp_settings.openweather_mcp_enabled:
            return MCPServerConfig(
                enabled=True,
                url=mcp_settings.openweather_mcp_url,
                api_key=mcp_settings.openweather_api_key,
                timeout_ms=mcp_settings.openweather_timeout_ms,
            )
        return None

    elif server_name == "zekalab":
        if mcp_settings.zekalab_mcp_enabled:
            return MCPServerConfig(
                enabled=True,
                url=mcp_settings.zekalab_mcp_url,
                secret=mcp_settings.zekalab_mcp_secret,
                timeout_ms=mcp_settings.zekalab_timeout_ms,
            )
        return None

    elif server_name == "ektis":
        if mcp_settings.ektis_mcp_enabled:
            return MCPServerConfig(
                enabled=True,
                url=mcp_settings.ektis_mcp_url,
                api_key=mcp_settings.ektis_api_key,
                timeout_ms=2000,
            )
        return None

    elif server_name == "cbar":
        if mcp_settings.cbar_mcp_enabled:
            return MCPServerConfig(
                enabled=True,
                url=mcp_settings.cbar_mcp_url,
                api_key=mcp_settings.cbar_api_key,
                timeout_ms=2000,
            )
        return None

    logger.warning("Unknown MCP server", server=server_name)
    return None
