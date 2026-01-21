# src/yonca/agent/__init__.py
"""Agent module - LangGraph-based conversation orchestration.

This module provides the core AI agent functionality:
- State management for conversations
- Multi-node graph execution
- Redis-based memory persistence (via langgraph-checkpoint-redis)
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
from yonca.agent.memory import get_checkpointer, get_checkpointer_async
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
    # Memory
    "get_checkpointer",
    "get_checkpointer_async",
]
