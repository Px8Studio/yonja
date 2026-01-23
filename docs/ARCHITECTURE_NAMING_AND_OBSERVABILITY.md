# 🏷️ Architecture: Naming & Observability

> **Purpose:** Clarify naming conventions and logging visibility gaps
> **Updated:** January 23, 2026

---

## 🎯 Naming Clarification

### The "Scenario" Terminology Problem

**Current naming** (`farm_scenario_plans`, `save_farm_scenario()`) implies **physical farm planning**.

**Reality:** We're storing **conversation parameters for role-play**:
- Agent persona configurations
- Hypothetical thinking contexts
- Dialogue session settings

### Semantic Map

```
┌─────────────────────────────────────────────────────┐
│ CONVERSATION CONTEXT (Not "Farm Scenario")          │
├─────────────────────────────────────────────────────┤
│ What: User-defined parameters for agent behavior    │
│ Contains:                                           │
│   • Crop type → conversation focus                  │
│   • Region → climate context for role               │
│   • Expertise level → agent persona complexity      │
│   • Action categories → dialogue scope              │
│                                                     │
│ Analogy: User = Director, Agent = Actor,            │
│          "Scenario" = Acting instructions           │
└─────────────────────────────────────────────────────┘
```

### Proposed Renames (Deferred)

| Old | New | Status |
|:----|:----|:------:|
| `farm_scenario_plans` | `conversation_contexts` | ⬜ Batch with next migration |
| `save_farm_scenario()` | `save_conversation_context()` | ⬜ Deferred |
| `ScenarioContext` | `ConversationContext` | ⬜ Deferred |

---

## 🔍 LangGraph Observability

### The Visibility Gap

**What you see** (server-level):
```
[info] Worker stats    active=0 available=1 max=1
[info] Queue stats     n_pending=0 n_running=0
```

**What you need** (application-level):
- ❌ Node execution traces
- ❌ State transitions
- ❌ LLM call logs
- ❌ Message flow between nodes

### 3-Layer Logging Strategy

```
┌────────────────────────────────────────────────────┐
│ LAYER 1: LangChain Native (Environment Variables)  │
├────────────────────────────────────────────────────┤
│ LANGCHAIN_TRACING_V2=true                          │
│ set_verbose(True); set_debug(True)                 │
└────────────────────────────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────┐
│ LAYER 2: Node-Level Instrumentation (structlog)    │
├────────────────────────────────────────────────────┤
│ Every node logs: entry, exit, decisions, errors    │
│ Include: thread_id, intent, conversation_stage     │
└────────────────────────────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────┐
│ LAYER 3: Langfuse Integration (Visual UI)          │
├────────────────────────────────────────────────────┤
│ See traces at http://localhost:3001                │
│ Trace view: node timings, LLM costs, state flow    │
└────────────────────────────────────────────────────┘
```

### Environment Variables

```env
# Layer 1: LangChain/LangGraph Verbosity
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=yonca-dev
LOG_LEVEL=DEBUG

# Layer 3: Langfuse
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_secret
LANGFUSE_HOST=http://localhost:3001
```

---

## 💡 Key Insight

> **Server logs** = "HTTP requests received, workers available"
> **Agent logs** = "Which node ran, what LLM said, what decision was made"
>
> You have #1 but need #2. Instrument the **agent**, not just the **server**.

---

## ✅ Implementation Status

| Phase | Task | Status |
|:------|:-----|:------:|
| 1 | Enable native logging (env vars) | ⬜ 15 min |
| 2 | Rename database schema | ⬜ Deferred |
| 3 | Add node-level logging | ⬜ 1 hour |
| 4 | Langfuse integration | ⬜ 30 min |

**Recommendation:** Start with Phase 1 (zero code changes, immediate visibility).
