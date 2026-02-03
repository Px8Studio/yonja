# ⚙️ ALEM Technical Architecture

> **Purpose:** Complete technical reference for ALEM (Agronomical Logic & Evaluation Model) — components, data flow, and operational guidance.

---

## 🌍 System Context: ALİM Ecosystem

> **Important Distinction:** We are building **ALİM** (ALEM-powered assistant) as a sidecar to the existing **ALİM Mobile App** (Digital Umbrella's production platform).

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph gov_existing["🏛️ GOVERNMENT SYSTEMS (Existing)"]
        direction TB
        ektis_db["<b>EKTIS Database</b><br/><i>Ministry of Agriculture</i><br/>━━━━━━━━━<br/>✅ Live: 100k+ farms<br/>• Crop declarations<br/>• Land registry<br/>• NDVI tracking"]
    end

    subgraph external["🌐 ALİM MOBILE (Digital Umbrella)"]
        direction TB
        ALİM_mobile["📱 <b>ALİM Mobile App</b><br/><i>Production • 100k+ users</i><br/>━━━━━━━━━<br/>✅ Existing Integrations:<br/>• EKTIS (farm data)<br/>• mygov ID (auth)<br/>• GPS tracking"]
    end

    subgraph future_partners["🔮 FUTURE DIRECT INTEGRATIONS (Phase 1-3)"]
        direction TB
        sima["🔐 <b>SİMA/ASAN</b><br/><i>IDDA</i><br/>Phase 1"]
        ektis_direct["🏛️ <b>EKTIS Direct API</b><br/><i>Ministry of Agriculture</i><br/>Phase 2"]
        cbar["💰 <b>CBAR Banking</b><br/><i>Central Bank</i><br/>Phase 2"]
        azerkosmos["🛰️ <b>Azərkosmos</b><br/><i>Space Agency</i><br/>Phase 3"]
        weather["🌡️ <b>Weather APIs</b><br/><i>Azerbaijan Meteorology</i><br/>Phase 2"]
    end

    subgraph our_system["🤖 ALİM (Our System)"]
        direction TB
        alem["🧠 <b>ALEM</b><br/><i>AI Model Stack</i>"]
        demo_ui["🖥️ <b>Demo UI</b><br/><i>Chainlit :8501</i>"]
        synthetic["💾 <b>Synthetic Data</b><br/><i>Current: Mirror-image</i>"]
    end

    %% Existing connections (solid green)
    ektis_db ==>|"✅ EXISTING<br/>Production API"| ALİM_mobile

    %% Current ALEM setup (solid)
    demo_ui --> alem
    alem --> synthetic

    %% Future indirect path (dashed orange)
    ALİM_mobile -.->|"🔮 Option A: Via ALİM Mobile<br/>Leverage existing integration"| our_system

    %% Future direct paths (dashed purple)
    sima -.->|"🔮 Phase 1: Auth"| our_system
    ektis_direct -.->|"🔮 Option B: Direct API<br/>Separate partnership"| our_system
    cbar -.->|"🔮 Phase 2: Finance"| our_system
    azerkosmos -.->|"🔮 Phase 3: Imagery"| our_system
    weather -.->|"🔮 Phase 2: Forecasts"| our_system

    style gov_existing fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style external fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style future_partners fill:#f3e5f5,stroke:#9c27b0,stroke-dasharray: 5 5,opacity:0.6
    style our_system fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style alem fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
```

**Legend:**
- **Solid green arrows** (⇒) = Existing production integrations
- **Dashed orange arrows** (⇢) = Future integration via existing ALİM Mobile
- **Dashed purple arrows** (⇢) = Future direct integrations (new partnerships)

| System | Owner | Purpose | Status | ALEM Integration Path |
|:-------|:------|:--------|:-------|:----------------------|
| **EKTIS** | Ministry of Agriculture | Official farm registry (100k+ farms) | ✅ Live | 🔮 **Option A**: Via ALİM Mobile (indirect)<br/>🔮 **Option B**: Direct API (new partnership) |
| **ALİM Mobile App** | Digital Umbrella | Production farming app | ✅ Live | 🔮 Data sync partner |
| **ALİM (ALEM)** | Zekalab | AI assistant sidecar | 🔄 Development | — |
| **SİMA/ASAN** | IDDA (Gov) | Sovereign authentication | 🔮 Planned (Phase 1) | 🔮 Direct integration |
| **CBAR Open Banking** | Central Bank | Financial integration | 🔮 Planned (Phase 2) | 🔮 Direct integration |
| **Azərkosmos** | Space Agency | Satellite imagery | 🔮 Planned (Phase 3) | 🔮 Direct integration |

> **See:** [18-ENTERPRISE-INTEGRATION-ROADMAP](18-ENTERPRISE-INTEGRATION-ROADMAP.md) for full partnership strategy.

---

## 🧩 Five-Component System

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph user["👤 USER LAYER"]
        farmer["🧑‍🌾 Farmer"]
    end

    subgraph ui["🖥️ PRESENTATION LAYER (app profile)"]
        chainlit["<b>Chainlit UI</b><br/>:8501<br/>━━━━━━━━━<br/>• Chat interface<br/>• Token streaming<br/>• Thread display<br/>• OAuth login"]
        fastapi["<b>FastAPI</b><br/>:8000<br/>━━━━━━━━━<br/>• REST API<br/>• Mobile clients<br/>• External integrations"]
    end

    subgraph brain["🧠 INTELLIGENCE LAYER (core profile)"]
        langgraph["<b>LangGraph Server</b><br/>:2024<br/>━━━━━━━━━<br/>• Supervisor node<br/>• Agronomist node<br/>• Weather node<br/>• Validator node<br/>• State checkpoints"]
        llm["<b>Ollama</b><br/>:11434<br/>━━━━━━━━━<br/>• qwen3:4b (default)<br/>• atllama (optional)"]
    end

    subgraph mcp["🔧 MCP LAYER (mcp profile)"]
        zekalab["<b>ZekaLab MCP</b><br/>:7777<br/>━━━━━━━━━<br/>• Irrigation rules<br/>• Fertilization<br/>• Pest control"]
        pythonviz["<b>Python Viz MCP</b><br/>:7778<br/>━━━━━━━━━<br/>• Chart generation<br/>• Data visualization"]
    end

    subgraph data["💾 APP DATA LAYER (core profile)"]
        direction LR
        postgres["<b>PostgreSQL</b><br/>:5433<br/>━━━━━━━━━<br/>📋 App Tables + Checkpoints"]
        redis["<b>Redis</b><br/>:6379<br/>━━━━━━━━━<br/>• Session cache<br/>• Rate limiting"]
    end

    subgraph observe["📊 OBSERVABILITY (observability profile)"]
        langfuse["<b>Langfuse</b><br/>:3001<br/>━━━━━━━━━<br/>Own database<br/>• LLM traces<br/>• Token costs"]
    end

    farmer --> chainlit
    farmer -.-> fastapi
    chainlit --> |"HTTP"| fastapi
    fastapi --> |"HTTP"| langgraph
    langgraph --> llm
    langgraph --> |"MCP Protocol"| zekalab
    langgraph --> |"MCP Protocol"| pythonviz
    langgraph --> |"Checkpoints"| postgres
    chainlit --> |"App data"| postgres
    langgraph -.-> |"Traces"| langfuse

    style chainlit fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style fastapi fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style langgraph fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style llm fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style zekalab fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style pythonviz fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style postgres fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style redis fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style langfuse fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

### Component Responsibility Matrix

| Component | Profile | Purpose | What It Stores | Key File |
|:----------|:--------|:--------|:---------------|:---------|
| **Chainlit** | `app` | Chat UI + thread display | UI state (delegates to App DB) | `demo-ui/app.py` |
| **FastAPI** | `app` | REST API for mobile/external | Routes to LangGraph | `src/alim/api/main.py` |
| **LangGraph Server** | `core` | Agent orchestration + checkpoints | State in PostgreSQL | `deploy/langgraph/` |
| **Ollama** | `core` | Local LLM inference | Model weights | Docker volume |
| **ZekaLab MCP** | `mcp` | Agricultural rules engine | None (stateless) | `src/alim/mcp_server/` |
| **Python Viz MCP** | `mcp` | Chart/visualization generation | Temp files | `Dockerfile.mcp.viz` |
| **PostgreSQL** | `core` | App data + LangGraph checkpoints | All persistent data | Docker volume |
| **Redis** | `core` | Session cache, rate limiting | Ephemeral cache | Docker volume |
| **Langfuse** | `observability` | LLM tracing dashboard | Own PostgreSQL DB | Docker image |

### 🐳 Docker Compose Profiles

The architecture uses **profiles** for flexible deployment:

| Profile | Services | Use Case |
|:--------|:---------|:---------|
| `core` | postgres, redis, ollama, langgraph | **Required** — Minimum viable stack |
| `observability` | langfuse-db, langfuse-server | **Recommended** — LLM debugging |
| `app` | api, demo-ui | **User-facing** — Chat interface |
| `mcp` | zekalab-mcp, python-viz-mcp | **Domain tools** — Agricultural rules |
| `setup` | model-setup | **One-time** — Pull/import models |

```bash
# Full development stack
docker compose --profile core --profile observability --profile app --profile mcp up -d

# Minimal (just agent + LLM)
docker compose --profile core up -d

# Production (no observability)
docker compose --profile core --profile app --profile mcp up -d
```

### 🎯 Architecture Clarification: LangGraph Server as Single Entry Point

> **Key Change:** LangGraph Server (:2024) is now THE single entry point for all agent interactions. Both Chainlit UI and FastAPI route through it.

| What It Is | Type | Port | Purpose | Required? |
|:-----------|:-----|:-----|:--------|:----------|
| **LangGraph Server** | Orchestration server | 2024 | Agent execution + state checkpoints | ✅ **Core** |
| **LangGraph Library** | Python package | — | Agent definition framework | ✅ **Core dependency** |
| **FastAPI Backend** | REST API gateway | 8000 | Routes to LangGraph Server | ✅ **For external clients** |
| **Chainlit UI** | Demo interface | 8501 | Routes through FastAPI → LangGraph | ✅ **For development** |

#### Why LangGraph Server?

```
┌─────────────────────────────────────────────────────┐
│     🧠 LANGGRAPH SERVER (:2024) — Single Source     │
│                                                      │
│  • Agent graph execution                            │
│  • State checkpointing (PostgreSQL)                 │
│  • Tool invocation (MCP servers)                    │
│  • LLM calls (Ollama)                               │
│                                                      │
│         Config: deploy/langgraph/langgraph.json    │
└─────────────────────────────────────────────────────┘
            ▲                        ▲
            │                        │
    ┌───────┴────────┐      ┌────────┴────────┐
    │  FastAPI :8000 │      │  Direct HTTP    │
    │  (REST gateway)│      │  (testing)      │
    └───────┬────────┘      └─────────────────┘
            │
    ┌───────┴────────┐
    │ Chainlit :8501 │
    │ (Demo UI)      │
    └────────────────┘
```

**Benefits:**
- ✅ Single source of truth for agent state
- ✅ Automatic checkpointing to PostgreSQL
- ✅ Health checks built-in (`/ok` endpoint)
- ✅ Consistent behavior across all clients

### 🔄 Request Flow: Unified Architecture

All traffic flows through LangGraph Server as the single orchestration point:

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart LR
    subgraph clients["👥 CLIENTS"]
        chainlit["Chainlit UI<br/>:8501"]
        mobile["Mobile App"]
        external["External API"]
    end

    subgraph gateway["🚪 API GATEWAY (app profile)"]
        fastapi["FastAPI<br/>:8000"]
    end

    subgraph core["🧠 CORE (core profile)"]
        langgraph["LangGraph Server<br/>:2024"]
        ollama["Ollama<br/>:11434"]
        postgres["PostgreSQL<br/>:5433"]
    end

    subgraph mcp_layer["🔧 MCP (mcp profile)"]
        zekalab["ZekaLab<br/>:7777"]
        pythonviz["Python Viz<br/>:7778"]
    end

    chainlit --> fastapi
    mobile --> fastapi
    external --> fastapi
    fastapi --> langgraph
    langgraph --> ollama
    langgraph --> postgres
    langgraph --> zekalab
    langgraph --> pythonviz

    style fastapi fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style langgraph fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style ollama fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style postgres fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style zekalab fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style pythonviz fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
```

| Client | Route | Use Case |
|:-------|:------|:---------|
| **Chainlit UI** | :8501 → :8000 → :2024 | Development/demo testing |
| **Mobile App** | → :8000 → :2024 | Production mobile clients |
| **External API** | → :8000 → :2024 | Third-party integrations |

> 🎯 **Key Insight**: LangGraph Server (:2024) handles ALL agent logic. FastAPI (:8000) is just a gateway for authentication, rate limiting, and request validation.

---

## 💾 Data Ecosystem

> **Key Architecture:** Profile-based storage with PostgreSQL for persistence, Redis for caching, and separate Langfuse database for observability.

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph docker["🐳 Docker Compose Profiles"]
        direction TB

        subgraph core_profile["💾 CORE PROFILE"]
            subgraph pg_app["🐘 PostgreSQL :5433<br/><code>alim-postgres</code>"]
                app_tables["📋 <b>App + Checkpoints</b><br/>━━━━━━━━━━━━━<br/>• users, threads, steps<br/>• farm_profiles, parcels<br/>• LangGraph checkpoints"]
            end

            subgraph redis["🔴 Redis :6379<br/><code>alim-redis</code>"]
                redis_data["⚡ <b>Cache Layer</b><br/>━━━━━━━━━━━━━<br/>• Session cache<br/>• Rate limiting"]
            end

            subgraph ollama["🧠 Ollama :11434<br/><code>alim-ollama</code>"]
                models["📦 <b>Models</b><br/>━━━━━━━━━━━━━<br/>• qwen3:4b<br/>• atllama (GGUF)"]
            end

            subgraph langgraph["🎯 LangGraph :2024<br/><code>alim-langgraph</code>"]
                agent["🤖 <b>Agent Server</b><br/>━━━━━━━━━━━━━<br/>• Graph execution<br/>• Checkpointing"]
            end
        end

        subgraph obs_profile["📊 OBSERVABILITY PROFILE"]
            subgraph pg_langfuse["🐘 Langfuse DB<br/><code>alim-langfuse-db</code>"]
                lf_tables["🔍 <b>Auto-Managed</b><br/>━━━━━━━━━━━━━<br/>traces, costs, latencies"]
            end

            langfuse_ui["🌐 <b>Langfuse :3001</b><br/><code>alim-langfuse</code>"]
        end

        subgraph mcp_profile["🔧 MCP PROFILE"]
            zekalab["🌾 ZekaLab :7777"]
            pythonviz["📊 Python Viz :7778"]
        end
    end

    langgraph --> pg_app
    langgraph --> ollama
    langgraph --> zekalab
    langgraph --> pythonviz
    pg_langfuse --> langfuse_ui

    style core_profile fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style obs_profile fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style mcp_profile fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
```
### 📦 Complete Storage Inventory

| Container | Profile | Type | Port | Purpose | You Manage? |
|:----------|:--------|:-----|:-----|:--------|:------------|
| `alim-postgres` | `core` | PostgreSQL 15 | **:5433** | App tables + LangGraph checkpoints | ✅ **Yes** |
| `alim-redis` | `core` | Redis Stack | **:6379** | Session cache, rate limiting | ✅ **Yes** |
| `alim-ollama` | `core` | Ollama | **:11434** | LLM inference | ✅ **Yes** |
| `alim-langgraph` | `core` | LangGraph Server | **:2024** | Agent orchestration | ✅ **Yes** |
| `alim-langfuse-db` | `observability` | PostgreSQL 15 | *internal* | Langfuse traces | ❌ **No** |
| `alim-langfuse` | `observability` | Next.js app | **:3001** | Observability dashboard | ❌ **No** |
| `alim-api` | `app` | FastAPI | **:8000** | REST API gateway | ✅ **Yes** |
| `alim-demo-ui` | `app` | Chainlit | **:8501** | Demo chat interface | ✅ **Yes** |
| `alim-zekalab-mcp` | `mcp` | FastMCP | **:7777** | Agricultural rules | ✅ **Yes** |
| `alim-python-viz-mcp` | `mcp` | FastMCP | **:7778** | Chart generation | ✅ **Yes** |

### 🔍 Langfuse: How It Works

**Q: Do we need to seed Langfuse with synthetic data?**
**A: No!** Langfuse auto-populates when you interact with ALEM:

```mermaid
%%{init: {'theme': 'neutral'}}%%
sequenceDiagram
    participant U as 👤 Demo User
    participant A as 🧠 ALEM Agent
    participant LF as 📊 Langfuse
    participant DB as 🐘 Langfuse DB

    U->>A: Send message
    A->>LF: Trace callback (auto)
    LF->>DB: INSERT trace, generation
    Note over DB: Auto-managed!<br/>No seeds needed

    A->>U: Response

    U->>LF: View dashboard :3001
    LF->>DB: Query traces
    DB->>LF: Return data
    LF->>U: Show analytics
```

**Key Points:**
1. **Traces auto-populate** — Every LLM call creates a trace automatically
2. **No synthetic Langfuse data needed** — Just use the app normally
3. **Read via API** — Dashboard queries Langfuse's own DB, we read via REST API
4. **Caching optional** — We can cache aggregated insights in our App DB

### 🔑 VS Code Database Access

To view databases directly from VS Code, install these extensions:

| Extension | ID | Purpose |
|:----------|:---|:--------|
| **Database Client** | `cweijan.vscode-database-client2` | PostgreSQL, Redis, SQLite GUI |
| **Redis** | `cweijan.vscode-redis-client` | Redis key browser |

**Connection strings:**
```bash
# ALİM App DB (your data)
postgresql://ALİM:ALİM_dev_password@localhost:5433/ALİM

# Redis
redis://localhost:6379

# Langfuse DB (just for viewing, don't modify!)
postgresql://langfuse:langfuse_secret@localhost:5432/langfuse
# Note: Langfuse DB runs on internal port, map it in docker-compose if needed
```

> ⚠️ **Warning:** The Langfuse DB port (5432) is internal only by default. To browse it, temporarily add port mapping: `- "5434:5432"` to `langfuse-db` in docker-compose.

### Storage Responsibilities

| Storage | Type | Tables/Keys | Purpose | Access |
|:--------|:-----|:------------|:--------|:-------|
| **ALİM App DB** | PostgreSQL :5433 | `users`, `threads`, `steps`, `feedbacks` | Conversation history | Read/Write |
| **ALİM App DB** | PostgreSQL :5433 | `user_profiles`, `farm_profiles`, `parcels` | Farm data (synthetic → real) | Read/Write |
| **Langfuse DB** | PostgreSQL (internal) | `traces`, `generations`, `scores` | LLM observability | **Auto-managed** |
| **Redis** | Redis Stack :6379 | `langgraph:checkpoint:*` | LangGraph state | Read/Write |
| **Redis** | Redis Stack :6379 | `session:*`, `rate_limit:*` | Runtime cache | Read/Write |

> 💡 **Langfuse is self-contained** — it manages its own PostgreSQL database. We query it via REST API for dashboard insights, but all trace data stays in Langfuse's DB. We can optionally cache aggregated insights in our App DB for faster access.

### Hot-Swap Strategy: Synthetic → Real Data

The ALİM mobile platform (Digital Umbrella) already serves many users with real farm data from EKTIS. Our architecture is designed for seamless integration:

| Phase | Data Source | Status |
|:------|:------------|:-------|
| **Now** | Synthetic profiles (schema-matched) | ✅ Active |
| **Pilot** | Real users, synced from ALİM mobile | ⏳ Pending handoff |
| **Production** | Full EKTIS integration | 🔜 Future |

> **No code changes required** — same `user_profiles`, `farm_profiles`, `parcels` tables, just different data source.

---

## 🔄 Message Lifecycle

```mermaid
%%{init: {'theme': 'neutral'}}%%
sequenceDiagram
    participant F as 🧑‍🌾 Farmer
    participant C as 🖥️ Chainlit
    participant G as 🧠 LangGraph
    participant R as 💾 Redis
    participant P as 🐘 PostgreSQL
    participant L as 📊 Langfuse

    Note over F,L: 1️⃣ User sends message
    F->>C: "Pomidor nə vaxt suvarmalıyam?"

    Note over C,P: 2️⃣ Chainlit saves to PostgreSQL
    C->>P: INSERT INTO steps (threadId, input, ...)

    Note over C,G: 3️⃣ LangGraph processes
    C->>G: invoke(message, thread_id)
    G->>R: Load checkpoint (if exists)
    G->>P: Query farm_profiles, parcels
    G->>L: Trace: supervisor → agronomist → validator

    Note over G,R: 4️⃣ LangGraph saves state
    G->>R: Save checkpoint (conversation memory)

    Note over G,C: 5️⃣ Response streams back
    G-->>C: Stream tokens
    C->>P: INSERT INTO steps (output, generation, ...)
    C-->>F: Display response
```

---

## 🧠 LangGraph Agent Structure

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

**Graph nodes** (see `src/ALİM/agent/graph.py`):
- `supervisor` — Routes intent, handles greetings
- `context_loader` — Loads farm/user context from PostgreSQL
- `agronomist` — Core agricultural reasoning (+ MCP tool calls)
- `weather` — Weather-related queries
- `validator` — Output validation + safety checks

---

## 🔌 MCP Integration Layer

LangGraph Server calls external tools via **Model Context Protocol (MCP)**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH SERVER + MCP                        │
│                                                                  │
│   ┌────────────────┐      ┌─────────────────────────────────┐   │
│   │  StateGraph    │      │         ToolNode                │   │
│   │                │      │   (auto-binds MCP tools)        │   │
│   │  supervisor ──────────▶  • evaluate_irrigation_rules   │   │
│   │       │        │      │  • evaluate_fertilization      │   │
│   │  agronomist ──────────▶  • evaluate_pest_control       │   │
│   │       │        │      │  • calculate_subsidy           │   │
│   │  validator     │      │  • predict_harvest_date        │   │
│   └────────────────┘      │  • generate_chart (viz)        │   │
│                           └─────────────┬───────────────────┘   │
│                                          │                       │
└──────────────────────────────────────────┼───────────────────────┘
                                           │ MCP Protocol
                         ┌─────────────────┼─────────────────┐
                         ▼                                   ▼
            ┌─────────────────────────┐     ┌─────────────────────────┐
            │   ZekaLab FastMCP       │     │   Python Viz MCP        │
            │   :7777                 │     │   :7778                 │
            │   (Agricultural rules)  │     │   (Chart generation)    │
            └─────────────────────────┘     └─────────────────────────┘
```

**Key Files:**
- `src/alim/mcp/adapters.py` — MCP client configuration
- `src/alim/mcp_server/zekalab_fastmcp.py` — Agricultural rules (5 tools)
- `Dockerfile.mcp.viz` — Python visualization server

> 📖 **Full MCP documentation:** See [MCP-ARCHITECTURE.md](MCP-ARCHITECTURE.md)

---

## 🚀 Operational Quick Reference

### 🎯 Profile-Based Deployment

| Profile | Services | Purpose |
|:--------|:---------|:--------|
| `core` | postgres, redis, ollama, langgraph | **Required** — Minimum stack |
| `observability` | langfuse-db, langfuse-server | **Recommended** — LLM tracing |
| `app` | api, demo-ui | **User-facing** — Chat + REST |
| `mcp` | zekalab-mcp, python-viz-mcp | **Domain tools** — Agri rules |
| `setup` | model-setup | **One-time** — Pull models |

### 🎬 Startup Sequences

```powershell
# ═══════════════════════════════════════════════════════
# FULL DEVELOPMENT STACK (Recommended)
# ═══════════════════════════════════════════════════════
docker compose --profile core --profile observability --profile app --profile mcp up -d

# ═══════════════════════════════════════════════════════
# MINIMAL (Just agent + LLM, no UI)
# ═══════════════════════════════════════════════════════
docker compose --profile core up -d

# ═══════════════════════════════════════════════════════
# ONE-TIME MODEL SETUP (Pull qwen3:4b, import ATLLaMA)
# ═══════════════════════════════════════════════════════
docker compose --profile setup up model-setup

# ═══════════════════════════════════════════════════════
# RUN MIGRATIONS (First time only)
# ═══════════════════════════════════════════════════════
$env:DATABASE_URL = "postgresql+asyncpg://alim:alim_dev_password@localhost:5433/alim"
alembic upgrade head
```

### Service URLs

| Service | Profile | URL | Purpose | Health Check |
|:--------|:--------|:----|:--------|:-------------|
| **LangGraph Server** | `core` | http://localhost:2024 | Agent orchestration | http://localhost:2024/ok |
| **Chainlit UI** | `app` | http://localhost:8501 | Demo chat interface | http://localhost:8501/health |
| **FastAPI Backend** | `app` | http://localhost:8000 | REST API gateway | http://localhost:8000/health |
| **Swagger UI** | `app` | http://localhost:8000/docs | Interactive API docs | N/A |
| **PostgreSQL** | `core` | localhost:5433 | App database | `pg_isready -h localhost -p 5433` |
| **Redis** | `core` | localhost:6379 | Session cache | `redis-cli ping` |
| **Ollama** | `core` | http://localhost:11434 | Local LLM | http://localhost:11434/api/tags |
| **Langfuse** | `observability` | http://localhost:3001 | LLM tracing | Dashboard loads |
| **ZekaLab MCP** | `mcp` | http://localhost:7777 | Agricultural rules | http://localhost:7777/health |
| **Python Viz MCP** | `mcp` | http://localhost:7778 | Chart generation | http://localhost:7778/health |

### Common Commands

```powershell
# ═══════════════════════════════════════════════════════
# DOCKER COMPOSE (Profile-based)
# ═══════════════════════════════════════════════════════

# Full stack
docker compose --profile core --profile observability --profile app --profile mcp up -d

# Check service health
docker compose ps

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f langgraph

# Stop all services
docker compose down

# ═══════════════════════════════════════════════════════
# DATABASE MANAGEMENT
# ═══════════════════════════════════════════════════════

# Run migrations (first time setup)
$env:DATABASE_URL = "postgresql+asyncpg://alim:alim_dev_password@localhost:5433/alim"
$env:PYTHONPATH = "src"
alembic upgrade head

# Create new migration (after model changes)
alembic revision --autogenerate -m "description"

# Seed database with synthetic data
python scripts/seed_database.py

# Verify Redis checkpoints
docker exec ALİM-redis redis-cli KEYS "langgraph:*"

# ═══════════════════════════════════════════════════════
# DEVELOPMENT SERVERS
# ═══════════════════════════════════════════════════════

# Start Chainlit UI (primary testing interface)
cd demo-ui
.\.venv\Scripts\Activate.ps1
chainlit run app.py -w --port 8501

# Start FastAPI Backend (for mobile app testing)
cd C:\Users\rjjaf\_Projects\yonja
.\.venv\Scripts\Activate.ps1
uvicorn ALİM.api.main:app --reload --port 8000

# Test FastAPI endpoints
curl http://localhost:8000/health
# or visit http://localhost:8000/docs for Swagger UI

# ═══════════════════════════════════════════════════════
# TESTING & VERIFICATION
# ═══════════════════════════════════════════════════════

# Run tests
pytest tests/ -v

# Check code quality
ruff check src/ tests/

# View Langfuse traces
# Open http://localhost:3001 in browser
```

### Verification Checklist

```sql
-- Verify Chainlit is persisting threads
SELECT id, name, "createdAt" FROM threads ORDER BY "createdAt" DESC LIMIT 5;

-- Verify messages are saved
SELECT id, type, "threadId", LEFT(output, 50) as preview FROM steps ORDER BY "createdAt" DESC LIMIT 10;
```

---

## 🌐 Enterprise Integration Strategy

ALEM's roadmap includes strategic partnerships with Azerbaijan's digital infrastructure ecosystem. See dedicated documentation for full details:

### Key Integration Partners

```mermaid
%%{init: {'theme': 'neutral'}}%%
mindmap
  root((🌐 Integration<br/>Partners))
    🏛️ Government
      SİMA/ASAN
      EKTİS
      State Tax
    💰 Financial
      CBAR Banking
      PASHA Bank
      ABB
    🛰️ Data Services
      Azərkosmos
      AzInTelecom
      Weather APIs
    🏢 Enterprise
      SAP/Oracle
      Agro Holdings
```

### Implementation Phases

| Phase | Timeline | Focus | Key Partners |
|:------|:---------|:------|:-------------|
| **Phase 1** | Q1-Q2 2026 | Authentication | SİMA/ASAN (IDDA) |
| **Phase 2** | Q2-Q3 2026 | Core Data | EKTİS, CBAR, Weather, AzInTelecom |
| **Phase 3** | Q3-Q4 2026 | Premium Intelligence | Azərkosmos, State Tax |
| **Phase 4** | Q4 2026 - Q1 2027 | Commercial Banking | PASHA Bank, ABB |
| **Phase 5** | Q1 2027+ | Enterprise B2B | SAP, Oracle |

### Architecture Impact

**Current (Development):**
- OAuth authentication (Google)
- Synthetic farm data
- Cloud LLM (Groq benchmark)
- Local PostgreSQL + Redis

**Future (Production):**
- SİMA biometric authentication
- Real EKTIS farm data ("hot-swap ready")
- Self-hosted LLM (AzInTelecom GPU)
- Real satellite imagery (Azərkosmos)
- Fermer Kartı integration (CBAR Open Banking)

### Documentation References

| Document | Purpose |
|:---------|:--------|
| [18-ENTERPRISE-INTEGRATION-ROADMAP](18-ENTERPRISE-INTEGRATION-ROADMAP.md) | Detailed partnership strategy, technical specs, action items |
| [19-ALİM-AI-INTEGRATION-UNIVERSE](19-ALİM-AI-INTEGRATION-UNIVERSE.md) | Visual integration landscape, data flows, phased timeline |
| [00-IMPLEMENTATION-BACKLOG](00-IMPLEMENTATION-BACKLOG.md) | Prioritized integration tasks (items 0.1-0.7) |
| [14-DISCOVERY-QUESTIONS](14-DISCOVERY-QUESTIONS.md) | Schema validation questions for Digital Umbrella |

---

## 📋 Implementation Gaps

| Gap | Priority | Effort |
|:----|:---------|:-------|
| Evaluation test suite | 🔴 High | 5 days |
| Prometheus metrics | 🟡 Medium | 1 day |
| Enterprise integrations | 🔴 High | See [18-ENTERPRISE-INTEGRATION-ROADMAP](18-ENTERPRISE-INTEGRATION-ROADMAP.md) |

> See [04-TESTING-STRATEGY.md](04-TESTING-STRATEGY.md) for evaluation framework.
