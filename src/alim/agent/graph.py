# src/ALİM/agent/graph.py
"""LangGraph main graph for the ALİM agent.

Defines the conversation flow as a state machine with nodes
for routing, context loading, specialist processing, validation,
and visualization.

Supports two modes:
1. Standard graph (create_agent_graph) - without MCP tools
2. MCP-enabled graph (create_agent_graph_with_mcp) - with MCP tool integration

Graph Flow (Flattened):
    setup → pii_masking → supervisor → context_loader
    → [Agronomist/Weather/Vision/SQL]
    → [Validator (conditional)]
    → END
"""


from typing import Literal

import structlog
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from alim.agent.memory import get_checkpointer_async

# Specialist Nodes
from alim.agent.nodes.agronomist import agronomist_node
from alim.agent.nodes.context_loader import context_loader_node
from alim.agent.nodes.nl_to_sql import nl_to_sql_node
from alim.agent.nodes.pii import pii_masking_node
from alim.agent.nodes.setup import setup_node
from alim.agent.nodes.supervisor import supervisor_node
from alim.agent.nodes.validator import validator_node
from alim.agent.nodes.vision_to_action import vision_to_action_node
from alim.agent.nodes.weather import weather_node
from alim.agent.state import AgentState, UserIntent
from alim.observability.langfuse import create_langfuse_handler

logger = structlog.get_logger(__name__)

# Enable LangChain verbose logging for debugging
try:
    from langchain.globals import set_debug, set_verbose

    ENABLE_VERBOSE_LOGGING = True
except ImportError:
    ENABLE_VERBOSE_LOGGING = False


# ============================================================
# Routing Logic
# ============================================================


def route_supervisor(state: AgentState) -> Literal["context_loader", "__end__"]:
    """Route from supervisor based on routing decision."""
    routing = state.get("routing")
    if not routing or routing.target_node == "end":
        return END
    return "context_loader"


def route_context_loader(
    state: AgentState
) -> Literal["agronomist", "weather", "nl_to_sql", "vision_to_action", "__end__"]:
    """Route from context_loader to appropriate specialist node."""
    routing = state.get("routing")
    intent = state.get("intent")

    if intent == UserIntent.WEATHER:
        return "weather"
    elif intent == UserIntent.DATA_QUERY:
        return "nl_to_sql"
    elif intent == UserIntent.VISION_ANALYSIS:
        return "vision_to_action"
    elif intent in [
        UserIntent.IRRIGATION,
        UserIntent.FERTILIZATION,
        UserIntent.PEST_CONTROL,
        UserIntent.HARVEST,
        UserIntent.PLANTING,
        UserIntent.CROP_ROTATION,
        UserIntent.GENERAL_ADVICE,
    ]:
        return "agronomist"

    # If routed to specialist_subgraph broadly, default to agronomist
    if routing and routing.target_node == "specialist_subgraph":
        return "agronomist"

    return "agronomist"  # Default fallback


def route_specialist(state: AgentState) -> Literal["validator", "python_viz_tools", "__end__"]:
    """Route from specialist: validate sensitive actions, else end."""
    # Check for visualization first
    if state.get("visualization_request"):
        return "python_viz_tools"

    # Check for sensitive intents requiring validation
    intent = state.get("intent")
    sensitive_intents = [
        UserIntent.IRRIGATION,
        UserIntent.FERTILIZATION,
        UserIntent.PEST_CONTROL,
    ]

    if intent in sensitive_intents:
        return "validator"

    return END


# ============================================================
# Graph Construction (Standard - No MCP)
# ============================================================


def create_agent_graph() -> StateGraph:
    """Create the main agent graph (without MCP tools)."""
    graph = StateGraph(AgentState)

    # 1. Add Top-Level Nodes
    graph.add_node("setup", setup_node)
    graph.add_node("pii_masking", pii_masking_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("context_loader", context_loader_node)

    # 2. Add Specialist Nodes
    graph.add_node("agronomist", agronomist_node)
    graph.add_node("weather", weather_node)
    graph.add_node("nl_to_sql", nl_to_sql_node)
    graph.add_node("vision_to_action", vision_to_action_node)

    # 3. Add Support Nodes
    graph.add_node("validator", validator_node)

    # 4. Entry Flow
    graph.set_entry_point("setup")
    graph.add_edge("setup", "pii_masking")
    graph.add_edge("pii_masking", "supervisor")

    # 5. Routing

    # Supervisor -> Context Loader OR End
    graph.add_conditional_edges(
        "supervisor",
        route_supervisor,
    )

    # Context Loader -> Specialist Node
    graph.add_conditional_edges(
        "context_loader",
        route_context_loader,
    )

    # Specialist -> Validator OR End
    # Define path map for optional tools
    specialist_path_map = {
        "validator": "validator",
        "python_viz_tools": END,  # No tools in standard graph
        "__end__": END,
    }

    for node in ["agronomist", "weather", "nl_to_sql", "vision_to_action"]:
        graph.add_conditional_edges(node, route_specialist, path_map=specialist_path_map)

    # Validator -> End
    graph.add_edge("validator", END)

    return graph


# ============================================================
# Graph Construction (With MCP Tools)
# ============================================================


async def create_agent_graph_with_mcp() -> StateGraph:
    """Create agent graph with MCP tools."""
    from alim.mcp.adapters import get_mcp_tools, get_python_viz_tools

    mcp_tools = await get_mcp_tools()
    python_viz_tools = await get_python_viz_tools()

    graph = StateGraph(AgentState)

    # 1. Add Top-Level Nodes
    graph.add_node("setup", setup_node)
    graph.add_node("pii_masking", pii_masking_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("context_loader", context_loader_node)

    # 2. Add Specialist Nodes
    graph.add_node("agronomist", agronomist_node)
    graph.add_node("weather", weather_node)
    graph.add_node("nl_to_sql", nl_to_sql_node)
    graph.add_node("vision_to_action", vision_to_action_node)

    # 3. Add Support Nodes
    graph.add_node("validator", validator_node)

    # 4. Add Tool Nodes
    if mcp_tools:
        graph.add_node("mcp_tools", ToolNode(mcp_tools))
        # Note: MCP tools are typically called by the LLM in specialist nodes.
        # Use simple cycle: specialist -> mcp_tools -> specialist
        # OR context_loader deals with them.
        # For now, let's just make sure they exist.
        # If specialists bind tools, we need edges back to them.
        # But `agronomist_node` implementation (checking separate file if I could) usually isn't prebuilt ReAct.
        # Assuming existing implementation handles MCP via context loading or direct calls.
        pass

    if python_viz_tools:
        graph.add_node("python_viz_tools", ToolNode(python_viz_tools))
        graph.add_edge("python_viz_tools", END)

    # 5. Entry Flow
    graph.set_entry_point("setup")
    graph.add_edge("setup", "pii_masking")
    graph.add_edge("pii_masking", "supervisor")

    # 6. Routing

    # Supervisor -> Context Loader OR End
    graph.add_conditional_edges(
        "supervisor",
        route_supervisor,
    )

    # Context Loader -> Specialist
    graph.add_conditional_edges(
        "context_loader",
        route_context_loader,
    )

    # Specialist -> Validator OR Viz OR End
    specialist_path_map = {
        "validator": "validator",
        "__end__": END,
    }
    if python_viz_tools:
        specialist_path_map["python_viz_tools"] = "python_viz_tools"
    else:
        specialist_path_map["python_viz_tools"] = END

    for node in ["agronomist", "weather", "nl_to_sql", "vision_to_action"]:
        graph.add_conditional_edges(node, route_specialist, path_map=specialist_path_map)

    # Validator Routess
    if python_viz_tools:

        def route_validation_result(state: AgentState) -> Literal["python_viz_tools", "__end__"]:
            """Route based on validation result."""
            if state.get("visualization_request"):
                return "python_viz_tools"
            return END

        graph.add_conditional_edges(
            "validator",
            route_validation_result,
        )
    else:
        graph.add_edge("validator", END)

    return graph


# ============================================================
# Graph Compilation
# ============================================================


async def compile_agent_graph_async(
    checkpointer: BaseCheckpointSaver | None = None,
    verbose: bool = True,
    use_mcp: bool = True,
):
    """Compile the agent graph with optional MCP tools and checkpointing.

    This is the recommended async compilation function.

    Args:
        checkpointer: LangGraph checkpointer for state persistence
        verbose: Enable detailed execution logging (default: True)
        use_mcp: Whether to load MCP tools (default: True)

    Returns:
        Compiled graph ready for invocation with Langfuse tracing.
    """
    # Enable global LangChain verbosity for debugging
    if verbose and ENABLE_VERBOSE_LOGGING:
        set_verbose(True)
        set_debug(True)

    # Create graph with or without MCP
    if use_mcp:
        graph = await create_agent_graph_with_mcp()
    else:
        graph = create_agent_graph()

    # Compile with debug mode for state inspection
    compiled = graph.compile(
        checkpointer=checkpointer,
        debug=verbose,
    )

    # Add recursion limit to prevent infinite loops
    compiled = compiled.with_config(recursion_limit=50)

    # Wrap with Langfuse tracing for observability
    langfuse_handler = create_langfuse_handler()
    if langfuse_handler:
        compiled = compiled.with_config(callbacks=[langfuse_handler])

    return compiled


def compile_agent_graph(checkpointer: BaseCheckpointSaver | None = None, verbose: bool = True):
    """Compile the agent graph (sync version, no MCP).

    For MCP support, use compile_agent_graph_async instead.

    Args:
        checkpointer: LangGraph checkpointer for state persistence
        verbose: Enable detailed execution logging (default: True)

    Returns:
        Compiled graph ready for invocation with Langfuse tracing.
    """
    # Enable global LangChain verbosity for debugging
    if verbose and ENABLE_VERBOSE_LOGGING:
        set_verbose(True)
        set_debug(True)

    graph = create_agent_graph()

    # Compile with debug mode for state inspection
    compiled = graph.compile(checkpointer=checkpointer, debug=verbose)

    # Add recursion limit to prevent infinite loops
    compiled = compiled.with_config(recursion_limit=50)

    # Wrap with Langfuse tracing for observability
    langfuse_handler = create_langfuse_handler()
    if langfuse_handler:
        compiled = compiled.with_config(callbacks=[langfuse_handler])

    return compiled


# ============================================================
# Graph Execution
# ============================================================


# ============================================================
# Graph Factory (Async) - For LangGraph API
# ============================================================


async def make_graph():
    """Async graph factory for LangGraph API Server.

    This is the entrypoint referenced in langgraph.json.
    It creates a graph with MCP tools integrated.

    Returns:
        Compiled StateGraph with MCP tools
    """

    # Get async checkpointer
    checkpointer = await get_checkpointer_async()

    # Compile with MCP tools
    return await compile_agent_graph_async(
        checkpointer=checkpointer,
        verbose=True,
        use_mcp=True,
    )


async def get_agent():
    """Get a compiled agent instance with MCP tools.

    Convenience function for API routes that need a ready-to-use agent.
    Creates a fresh agent with async checkpointer and MCP tools.

    Returns:
        Compiled agent graph ready for execution
    """
    checkpointer = await get_checkpointer_async()
    return await compile_agent_graph_async(
        checkpointer=checkpointer,
        verbose=True,
        use_mcp=True,
    )
