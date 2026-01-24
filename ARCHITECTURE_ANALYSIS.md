# ALİM: Architecture Analysis & Refactoring Plan

## 🔍 Current State Analysis

### 1. **UI Architecture Overview**

You currently have **THREE separate UI entry points**, which is causing confusion:

#### **UI Layer 1: Chainlit Demo UI** (Primary - Port 8501)
- **Location**: `demo-ui/app.py` (3,248 lines)
- **Purpose**: Main user-facing chat interface
- **Technology**: Python + Chainlit (Streamlit wrapper)
- **Features**:
  - Google OAuth integration
  - Persona management (farmer profiles)
  - Farm selector
  - Thinking steps visualization
  - Feedback system (👍/👎)
  - File upload support

#### **UI Layer 2: FastAPI REST API** (Backend - Port 8000)
- **Location**: `src/ALİM/api/main.py`
- **Routes**: `src/ALİM/api/routes/`
  - `auth.py` - OAuth & authentication
  - `chat.py` - Chat endpoint
  - `graph.py` - Agent/graph control
  - `health.py` - Health checks
  - `models.py` - Model management
  - `vision.py` - Vision/image processing
- **Purpose**: RESTful backend for Chainlit UI and external clients
- **Documentation**: Swagger (`/docs`), ReDoc (`/redoc`)

#### **UI Layer 3: ZekaLab MCP Server** (Internal Rules - Port 7777)
- **Location**: `src/ALİM/mcp_server/main.py` (863 lines)
- **Purpose**: Internal agricultural rules engine exposed as MCP tools
- **Technology**: FastMCP (FastAPI-based)
- **Tools**:
  - Irrigation rules
  - Fertilization recommendations
  - Pest control guidance
  - Subsidy information
  - Harvest prediction

#### **Background Services**
- **LangGraph Dev Server** (Port 2024): Agent orchestration
- **Ollama** (Port 11434): Local LLM inference
- **PostgreSQL** (Port 5433): Data persistence
- **Redis** (Port 6379): Session/checkpoint storage
- **Langfuse** (Port 3001): LLM tracing & observability

---

## ❌ Problem: Chat Fails on Refresh

### Root Cause Analysis

From the logs, I see:
```
2026-01-24 00:04:57 [info     ] mcp_health_check_complete
  results={'zekalab': {'status': 'offline', 'error': 'All connection attempts failed'}}

2026-01-24 00:04:57 [error    ] mcp_tools_load_failed_for_profile
  error=unhandled errors in a TaskGroup (1 sub-exception)
```

**The issue**: MCP server initialization fails initially, but then succeeds on subsequent checks. This causes:

1. **Session State Loss**: On refresh, Chainlit creates a new session
2. **MCP Tools Not Available**: Tools fail to load because MCP server was offline during initialization
3. **State Serialization Issue**: UI state (farm selection, settings) is lost on refresh
4. **Race Condition**: Chat message handler executes before MCP initialization completes

### Why UI Changes on Refresh

Chainlit recreates the `cl.user_session` on refresh. Your code doesn't persist:
- Farm selection
- Persona settings
- Chat profile (Agent vs Fast mode)
- User preferences (thinking steps, feedback enabled)

These are stored in `cl.user_session` (in-memory), not in the database.

---

## 📐 12-Factor App Refactoring Plan

Your architecture violates several 12-factor principles:

### **Current Violations**

| Factor | Current State | Issue |
|--------|---------------|-------|
| **I. Codebase** | 3 different entry points in 1 repo | Confuses deployment & versioning |
| **II. Dependencies** | Mixed implicit/explicit deps | `pyproject.toml` doesn't clearly separate UI vs API vs MCP |
| **III. Config** | `.env` files + env vars | No config validation layer; scattered settings |
| **IV. Backing Services** | Hardcoded URLs | Services assumed to be up; no health checks |
| **V. Build/Run/Release** | 5+ different tasks | No clear CI/CD pipeline; manual deployment |
| **VI. Processes** | Stateful UI + stateless API | Session data in memory → lost on restart |
| **VII. Port Binding** | Self-contained but entangled | Hard to scale; all services in one task |
| **VIII. Concurrency** | Async/await but single-threaded | Chainlit + MCP + LangGraph share one process |

---

## 🏗️ Proposed Refactored Architecture

### **Layer 1: Frontend Tier** (Separate Repo)
```
frontend/
├── src/
│   ├── components/          # React components
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API clients
│   ├── store/              # State management (Zustand/Redux)
│   └── App.tsx
├── public/                 # Static assets
├── package.json
└── Dockerfile
```

**Benefits:**
- ✅ Decoupled versioning
- ✅ Easy horizontal scaling
- ✅ State management via Redux/Zustand
- ✅ Client-side persistence (localStorage, IndexedDB)
- ✅ Can be deployed to CDN

---

### **Layer 2: Backend Microservices** (Mono-repo with clear boundaries)

```
backend/
├── services/
│   ├── api-gateway/        # FastAPI router
│   │   ├── main.py
│   │   ├── middleware.py   # Auth, logging, rate-limiting
│   │   └── routes/         # All API endpoints
│   │
│   ├── agent-service/      # LangGraph wrapper
│   │   ├── main.py
│   │   └── client.py       # LangGraph HTTP client
│   │
│   ├── rules-engine/       # MCP Server (ZekaLab)
│   │   ├── main.py
│   │   └── tools/
│   │
│   └── chat-service/       # Optional: Chainlit replacement
│       ├── main.py
│       └── handlers.py
│
├── shared/
│   ├── models/             # Pydantic schemas
│   ├── config/             # Configuration management
│   ├── database/           # SQLAlchemy models
│   └── observability/      # Logging, tracing
│
├── docker-compose.yml      # Local dev
└── pyproject.toml          # Unified dependencies
```

**Benefits:**
- ✅ Clear service boundaries
- ✅ Independent scaling (rules-engine ≠ api-gateway)
- ✅ Separate containerization
- ✅ Clear deployment pipeline

---

## 🔧 Immediate Fixes (Quick Wins)

### **Fix #1: Session Persistence**

**Current Problem**: User preferences lost on refresh

**Solution**: Use Chainlit's data layer to persist session data

```python
# demo-ui/app.py
@cl.on_chat_start
async def on_chat_start():
    """Initialize session with persisted data."""
    user_id = cl.user_session.get("user_id")

    # Load from database instead of in-memory
    persisted_data = await load_user_session_from_db(user_id)

    cl.user_session.set("farm_id", persisted_data["farm_id"])
    cl.user_session.set("expertise_areas", persisted_data["expertise_areas"])
    cl.user_session.set("chat_profile", persisted_data["chat_profile"])
    # ... restore other preferences
```

**Status**: ✅ Already partially implemented in your `data_layer.py`
**Action**: Ensure `@cl.on_chat_start` loads ALL session state from DB

---

### **Fix #2: MCP Initialization Race Condition**

**Current Problem**: MCP tools fail to load if server isn't ready

**Solution**: Implement retry logic with exponential backoff

```python
# demo-ui/services/mcp_connector.py
async def initialize_mcp_with_retry(max_retries=3, initial_delay=1.0):
    """Initialize MCP client with exponential backoff."""
    for attempt in range(max_retries):
        try:
            await client.get_tools()
            logger.info("mcp_initialized", attempt=attempt)
            return True
        except Exception as e:
            delay = initial_delay * (2 ** attempt)
            logger.warning(
                "mcp_init_failed_retrying",
                attempt=attempt,
                next_retry_in_seconds=delay,
                error=str(e)
            )
            await asyncio.sleep(delay)

    logger.error("mcp_initialization_failed")
    return False
```

---

### **Fix #3: Graceful Degradation**

**Current Problem**: Chat fails completely if MCP is offline

**Solution**: Continue without tools if MCP unavailable

```python
# demo-ui/app.py - on_message()
try:
    mcp_tools = await load_mcp_tools()
except Exception:
    logger.warning("mcp_unavailable_continuing_without_tools")
    mcp_tools = []  # Empty tools list

# Pass empty list to LLM instead of failing
state["mcp_tools_available"] = mcp_tools
```

---

### **Fix #4: Clear State Management**

**Problem**: Confusing where session state lives (in-memory vs DB vs Redis)

**Solution**: Create state layer abstraction

```python
# demo-ui/services/session_manager.py
class SessionManager:
    """Unified session state management."""

    def __init__(self, user_id: str, db_session):
        self.user_id = user_id
        self.db = db_session

    async def load_preferences(self) -> dict:
        """Load from persistent storage."""
        return await self.db.get_user_preferences(self.user_id)

    async def save_preferences(self, prefs: dict) -> None:
        """Persist to database."""
        await self.db.save_user_preferences(self.user_id, prefs)

    async def get_farm(self) -> str:
        """Get farm ID with fallback."""
        prefs = await self.load_preferences()
        return prefs.get("farm_id", "demo_farm_001")
```

---

## 📋 Refactoring Roadmap (12-Factor Compliant)

### **Phase 1: Configuration Management** (Week 1)
- [ ] Create unified config layer (`src/ALİM/config_schema.py`)
- [ ] Validate all env vars at startup
- [ ] Add config documentation
- [ ] Separate demo/dev/prod configs

**Files to create:**
```python
# src/ALİM/config_schema.py
class AppConfig(BaseModel):
    """12-factor compliant config."""
    # Backend services
    langgraph_url: HttpUrl = "http://localhost:2024"
    mcp_url: HttpUrl = "http://localhost:7777"
    postgres_url: str
    redis_url: str

    # Feature flags
    enable_mcp: bool = True
    enable_oauth: bool = True

    def validate_connectivity(self):
        """Health check all services."""
        # Validation logic
```

### **Phase 2: Session Persistence** (Week 1)
- [ ] Implement `SessionManager` class
- [ ] Ensure all state persisted to PostgreSQL
- [ ] Add session cleanup/TTL
- [ ] Test refresh scenario

### **Phase 3: Graceful Degradation** (Week 2)
- [ ] Implement MCP retry logic
- [ ] Add feature flags for optional services
- [ ] Test with services down
- [ ] Add degraded-mode indicators to UI

### **Phase 4: Service Separation** (Week 2-3)
- [ ] Extract API routes to standalone app
- [ ] Extract MCP server to separate process
- [ ] Create service communication layer
- [ ] Docker Compose with clear service boundaries

### **Phase 5: Frontend Separation** (Week 3-4)
- [ ] Create React/Next.js frontend (optional)
- [ ] Or: Replace Chainlit with custom UI
- [ ] Implement proper state management
- [ ] Add client-side persistence

---

## 🎯 Why You Have Three UIs

| UI | Purpose | Problem |
|----|---------|---------|
| **Chainlit** | User-facing chat | Stateful, tightly coupled, ~3k lines |
| **FastAPI** | Backend REST API | Meant for external clients, but only used by Chainlit |
| **MCP Server** | Tool definitions | Should be called via MCP client, not exposed separately |

**Better Architecture:**
```
React Frontend
    ↓ (HTTP REST)
FastAPI Gateway
    ├→ Agent Service (LangGraph client)
    ├→ Rules Service (MCP client)
    └→ Auth Service
```

Single UI, clear separation of concerns.

---

## 🚀 Immediate Action Items

### **Priority 1: Fix Session Persistence** (30 min)
1. Update `@cl.on_chat_start` to load from DB
2. Add session TTL/cleanup
3. Test refresh scenario

### **Priority 2: MCP Graceful Degradation** (1 hour)
1. Add retry logic with exponential backoff
2. Catch MCP errors, continue without tools
3. Show user indicator when offline

### **Priority 3: State Layer** (2 hours)
1. Create `SessionManager` class
2. Move all state access through it
3. Add logging/debugging

### **Priority 4: Config Validation** (1 hour)
1. Create config schema with Pydantic
2. Validate at startup
3. Document all env vars

**Total: ~4 hours to stabilize**

---

## 📊 Recommended Tech Stack for Clean Refactoring

| Layer | Current | Recommended |
|-------|---------|-------------|
| **Frontend** | Chainlit (3k lines) | React/Next.js (easier to maintain) |
| **State** | In-memory + DB | Zustand/Redux (React) + IndexedDB |
| **Backend** | Mixed FastAPI/Chainlit | FastAPI (REST only) |
| **Services** | All in one process | Docker Compose (separate containers) |
| **Persistence** | PostgreSQL + Redis | Same, but clearer schema |
| **Observability** | Langfuse + structlog | Same (works great!) |

---

## Summary

**Your system is architecturally sound but operationally fragile:**

✅ **Good:**
- LangGraph integration
- Langfuse observability
- MCP tools framework
- Persona system

❌ **Issues:**
- Stateful UI loses data on refresh
- 3 UIs causing confusion
- MCP initialization race condition
- No graceful degradation

**Quick fixes (4 hours):**
1. Persist session state to DB
2. Add MCP retry/fallback
3. Create config validation
4. Add state layer abstraction

**Long-term (refactor):**
1. Separate frontend (React) from backend (FastAPI)
2. Clear microservice boundaries
3. 12-factor compliance
4. Better testing/deployment
