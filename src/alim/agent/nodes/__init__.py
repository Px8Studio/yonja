# src/ALİM/agent/nodes/__init__.py
"""Agent nodes - specialist components of the LangGraph.

Each node handles a specific aspect of the conversation:
- Supervisor: Routes messages to appropriate handlers
- ContextLoader: Loads farm and user data
- Agronomist: Provides farming advice
- Weather: Analyzes weather conditions
- Validator: Checks rules and adds warnings
"""

from alim.agent.nodes.agronomist import agronomist_node
from alim.agent.nodes.context_loader import context_loader_node, route_after_context
from alim.agent.nodes.supervisor import (
    route_from_supervisor,
    supervisor_node,
)
from alim.agent.nodes.validator import quick_validate, validator_node
from alim.agent.nodes.weather import weather_node

__all__ = [
    # Nodes
    "supervisor_node",
    "context_loader_node",
    "agronomist_node",
    "weather_node",
    "validator_node",
    # Routing functions
    "route_from_supervisor",
    "route_after_context",
    # Utilities
    "quick_validate",
]
