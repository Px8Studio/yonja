# src/ALİM/agent/graph.py
"""LangGraph main graph for the ALİM agent.

Defines the conversation flow as a state machine with nodes
for routing, context loading, specialist processing, validation,
and visualization.

Supports two modes:
1. Standard graph (create_agent_graph) - without MCP tools
2. MCP-enabled graph (create_agent_graph_with_mcp) - with MCP tool integration

Graph Flow (with visualizer):
    supervisor → context_loader → specialist → validator → visualizer → END
"""

from typing import Any

import structlog
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from alim.agent.memory import get_checkpointer_async
from alim.agent.nodes.agronomist import agronomist_node
from alim.agent.nodes.context_loader import context_loader_node, route_after_context
from alim.agent.nodes.nl_to_sql import nl_to_sql_node
from alim.agent.nodes.pii import pii_masking_node
from alim.agent.nodes.sql_executor import sql_executor_node
from alim.agent.nodes.supervisor import route_from_supervisor, supervisor_node
from alim.agent.nodes.validator import validator_node
from alim.agent.nodes.vision_to_action import vision_to_action_node
from alim.agent.nodes.visualizer import route_after_visualizer, visualizer_node
from alim.agent.nodes.weather import weather_node
from alim.agent.state import AgentState, setup_node
from alim.observability.langfuse import create_langfuse_handler

logger = structlog.get_logger(__name__)

# Enable LangChain verbose logging for debugging
try:
    from langchain.globals import set_debug, set_verbose

    ENABLE_VERBOSE_LOGGING = True
except ImportError:
    ENABLE_VERBOSE_LOGGING = False


# ============================================================
# Stub Nodes for HITL (Human-in-the-Loop)
# ============================================================


async def delete_parcel_node(state: AgentState) -> dict[str, Any]:
    """Placeholder node for parcel deletion (requires human approval).

    This node executes the actual deletion after human approval.
    The interrupt_before mechanism pauses the graph before this node.
    """
    logger.info("delete_parcel_node_executed", state_keys=list(state.keys()))
    return {
        "current_response": "Parsel silmə əməliyyatı icra edildi.",
        "nodes_visited": state.get("nodes_visited", []) + ["delete_parcel"],
    }


async def human_approval_node(state: AgentState) -> dict[str, Any]:
    """Placeholder node for human approval workflow.

    This node prepares the approval request for destructive operations.
    The actual approval happens via Chainlit's AskActionMessage.
    """
    logger.info("human_approval_node_executed", state_keys=list(state.keys()))
    return {
        "pending_approval": True,
        "approval_action": "delete_parcel",
        "nodes_visited": state.get("nodes_visited", []) + ["human_approval"],
    }


# ============================================================
# Graph Construction (Standard - No MCP)
# ============================================================


def create_agent_graph() -> StateGraph:
    """Create the main agent graph (without MCP tools).

    Graph Structure:
    ```
    START
      │
      ▼
    supervisor ──┬──> end (greeting/off-topic handled)
                 │
                 ▼
           context_loader
                 │
                 ├──> agronomist ──> validator ──> visualizer ──> end
                 │
                 └──> weather ──────> validator ──> visualizer ──> end
    ```

    Returns:
        Configured StateGraph ready for execution.
    """
    # Create the graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("setup", setup_node)
    graph.add_node("pii_masking", pii_masking_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("context_loader", context_loader_node)
    graph.add_node("agronomist", agronomist_node)
    graph.add_node("weather", weather_node)
    graph.add_node("nl_to_sql", nl_to_sql_node)
    graph.add_node("sql_executor", sql_executor_node)
    graph.add_node("vision_to_action", vision_to_action_node)
    graph.add_node("validator", validator_node)
    graph.add_node("visualizer", visualizer_node.with_config(tags=["final_response"]))

    # Set entry point
    graph.set_entry_point("setup")

    # Connect setup to PII masking
    graph.add_edge("setup", "pii_masking")

    # Connect PII masking to supervisor
    graph.add_edge("pii_masking", "supervisor")

    # Conditional routing from supervisor
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "end": END,
            "context_loader": "context_loader",
            "agronomist": "agronomist",
            "weather": "weather",
            "nl_to_sql": "nl_to_sql",
            "vision_to_action": "vision_to_action",
        },
    )

    # Route from context loader to specialist
    graph.add_conditional_edges(
        "context_loader",
        route_after_context,
        {
            "agronomist": "agronomist",
            "weather": "weather",
            "nl_to_sql": "nl_to_sql",
            "vision_to_action": "vision_to_action",
        },
    )

    # Specialist nodes go to validator
    graph.add_edge("agronomist", "validator")
    graph.add_edge("weather", "validator")
    graph.add_edge("nl_to_sql", "sql_executor")
    graph.add_edge("sql_executor", "validator")
    graph.add_edge("vision_to_action", "validator")

    # Validator goes to visualizer (reflection step)
    graph.add_edge("validator", "visualizer")

    # Visualizer goes to end
    graph.add_edge("visualizer", END)

    return graph


# ============================================================
# Graph Construction (With MCP Tools)
# ============================================================


async def create_agent_graph_with_mcp() -> StateGraph:
    """Create agent graph with MCP tools integrated.

    This is the recommended factory for production use.
    It loads tools from configured MCP servers and adds a ToolNode
    for automatic tool execution.

    Graph Structure:
    ```
    START
      │
      ▼
    supervisor ──┬──> end
                 │
                 ├──> context_loader ──> specialist ──> validator ──> visualizer ──> end
                 │
                 ├──> mcp_tools ──> context_loader (if tools return context)
                 │
                 └──> python_viz_tools ──> end (visualization generation)
    ```

    Returns:
        StateGraph with MCP tools integrated
    """
    from alim.mcp.adapters import get_mcp_tools, get_python_viz_tools

    # Load MCP tools (returns empty list if no servers enabled)
    mcp_tools = await get_mcp_tools()
    python_viz_tools = await get_python_viz_tools()

    # Create base graph
    # Create base graph
    graph = StateGraph(AgentState)

    # Add standard nodes
    graph.add_node("setup", setup_node)
    graph.add_node("pii_masking", pii_masking_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("context_loader", context_loader_node)
    graph.add_node("agronomist", agronomist_node)
    graph.add_node("weather", weather_node)
    graph.add_node("nl_to_sql", nl_to_sql_node)
    graph.add_node("sql_executor", sql_executor_node)
    graph.add_node("vision_to_action", vision_to_action_node)
    graph.add_node("validator", validator_node)
    graph.add_node("visualizer", visualizer_node)

    # Add HITL nodes for destructive operations
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("delete_parcel", delete_parcel_node)

    # Add MCP ToolNode if tools are available
    if mcp_tools:
        graph.add_node("mcp_tools", ToolNode(mcp_tools))
        logger.info(
            "mcp_tools_added_to_graph",
            tool_count=len(mcp_tools),
            tool_names=[t.name for t in mcp_tools],
        )
    else:
        logger.info("mcp_tools_not_available", reason="no_tools_loaded")

    # Add Python Viz MCP ToolNode for visualization
    if python_viz_tools:
        graph.add_node("python_viz_tools", ToolNode(python_viz_tools))
        logger.info(
            "python_viz_tools_added_to_graph",
            tool_count=len(python_viz_tools),
            tool_names=[t.name for t in python_viz_tools],
        )
    else:
        logger.info("python_viz_tools_not_available", reason="no_tools_loaded")

    # Set entry point
    # Set entry point
    # Set entry point
    graph.set_entry_point("setup")

    # Connect setup to PII masking
    graph.add_edge("setup", "pii_masking")

    # Connect PII masking to supervisor
    graph.add_edge("pii_masking", "supervisor")

    # Build routing destinations
    routing_map = {
        "end": END,
        "context_loader": "context_loader",
        "agronomist": "agronomist",
        "weather": "weather",
        "nl_to_sql": "nl_to_sql",
        "vision_to_action": "vision_to_action",
        "human_approval": "human_approval",
    }

    # Add mcp_tools route if available
    if mcp_tools:
        routing_map["mcp_tools"] = "mcp_tools"

    # Conditional routing from supervisor
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        routing_map,
    )

    # Route from context loader to specialist
    graph.add_conditional_edges(
        "context_loader",
        route_after_context,
        {
            "agronomist": "agronomist",
            "weather": "weather",
            "nl_to_sql": "nl_to_sql",
            "vision_to_action": "vision_to_action",
        },
    )

    # Specialist nodes go to validator
    graph.add_edge("agronomist", "validator")
    graph.add_edge("weather", "validator")
    graph.add_edge("nl_to_sql", "sql_executor")
    graph.add_edge("sql_executor", "validator")
    graph.add_edge("vision_to_action", "validator")

    # Validator goes to visualizer (reflection step)
    graph.add_edge("validator", "visualizer")

    # Visualizer conditional routing
    if python_viz_tools:
        graph.add_conditional_edges(
            "visualizer",
            route_after_visualizer,
            {
                "python_viz_tools": "python_viz_tools",
                "end": END,
            },
        )
        # Python viz tools go to end after generating visualization
        graph.add_edge("python_viz_tools", END)
    else:
        # No viz tools, go straight to end
        graph.add_edge("visualizer", END)

    # MCP tools go to context_loader (to enrich context with tool results)
    if mcp_tools:
        graph.add_edge("mcp_tools", "context_loader")

    # HITL flow for destructive operations
    graph.add_edge("human_approval", "delete_parcel")
    graph.add_edge("delete_parcel", "validator")

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
    compiled = graph.compile(checkpointer=checkpointer, debug=verbose)

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
