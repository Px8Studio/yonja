# src/yonca/agent/__init__.py
"""Agent module - LangGraph-based conversation orchestration.

This module provides the core AI agent functionality:
- State management for conversations
- Multi-node graph execution
- PostgreSQL/Redis-based memory persistence (via langgraph-checkpoint-*)
- Intent classification and routing

Example:
    ```python
    from yonca.agent import get_agent

    agent = get_agent()
    response = await agent.chat(
        message="Pomidorları nə vaxt suvarmaq lazımdır?",
        user_id="user_123",
    )
    print(response.content)
    ```
"""

from yonca.agent.graph import AgentResponse, YoncaAgent, get_agent
from yonca.agent.memory import (
    configure_windows_event_loop,
    get_checkpointer,
    get_checkpointer_async,
)
from yonca.agent.state import (
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
    # Main agent
    "YoncaAgent",
    "AgentResponse",
    "get_agent",
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
