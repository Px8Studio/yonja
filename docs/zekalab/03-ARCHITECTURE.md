# ⚙️ ALEM Technical Architecture

> **Purpose:** Complete technical reference for ALEM (Agronomical Logic & Evaluation Model) — components, data flow, and operational guidance.

---

## 🌍 System Context: Yonca Ecosystem

> **Important Distinction:** We are building **Yonca AI** (ALEM-powered assistant) as a sidecar to the existing **Yonca Mobile App** (Digital Umbrella's production platform).

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph external["🌐 EXTERNAL SYSTEMS (Digital Umbrella)"]
        direction TB
        yonca_mobile["📱 <b>Yonca Mobile App</b><br/><i>Production • 100k+ users</i><br/>━━━━━━━━━<br/>• Real farmers<br/>• Real farms/parcels<br/>• EKTIS integration"]
        ektis_db["🏛️ <b>EKTIS Database</b><br/><i>Government • Read-only</i>"]
    end

    subgraph our_system["🤖 YONCA AI (Our System)"]
        direction TB
        alem["🧠 <b>ALEM</b><br/><i>AI Model Stack</i>"]
        demo_ui["🖥️ <b>Demo UI</b><br/><i>Chainlit :8501</i>"]
    end

    yonca_mobile -.->|"Future: Real data sync"| our_system
    ektis_db --> yonca_mobile
    
    style external fill:#fff3e0,stroke:#f57c00,stroke-dasharray: 5 5
    style our_system fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style alem fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
```

| System | Owner | Purpose | Status |
|:-------|:------|:--------|:-------|
| **Yonca Mobile App** | Digital Umbrella | Production farming app (100k+ users) | ✅ Live |
| **EKTIS** | Government | Official farm registry | ✅ Live |
| **Yonca AI (ALEM)** | Zekalab | AI assistant sidecar | 🔄 Development |

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

### Service URLs

| Service | URL | Health Check |
|:--------|:----|:-------------|
| **Chainlit UI** | http://localhost:8501 | Visual check |
| **PostgreSQL** | localhost:5433 | `pg_isready -h localhost -p 5433` |
| **Redis** | localhost:6379 | `redis-cli ping` |
| **Langfuse** | http://localhost:3001 | Dashboard loads |
| **Ollama** | http://localhost:11434 | `curl http://localhost:11434/api/tags` |

### Common Commands

```powershell
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Run database migrations
$env:DATABASE_URL = "postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca"
alembic upgrade head

# Verify Redis checkpoints
docker exec yonca-redis redis-cli KEYS "langgraph:*"

# Start Chainlit UI
cd demo-ui && chainlit run app.py -w --port 8501
```

### Verification Checklist

```sql
-- Verify Chainlit is persisting threads
SELECT id, name, "createdAt" FROM threads ORDER BY "createdAt" DESC LIMIT 5;

-- Verify messages are saved
SELECT id, type, "threadId", LEFT(output, 50) as preview FROM steps ORDER BY "createdAt" DESC LIMIT 10;
```

---

## 📋 Implementation Gaps

| Gap | Priority | Effort |
|:----|:---------|:-------|
| Evaluation test suite | 🔴 High | 5 days |
| Prometheus metrics | 🟡 Medium | 1 day |

> See [04-TESTING-STRATEGY.md](04-TESTING-STRATEGY.md) for evaluation framework.
