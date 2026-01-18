# src/yonca/agent/graph.py
"""LangGraph main graph for the Yonca AI agent.

Defines the conversation flow as a state machine with nodes
for routing, context loading, specialist processing, and validation.
"""

from typing import Any, Literal

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver

from yonca.agent.memory import get_checkpointer
from yonca.agent.nodes.agronomist import agronomist_node
from yonca.agent.nodes.context_loader import context_loader_node, route_after_context
from yonca.agent.nodes.supervisor import route_from_supervisor, supervisor_node
from yonca.agent.nodes.validator import validator_node
from yonca.agent.nodes.weather import weather_node
from yonca.agent.state import AgentState, create_initial_state


# ============================================================
# Graph Construction
# ============================================================

def create_agent_graph() -> StateGraph:
    """Create the main agent graph.
    
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
                 ├──> agronomist ──> validator ──> end
                 │
                 └──> weather ──────> validator ──> end
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
    graph.add_node("validator", validator_node)
    
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
        },
    )
    
    # Route from context loader to specialist
    graph.add_conditional_edges(
        "context_loader",
        route_after_context,
        {
            "agronomist": "agronomist",
            "weather": "weather",
        },
    )
    
    # Specialist nodes go to validator
    graph.add_edge("agronomist", "validator")
    graph.add_edge("weather", "validator")
    
    # Validator goes to end
    graph.add_edge("validator", END)
    
    return graph


def compile_agent_graph(checkpointer: BaseCheckpointSaver | None = None):
    """Compile the agent graph with optional checkpointing.
    
    Args:
        checkpointer: LangGraph checkpointer for state persistence
                     (RedisSaver, MemorySaver, or any BaseCheckpointSaver)
        
    Returns:
        Compiled graph ready for invocation.
    """
    graph = create_agent_graph()
    
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    
    return graph.compile()


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
        
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        
        # Add metadata for farm ID and user region
        config["metadata"] = {"farm_id": "your_farm_id", "user_region": "Baku"}
        
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
        
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        
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
            config = {"configurable": {"thread_id": thread_id}}
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
