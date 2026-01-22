# 🎯 Chat UI: Model Selection & Interaction Mode

> **Purpose:** Clear documentation of the dual-selection UI architecture for model and interaction mode
> **Status:** Implemented and tested
> **Updated:** January 22, 2026

---

## 🎨 UI Architecture Overview

The Yonca/ALEM chat UI uses a **two-part selection system** that respects Chainlit's architectural constraints:

```
┌─────────────────────────────────────────────────────────────┐
│ CHAINLIT HEADER                                              │
│ [🌿 Yonca ALEM] [Model: Qwen3 4B ▼] [⚙️ Settings]          │
│                   ↑                        ↑                 │
│            Chat Profiles              Settings Menu          │
│            (persistent)               (dynamic)             │
└─────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
    ┌─────────────┐           ┌──────────────────────┐
    │ Header      │           │ Sidebar Panel        │
    │ Dropdown    │           │ (Slides from right)  │
    │             │           │                      │
    │ • Qwen3 4B  │           │ 💬 Rejim / Mode:    │
    │ • ATLlama   │           │    ○ Ask             │
    │ • Llama     │           │    ○ Plan            │
    │ • Mistral   │           │    ○ Agent           │
    │ • Gemma     │           │                      │
    └─────────────┘           │ 🌾 Farm Settings    │
         │                    │ 📊 Other Prefs      │
         ▼                    └──────────────────────┘
    Persistent                       │
    (entire session)                 ▼
                             Dynamic
                             (can change mid-conversation)
```

---

## 📋 Selection Details

### 1. LLM Model Selection (Header Dropdown)

**Location:** Chat Profile selector in header
**UI Control:** `@cl.set_chat_profiles`
**Implementation:** [demo-ui/app.py, lines 405-430](../demo-ui/app.py#L405-L430)

#### Characteristics

| Aspect | Value |
|--------|-------|
| **Persistence** | ✅ Lasts entire session |
| **Changeable** | Requires page reload to switch |
| **Visibility** | Always visible (header) |
| **Scope** | Applies to ALL future messages |
| **Storage** | `cl.user_session.get("chat_profile")` |
| **Flow to Graph** | `config["metadata"]["model"]` |

#### Available Models

```python
LLM_MODEL_PROFILES = {
    "qwen3:4b": ChatProfile(
        name="Qwen3 4B",
        markdown_description="Fastest, lightweight, ideal for mobile",
        icon_url="https://..."
    ),
    "atllama:7b": ChatProfile(
        name="ATLlama 7B",
        markdown_description="Balanced speed and quality",
        ...
    ),
    "llama3:7b": ChatProfile(
        name="Llama 3 7B",
        markdown_description="High quality, slower",
        ...
    ),
    "mistral:7b": ChatProfile(
        name="Mistral 7B",
        markdown_description="Reasoning tasks",
        ...
    ),
    "gemma:7b": ChatProfile(
        name="Gemma 7B",
        markdown_description="Google's lightweight model",
        ...
    ),
}
```

#### Implementation

**In Chainlit:**
```python
@cl.set_chat_profiles
async def chat_profiles():
    """Return available LLM models as Chat Profiles"""
    return [
        ChatProfile(
            name=profile.name,
            markdown_description=profile.markdown_description,
            icon_url=profile.icon_url,
        )
        for profile in LLM_MODEL_PROFILES.values()
    ]
```

**Reading the Selection:**
```python
# In any message handler or setup function
model_name = cl.user_session.get("chat_profile")
# → "qwen3:4b" or "atllama:7b", etc.
```

**Passing to Graph:**
```python
# In message handler
config = {"metadata": {"model": model_name}}
response = await graph.ainvoke(state, config=config)
```

#### Node Usage

Every node receives `config` and extracts the model:

```python
from yonca.llm import get_llm_from_config

async def agronomist_node(state: AgentState, config: RunnableConfig | None = None):
    # Get model from user's Chat Profile selection
    provider = get_llm_from_config(config)

    # Use selected model (not cached default)
    response = await provider.ainvoke(prompt)
    return {"messages": [response]}
```

---

### 2. Interaction Mode Selection (Settings Sidebar)

**Location:** Chat Settings sidebar (right panel)
**UI Control:** `@cl.on_chat_settings_update`
**Implementation:** [demo-ui/app.py, lines 1334-1400](../demo-ui/app.py#L1334-L1400)

#### Characteristics

| Aspect | Value |
|--------|-------|
| **Persistence** | ⚠️ Session-only (lost on page reload) |
| **Changeable** | ✅ Can change at ANY time |
| **Visibility** | Settings panel (click ⚙️) |
| **Scope** | Applies to NEXT message only |
| **Storage** | `cl.user_session["chat_settings"]` |
| **Flow to State** | `state.metadata["interaction_mode"]` |

#### Available Modes

```python
mode_values = [
    "Ask",      # 🎤 Ask Question - Direct answer
    "Plan",     # 📋 Plan - Month-by-month breakdown
    "Agent",    # 🤖 Agent - Multi-step reasoning
]
```

#### Implementation

**In Chainlit:**
```python
async def setup_chat_settings():
    """Configure sidebar settings"""
    await cl.ChatSettings(
        [
            Select(
                id="interaction_mode",
                label="💬 Rejim / Interaction Mode",
                values=["Ask", "Plan", "Agent"],
                initial_index=0,
            ),
            # ... other settings
        ]
    ).send()

@cl.on_settings_update
async def settings_update(settings):
    """Handle mode change mid-conversation"""
    mode = settings["interaction_mode"]
    cl.user_session["chat_settings"]["interaction_mode"] = mode

    # Next message will use new mode
    await cl.Message(
        content=f"📋 Mode changed to: {mode}"
    ).send()
```

**Reading the Selection:**
```python
# In message handler
settings = cl.user_session.get("chat_settings", {})
mode = settings.get("interaction_mode", "Ask")
# → "Ask", "Plan", or "Agent"
```

#### Agent-Level Routing

The supervisor node uses the mode to route differently:

```python
from yonca.agent.nodes.supervisor import classify_intent

async def supervisor_node(state: AgentState, config: RunnableConfig | None = None):
    # 1. Get current interaction mode
    mode = state.metadata.get("interaction_mode", "Ask")

    # 2. Classify intent with mode-aware system prompt
    intent = await classify_intent(user_input, config=config)

    # 3. Route based on intent + mode
    if mode == "Ask":
        return {"next": "agronomist"}  # Direct answer
    elif mode == "Plan":
        return {"next": "calendar_planner"}  # Month-by-month
    elif mode == "Agent":
        return {"next": "reasoning_loop"}  # Multi-step
```

---

## 🔄 Data Flow: From UI to Graph

### Scenario: User Changes Model Selection

```
1. User clicks header dropdown
   ↓
2. Selects "Llama 3 7B"
   ↓
3. Chainlit stores in session
   cl.user_session["chat_profile"] = "llama3:7b"
   ↓
4. User sends message
   ↓
5. Message handler:
   config = {"metadata": {"model": "llama3:7b"}}
   ↓
6. Graph invocation:
   response = await graph.ainvoke(state, config=config)
   ↓
7. Each node receives config:
   async def node(state, config):
       provider = get_llm_from_config(config)
       # ✅ Uses "Llama 3 7B", not cached default
   ↓
8. Response uses selected model
   ✅ Model switching successful!
```

### Scenario: User Changes Interaction Mode

```
1. User clicks settings ⚙️
   ↓
2. Settings panel opens (right side)
   ↓
3. Selects "Plan" mode
   ↓
4. @on_settings_update triggered
   ↓
5. Session updated:
   cl.user_session["chat_settings"]["interaction_mode"] = "Plan"
   ↓
6. User sends NEXT message
   ↓
7. Message handler reads mode:
   mode = cl.user_session["chat_settings"]["interaction_mode"]
   state.metadata["interaction_mode"] = "Plan"
   ↓
8. Supervisor node routes differently:
   "Plan" → calendar_planner_node (instead of agronomist)
   ↓
9. Response uses planning format
   ✅ Mode change successful!
```

---

## 🎯 Key Design Principles

### 1. Model Selection is STRUCTURAL

- **Persistent** across session (survives multiple messages)
- **Header-level** (always visible, important decision)
- **Session-wide** (affects every message until changed)
- **Explicit** (requires deliberate selection at session start)

### Rationale:
- Farmers might want to say "use Qwen3 for quick answers all session"
- Model choice is an upfront decision, not mid-conversation
- Header prominence reflects importance

### 2. Interaction Mode is TACTICAL

- **Dynamic** (can change mid-conversation)
- **Sidebar** (not in the way, but easy to access)
- **Per-message** (next message uses new mode)
- **Reversible** (can switch back without resetting session)

### Rationale:
- Farmer might ask a quick question (Ask), then say "Plan it out" (Plan)
- Mode is tactical adaptation, not fundamental choice
- Sidebar keeps UI clean while allowing quick adjustments

---

## 📊 State Management

### In LangGraph State

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    metadata: dict  # ← Carries both selections
    # metadata["model"] = "qwen3:4b" (from Chat Profile)
    # metadata["interaction_mode"] = "Plan" (from Settings)
```

### In Chainlit Session

```python
# Model selection
cl.user_session.get("chat_profile")  # "qwen3:4b"

# Interaction mode
cl.user_session.get("chat_settings", {}).get("interaction_mode")  # "Plan"
```

### Transition to Graph

```python
@cl.on_message
async def handle_message(msg: cl.Message):
    # Extract both selections
    model = cl.user_session.get("chat_profile", "qwen3:4b")
    mode = cl.user_session.get("chat_settings", {}).get("interaction_mode", "Ask")

    # Build config for graph
    config = {
        "metadata": {
            "model": model,
            "interaction_mode": mode
        }
    }

    # Graph receives both and uses appropriately
    response = await graph.ainvoke(state, config=config)
```

---

## ✅ Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Chat Profiles (models) | ✅ Implemented | 5 models available (Qwen3, ATLlama, Llama, Mistral, Gemma) |
| Chat Settings sidebar | ✅ Implemented | Interaction modes (Ask, Plan, Agent) configurable |
| Model persistence | ✅ Working | Lasts entire session |
| Mode dynamicity | ✅ Working | Can change mid-conversation |
| Config passing | ✅ Wired | Flows from Chainlit → LangGraph nodes |
| Node usage | ✅ Active | All nodes use `get_llm_from_config(config)` |
| Database storage | ✅ Supports | Can persist settings if data_persistence_enabled |

---

## 🚀 Future Enhancements

### Potential Additions

1. **Model-specific prompts** — Use different system prompts for different models
2. **Temperature per model** — Adjust parameters based on selection
3. **Streaming speed indicator** — Show expected latency for selected model
4. **Cost per model** — Display token cost for transparent pricing
5. **Settings persistence** — Save interaction mode preferences across sessions
6. **A/B testing** — Compare model outputs side-by-side
7. **Custom models** — Admin upload custom model profiles

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| [demo-ui/app.py](../demo-ui/app.py#L405-L430) | Chat Profile definitions |
| [demo-ui/app.py](../demo-ui/app.py#L1334-L1400) | Chat Settings implementation |
| [src/yonca/llm/factory.py](../src/yonca/llm/factory.py) | `get_llm_from_config()` function |
| [src/yonca/agent/nodes/supervisor.py](../src/yonca/agent/nodes/supervisor.py) | Node implementation with config |
| [.chainlit/config.toml](.chainlit/config.toml) | Chainlit configuration |

---

## 💡 Pro-Tips

### Tip 1: Testing Model Selection

```python
# Simulate different models in tests
async def test_supervisor_with_model():
    state = AgentState(messages=[...])

    # Test with Qwen3
    config_qwen = {"metadata": {"model": "qwen3:4b"}}
    result_qwen = await supervisor_node(state, config_qwen)

    # Test with Llama
    config_llama = {"metadata": {"model": "llama3:7b"}}
    result_llama = await supervisor_node(state, config_llama)

    # Results should differ
    assert result_qwen != result_llama
```

### Tip 2: Debug Current Selections

Add to message handler for debugging:

```python
@cl.on_message
async def debug_selections(msg: cl.Message):
    model = cl.user_session.get("chat_profile")
    mode = cl.user_session.get("chat_settings", {}).get("interaction_mode")

    print(f"🤖 Model: {model}")
    print(f"💬 Mode: {mode}")
```

### Tip 3: Reset to Defaults

```python
# Allow farmers to reset settings
async def reset_settings():
    cl.user_session["chat_profile"] = "qwen3:4b"
    cl.user_session["chat_settings"] = {
        "interaction_mode": "Ask"
    }
    await cl.Message("✅ Settings reset to defaults").send()
```
