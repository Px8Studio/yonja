# demo-ui/services/welcome.py
"""Dashboard welcome message handler.

Provides the primary welcome experience when users start a chat session.
Creates personalized greeting with farm status and quick action buttons.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import chainlit as cl
from constants import AgentMode

from services.logger import get_logger

if TYPE_CHECKING:
    pass

# Initialize logger
logger = get_logger(__name__)

# Localized strings for welcome UI
AZ_WELCOME_STRINGS = {
    "weather": "Hava",
    "subsidy": "Subsidiya",
    "irrigation": "Suvarma",
}


async def send_dashboard_welcome(
    user: cl.User | None = None,
    mcp_status: dict | None = None,
) -> None:
    """Send primary welcome message to main chat with farm status and quick actions.

    This is the FIRST message users see after logging in (main chat).
    Displays personalized greeting, farm context, and action buttons.

    Creates a "Warm Handshake" experience that transforms the chat from
    a generic interface into an agricultural command center.

    Args:
        user: Optional authenticated user for personalization
        mcp_status: Optional MCP status dict (avoids redundant fetch)
    """
    try:
        # Personalized greeting
        if user and user.metadata:
            user_name = user.metadata.get("name", "").split()[0]  # First name
            greeting = f"Salam, **{user_name}**! 👋"
        else:
            greeting = "Xoş gəlmisiniz! 👋"

        # Check MCP service health
        try:
            if mcp_status is None:
                from services.mcp_connector import get_mcp_status

                mcp_status = await get_mcp_status(profile=AgentMode.AGENT.value)

            servers = mcp_status.get("servers", {}) if isinstance(mcp_status, dict) else {}
            online_count = sum(1 for info in servers.values() if info.get("status") == "online")
            total_count = len(servers)
            offline_servers = [
                name for name, info in servers.items() if info.get("status") != "online"
            ]

            # Build status lines
            system_status = "✓ LangGraph server online"
            if offline_servers:
                mcp_status_line = f"⚠️ MCP servers: {online_count}/{total_count} online (offline: {', '.join(offline_servers)})"
            else:
                mcp_status_line = (
                    f"✓ MCP servers: {online_count}/{total_count} online"
                    if total_count
                    else "⚠️ MCP status unknown"
                )
        except Exception:
            system_status = "✓ LangGraph server online"
            mcp_status_line = "⚠️ MCP status unknown"
            online_count = 0
            total_count = 0

        # Build dashboard message
        dashboard_content = f"""{greeting}

🌿 **ALEM | Aqronom Assistentiniz**

Mən sizin virtual aqronomam — əkin, suvarma və subsidiya məsələlərində kömək edirəm.

**📊 Sistem Vəziyyəti:**
- {system_status}
- ✓ SİMA inteqrasiyası hazır
- {mcp_status_line}

---

**Sürətli Əməliyyatlar** — Aşağıdakı düymələrə klikləyin:
"""

        # Create quick action buttons
        actions = [
            cl.Action(
                name="weather",
                payload={"action": "weather"},
                label="🌤️ " + AZ_WELCOME_STRINGS["weather"],
            ),
            cl.Action(
                name="subsidy",
                payload={"action": "subsidy"},
                label="📋 " + AZ_WELCOME_STRINGS["subsidy"],
            ),
            cl.Action(
                name="irrigation",
                payload={"action": "irrigation"},
                label="💧 " + AZ_WELCOME_STRINGS["irrigation"],
            ),
            cl.Action(
                name="show_mcp_status",
                payload={"action": "show_mcp_status"},
                label="🔌 MCP Status",
                description="Show connected MCP servers and tools",
            ),
        ]

        # Send the dashboard welcome message
        await cl.Message(
            content=dashboard_content,
            author="ALEM",
            actions=actions,
        ).send()

        # Store MCP status in session
        cl.user_session.set("mcp_status", mcp_status or {})

        logger.info(
            "welcome_message_sent",
            user_id=user.identifier if user else "anonymous",
            mcp_online_count=online_count,
            mcp_total_count=total_count,
        )

    except Exception as e:
        logger.error("welcome_message_failed", error=str(e), exc_info=True)
        # Fallback simple welcome
        await cl.Message(content="👋 Xoş gəlmisiniz! Mən ALEM-əm, sizin virtual aqronomun.").send()
