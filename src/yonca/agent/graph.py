# src/yonca/agent/graph.py
"""LangGraph main graph for the Yonca AI agent.

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
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from yonca.agent.memory import get_checkpointer
from yonca.agent.nodes.agronomist import agronomist_node
from yonca.agent.nodes.context_loader import context_loader_node, route_after_context
from yonca.agent.nodes.nl_to_sql import nl_to_sql_node
from yonca.agent.nodes.sql_executor import sql_executor_node
from yonca.agent.nodes.supervisor import route_from_supervisor, supervisor_node
from yonca.agent.nodes.validator import validator_node
from yonca.agent.nodes.vision_to_action import vision_to_action_node
from yonca.agent.nodes.visualizer import route_after_visualizer, visualizer_node
from yonca.agent.nodes.weather import weather_node
from yonca.agent.state import AgentState, create_initial_state
from yonca.observability.langfuse import create_langfuse_handler

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
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("context_loader", context_loader_node)
    graph.add_node("agronomist", agronomist_node)
    graph.add_node("weather", weather_node)
    graph.add_node("nl_to_sql", nl_to_sql_node)
    graph.add_node("sql_executor", sql_executor_node)
    graph.add_node("vision_to_action", vision_to_action_node)
    graph.add_node("validator", validator_node)
    graph.add_node("visualizer", visualizer_node)

    # Set entry point
    graph.set_entry_point("supervisor")

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
    from yonca.mcp.adapters import get_mcp_tools, get_python_viz_tools

    # Load MCP tools (returns empty list if no servers enabled)
    mcp_tools = await get_mcp_tools()
    python_viz_tools = await get_python_viz_tools()

    # Create base graph
    graph = StateGraph(AgentState)

    # Add standard nodes
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
    graph.set_entry_point("supervisor")

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


class YoncaAgent:
    """Main Yonca AI agent interface.

    Provides a clean API for interacting with the agent graph,
    handling thread management and state persistence.

    Example:
        ```python
        agent = YoncaAgent()

        # Start a new conversation
        response = await agent.chat(
            message="Pomidorları nə vaxt suvarmaq lazımdır?",
            user_id="user_123",
        )
        print(response.content)

        # Continue the conversation
        response = await agent.chat(
            message="Bəs gübrə?",
            thread_id=response.thread_id,
        )
        ```
    """

    def __init__(self, use_checkpointer: bool = True):
        """Initialize the agent.

        Args:
            use_checkpointer: Whether to enable state persistence
        """
        self.use_checkpointer = use_checkpointer
        self._graph = None
        self._checkpointer = None

    async def _get_graph(self):
        """Get or create the compiled graph."""
        if self._graph is None:
            if self.use_checkpointer:
                self._checkpointer = get_checkpointer()
                self._graph = compile_agent_graph(self._checkpointer)
            else:
                self._graph = compile_agent_graph()

        return self._graph

    async def chat(
        self,
        message: str,
        thread_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        language: str = "az",
    ) -> "AgentResponse":
        """Send a message and get a response.

        Args:
            message: The user's message
            thread_id: Conversation thread ID (creates new if None)
            user_id: Authenticated user ID (for context loading)
            session_id: API session ID
            language: Response language (default: Azerbaijani)

        Returns:
            AgentResponse with the response and metadata
        """
        import uuid

        # Create or use thread ID
        if thread_id is None:
            thread_id = f"thread_{uuid.uuid4().hex[:12]}"

        # Create initial state
        initial_state = create_initial_state(
            thread_id=thread_id,
            user_input=message,
            user_id=user_id,
            session_id=session_id,
            language=language,
        )

        # Run the graph
        graph = await self._get_graph()

        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # Add Langfuse callback for self-hosted observability
        # Traces appear at: http://localhost:3001 (Langfuse dashboard)
        # ✅ CRITICAL: session_id parameter maps to thread_id for correlation
        #    This ensures Langfuse traces are grouped by conversation thread
        langfuse_handler = create_langfuse_handler(
            session_id=thread_id,  # ✅ Maps thread_id → Langfuse session
            user_id=user_id,
            tags=["yonca", "chat", language],
            metadata={
                "session_id": session_id,  # API session ID (different from thread)
                "language": language,
            },
            trace_name=f"yonca_chat_{thread_id[:8]}",
        )

        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]

        final_state = await graph.ainvoke(initial_state, config=config)

        # Extract response
        response_content = final_state.get("current_response", "")

        return AgentResponse(
            content=response_content,
            thread_id=thread_id,
            intent=final_state.get("intent"),
            intent_confidence=final_state.get("intent_confidence", 0.0),
            nodes_visited=final_state.get("nodes_visited", []),
            alerts=[a for a in final_state.get("alerts", [])],
            matched_rules=[r for r in final_state.get("matched_rules", [])],
            error=final_state.get("error"),
        )

    async def stream_chat(
        self,
        message: str,
        thread_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        language: str = "az",
    ):
        """Stream a response token by token.

        Yields tokens as they are generated for real-time display.

        Args:
            message: The user's message
            thread_id: Conversation thread ID
            user_id: Authenticated user ID
            session_id: API session ID
            language: Response language

        Yields:
            Dict with 'type' (token/metadata/final) and content
        """
        import uuid

        if thread_id is None:
            thread_id = f"thread_{uuid.uuid4().hex[:12]}"

        initial_state = create_initial_state(
            thread_id=thread_id,
            user_input=message,
            user_id=user_id,
            session_id=session_id,
            language=language,
        )

        graph = await self._get_graph()

        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # Add Langfuse callback for streaming observability
        # ✅ CRITICAL: session_id=thread_id for conversation tracking
        langfuse_handler = create_langfuse_handler(
            session_id=thread_id,  # ✅ Maps thread_id → Langfuse session
            user_id=user_id,
            tags=["yonca", "stream", language],
            metadata={"session_id": session_id, "language": language},
            trace_name=f"yonca_stream_{thread_id[:8]}",
        )

        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]

        # Stream execution
        async for event in graph.astream(initial_state, config=config):
            # Yield intermediate states
            for node_name, node_output in event.items():
                if node_name == "agronomist":
                    # Check for response
                    if "current_response" in node_output:
                        yield {
                            "type": "response",
                            "content": node_output["current_response"],
                            "node": node_name,
                        }
                elif node_name == "weather":
                    if "current_response" in node_output:
                        yield {
                            "type": "response",
                            "content": node_output["current_response"],
                            "node": node_name,
                        }
                elif node_name == "supervisor":
                    if "current_response" in node_output:
                        yield {
                            "type": "response",
                            "content": node_output["current_response"],
                            "node": node_name,
                        }
                elif node_name == "validator":
                    if "matched_rules" in node_output and node_output["matched_rules"]:
                        yield {
                            "type": "rules",
                            "content": node_output["matched_rules"],
                            "node": node_name,
                        }

        yield {
            "type": "final",
            "thread_id": thread_id,
        }

    async def get_conversation_history(
        self,
        thread_id: str,
    ) -> list[dict]:
        """Get conversation history for a thread.

        Uses LangGraph's checkpointer to retrieve the latest state.

        Args:
            thread_id: Thread ID

        Returns:
            List of messages
        """
        if not self._checkpointer:
            return []

        try:
            # Use LangGraph's standard interface
            config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
            checkpoint_tuple = await self._checkpointer.aget_tuple(config)
            if checkpoint_tuple and checkpoint_tuple.checkpoint:
                return checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
        except Exception:
            pass

        return []

    async def delete_conversation(self, thread_id: str) -> bool:
        """Delete a conversation and its history.

        Uses LangGraph's checkpointer to delete thread data.

        Args:
            thread_id: Thread ID to delete

        Returns:
            True if deleted successfully
        """
        if not self._checkpointer:
            return False

        try:
            # Use LangGraph's standard interface - adelete_thread takes thread_id directly
            await self._checkpointer.adelete_thread(thread_id)
            return True
        except Exception:
            return False


class AgentResponse:
    """Response from the Yonca agent."""

    def __init__(
        self,
        content: str,
        thread_id: str,
        intent: Any = None,
        intent_confidence: float = 0.0,
        nodes_visited: list[str] | None = None,
        alerts: list[dict] | None = None,
        matched_rules: list[dict] | None = None,
        error: str | None = None,
    ):
        self.content = content
        self.thread_id = thread_id
        self.intent = intent
        self.intent_confidence = intent_confidence
        self.nodes_visited = nodes_visited or []
        self.alerts = alerts or []
        self.matched_rules = matched_rules or []
        self.error = error

    @property
    def has_alerts(self) -> bool:
        """Check if there are any alerts."""
        return len(self.alerts) > 0

    @property
    def has_errors(self) -> bool:
        """Check if there were any errors."""
        return self.error is not None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "thread_id": self.thread_id,
            "intent": self.intent.value if self.intent else None,
            "intent_confidence": self.intent_confidence,
            "nodes_visited": self.nodes_visited,
            "alerts": self.alerts,
            "matched_rules": self.matched_rules,
            "error": self.error,
        }


# ============================================================
# Singleton Agent Instance
# ============================================================

_agent: YoncaAgent | None = None


def get_agent(use_checkpointer: bool = True) -> YoncaAgent:
    """Get the singleton agent instance.

    Args:
        use_checkpointer: Whether to use Redis checkpointing

    Returns:
        YoncaAgent instance
    """
    global _agent
    if _agent is None:
        _agent = YoncaAgent(use_checkpointer=use_checkpointer)
    return _agent


async def make_graph():
    """Async graph factory for LangGraph API Server.

    This is the entrypoint referenced in langgraph.json.
    It creates a graph with MCP tools integrated.

    Returns:
        Compiled StateGraph with MCP tools
    """
    from yonca.agent.memory import get_checkpointer_async

    # Get async checkpointer
    checkpointer = await get_checkpointer_async()

    # Compile with MCP tools
    return await compile_agent_graph_async(
        checkpointer=checkpointer,
        verbose=True,
        use_mcp=True,
    )
