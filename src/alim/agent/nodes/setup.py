# src/alim/agent/nodes/setup.py
"""Setup node for hydrating agent state."""

from datetime import UTC, datetime

import structlog
from langchain_core.messages import HumanMessage

from alim.agent.state import AgentState

logger = structlog.get_logger(__name__)


def setup_node(state: AgentState) -> dict:
    """Entry node to hydrate state from simple inputs.

    Inspects input state (potentially partial) and ensures all
    required fields are initialized. Appends current_input to messages
    if strictly necessary.

    Args:
        state: Input state (potentially partial)

    Returns:
        State updates (will be merged by LangGraph)
    """
    updates = {}

    # 1. Initialize Metadata Defaults
    if not state.get("processing_start"):
        updates["processing_start"] = datetime.now(UTC)

    if "nodes_visited" not in state:
        updates["nodes_visited"] = []

    # 2. Handle Message Creation from current_input
    # Ensure current_input is added as a message if it's new
    current_input = state.get("current_input")
    messages = state.get("messages", [])

    # Check if we need to append the input
    should_append = False
    if current_input:
        if not messages:
            should_append = True
        else:
            # Check if the last message matches current input to avoid duplicates
            # (Simple check, can be refined if needed)
            last_msg = messages[-1]
            if isinstance(last_msg, HumanMessage):
                if last_msg.content != current_input:
                    should_append = True
            else:
                # Last message was AI or System, so this input is definitely new
                should_append = True

    if should_append:
        # Note: LangGraph 'messages' key with reducer=add_messages will append this list
        updates["messages"] = [HumanMessage(content=current_input)]
        logger.info("setup_node_appended_message", length=len(current_input))

    # 3. Initialize Phase 2/3 Defaults (MCP, etc)
    if "mcp_server_health" not in state:
        updates["mcp_server_health"] = {
            "openweather": True,
            "zekalab": True,
        }

    if "mcp_config" not in state:
        updates["mcp_config"] = {
            "use_mcp": True,
            "fallback_to_synthetic": True,
            "max_mcp_calls_per_turn": 10,
            "mcp_timeout_seconds": 5,
        }

    # 4. Handle Versioning (Simple Migrations)
    current_version = state.get("version", 0)
    target_version = 1

    if current_version < target_version:
        logger.info(
            "state_migration_triggered", from_version=current_version, to_version=target_version
        )
        updates["version"] = target_version

    return updates
