# ⚙️ ALEM Technical Architecture

> **Purpose:** Complete technical reference for ALEM (Agronomical Logic & Evaluation Model) — components, data flow, and operational guidance.

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

    subgraph data["💾 PERSISTENCE LAYER"]
        direction LR
        postgres["<b>PostgreSQL</b><br/>:5433<br/>━━━━━━━━━<br/>🟢 Domain Data:<br/>• user_profiles<br/>• farms, parcels<br/>• crop_rotation<br/>━━━━━━━━━<br/>🔵 Chainlit Data:<br/>• users (OAuth)<br/>• threads<br/>• steps, feedbacks"]
        redis["<b>Redis Stack</b><br/>:6379<br/>━━━━━━━━━<br/>• LangGraph checkpoints<br/>• Session state<br/>• Rate limiting"]
    end

    subgraph observe["📊 OBSERVABILITY LAYER"]
        langfuse["<b>Langfuse</b><br/>:3001<br/>━━━━━━━━━<br/>• LLM traces<br/>• Token costs<br/>• Latency metrics"]
    end

    farmer --> chainlit
    chainlit --> |"Direct Mode"| langgraph
    langgraph --> llm
    langgraph --> |"State checkpoints"| redis
    chainlit --> |"Conversation history"| postgres
    langgraph --> |"Farm context"| postgres
    langgraph --> |"Traces"| langfuse

    style chainlit fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style langgraph fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style postgres fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style redis fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style langfuse fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

### Component Responsibility Matrix

| Component | Purpose | What It Stores | Key File |
|:----------|:--------|:---------------|:---------|
| **Chainlit** | Chat UI + thread display | UI state (delegates storage) | `demo-ui/app.py` |
| **PostgreSQL** | Domain + Chainlit persistence | Users, farms, threads, messages | `demo-ui/data_layer.py` |
| **Redis** | Fast state + checkpoints | LangGraph state, sessions | `src/yonca/agent/memory.py` |
| **Langfuse** | LLM observability | Traces, costs, latencies | `src/yonca/observability/langfuse.py` |
| **LangGraph** | Agent orchestration | In-memory graph execution | `src/yonca/agent/graph.py` |

---

## 💾 Storage Architecture

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph LR
    subgraph yonca_db["🐘 PostgreSQL: yonca (:5433)"]
        direction TB
        domain["<b>Domain Tables</b><br/>user_profiles<br/>farm_profiles<br/>parcels<br/>ndvi_readings"]
        chainlit_tables["<b>Chainlit Tables</b><br/>users (OAuth)<br/>threads<br/>steps<br/>feedbacks"]
    end

    subgraph redis_db["🔴 Redis Stack (:6379)"]
        direction TB
        checkpoints["<b>LangGraph</b><br/>langgraph:checkpoint:{thread_id}"]
        sessions["<b>Sessions</b><br/>session:{user_id}"]
    end

    style yonca_db fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style redis_db fill:#ffebee,stroke:#c62828,stroke-width:2px
```

| Storage | Tables/Keys | Purpose |
|:--------|:------------|:--------|
| **PostgreSQL** | `users`, `threads`, `steps`, `feedbacks` | Chainlit conversation persistence |
| **PostgreSQL** | `user_profiles`, `farm_profiles`, `parcels` | Domain/farm data |
| **Redis** | `langgraph:checkpoint:{thread_id}` | LangGraph state between turns |
| **Redis** | `session:{user_id}`, `rate_limit:{ip}` | Sessions & rate limiting |

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
