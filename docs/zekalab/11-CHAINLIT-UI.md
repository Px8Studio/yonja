# 🖥️ ALEM Demo UI Guide (Chainlit)

> **Purpose:** Chainlit-based demo UI for ALEM — features, architecture, and implementation patterns.

---

## ✅ Implementation Status

| Feature | Status | Location |
|:--------|:------:|:---------|
| Chat Interface | ✅ | `demo-ui/app.py` |
| Token Streaming | ✅ | Native LangGraph |
| OAuth (Google) | ✅ | `.chainlit/`, `data_layer.py` |
| Data Persistence | ✅ | SQLAlchemy → PostgreSQL |
| Quick Actions | ✅ | Weather, Subsidy, Irrigation buttons |
| Chat Settings | ✅ | Language, currency, expertise |
| Element Sidebar | ✅ | Activity dashboard (Langfuse) |
| Custom CSS/JS | ✅ | `public/custom.css`, `profile-enhancer.js` |
| Audio Input | ✅ | `@cl.on_audio_start/chunk/end` |
| Chat Profiles | ⏳ | Planned (farmer personas) |
| NDVI Visualization | ⏳ | Planned |

---

## 🏗️ Architecture

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph ui["🖥️ Chainlit Demo UI (:8501)"]
        chat["💬 Chat Interface"]
        sidebar["📋 Activity Dashboard"]
        actions["⚡ Quick Actions"]
    end
    
    subgraph backend["⚙️ Backend"]
        agent["🧠 LangGraph Agent"]
        llm["🤖 LLM Provider"]
    end
    
    subgraph appdata["💾 Yonca App Data"]
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
    
    ui <-->|"Stream"| agent
    agent --> llm
    agent <--> redis_app
    agent <--> pg_app
    agent -.->|"traces"| pg_langfuse
    pg_langfuse --> langfuse_ui
    langfuse_ui -.->|"insights API"| sidebar
```

---

## 📁 Project Structure

```
demo-ui/
├── app.py                    # Main Chainlit app (1784 lines)
├── config.py                 # Configuration
├── data_layer.py             # SQLAlchemy persistence
├── alem_persona.py           # Farmer persona management
├── alem_persona_db.py        # Persona database operations
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
    ├── yonca_client.py       # API client
    ├── langfuse_insights.py  # Langfuse data fetch
    └── mock_data.py          # Demo data
```

---

## 🔑 Key Patterns

### Native LangGraph Integration

Chainlit provides first-class LangGraph support via callbacks:

```python
from yonca.agent.graph import compile_agent_graph
from yonca.agent.memory import get_checkpointer_async

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
DATABASE_URL=postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...
YONCA_LANGFUSE_SECRET_KEY=sk-lf-...
YONCA_LANGFUSE_PUBLIC_KEY=pk-lf-...
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

| Feature | Priority | Notes |
|---------|----------|-------|
| Chat Profiles | P1 | Different farmer personas |
| NDVI Visualization | P2 | Satellite imagery display |
| Export Chat | P2 | Download conversation |
