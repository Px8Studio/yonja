# src/yonca/mcp/adapters.py
"""MCP Adapters using official langchain-mcp-adapters.

This module provides the bridge between LangGraph and MCP servers
using the official langchain-mcp-adapters library.

Usage:
    from yonca.mcp.adapters import create_mcp_client, get_mcp_tools

    # In your graph factory
    async def make_graph():
        tools = await get_mcp_tools()
        # Use tools with ToolNode
        graph.add_node("tools", ToolNode(tools))
"""

from typing import Any

import structlog
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from yonca.mcp.config import get_settings

logger = structlog.get_logger(__name__)

# ============================================================
# Configuration Builder
# ============================================================


def get_mcp_client_config() -> dict[str, dict[str, Any]]:
    """Build MCP client configuration from settings.

    Returns configuration dict for MultiServerMCPClient based on
    enabled MCP servers in settings.

    Returns:
        Configuration dict for MultiServerMCPClient
    """
    settings = get_settings()
    config: dict[str, dict[str, Any]] = {}

    # ZekaLab Internal MCP (Rules Engine)
    if settings.zekalab_mcp_enabled:
        zekalab_config: dict[str, Any] = {
            "url": f"{settings.zekalab_mcp_url}/mcp",
            "transport": "http",
        }

        # Add headers if secret is configured
        if settings.zekalab_mcp_secret:
            zekalab_config["headers"] = {
                "X-Secret": settings.zekalab_mcp_secret,
            }

        config["zekalab"] = zekalab_config
        logger.info(
            "mcp_server_configured",
            server="zekalab",
            url=settings.zekalab_mcp_url,
        )

    # OpenWeather MCP (External Weather API)
    if settings.openweather_mcp_enabled:
        openweather_config: dict[str, Any] = {
            "url": f"{settings.openweather_mcp_url}/mcp",
            "transport": "http",
        }

        # Add API key if configured
        if settings.openweather_api_key:
            openweather_config["headers"] = {
                "Authorization": f"Bearer {settings.openweather_api_key}",
            }

        config["openweather"] = openweather_config
        logger.info(
            "mcp_server_configured",
            server="openweather",
            url=settings.openweather_mcp_url,
        )

    return config


# ============================================================
# MCP Client Factory
# ============================================================


def create_mcp_client() -> MultiServerMCPClient | None:
    """Create configured MCP client.

    Returns MultiServerMCPClient if any MCP servers are enabled,
    otherwise returns None.

    Returns:
        MultiServerMCPClient instance or None
    """
    config = get_mcp_client_config()

    if not config:
        logger.warning("no_mcp_servers_enabled")
        return None

    logger.info(
        "mcp_client_created",
        servers=list(config.keys()),
    )

    return MultiServerMCPClient(config)


async def get_mcp_tools() -> list[BaseTool]:
    """Get all tools from configured MCP servers.

    Connects to all enabled MCP servers and returns their tools
    as LangChain BaseTool instances for use with LangGraph.

    Returns:
        List of LangChain tools from MCP servers
    """
    client = create_mcp_client()

    if client is None:
        logger.info("mcp_tools_empty", reason="no_servers_enabled")
        return []

    try:
        tools = await client.get_tools()

        logger.info(
            "mcp_tools_loaded",
            tool_count=len(tools),
            tool_names=[t.name for t in tools],
        )

        return tools
    except Exception as e:
        logger.error(
            "mcp_tools_load_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        return []


# ============================================================
# Profile-Based Tool Loading
# ============================================================

# Map chat profiles to allowed MCP servers
PROFILE_MCP_SERVERS: dict[str, list[str]] = {
    "general": ["zekalab"],  # Basic rules only
    "orchard": ["zekalab", "openweather"],  # + Weather
    "cotton": ["zekalab", "openweather"],  # + Weather
    "wheat": ["zekalab", "openweather"],  # + Weather
    "expert": ["zekalab", "openweather"],  # Full access
}


def get_mcp_client_for_profile(profile: str) -> MultiServerMCPClient | None:
    """Create MCP client filtered by profile.

    Different user profiles get access to different MCP servers.
    This implements profile-based tool loading.

    Args:
        profile: User profile name (general, orchard, cotton, etc.)

    Returns:
        MultiServerMCPClient with profile-appropriate servers
    """
    full_config = get_mcp_client_config()
    allowed_servers = PROFILE_MCP_SERVERS.get(profile, ["zekalab"])

    # Filter config to allowed servers
    filtered_config = {
        server: config for server, config in full_config.items() if server in allowed_servers
    }

    if not filtered_config:
        logger.warning(
            "no_mcp_servers_for_profile",
            profile=profile,
            allowed=allowed_servers,
        )
        return None

    logger.info(
        "mcp_client_created_for_profile",
        profile=profile,
        servers=list(filtered_config.keys()),
    )

    return MultiServerMCPClient(filtered_config)


async def get_mcp_tools_for_profile(profile: str) -> list[BaseTool]:
    """Get MCP tools filtered by user profile.

    Args:
        profile: User profile name

    Returns:
        List of LangChain tools available for the profile
    """
    client = get_mcp_client_for_profile(profile)

    if client is None:
        return []

    try:
        tools = await client.get_tools()

        logger.info(
            "mcp_tools_loaded_for_profile",
            profile=profile,
            tool_count=len(tools),
        )

        return tools
    except Exception as e:
        logger.error(
            "mcp_tools_load_failed_for_profile",
            profile=profile,
            error=str(e),
        )
        return []


# ============================================================
# Health Check
# ============================================================


async def check_mcp_servers_health() -> dict[str, dict[str, Any]]:
    """Check health of all configured MCP servers.

    Returns:
        Dict mapping server names to health status
    """
    config = get_mcp_client_config()
    results: dict[str, dict[str, Any]] = {}

    import httpx

    for server_name, server_config in config.items():
        url = server_config.get("url", "").replace("/mcp", "/health")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)

                results[server_name] = {
                    "status": "online" if response.status_code == 200 else "degraded",
                    "response_code": response.status_code,
                    "url": url,
                }
        except Exception as e:
            results[server_name] = {
                "status": "offline",
                "error": str(e),
                "url": url,
            }

    logger.info(
        "mcp_health_check_complete",
        results=results,
    )

    return results
