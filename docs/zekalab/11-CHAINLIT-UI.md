# 🖥️ ALEM Demo UI Guide (Chainlit)

> **Purpose:** Chainlit-based demo UI for ALEM — features, architecture, and implementation patterns.
> **Status:** Production-ready with Thread Resume & Chat Profiles active
> **Updated:** 2026-01-21

---

## ✅ Implementation Status

| Feature | Status | Location | Notes |
|:--------|:------:|:---------|:------|
| Chat Interface | ✅ | `demo-ui/app.py` | Full conversation UI |
| Token Streaming | ✅ | Native LangGraph | Real-time response |
| OAuth (Google) | ✅ | `.chainlit/`, `data_layer.py` | Authentication |
| Data Persistence | ✅ | SQLAlchemy → PostgreSQL | Full history |
| Thread Resume | ✅ **NEW** | `app.py` L1809-1893 | Restore after refresh |
| Chat Profiles | ✅ **NEW** | `app.py` L410-730 | Expertise-based AI |
| Quick Actions | ✅ | `app.py` L514-670 | Profile-aware starters |
| Chat Settings | ✅ | `app.py` L1028-1183 | Sidebar preferences |
| Element Sidebar | ✅ | `components/insights_dashboard.py` | Activity dashboard |
| Custom CSS/JS | ✅ | `public/custom.css`, `profile-enhancer.js` | ALEM branding |
| Audio Input | ✅ | `app.py` L1422-1518 | Whisper transcription |
| Feedback Actions | ✅ | `app.py` L1407-1420 | 👍/👎 buttons |
| Elements (Files) | ⏳ | Planned | Image/PDF uploads |
| NDVI Visualization | ⏳ | Planned | Satellite imagery |

---

## 🏗️ Architecture

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph ui["🖥️ Chainlit Demo UI (:8501)"]
        chat["💬 Chat Interface"]
        sidebar["📋 Activity Dashboard"]
        actions["⚡ Quick Actions"]
        profiles["👤 Chat Profiles"]
    end

    subgraph backend["⚙️ Backend"]
        agent["🧠 LangGraph Agent"]
        llm["🤖 LLM Provider"]
    end

    subgraph appdata["💾 ALİM App Data"]
        subgraph pg_app["🐘 PostgreSQL :5433"]
            app_tables["users, threads, farms..."]
        end
        subgraph redis_app["🔴 Redis :6379"]
            checkpoints["LangGraph checkpoints"]
        end
    end

    subgraph observe["📊 Langfuse (Separate Stack)"]
        subgraph pg_langfuse["🐘 PostgreSQL (internal)"]
            traces["Auto-managed traces"]
        end
        langfuse_ui["Langfuse UI :3001"]
    end

    ui <-->|"Stream + Profiles"| agent
    agent --> llm
    agent <--> redis_app
    agent <--> pg_app
    agent -.->|"traces"| pg_langfuse
    pg_langfuse --> langfuse_ui
    langfuse_ui -.->|"insights API"| sidebar
    profiles -.->|"system prompt"| agent
```

---

## 🎯 Chat Profiles — Expertise-Based AI

### How It Works

**Automatic Expertise Detection:**
1. User logs in via OAuth
2. ALEM persona loaded from database (crop type + experience)
3. System detects relevant expertise areas (cotton, wheat, orchard, etc.)
4. Builds combined system prompt from profile templates
5. Agent behavior adapts based on expertise

**Example Flow:**

```
Farmer grows: Cotton (Pambıq)
Experience: Expert
           ↓
Detected Expertise: ["cotton", "advanced"]
           ↓
System Prompt: "Sən pambıqçılıq üzrə ixtisaslaşmış...
                + Cavablarını daha texniki və ətraflı ver..."
           ↓
Agent Behavior: Cotton-specific advice with technical depth
```

### Profile Prompts

| Expertise | Azerbaijani Label | Agent Behavior |
|:----------|:------------------|:---------------|
| `general` | Ümumi kənd təsərrüfatı | Default agricultural assistant |
| `cotton` | Pambıqçılıq | Cotton specialist (Aran region focus) |
| `wheat` | Taxılçılıq | Grain crops expert (wheat/barley) |
| `orchard` | Meyvəçilik | Fruit growing (apple, grape, nuts) |
| `vegetable` | Tərəvəzçilik | Vegetable farming (greenhouse + field) |
| `livestock` | Heyvandarlıq | Animal husbandry |
| `advanced` | Qabaqcıl texnologiyalar | Technical depth + scientific terms |

### Profile-Aware Starters

Each expertise area gets specialized quick actions:

**Cotton Profile:**
- 🌱 Pambıq əkini — Best planting time
- 🐛 Pambıq zərərvericisi — Common pests
- 💧 Pambıq suvarması — Irrigation norms
- 🧪 Torpaq analizi — Soil testing

**Wheat Profile:**
- 🌾 Payızlıq buğda — Fall wheat timing
- 🌡️ Don zədəsi — Frost damage prevention
- 🧪 Gübrələmə — Fertilization schedule

---

## 🔄 Thread Resume — Conversation Continuity

**What It Does:**
- Users can refresh browser and resume conversations
- Thread list appears in sidebar
- Clicking "Resume" restores full session state

**Implementation:** [app.py](../../demo-ui/app.py#L1809-L1893)

```python
@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """Restore session state when user resumes thread."""
    # 1. Extract user & thread IDs
    user_id = thread.get("userId")
    thread_id = thread["id"]

    # 2. Restore user from database
    # 3. Restore ALEM persona
    # 4. Restore chat settings
    # 5. Restore expertise areas → rebuild profile prompt
    # 6. Reinitialize LangGraph with SAME thread_id
    # 7. Send "🔄 Söhbət bərpa olundu" message
```

**Key Insight:** LangGraph checkpoints are tied to `thread_id`, so using the **same ID** loads full conversation history.

---

## 📁 Project Structure

```
demo-ui/
├── app.py                    # Main Chainlit app (1784 lines)
├── config.py                 # Configuration
├── data_layer.py             # SQLAlchemy persistence
├── alim_persona.py           # Farmer persona management
├── alim_persona_db.py        # Persona database operations
├── chainlit.md               # Welcome message
├── .chainlit/
│   └── config.toml           # Chainlit config
├── public/
│   ├── custom.css            # ALEM message styling
│   ├── theme.json            # Color scheme
│   └── avatars/              # Bot/user avatars
├── components/
│   ├── insights_dashboard.py # Langfuse activity display
│   ├── farm_selector.py      # Farm selection UI
│   └── spinners.py           # Loading indicators
└── services/
    ├── ALİM_client.py       # API client
    ├── langfuse_insights.py  # Langfuse data fetch
    └── mock_data.py          # Demo data
```

---

## 🔑 Key Patterns

### Native LangGraph Integration

Chainlit provides first-class LangGraph support via callbacks:

```python
from ALİM.agent.graph import compile_agent_graph
from ALİM.agent.memory import get_checkpointer_async

@cl.on_message
async def on_message(message: cl.Message):
    graph = compile_agent_graph()
    checkpointer = await get_checkpointer_async()

    config = {"configurable": {"thread_id": thread_id}}

    async for event in graph.astream_events(
        {"messages": [HumanMessage(content=message.content)]},
        config=config,
    ):
        # Automatic step visualization + token streaming
        pass
```

### Welcome Flow

Two distinct welcome components:

1. **Dashboard Welcome** (Main Chat) — `send_dashboard_welcome()`
   - Personalized greeting from OAuth
   - Farm status display
   - Quick action buttons

2. **Activity Stats** (Sidebar) — `render_dashboard_sidebar()`
   - Langfuse usage metrics
   - Session statistics

### Audio Input (Implemented)

```python
@cl.on_audio_start
async def on_audio_start():
    return True  # Allow recording

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    # Process audio chunks
    pass

@cl.on_audio_end
async def on_audio_end(elements: list[cl.Audio]):
    # Speech-to-text → process as message
    pass
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# demo-ui/.env
DATABASE_URL=postgresql+asyncpg://ALİM:ALİM_dev_password@localhost:5433/ALİM
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...
ALİM_LANGFUSE_SECRET_KEY=sk-lf-...
ALİM_LANGFUSE_PUBLIC_KEY=pk-lf-...
```

### Chainlit Config (`.chainlit/config.toml`)

```toml
[features]
prompt_playground = true
unsafe_allow_html = true

[features.audio]
enabled = true
sample_rate = 24000

[UI]
name = "ALEM"
default_theme = "light"
cot = "full"  # Chain of thought display
```

---

## 🚀 Running the Demo

```powershell
cd demo-ui
chainlit run app.py -w --port 8501
```

Open http://localhost:8501

---

## 📋 Backlog

| Feature | Priority | Status | Notes |
|---------|----------|--------|-------|
| Elements (Files/Images) | HIGH | ⏳ | Upload images for vision analysis |
| NDVI Visualization | MEDIUM | ⏳ | Satellite imagery display |
| `@cl.on_stop` Handler | LOW | ⏳ | Cancel agent execution |
| Custom Avatars | LOW | ⏳ | Profile-based avatars |
| Step Nesting | LOW | ⏳ | Hierarchical step display |

**Completed:**
- ✅ Thread Resume (2026-01-21)
- ✅ Chat Profiles (2026-01-21)
- ✅ Profile-based system prompts

**Related Documentation:**
- [SPINNER-GUIDE.md](../../demo-ui/docs/SPINNER-GUIDE.md) — Loading state patterns
- [PERSISTENCE-FIX.md](../../demo-ui/docs/PERSISTENCE-FIX.md) — Data layer troubleshooting
- [CHAINLIT_SCHEMA_RULES.md](../CHAINLIT_SCHEMA_RULES.md) — Database constraints

---

## ⚙️ Configuration

### Environment Variables

```bash
# demo-ui/.env
DATABASE_URL=postgresql+asyncpg://ALİM:ALİM_dev_password@localhost:5433/ALİM
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...
ALİM_LANGFUSE_SECRET_KEY=sk-lf-...
ALİM_LANGFUSE_PUBLIC_KEY=pk-lf-...
```

### Chainlit Config (`.chainlit/config.toml`)

```toml
[features]
prompt_playground = true
unsafe_allow_html = true

[features.audio]
enabled = true
sample_rate = 24000

[UI]
name = "ALEM"
default_theme = "light"
cot = "full"  # Chain of thought display
```

---

## 🚀 Running the Demo

```powershell
cd demo-ui
chainlit run app.py -w --port 8501
```

Open http://localhost:8501

---

## 🔗 Related Documentation

- [03-ARCHITECTURE.md](03-ARCHITECTURE.md) — Overall system design
- [07-OBSERVABILITY.md](07-OBSERVABILITY.md) — Langfuse integration
- [20-INTEGRATION-API.md](20-INTEGRATION-API.md) — FastAPI endpoints for mobile app
- [chainlit-ui-ux.md](../../.agent/rules/chainlit-ui-ux.md) — **Agent rules for UI/UX code**
| Chat Profiles | P1 | Different farmer personas |
| NDVI Visualization | P2 | Satellite imagery display |
| Export Chat | P2 | Download conversation |
