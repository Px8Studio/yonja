---
description: LangGraph patterns and best practices for ALİM agent development
---

# LangGraph Development Patterns

This document defines LangGraph best practices for the ALİM agricultural AI agent.

## State Schema Patterns

### TypedDict with Reducers
Always use `TypedDict` with `Annotated` for reducer fields:

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict, total=False):
    # Use add_messages reducer for conversation history
    messages: Annotated[list, add_messages]
    
    # Custom reducer for deduplication
    alerts: Annotated[list[dict], _merge_alerts]
    
    # Simple fields (overwrite behavior)
    current_response: str | None
```

### Required Reducer Functions
- Use `add_messages` for message lists (handles deduplication by ID)
- Create custom reducers for domain data requiring merge logic

## Node Function Patterns

### Standard Node Signature
```python
async def node_name(
    state: AgentState, 
    config: RunnableConfig | None = None
) -> dict[str, Any]:
    """Node docstring with clear purpose."""
    try:
        # Node logic
        return {
            "field_to_update": value,
            "nodes_visited": state.get("nodes_visited", []) + ["node_name"],
        }
    except Exception as e:
        logger.exception("node_error", node="node_name")
        return {
            "error": str(e),
            "error_node": "node_name",
            "nodes_visited": state.get("nodes_visited", []) + ["node_name"],
        }
```

### Key Rules
1. **Always return a dict** - never return the full state
2. **Track visited nodes** - append node name to `nodes_visited`
3. **Handle errors** - catch exceptions and set error fields
4. **Accept config** - use `RunnableConfig` for model overrides

## Graph Construction

### Entry Point
Use `set_entry_point` exactly once:
```python
graph = StateGraph(AgentState)
graph.add_node("setup", setup_node)
graph.set_entry_point("setup")  # Only once!
```

### Edge Types
1. **Normal edges** - deterministic routing:
   ```python
   graph.add_edge("agronomist", "validator")
   ```

2. **Conditional edges** - dynamic routing without state update:
   ```python
   graph.add_conditional_edges(
       "supervisor",
       route_from_supervisor,
       {"agronomist": "agronomist", "end": END}
   )
   ```

### Compilation with HITL
Always specify interrupt points for destructive operations:
```python
compiled = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_approval", "delete_parcel"],
)
```

## Checkpointer Best Practices

### Priority Order
1. **PostgreSQL** (production) - durable, queryable
2. **Redis** (development) - fast, ephemeral  
3. **Memory** (testing) - no persistence

### Async Initialization
```python
checkpointer = await get_checkpointer_async(backend="auto")
compiled = graph.compile(checkpointer=checkpointer)
```

## Error Handling

### Node-Level Errors
Set error fields in state, don't raise exceptions:
```python
return {
    "error": str(e),
    "error_node": "node_name",
}
```

### Graph-Level Recovery
Use conditional edges to route to error handler:
```python
def route_after_node(state):
    if state.get("error"):
        return "error_handler"
    return "next_node"
```

## Streaming Modes

Use appropriate stream modes for different scenarios:
- `"values"` - full state after each node
- `"updates"` - state changes only
- `"messages"` - LLM tokens for real-time display

## Common Anti-Patterns to Avoid

❌ **Don't** mutate state directly - always return updates  
❌ **Don't** use `create_react_agent` - build custom graphs  
❌ **Don't** skip checkpointer in production  
❌ **Don't** forget `nodes_visited` tracking  
❌ **Don't** duplicate entry point declarations  
