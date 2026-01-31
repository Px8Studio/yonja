from services.startup import MCPServiceStatus


def format_mcp_status_badge(status: MCPServiceStatus) -> str:
    """Format a single MCP status as a markdown badge."""
    if status["status"] == "online":
        time_str = f"{status['response_time_ms']}ms" if status["response_time_ms"] else ""
        return f"✓ {status['name']} ({time_str})"
    elif status["status"] == "degraded":
        return f"⚠ {status['name']} (degraded)"
    else:
        return f"✗ {status['name']} (offline)"


def format_mcp_status_line(statuses: dict[str, MCPServiceStatus]) -> str:
    """Format all MCP statuses as a single-line status indicator."""
    badges = [format_mcp_status_badge(s) for s in statuses.values()]
    return "🔌 " + " • ".join(badges)
