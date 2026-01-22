# 🏗️ LangGraph Architecture: Dev vs Production

> **Purpose:** Crystal-clear explanation of LangGraph's role, the Dev vs Production distinction, and recommended multi-tier architecture for ZekaLab.
> **Updated:** January 22, 2026
> **Status:** Production-ready architectural guidance

---

## 🎯 Executive Summary

The term **"Dev Server"** causes confusion. Here's the reality:

| Term | What It Actually Is | Persistence | Best For |
|------|-------------------|-------------|----------|
| **LangGraph Dev Server** (`langgraph dev`) | In-memory, auto-reloading server | ❌ None — loses all data on restart | Your laptop during coding |
| **LangGraph Server** (Production) | Same engine, persistent backend | ✅ Postgres/Redis — full state recovery | AzInTelecom, Docker, production |

**The key insight:** You're using the **same library** (`langgraph`), just deployed differently.

---

## 🧩 Component Relationship Matrix

Who does what? How do they talk?

```
┌──────────────────────────────────────────────────────────────┐
│                    THE YONCA STACK                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  📱 Clients (Any language/platform)                          │
│  ├─ Chainlit Web UI (Python)                                 │
│  ├─ Yonca Mobile App (Java/Kotlin)                           │
│  ├─ Telegram Bot (Python)                                    │
│  └─ cURL / Custom integrations                               │
│         │                                                     │
│         │ HTTP REST Calls                                     │
│         ▼                                                     │
│  🚪 FastAPI (Port 8000)                                      │
│  │  "The Doors & Windows"                                    │
│  │  Endpoints: /api/v1/chat, /api/v1/graph/invoke, etc.     │
│  │                                                            │
│  └─────┬──────────────────────────────────────────────────┐  │
│        │ HTTP Internal Call                               │  │
│        ▼                                                  │  │
│  🧠 LangGraph Server (Port 2024)                         │  │
│  │  "The Brain / Logic Engine"                           │  │
│  │  Runs your graph: compile_agent_graph()               │  │
│  │  Executes nodes: supervisor → context → agronomist   │  │
│  │                                                        │  │
│  └─────┬──────────────────────────────────────────────────┘  │
│        │ SQL Queries                                         │
│        ▼                                                      │
│  🗄️ PostgreSQL (Port 5433)                                   │
│  │  "The Memory"                                             │
│  │  Stores: checkpoints, threads, users, settings           │
│  │  LangGraph automatically saves state here                │
│  │                                                            │
│  └─────┬──────────────────────────────────────────────────────┘
│        │ Caching layer                                        │
│        ▼                                                      │
│  💾 Redis (Port 6379)                                        │
│     "The Cache"                                              │
│     LangGraph checkpoint speeds + conversation memory        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Role Breakdown

| Component | Responsibility | Analogy |
|-----------|-----------------|---------|
| **LangGraph (Library)** | Graph compilation, node routing, state management | "The blueprint and construction logic" |
| **LangGraph Server** | API endpoint for executing graphs | "The factory that runs the blueprint" |
| **FastAPI** | Web framework, request routing, authentication | "The front desk and doorman" |
| **PostgreSQL** | Persistent state storage, user data, conversation history | "The filing cabinet and library" |
| **Redis** | Fast caching, checkpoint acceleration | "The desk drawer for today's important docs" |
| **Chainlit** | Web UI for conversation, user interaction | "The monitor and keyboard" |

---

## 🚀 Dev vs Production Deployment

### Local Development: `langgraph dev`

**When:** Running on your laptop
**How:** `langgraph dev` command
**Server:** In-memory only

```powershell
# Your laptop
$env:PYTHONPATH = "C:\path\to\yonja\src"
.\.venv\Scripts\langgraph.exe dev

# ✅ Auto-reloads when you change code
# ❌ Loses ALL data (checkpoints, memory) when server restarts
# ⚠️ Only works for 1-2 concurrent users
```

**Data Flow:**
```
Your Code → langgraph dev (in-memory) → Response
              ↓ (on restart)
           ALL DATA LOST
```

### Production Deployment: Docker Container

**When:** Running on AzInTelecom or cloud servers
**How:** Docker container with Postgres backend
**Server:** Persistent, scalable

```dockerfile
# Dockerfile (production)
FROM python:3.11-slim

WORKDIR /app
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Start LangGraph Server with Postgres persistence
CMD ["langgraph", "up", "--host", "0.0.0.0", "--port", "2024"]
```

**Data Flow:**
```
Request → LangGraph Server → PostgreSQL (persistent)
           ↓
        Redis Cache (fast)
           ↓
        Response

On restart:
Request → LangGraph Server (reload from Postgres) → Response
           ✅ ALL DATA PRESERVED
```

---

## 🌐 Multi-Channel Architecture

By separating **Chainlit** from **LangGraph Server**, you enable multiple clients to use the same logic:

```
┌──────────────────────────────────────────────┐
│    LangGraph Server (One Brain)              │
│    Port 2024: /invoke endpoint               │
└────────────┬─────────────────────────────────┘
             │
        ┌────┴─────────────────────┐
        ▼                          ▼
   ┌─────────────┐         ┌──────────────┐
   │ Chainlit    │         │ Yonca Mobile │
   │ Web UI      │         │ App          │
   │ (localhost) │         │ (iOS/Android)│
   └─────────────┘         └──────────────┘
        │                        │
        └────────┬───────────────┘
                 │
            All talk to the SAME
            graph engine via HTTP
```

**Future Channels (Same Logic, Different UI):**
- ✅ Telegram Bot (`telegram_to_langgraph_bridge.py`)
- ✅ WhatsApp Bot (via Twilio)
- ✅ Yonca Mobile Deep Link Handler
- ✅ SMS Gateway (USSD-style)
- ✅ REST API for third-party integrations

**Benefit:** Write agricultural logic **once**, serve it **everywhere**.

---

## 🐳 Recommended ZekaLab Production Stack

For a team of 5 + production deployment to AzInTelecom:

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│        AzInTelecom Cloud / On-Premises VM                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Container 1: Chainlit UI                                  │
│  ├─ Port: 8501                                             │
│  ├─ Purpose: Web interface for farmers                     │
│  ├─ Restart policy: Always (manage separately)            │
│  └─ Env: LANGGRAPH_HOST=http://langgraph:2024            │
│                                                              │
│  Container 2: LangGraph Server                             │
│  ├─ Port: 2024                                             │
│  ├─ Purpose: Graph execution engine                        │
│  ├─ Restart policy: Always                                 │
│  ├─ Persistence: Connects to Postgres                      │
│  └─ Env: DATABASE_URL=postgresql://user:pass@postgres:5432│
│                                                              │
│  Container 3: FastAPI Backend                              │
│  ├─ Port: 8000                                             │
│  ├─ Purpose: REST API for integrations                    │
│  ├─ Restart policy: Always                                 │
│  ├─ Persistence: Connects to Postgres                      │
│  └─ Routes calls to LangGraph Server                       │
│                                                              │
│  Container 4: PostgreSQL                                   │
│  ├─ Port: 5432 (internal only)                            │
│  ├─ Purpose: Persistent storage                           │
│  ├─ Data: Checkpoints, users, threads, farm data          │
│  └─ Volume: /data/postgres (persistent disk)              │
│                                                              │
│  Container 5: Redis (Optional but recommended)             │
│  ├─ Port: 6379 (internal only)                            │
│  ├─ Purpose: Checkpoint cache + session storage           │
│  └─ Volume: /data/redis (persistent disk)                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  # 1. LangGraph Server - The Brain
  langgraph:
    build:
      context: .
      dockerfile: Dockerfile.langgraph
    ports:
      - "2024:2024"
    environment:
      DATABASE_URL: postgresql://yonca:password@postgres:5432/yonca
      REDIS_URL: redis://redis:6379
      LANGGRAPH_GRAPHS: "yonca_agent=yonca.agent.graph:compile_agent_graph"
    depends_on:
      - postgres
      - redis
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:2024/ok"]
      interval: 10s
      timeout: 5s
      retries: 3

  # 2. FastAPI - The API Gateway
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://yonca:password@postgres:5432/yonca
      LANGGRAPH_HOST: http://langgraph:2024
      LANGGRAPH_GRAPH_ID: yonca_agent
    depends_on:
      - postgres
      - langgraph
    restart: always
    command: ["uvicorn", "src.yonca.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

  # 3. Chainlit - The Web UI
  chainlit:
    build:
      context: demo-ui
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    environment:
      LANGGRAPH_HOST: http://langgraph:2024
      LANGGRAPH_GRAPH_ID: yonca_agent
      YONCA_API_URL: http://fastapi:8000
      DATABASE_URL: postgresql://yonca:password@postgres:5432/yonca
    depends_on:
      - langgraph
      - fastapi
      - postgres
    restart: always

  # 4. PostgreSQL - The Memory
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: yonca
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: yonca
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U yonca"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 5. Redis - The Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  postgres_data:
  redis_data:
```

---

## 💡 Pro-Tip: `langgraph build` for Production

When deploying to production (AzInTelecom, Kubernetes, etc.), don't manually create Dockerfiles. Use the **LangGraph CLI**:

```bash
# This generates a production-ready Docker image
langgraph build -t yonca-alem:latest

# It:
# ✅ Packages your graph code
# ✅ Includes FastAPI server
# ✅ Installs all dependencies
# ✅ Sets up health checks
# ✅ Configures logging
# ✅ Optimizes image size

# Then deploy with:
docker run -d \
  -p 2024:2024 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  yonca-alem:latest
```

---

## 🎯 Current UI Implementation

### Model Selection (Persistent)

**Location:** Header dropdown (Chat Profiles)

- User selects LLM model (e.g., "Qwen3 4B", "ATLlama")
- Selection stored in `cl.user_session.get("chat_profile")`
- Passed to LangGraph as `config["metadata"]["model"]`
- **Persists across entire session** until page refresh
- Each node respects selection: `provider = get_llm_from_config(config)`

**Flow:**
```
User picks model → Header dropdown → Session storage → Every node call
```

### Interaction Mode (Dynamic)

**Location:** Settings sidebar (Chat Settings)

- User selects mode (Ask, Plan, Agent) **at any time**
- Selection stored in `cl.user_session["chat_settings"]`
- Can be changed **mid-conversation**
- Agent adapts behavior based on current mode

**Flow:**
```
User changes mode → Sidebar panel → Immediate effect on next message
```

### Architecture

```
┌─────────────────────────────────────────┐
│     Chainlit Header                     │
│  [Logo] [🤖 Model Dropdown ▼] [⚙️]      │
└────────────────┬────────────────────────┘
                 │ Selection persists
                 ▼
┌─────────────────────────────────────────┐
│  Chat Input Area                        │
│  [Message box...]                       │
└─────────────────────────────────────────┘
                 │ Click ⚙️
                 ▼
┌─────────────────────────────────────────┐
│  Settings Sidebar (Slides from right)   │
│  💬 Interaction Mode: [Ask ▼]           │
│  (Can change mid-conversation)          │
│  🌾 Farm Settings                       │
│  📊 Preferences                         │
└─────────────────────────────────────────┘
```

**Key Benefits:**
- ✅ Model selection is **header-level** (always visible)
- ✅ Model selection is **persistent** (lasts whole session)
- ✅ Interaction mode is **easy to change** (sidebar button)
- ✅ Interaction mode is **dynamic** (affects next message, not history)
- ✅ Clear mental model: "what" (model) vs "how" (mode)

---

## 📚 Related Documentation

- [LANGGRAPH_TESTING_GUIDE.md](LANGGRAPH_TESTING_GUIDE.md) — How to test graph execution
- [LANGGRAPH_DOCKER_DEPLOYMENT.md](LANGGRAPH_DOCKER_DEPLOYMENT.md) — Docker-specific configuration
- [09-PERFORMANCE-SLA.md](09-PERFORMANCE-SLA.md) — Production performance targets

---

## 🎓 Key Takeaways for ZekaLab

1. **LangGraph is a library**, not a monolithic "server"
2. **"Dev Server"** = in-memory, auto-reload, laptop only
3. **Production = Persistent backend** (Postgres + Redis)
4. **Separate Chainlit from LangGraph** to enable multi-channel
5. **Use `langgraph build`** when deploying to AzInTelecom
6. **Same graph logic serves all clients** (Web, Mobile, Bot, API)
