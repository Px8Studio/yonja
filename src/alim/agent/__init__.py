# src/ALİM/agent/__init__.py
"""Agent module - LangGraph-based conversation orchestration.

This module provides the core AI agent functionality:
- State management for conversations
- Multi-node graph execution
- PostgreSQL/Redis-based memory persistence (via langgraph-checkpoint-*)
- Intent classification and routing

Example:
    ```python
    from alim.agent import get_agent

    agent = get_agent()
    response = await agent.chat(
        message="Pomidorları nə vaxt suvarmaq lazımdır?",
        user_id="user_123",
    )
    print(response.content)
    ```
"""

from alim.agent.graph import compile_agent_graph, get_agent, make_graph
from alim.agent.memory import (
    configure_windows_event_loop,
    get_checkpointer,
    get_checkpointer_async,
)
from alim.agent.state import (
    AgentState,
    Alert,
    FarmContext,
    Message,
    RoutingDecision,
    Severity,
    UserContext,
    UserIntent,
    WeatherContext,
    create_initial_state,
    serialize_state_for_api,
)

__all__ = [
    # Graph Factory
    "compile_agent_graph",
    "get_agent",
    "make_graph",
    # State
    "AgentState",
    "UserIntent",
    "Severity",
    "Message",
    "Alert",
    "UserContext",
    "FarmContext",
    "WeatherContext",
    "RoutingDecision",
    "create_initial_state",
    "serialize_state_for_api",
    # Memory
    "get_checkpointer",
    "get_checkpointer_async",
    "configure_windows_event_loop",
]
