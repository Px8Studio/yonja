# Architecture: Naming Conventions & Observability

**Date:** January 21, 2026
**Issue:** Misleading naming ("farm_scenario") + Insufficient LangGraph execution visibility

---

## 🎯 Problem Statement

### 1. Naming Mismatch
Current naming (`farm_scenario_plans`, `save_farm_scenario()`) implies **physical farm planning**, but the reality is:

**What we're actually storing:**
- Conversation parameters for role-play
- Hypothetical thinking contexts
- Agent persona configurations
- Dialogue session settings

**Analogy:**
- User = Director setting the scene
- Agent = Actor playing a role
- "Scenario" = The parameters defining that role (crop, region, expertise)
- Conversation = The improvised performance within those constraints

### 2. Logging Visibility Gap
**Current LangGraph Server Logs:**
```
[info] Worker stats    active=0 available=1 max=1
[info] Queue stats     n_pending=0 n_running=0
```

**What's Missing:**
❌ No node execution traces
❌ No state transitions
❌ No LLM call logs
❌ No message flow between nodes
❌ No error details from agent logic

---

## 📚 Proposed Naming Refactor

### Database Table Rename
```sql
-- OLD (Misleading)
farm_scenario_plans

-- NEW (Accurate)
conversation_contexts
-- OR
agent_session_profiles
-- OR
dialogue_parameters
```

### Function Rename Map
```python
# OLD → NEW
save_farm_scenario()     → save_conversation_context()
load_farm_scenario()     → load_conversation_context()
scenario_context         → conversation_context
farm_scenario_plans      → conversation_contexts table

# State Field
ScenarioContext          → ConversationContext
scenario_context: dict   → conversation_context: dict
```

### Semantic Clarity
```
┌─────────────────────────────────────────────────────┐
│ CONVERSATION CONTEXT                                │
│                                                     │
│ What: User-defined parameters for agent behavior   │
│ Why:  Enable role-play and hypothetical reasoning  │
│ How:  Stored per thread, evolves with dialogue     │
│                                                     │
│ Contains:                                           │
│ - Crop type (conversation focus)                   │
│ - Region (climate context for role)                │
│ - Expertise level (agent persona complexity)       │
│ - Soil/irrigation (scenario constraints)           │
│ - Action categories (dialogue scope)               │
│ - Conversation stage (progression tracking)        │
│                                                     │
│ NOT a farm plan - it's agent acting instructions!  │
└─────────────────────────────────────────────────────┘
```

---

## 🔍 LangGraph Observability Enhancement

### Current Setup Analysis
✅ **What Works:**
- `debug=True` in `compile_agent_graph()` (just added)
- LangSmith organization configured (in langgraph-api logs)
- Langfuse running on port 3001
- Checkpointer persisting state to Redis/Postgres

❌ **What's Missing:**
- Agent execution traces not visible in logs
- Node-to-node flow not logged
- LLM calls not captured in console output
- Error details buried

### Solution: 3-Layer Logging Strategy

#### Layer 1: LangChain Callbacks (Native)
Enable verbose logging with structured callbacks:

```python
# src/yonca/agent/graph.py
from langchain.globals import set_verbose, set_debug

def compile_agent_graph(checkpointer=None, verbose=True):
    """Compile with verbose execution logging."""

    # Enable global LangChain verbosity
    if verbose:
        set_verbose(True)
        set_debug(True)

    graph = create_agent_graph()

    # Compile with debug mode
    return graph.compile(
        checkpointer=checkpointer,
        debug=True,  # Already added
        interrupt_before=[],  # Optional: for human-in-loop
        interrupt_after=[],
    )
```

#### Layer 2: Node-Level Instrumentation
Add structured logging to every node:

```python
# src/yonca/agent/nodes/supervisor.py
import structlog

logger = structlog.get_logger(__name__)

async def supervisor_node(state: AgentState, config: RunnableConfig):
    """Route with detailed logging."""

    logger.info(
        "supervisor_node_start",
        thread_id=config.get("configurable", {}).get("thread_id"),
        message=state["messages"][-1].content[:100],
        conversation_stage=state.get("conversation_context", {}).get("conversation_stage"),
    )

    # ... existing logic ...

    logger.info(
        "supervisor_node_complete",
        route_decision=next_node,
        intent_detected=state.get("intent"),
    )

    return state
```

#### Layer 3: Langfuse Trace Integration
Stream execution to Langfuse UI (http://localhost:3001):

```python
# src/yonca/agent/graph.py
from langfuse.callback import CallbackHandler

def compile_agent_graph(checkpointer=None):
    """Compile with Langfuse tracing."""
    from yonca.observability.langfuse import create_langfuse_handler

    graph = create_agent_graph()
    compiled = graph.compile(checkpointer=checkpointer, debug=True)

    # Wrap with Langfuse tracing
    langfuse_handler = create_langfuse_handler()
    if langfuse_handler:
        compiled = compiled.with_config(callbacks=[langfuse_handler])

    return compiled
```

### Environment Variables for Verbose Logging

Create `.env` settings:

```bash
# .env (root)

# LangChain/LangGraph Verbosity
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=yonca-dev
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_key_here  # Optional if using local only

# Langfuse Observability
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_secret
LANGFUSE_HOST=http://localhost:3001

# Python Logging Level
LOG_LEVEL=DEBUG  # or INFO for less verbose

# LangGraph API Verbosity
LANGGRAPH_API_LOG_LEVEL=DEBUG
```

### langgraph.json Enhancement

```json
{
    "$schema": "https://langchain-ai.github.io/langgraph/langgraph.json",
    "dependencies": ["."],
    "graphs": {
        "yonca_agent": "./src/yonca/agent/graph.py:create_agent_graph"
    },
    "env": ".env",
    "python_version": "3.11",
    "store": {
        "type": "postgres",
        "uri": "postgresql://yonca:yonca_dev_password@localhost:5433/yonca"
    }
}
```

---

## 🎨 Expected Output After Implementation

### Console Logs (Structured JSON)
```json
{
  "event": "supervisor_node_start",
  "timestamp": "2026-01-21T06:45:32.123Z",
  "thread_id": "abc-123",
  "message": "Pambıqda xəstəlik necə müalicə edilir?",
  "conversation_context": {
    "crop": "Pambıq",
    "region": "Aran",
    "stage": "problem_solving"
  }
}

{
  "event": "llm_call",
  "model": "gpt-4",
  "input_tokens": 1234,
  "output_tokens": 567,
  "latency_ms": 2345
}

{
  "event": "supervisor_node_complete",
  "route_decision": "agronomist",
  "intent": "disease_treatment"
}
```

### Langfuse UI (http://localhost:3001)
```
┌─────────────────────────────────────────────────────┐
│ Trace: Conversation abc-123                         │
├─────────────────────────────────────────────────────┤
│ ├─ supervisor_node         250ms                    │
│ │   ├─ LLM: gpt-4          200ms                    │
│ │   └─ Decision: agronomist 50ms                    │
│ ├─ context_loader_node     100ms                    │
│ │   └─ DB Query            100ms                    │
│ ├─ agronomist_node         3500ms                   │
│ │   ├─ LLM: gpt-4          3200ms                   │
│ │   └─ Response format     300ms                    │
│ └─ validator_node          150ms                    │
│                                                      │
│ Total: 4000ms | Cost: $0.03 | Success: ✅           │
└─────────────────────────────────────────────────────┘
```

### LangGraph Studio (https://smith.langchain.com/studio)
Visual graph with live state inspection:
- See which node is currently executing
- Inspect state after each node
- Replay conversations step-by-step
- Time travel debugging

---

## 🚀 Implementation Plan

### Phase 1: Enable Native Logging (15 min)
1. Add environment variables to `.env`
2. Update `compile_agent_graph()` with `set_verbose(True)`
3. Restart LangGraph server
4. Test: Send message, verify logs show node execution

### Phase 2: Rename Database Schema (30 min)
1. Create Alembic migration: `conversation_contexts` table
2. Add backward compatibility view: `CREATE VIEW farm_scenario_plans AS SELECT * FROM conversation_contexts`
3. Update function names in `data_layer.py`
4. Update imports in `app.py`
5. Run migration, verify no breakage

### Phase 3: Add Node Logging (1 hour)
1. Create `logging_middleware.py` decorator
2. Apply to all 8 nodes (supervisor, agronomist, weather, etc.)
3. Log entry/exit with state summary
4. Capture errors with full context

### Phase 4: Langfuse Integration (30 min)
1. Configure Langfuse callback in `compile_agent_graph()`
2. Test trace appears in http://localhost:3001
3. Document trace exploration workflow

---

## 📖 Recommendation

**Start with Phase 1** (Native Logging) - it requires zero code changes, just environment variables. This gives you immediate visibility into agent execution.

**Then Phase 3** (Node Logging) - adds structured events to your existing logs.

**Defer Phase 2** (Renaming) - it's cosmetic and can be batched with next schema update.

**Phase 4** (Langfuse) - Nice-to-have for visual debugging, but console logs may be sufficient.

---

## 💡 Key Insight

The LangGraph logs you're seeing are **server-level** (queue management), not **application-level** (agent execution). You need to instrument the agent itself, not just the server hosting it.

Think of it like:
- **Server logs** = "HTTP requests received, workers available"
- **Agent logs** = "Which node ran, what LLM said, what decision was made"

You have #1 but need #2!
