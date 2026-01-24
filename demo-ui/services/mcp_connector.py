# demo-ui/services/mcp_connector.py
"""Chainlit MCP Connector — Bridge between UI and MCP servers.

This module provides Chainlit-specific integration with Model Context Protocol (MCP)
servers, enabling the UI to display and interact with external tools/data sources.

Features:
- Auto-discovery of available MCP tools
- Profile-based tool filtering
- UI display of MCP connections
- Tool invocation from chat
- Connection status monitoring

Architecture:
    Chainlit UI
        ↓
    MCPConnector (this file)
        ↓
    yonca.mcp.adapters (LangChain MCP adapters)
        ↓
    MCP Servers (ZekaLab, OpenWeather, etc.)

Usage:
    from services.mcp_connector import get_mcp_status, invoke_mcp_tool

    # Show available MCP connections
    status = await get_mcp_status(profile="agent")
    await cl.Message(content=format_mcp_status(status)).send()

    # Invoke a tool
    result = await invoke_mcp_tool("zekalab", "evaluate_irrigation_rules", {...})
"""

# Import from the main MCP adapters module
import sys
from pathlib import Path
from typing import Any

import chainlit as cl
import structlog
from langchain_core.tools import BaseTool

# noqa: E402 - sys.path manipulation needed before relative imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from alim.mcp.adapters import (  # noqa: E402
    PROFILE_MCP_SERVERS,
    check_mcp_servers_health,
    get_mcp_client_for_profile,
    get_mcp_tools_for_profile,
)

logger = structlog.get_logger(__name__)


# ============================================================
# MCP Status Display
# ============================================================


async def get_mcp_status(profile: str = "fast") -> dict[str, Any]:
    """Get MCP connection status for current profile.

    Args:
        profile: Agent mode (fast, thinking, pro)

    Returns:
        Dict with server statuses and available tools
    """
    # Get health status of all servers
    health = await check_mcp_servers_health()

    # Get tools available for this profile
    tools = await get_mcp_tools_for_profile(profile)

    # Get allowed servers for profile
    allowed_servers = PROFILE_MCP_SERVERS.get(profile, [])

    # Filter health to only show allowed servers
    filtered_health = {
        server: status for server, status in health.items() if server in allowed_servers
    }

    return {
        "profile": profile,
        "servers": filtered_health,
        "tools": [{"name": t.name, "description": t.description} for t in tools],
        "tool_count": len(tools),
        "connectors_enabled": bool(allowed_servers),
    }


async def get_native_mcp_connections() -> dict[str, Any]:
    """Get MCP connections from Chainlit's native modal (browser localStorage).

    This reads what the user manually added via the 🔌 button.
    Returns connection info that backend can use to fetch tools.

    Returns:
        Dict with user-connected MCP servers from native modal
    """
    # NOTE: This is retrieved from Chainlit's frontend context
    # The actual localStorage data comes from the user session
    # We can access it via cl.user_session or cl.context if available

    try:
        import chainlit as cl

        # Try to get from user session (set by frontend)
        native_connections = cl.user_session.get("mcp_connections_native", {})

        return {
            "native_connections": native_connections,
            "count": len(native_connections),
        }
    except Exception as e:
        logger.warning("failed_to_get_native_mcp_connections", error=str(e), exc_info=True)
        return {
            "native_connections": {},
            "count": 0,
        }


def format_mcp_status(status: dict[str, Any]) -> str:
    """Format MCP status for display in Chainlit UI.

    Args:
        status: Status dict from get_mcp_status()

    Returns:
        Formatted markdown string
    """
    lines = [
        "## 🔌 MCP Connections",
        "",
        f"**Profile:** {status['profile']}",
        "",
        "### Servers",
    ]

    for server_name, server_status in status["servers"].items():
        status_emoji = (
            "🟢"
            if server_status["status"] == "online"
            else "🔴"
            if server_status["status"] == "offline"
            else "🟡"
        )
        lines.append(f"- {status_emoji} **{server_name}**: {server_status['status']}")

    lines.extend(
        [
            "",
            f"### Available Tools ({status['tool_count']})",
        ]
    )

    if not status.get("connectors_enabled", False):
        lines.append("- (connectors disabled for this mode)")
        return "\n".join(lines)

    for tool in status["tools"][:10]:  # Show first 10 tools
        lines.append(f"- `{tool['name']}`: {tool['description'][:80]}...")

    if len(status["tools"]) > 10:
        lines.append(f"\n*...and {len(status['tools']) - 10} more tools*")

    return "\n".join(lines)


# ============================================================
# Tool Invocation
# ============================================================


async def invoke_mcp_tool(
    server: str,
    tool_name: str,
    args: dict[str, Any],
    profile: str = "fast",
) -> dict[str, Any]:
    """Invoke an MCP tool from Chainlit UI.

    Args:
        server: Server name (zekalab, openweather, etc.)
        tool_name: Name of the tool to invoke
        args: Tool arguments
        profile: Agent mode (fast/thinking/pro) for permission checking

    Returns:
        Tool result or error
    """
    try:
        # Check if server is allowed for profile
        allowed_servers = PROFILE_MCP_SERVERS.get(profile, [])
        if server not in allowed_servers:
            return {
                "success": False,
                "error": f"Server '{server}' not allowed for profile '{profile}'",
            }

        # Get MCP client for profile
        client = get_mcp_client_for_profile(profile)
        if not client:
            return {
                "success": False,
                "error": "No MCP client available",
            }

        # Get all tools and find the requested one
        tools = await client.get_tools()
        tool = next((t for t in tools if t.name == tool_name), None)

        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
            }

        # Invoke the tool
        result = await tool.ainvoke(args)

        logger.info(
            "mcp_tool_invoked",
            server=server,
            tool=tool_name,
            profile=profile,
        )

        return {
            "success": True,
            "result": result,
        }

    except Exception as e:
        logger.error(
            "mcp_tool_invocation_failed",
            server=server,
            tool=tool_name,
            error=str(e),
            exc_info=True,
        )
        return {
            "success": False,
            "error": str(e),
        }


# ============================================================
# Chainlit Actions (UI Commands)
# ============================================================


@cl.action_callback("show_mcp_status")
async def on_show_mcp_status(action: cl.Action):
    """Handle 'Show MCP Status' button click."""
    # Get current profile from user session
    profile = cl.user_session.get("chat_profile", "fast")

    # Fetch and display status
    status = await get_mcp_status(profile)
    formatted = format_mcp_status(status)

    await cl.Message(content=formatted).send()


async def add_mcp_actions():
    """Add MCP action buttons to Chainlit UI.

    Call this from @cl.on_chat_start to add MCP controls.
    """
    actions = [
        cl.Action(
            name="show_mcp_status",
            value="show",
            label="🔌 Show MCP Status",
            description="Display MCP server connections and available tools",
        ),
    ]

    await cl.Message(
        content="**MCP Controls Available**\nClick the button below to see MCP connections.",
        actions=actions,
    ).send()


# ============================================================
# Tool Listing for Graph
# ============================================================


async def get_tools_for_session() -> list[BaseTool]:
    """Get MCP tools for current Chainlit session.

    Returns tools filtered by the current user's profile.
    Used when building LangGraph with profile-specific tools.

    Returns:
        List of LangChain BaseTool instances
    """
    profile = cl.user_session.get("chat_profile", "fast")
    tools = await get_mcp_tools_for_profile(profile)

    logger.info(
        "mcp_tools_loaded_for_session",
        profile=profile,
        tool_count=len(tools),
    )

    return tools
