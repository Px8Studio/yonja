# ⚙️ ALEM Technical Architecture

> **Purpose:** Complete technical reference for ALEM (Agronomical Logic & Evaluation Model) — components, data flow, and operational guidance.

---

## 🌍 System Context: Yonca Ecosystem

> **Important Distinction:** We are building **Yonca AI** (ALEM-powered assistant) as a sidecar to the existing **Yonca Mobile App** (Digital Umbrella's production platform).

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph gov_existing["🏛️ GOVERNMENT SYSTEMS (Existing)"]
        direction TB
        ektis_db["<b>EKTIS Database</b><br/><i>Ministry of Agriculture</i><br/>━━━━━━━━━<br/>✅ Live: 100k+ farms<br/>• Crop declarations<br/>• Land registry<br/>• NDVI tracking"]
    end
    
    subgraph external["🌐 YONCA MOBILE (Digital Umbrella)"]
        direction TB
        yonca_mobile["📱 <b>Yonca Mobile App</b><br/><i>Production • 100k+ users</i><br/>━━━━━━━━━<br/>✅ Existing Integrations:<br/>• EKTIS (farm data)<br/>• mygov ID (auth)<br/>• GPS tracking"]
    end

    subgraph future_partners["🔮 FUTURE DIRECT INTEGRATIONS (Phase 1-3)"]
        direction TB
        sima["🔐 <b>SİMA/ASAN</b><br/><i>IDDA</i><br/>Phase 1"]
        ektis_direct["🏛️ <b>EKTIS Direct API</b><br/><i>Ministry of Agriculture</i><br/>Phase 2"]
        cbar["💰 <b>CBAR Banking</b><br/><i>Central Bank</i><br/>Phase 2"]
        azerkosmos["🛰️ <b>Azərkosmos</b><br/><i>Space Agency</i><br/>Phase 3"]
        weather["🌡️ <b>Weather APIs</b><br/><i>Azerbaijan Meteorology</i><br/>Phase 2"]
    end

    subgraph our_system["🤖 YONCA AI (Our System)"]
        direction TB
        alem["🧠 <b>ALEM</b><br/><i>AI Model Stack</i>"]
        demo_ui["🖥️ <b>Demo UI</b><br/><i>Chainlit :8501</i>"]
        synthetic["💾 <b>Synthetic Data</b><br/><i>Current: Mirror-image</i>"]
    end

    %% Existing connections (solid green)
    ektis_db ==>|"✅ EXISTING<br/>Production API"| yonca_mobile
    
    %% Current ALEM setup (solid)
    demo_ui --> alem
    alem --> synthetic
    
    %% Future indirect path (dashed orange)
    yonca_mobile -.->|"🔮 Option A: Via Yonca Mobile<br/>Leverage existing integration"| our_system
    
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
- **Dashed orange arrows** (⇢) = Future integration via existing Yonca Mobile
- **Dashed purple arrows** (⇢) = Future direct integrations (new partnerships)

| System | Owner | Purpose | Status | ALEM Integration Path |
|:-------|:------|:--------|:-------|:----------------------|
| **EKTIS** | Ministry of Agriculture | Official farm registry (100k+ farms) | ✅ Live | 🔮 **Option A**: Via Yonca Mobile (indirect)<br/>🔮 **Option B**: Direct API (new partnership) |
| **Yonca Mobile App** | Digital Umbrella | Production farming app | ✅ Live | 🔮 Data sync partner |
| **Yonca AI (ALEM)** | Zekalab | AI assistant sidecar | 🔄 Development | — |
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

    subgraph ui["🖥️ PRESENTATION LAYER"]
        chainlit["<b>Chainlit UI</b><br/>:8501<br/>━━━━━━━━━<br/>• Chat interface<br/>• Token streaming<br/>• Thread display<br/>• OAuth login"]
    end

    subgraph brain["🧠 INTELLIGENCE LAYER"]
        langgraph["<b>LangGraph Agent</b><br/>━━━━━━━━━<br/>• Supervisor node<br/>• Agronomist node<br/>• Weather node<br/>• Validator node"]
        llm["<b>LLM Providers</b><br/>━━━━━━━━━<br/>• Groq (cloud)<br/>• Ollama (local)"]
    end

    subgraph data["💾 APP DATA LAYER"]
        direction LR
        postgres["<b>Yonca App DB</b><br/>:5433<br/>━━━━━━━━━<br/>📋 App Tables:<br/>• users (OAuth)<br/>• threads, steps<br/>• user_profiles<br/>• farms, parcels<br/>• alem_personas"]
        redis["<b>Redis</b><br/>:6379<br/>━━━━━━━━━<br/>• LangGraph checkpoints<br/>• Session state<br/>• Rate limiting"]
    end

    subgraph observe["📊 OBSERVABILITY (Separate DB)"]
        langfuse["<b>Langfuse</b><br/>:3001<br/>━━━━━━━━━<br/>Own database<br/>• LLM traces<br/>• Token costs<br/>• Latencies"]
    end

    farmer --> chainlit
    chainlit --> |"Direct Mode"| langgraph
    langgraph --> llm
    langgraph --> |"State checkpoints"| redis
    chainlit --> |"App data"| postgres
    langgraph --> |"Farm context"| postgres
    langgraph -.-> |"Traces"| langfuse
    langfuse -.-> |"Insights API"| postgres

    style chainlit fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style langgraph fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style postgres fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style redis fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style langfuse fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

### Component Responsibility Matrix

| Component | Purpose | What It Stores | Key File |
|:----------|:--------|:---------------|:---------|
| **Chainlit** | Chat UI + thread display | UI state (delegates to App DB) | `demo-ui/app.py` |
| **Yonca App DB** | All app data | Users, farms, threads, personas | `demo-ui/data_layer.py` |
| **Redis** | Fast state + checkpoints | LangGraph state, sessions | `src/yonca/agent/memory.py` |
| **Langfuse** | LLM observability (separate DB) | Traces, costs, latencies | `src/yonca/observability/langfuse.py` |
| **LangGraph** | Agent orchestration | In-memory graph execution | `src/yonca/agent/graph.py` |

### 🎯 Architecture Clarification: Three Different "LangGraphs"

> **Common Confusion:** The term "LangGraph" appears in three contexts. Understanding these distinctions is critical for navigating the codebase.

| What It Is | Type | Port | Purpose | Required? |
|:-----------|:-----|:-----|:--------|:----------|
| **LangGraph Library** | Python package | — | Agent orchestration framework (like React) | ✅ **Core dependency** |
| **LangGraph Dev Server** | Development tool | 2024 | Visual debugger (LangGraph Studio) | ❌ **Optional** |
| **FastAPI Backend** | Production API | 8000 | REST endpoints for mobile app | ✅ **Production critical** |

#### 1️⃣ LangGraph Library (The Brain)

```python
from langgraph.graph import StateGraph  # ← This is the library
agent = StateGraph(AgentState)
agent.add_node("supervisor", supervisor_node)
```

- **What**: Python library you import and use in code
- **Where**: `src/yonca/agent/` — all agent logic
- **Analogy**: Like React — you build your app with it
- **Status**: ✅ **Required** — this is your agent's foundation

#### 2️⃣ LangGraph Dev Server (Optional Debugger)

```bash
langgraph dev  # Starts on http://127.0.0.1:2024
```

- **What**: Visual debugger for LangGraph applications
- **Where**: Started separately via CLI command
- **Analogy**: Like React DevTools — helpful for debugging
- **Status**: ❌ **Optional** — you can safely ignore this for development

> 💡 **Decision**: We **don't use** the LangGraph Dev Server. Chainlit provides built-in step visualization, making this redundant.

#### 3️⃣ FastAPI Backend (Production API)

```python
# src/yonca/api/main.py
@app.post("/api/v1/chat")
async def chat(request: ChatMessage):
    # Imports LangGraph library internally
    agent = get_agent()
    response = await agent.chat(request.message)
```

- **What**: REST API server exposing agent functionality
- **Where**: `src/yonca/api/` — all HTTP endpoints
- **Analogy**: Express.js server for your React app
- **Status**: ✅ **Required** — mobile app calls these endpoints

### 🔄 Integration Modes: Direct vs API Bridge

The Chainlit demo UI supports **two integration patterns** for flexibility:

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph dev["🔧 DEVELOPMENT MODE (Current)"]
        chainlit1["Chainlit UI<br/>:8501"]
        langgraph_lib1["LangGraph Library<br/>(imported directly)"]
        llm1["Ollama/Groq"]
        
        chainlit1 --> langgraph_lib1
        langgraph_lib1 --> llm1
        
        note1["✅ Direct Mode<br/>Fast iteration<br/>No HTTP overhead"]
    end
    
    subgraph prod["🚀 PRODUCTION SIMULATION"]
        mobile["Mobile App"]
        fastapi["FastAPI<br/>:8000"]
        langgraph_lib2["LangGraph Library<br/>(imported by FastAPI)"]
        llm2["Groq API"]
        
        mobile --> fastapi
        fastapi --> langgraph_lib2
        langgraph_lib2 --> llm2
        
        note2["🌐 API Bridge Mode<br/>Tests production API<br/>(optional for demo)"]
    end
    
    style dev fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style prod fill:#fff3e0,stroke:#f57c00,stroke-width:2px
```

| Mode | How It Works | When to Use |
|:-----|:-------------|:------------|
| **Direct Mode** | Chainlit → LangGraph Library (in-process) | ✅ **Development** — Faster, simpler |
| **API Bridge Mode** | Chainlit → FastAPI → LangGraph Library | ⚙️ **Testing** — Validates API contract |

> 🎯 **Recommendation**: Use **Direct Mode** for daily development. The "API Bridge" exists to test the same HTTP endpoints the mobile app will use, but it's not required for building the agent.

**Configuration** (`.env` or `demo-ui/.env`):
```env
# Simple setup (recommended)
INTEGRATION_MODE=direct
```

### 🧠 Mental Model: One Backend, Two Entry Points

```
┌─────────────────────────────────────────────────────┐
│         🧠 LANGGRAPH AGENT (Core Logic)             │
│                                                      │
│  • Supervisor node (routes intent)                 │
│  • Agronomist node (agricultural advice)           │
│  • Weather node (weather queries)                  │
│  • Validator node (safety checks)                  │
│                                                      │
│         Location: src/yonca/agent/                  │
└─────────────────────────────────────────────────────┘
            ▲                        ▲
            │                        │
    ┌───────┴────────┐      ┌────────┴────────┐
    │                │      │                 │
    │  Entry Point 1 │      │  Entry Point 2  │
    │                │      │                 │
    │   📱 Chainlit  │      │   🌐 FastAPI    │
    │   (Direct)     │      │   (HTTP API)    │
    │                │      │                 │
    │   For: Demo    │      │   For: Mobile   │
    │        Testing │      │        App      │
    └────────────────┘      └─────────────────┘
```

**Key Insight**: Both entry points use the **same LangGraph agent code**. The only difference is how they access it:
- **Chainlit**: Imports directly (`from yonca.agent import get_agent`)
- **FastAPI**: Also imports directly, but exposes via HTTP endpoints

There's **no duplication** — just different interfaces to the same intelligence layer.

---

## 💾 Data Ecosystem

> **Key Architecture:** THREE storage systems running in Docker — two PostgreSQL instances + Redis.

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph docker["🐳 Docker Compose Stack"]
        direction TB
        
        subgraph yonca_ai_data["💾 YONCA AI APP DATA"]
            subgraph pg_app["🐘 PostgreSQL :5433<br/><code>yonca-postgres</code>"]
                app_tables["📋 <b>App Tables</b><br/>━━━━━━━━━━━━━<br/>users, threads, steps<br/>user_profiles, farm_profiles<br/>parcels, alem_personas"]
            end
            
            subgraph redis["🔴 Redis Stack :6379<br/><code>yonca-redis</code>"]
                redis_data["⚡ <b>Runtime State</b><br/>━━━━━━━━━━━━━<br/>LangGraph checkpoints<br/>Session cache<br/>Rate limits"]
            end
        end
        
        subgraph langfuse_stack["📊 LANGFUSE STACK (Self-Contained)"]
            subgraph pg_langfuse["🐘 PostgreSQL :5432<br/><code>yonca-langfuse-db</code><br/><i>Internal only</i>"]
                lf_tables["🔍 <b>Auto-Managed</b><br/>━━━━━━━━━━━━━<br/>traces, generations<br/>scores, prompts<br/>sessions, users"]
            end
            
            langfuse_ui["🌐 <b>Langfuse UI :3001</b><br/><code>yonca-langfuse</code>"]
        end
    end
    
    subgraph external["🌐 FUTURE: External Data"]
        yonca_mobile["📱 Yonca Mobile<br/>(Digital Umbrella)"]
    end
    
    pg_langfuse --> langfuse_ui
    langfuse_ui -.->|"REST API<br/>read-only"| pg_app
    yonca_mobile -.->|"Hot-swap<br/>when ready"| pg_app
    
    style yonca_ai_data fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style langfuse_stack fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style external fill:#fff3e0,stroke:#f57c00,stroke-dasharray: 5 5
```

### 📦 Complete Storage Inventory

| Container | Type | Port | Database/Purpose | You Manage? |
|:----------|:-----|:-----|:-----------------|:------------|
| `yonca-postgres` | PostgreSQL 15 | **:5433** | Yonca App tables | ✅ **Yes** — migrations, seeds |
| `yonca-redis` | Redis Stack | **:6379** | LangGraph checkpoints, sessions | ✅ **Yes** — ephemeral |
| `yonca-langfuse-db` | PostgreSQL 15 | *internal* | Langfuse traces (auto-managed) | ❌ **No** — Langfuse handles |
| `yonca-langfuse` | Next.js app | **:3001** | Observability dashboard | ❌ **No** — just view it |

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
# Yonca App DB (your data)
postgresql://yonca:yonca_dev_password@localhost:5433/yonca

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
| **Yonca App DB** | PostgreSQL :5433 | `users`, `threads`, `steps`, `feedbacks` | Conversation history | Read/Write |
| **Yonca App DB** | PostgreSQL :5433 | `user_profiles`, `farm_profiles`, `parcels` | Farm data (synthetic → real) | Read/Write |
| **Langfuse DB** | PostgreSQL (internal) | `traces`, `generations`, `scores` | LLM observability | **Auto-managed** |
| **Redis** | Redis Stack :6379 | `langgraph:checkpoint:*` | LangGraph state | Read/Write |
| **Redis** | Redis Stack :6379 | `session:*`, `rate_limit:*` | Runtime cache | Read/Write |

> 💡 **Langfuse is self-contained** — it manages its own PostgreSQL database. We query it via REST API for dashboard insights, but all trace data stays in Langfuse's DB. We can optionally cache aggregated insights in our App DB for faster access.

### Hot-Swap Strategy: Synthetic → Real Data

The Yonca mobile platform (Digital Umbrella) already serves many users with real farm data from EKTIS. Our architecture is designed for seamless integration:

| Phase | Data Source | Status |
|:------|:------------|:-------|
| **Now** | Synthetic profiles (schema-matched) | ✅ Active |
| **Pilot** | Real users, synced from Yonca mobile | ⏳ Pending handoff |
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

**Graph nodes** (see `src/yonca/agent/graph.py`):
- `supervisor` — Routes intent, handles greetings
- `context_loader` — Loads farm/user context from PostgreSQL
- `agronomist` — Core agricultural reasoning
- `weather` — Weather-related queries
- `validator` — Output validation + safety checks

---

## 🚀 Operational Quick Reference

### 🎯 Essential vs Optional Components

Before diving into service URLs and commands, understand what you actually need:

| Component | Status | Why |
|:----------|:-------|:----|
| **Docker Services** | ✅ **Required** | PostgreSQL, Redis, Langfuse, Ollama |
| **FastAPI Backend** | ✅ **Required** | Mobile app integration point |
| **Chainlit UI (Direct Mode)** | ✅ **Required** | Primary testing interface |
| **LangGraph Library** | ✅ **Required** | Agent brain (imported by both above) |
| **LangGraph Dev Server** | ❌ **Optional** | Visual debugger (redundant with Chainlit) |
| **API Bridge Mode** | ❌ **Optional** | Tests FastAPI contract (use Swagger instead) |

### 🎬 Simplified Startup Sequence

```powershell
# 1. Start Docker services
docker-compose -f docker-compose.local.yml up -d

# 2. Run migrations (first time only)
$env:DATABASE_URL = "postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca"
alembic upgrade head

# 3. Start Chainlit UI (development testing)
cd demo-ui
.\.venv\Scripts\Activate.ps1
chainlit run app.py -w --port 8501

# 4. Start FastAPI (mobile app testing - separate terminal)
cd C:\Users\rjjaf\_Projects\yonja
.\.venv\Scripts\Activate.ps1
uvicorn yonca.api.main:app --reload

# That's it! No LangGraph dev server needed.
```

> 💡 **Pro Tip**: Chainlit and FastAPI can run simultaneously. Test the agent in Chainlit, then validate the HTTP API via Swagger UI (http://localhost:8000/docs).

### Service URLs

| Service | URL | Purpose | Health Check |
|:--------|:----|:--------|:-------------|
| **Chainlit UI** | http://localhost:8501 | Demo testing interface | Visual check |
| **FastAPI Backend** | http://localhost:8000 | Mobile app API | http://localhost:8000/health |
| **Swagger UI** | http://localhost:8000/docs | Interactive API testing | N/A |
| **ReDoc** | http://localhost:8000/redoc | API documentation | N/A |
| **PostgreSQL** | localhost:5433 | App database | `pg_isready -h localhost -p 5433` |
| **Redis** | localhost:6379 | State persistence | `redis-cli ping` |
| **Langfuse** | http://localhost:3001 | LLM observability | Dashboard loads |
| **Ollama** | http://localhost:11434 | Local LLM (dev) | `curl http://localhost:11434/api/tags` |

> 🎯 **Testing Workflow**: Develop in Chainlit → Test API via Swagger → Mobile app uses FastAPI endpoints

### Common Commands

```powershell
# ═══════════════════════════════════════════════════════
# DOCKER SERVICES
# ═══════════════════════════════════════════════════════

# Start all services (PostgreSQL, Redis, Langfuse, Ollama)
docker-compose -f docker-compose.local.yml up -d

# Check service health
docker ps
docker-compose -f docker-compose.local.yml ps

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Stop all services
docker-compose -f docker-compose.local.yml down

# ═══════════════════════════════════════════════════════
# DATABASE MANAGEMENT
# ═══════════════════════════════════════════════════════

# Run migrations (first time setup)
$env:DATABASE_URL = "postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca"
$env:PYTHONPATH = "C:\Users\rjjaf\_Projects\yonja\src"
alembic upgrade head

# Create new migration (after model changes)
alembic revision --autogenerate -m "description"

# Seed database with synthetic data
python scripts/seed_database.py

# Verify Redis checkpoints
docker exec yonca-redis redis-cli KEYS "langgraph:*"

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
uvicorn yonca.api.main:app --reload --port 8000

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
| [19-YONCA-AI-INTEGRATION-UNIVERSE](19-YONCA-AI-INTEGRATION-UNIVERSE.md) | Visual integration landscape, data flows, phased timeline |
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
