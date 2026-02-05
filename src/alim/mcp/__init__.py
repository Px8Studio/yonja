# src/ALİM/mcp/__init__.py
"""MCP (Model Context Protocol) client layer for ALİM.

This module provides standardized access to MCP servers for:
- Weather data (OpenWeather MCP)
- Agronomy rules (ZekaLab Internal MCP)
- Future: EKTİS, CBAR Banking, Satellite data, etc.

Philosophy:
-----------
MCP is the "USB port" for AI systems. We abstract all external data sources
through MCP to maintain clean interfaces and enable hot-swapping of providers
without changing LangGraph node logic.

Architecture:
-------------
  LangGraph Nodes
        │
        ├─► weather_node ─┐
        │                 ├─► MCP Client Layer (this module)
        ├─► agronomist ──┤        ├─► Weather MCP Server (public)
        │                ├─► MCP  ├─► Rules MCP Server (private)
        └─► context_loader       ├─► EKTİS MCP Server (future)
                          ├─► MCP └─► CBAR MCP Server (future)

State flows: LangGraph State → MCP ──request──> Server
                                    ←─response── Server

Example Usage:
--------------
    from alim.mcp.client import get_mcp_client

    client = await get_mcp_client()

    # Call a public MCP tool
    weather = await client.call_tool(
        server="weather",
        tool="get_forecast",
        args={"latitude": 40.4, "longitude": 49.9, "days": 7}
    )

    # Call a private MCP tool
    recommendations = await client.call_tool(
        server="zekalab-internal",
        tool="evaluate_irrigation_rules",
        args={"farm_data": farm_context, "weather": weather}
    )

See docs/zekalab/MCP-BLUEPRINT.md and PHASE-3-COMPLETION-SUMMARY.md for design details.
"""

from alim.mcp.client import MCPClient, get_mcp_client

__all__ = ["MCPClient", "get_mcp_client"]
