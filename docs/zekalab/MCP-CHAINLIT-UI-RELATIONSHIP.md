# 🔗 Chainlit UI ⟷ MCP Setup: Relationship & Connections

## 📌 Overview

**YES, there is a direct relationship** between the MCP button/status display in Chainlit UI and the MCP setup created. They are **tightly integrated** and work together as a complete system.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CHAINLIT UI (8501)                       │
│                      demo-ui/app.py                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 🔌 MCP Status Indicator (UI LAYER)                   │   │
│  │ ├─ Button: View MCP Connection Status                │   │
│  │ ├─ Real-time health checks (check_mcp_health)        │   │
│  │ ├─ Status badges: ✅ Online | ❌ Offline            │   │
│  │ └─ MCP_SERVICES config dict                          │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │ HTTP Requests                        │
└───────────────────────┼──────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
    PORT 7777                    PORT 2024
┌──────────────────┐        ┌──────────────────┐
│  ZekaLab MCP     │        │   LangGraph API  │
│  (FastMCP Server)│        │   (Graph Server) │
│                  │        │                  │
│ • /health        │        │ • /ok            │
│ • /mcp (proxy)   │        │ • Graph exec     │
│                  │        │                  │
│ ✅ Running      │        │ ✅ Running      │
└──────────────────┘        └──────────────────┘
        ▲                               ▲
        │                               │
        └───────────────┬───────────────┘
                        │
         ┌──────────────┴──────────────┐
         │                             │
    Configured via:              Configured via:
    - ZEKALAB_MCP_ENABLED=true   - langgraph.json
    - ZEKALAB_MCP_URL=...        - env vars
    - ZEKALAB_MCP_SECRET=...
```

---

## 🔌 The Connections (Links)

### 1️⃣ **Configuration Connection** (Static)

#### Chainlit reads from environment:
```python
# demo-ui/app.py (lines 327-343)

MCP_SERVICES = {
    "zekalab": {
        "name": "ZekaLab Internal Rules",
        "url": os.getenv("ZEKALAB_MCP_URL", "http://localhost:7777"),  # ← Env var
        "health_endpoint": "/health",
    },
    "langgraph": {
        "name": "LangGraph API",
        "url": demo_settings.langgraph_base_url,  # ← From config
        "health_endpoint": "/ok",
    },
}
```

**Where they come from:**
- `.env` file → `ZEKALAB_MCP_URL=http://localhost:7777`
- `langgraph.json` → `ZEKALAB_MCP_ENABLED=true`
- Settings objects → `demo_settings.langgraph_base_url`

---

### 2️⃣ **Health Check Connection** (Dynamic)

#### Chainlit actively monitors MCP servers:
```python
# demo-ui/app.py (lines 345-370)

async def check_mcp_health(service_key: str) -> MCPServiceStatus:
    """Check health of a single MCP service."""
    service = MCP_SERVICES.get(service_key)
    url = f"{service['url']}{service['health_endpoint']}"  # Constructs URL

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)  # HTTP GET to /health endpoint
            # Returns: MCPServiceStatus with online/offline status
```

**What it checks:**
- `http://localhost:7777/health` → ZekaLab MCP FastMCP server
- `http://localhost:2024/ok` → LangGraph server

---

### 3️⃣ **Tool Loading Connection** (Functional)

#### LangGraph loads MCP tools via adapters:
```python
# src/ALİM/mcp/adapters.py (lines 33-88)

def get_mcp_client_config() -> dict[str, dict[str, Any]]:
    """Build MCP client configuration from settings."""

    # Configuration built from same env vars Chainlit reads
    if settings.zekalab_mcp_enabled:
        zekalab_config = {
            "url": f"{settings.zekalab_mcp_url}/mcp",  # Same URL, + /mcp suffix
            "transport": "http",
        }

    return config  # Dict passed to MultiServerMCPClient

async def get_mcp_tools() -> list[BaseTool]:
    """Get all tools from configured MCP servers."""
    client = create_mcp_client()
    tools = await client.get_tools()  # Fetches tools from ZekaLab FastMCP
    return tools
```

**Flow:**
1. Chainlit reads config & checks health ✓
2. LangGraph reads **same config** & loads tools ✓
3. Both point to same MCP server (port 7777)

---

### 4️⃣ **Agent State Connection** (Observability)

#### MCP traces recorded in LangGraph state:
```python
# src/ALİM/agent/state.py

class AgentState(TypedDict):
    # ... other fields
    mcp_traces: list[MCPTrace]  # Records every MCP call
    mcp_source: str  # "zekalab" | "openweather" | "local"
    mcp_config: dict  # Config used for this run
```

#### Chainlit displays these traces:
```python
# demo-ui/app.py (lines 2847-2900)

def _format_mcp_data_flow(mcp_traces: list[dict]) -> str | None:
    """Format MCP call traces for display."""
    # Renders:
    # - Server name (zekalab, openweather)
    # - Tool called (evaluate_irrigation_rules, etc.)
    # - Duration (42.5ms)
    # - Success/error status
    # - Data source attribution
```

---

## 📊 The Three Layers

### **Layer 1: UI (Chainlit)**
- **Role:** Display & health monitoring
- **Responsibilities:**
  - ✅ Show MCP status buttons
  - ✅ Real-time health checks
  - ✅ Display MCP data flow visualization
  - ✅ Show which data source was used

- **Files:** `demo-ui/app.py` (lines 327-400+)

### **Layer 2: Orchestration (LangGraph)**
- **Role:** Graph execution & tool binding
- **Responsibilities:**
  - ✅ Load MCP tools via adapters
  - ✅ Execute MCP calls via ToolNode
  - ✅ Record MCPTrace for observability
  - ✅ Handle fallback if MCP unavailable

- **Files:**
  - `src/ALİM/agent/graph.py` (ToolNode setup)
  - `src/ALİM/mcp/adapters.py` (MCP client config)

### **Layer 3: MCP Servers (Backend)**
- **Role:** Tool/resource providers
- **Responsibilities:**
  - ✅ Expose tools via standardized MCP protocol
  - ✅ Respond to health checks
  - ✅ Execute agricultural rules

- **Files:**
  - `src/ALİM/mcp_server/zekalab_fastmcp.py` (ZekaLab, port 7777)
  - External: OpenWeather MCP

---

## 🔗 Specific Links (What Points Where)

### **Link 1: Configuration Source → All Components**
```
.env (or environment)
  ├─ ZEKALAB_MCP_ENABLED → adapters.py, app.py
  ├─ ZEKALAB_MCP_URL → adapters.py, app.py
  ├─ ZEKALAB_MCP_SECRET → adapters.py
  └─ ZEKALAB_PORT → zekalab_fastmcp.py (server)

langgraph.json
  ├─ ZEKALAB_MCP_ENABLED (environment)
  ├─ ZEKALAB_MCP_URL (environment)
  └─ Passes env to LangGraph runtime
```

### **Link 2: Chainlit Button → Health Check → MCP Server**
```
User clicks "MCP Status" button (UI)
  ↓
check_mcp_health("zekalab") called
  ↓
HTTP GET http://localhost:7777/health
  ↓
ZekaLab FastMCP responds with status
  ↓
Chainlit displays badge: ✅ Online (42ms)
```

### **Link 3: Chainlit Chat → LangGraph → MCP Tools**
```
User sends message
  ↓
Chainlit sends to LangGraph at http://localhost:2024
  ↓
LangGraph ToolNode has MCP tools available
  ↓
If LLM decides to call MCP tool:
  → LLM says: "use evaluate_irrigation_rules"
  → ToolNode calls tool via MCP adapter
  → HTTP to http://localhost:7777/mcp (proxy endpoint)
  → Tool executes, returns result
  → ToolNode records MCPTrace
  ↓
MCPTrace sent back to Chainlit
  ↓
Chainlit displays: "📊 Data from ZekaLab (irrigation rules, 28ms)"
```

### **Link 4: Profile-Based Tool Access**
```
User selects profile: "cotton"
  ↓
Chainlit sends profile to LangGraph
  ↓
LangGraph calls: get_mcp_tools_for_profile("cotton")
  ↓
adapters.py filters by PROFILE_MCP_SERVERS["cotton"]
  = ["zekalab", "openweather"]  # Cotton gets weather + rules
  ↓
Only these tools loaded into ToolNode
  ↓
LLM can only call tools from these servers
```

---

## ✅ What SHOULD Be Linked (Currently Implemented)

### 1. **Configuration Sync** ✅
- [ ] **Status:** All components read from same env vars
- **Verification:** Check that `.env` has these keys:
  ```bash
  ZEKALAB_MCP_ENABLED=true
  ZEKALAB_MCP_URL=http://localhost:7777
  ZEKALAB_MCP_SECRET=<optional>
  ```

### 2. **Server Discovery** ✅
- **Status:** Both UI & LangGraph can find MCP servers
- **Verification:**
  ```bash
  curl http://localhost:7777/health  # ZekaLab
  curl http://localhost:2024/ok      # LangGraph
  ```

### 3. **Tool Loading** ✅
- **Status:** LangGraph loads tools from MCP servers
- **Verification:**
  ```bash
  # Check MCP client config in adapters.py
  # Look for: get_mcp_tools() returns []  → tools loaded
  ```

### 4. **Health Monitoring** ✅
- **Status:** Chainlit monitors server health continuously
- **Verification:**
  ```python
  # In demo-ui/app.py
  # check_mcp_health() runs every N seconds
  # Chainlit UI shows status badges
  ```

### 5. **Observability** ✅
- **Status:** MCPTrace records each tool call
- **Verification:**
  ```python
  # In agent/state.py
  # AgentState.mcp_traces contains list of MCPTrace
  # Chainlit displays: _format_mcp_data_flow()
  ```

---

## 🚀 How to Verify the Connections

### **Test 1: Config Consistency**
```bash
# Check all three read the same URL
grep -r "ZEKALAB_MCP_URL" src/ALİM/mcp/adapters.py
grep -r "ZEKALAB_MCP_URL" demo-ui/app.py
grep -r "zekalab_mcp_url" langgraph.json
```

### **Test 2: Health Check End-to-End**
```bash
# 1. Start MCP server
Task: "🌿 ALİM: 🧠 ZekaLab MCP Start"

# 2. Check it responds
curl http://localhost:7777/health
# Expected: {"status": "healthy", ...}

# 3. Start Chainlit
Task: "🌿 ALİM: 🖥️ UI Start"

# 4. Open UI and look for MCP status badge
# Should show: ✅ ZekaLab (12ms) • ✅ LangGraph (8ms)
```

### **Test 3: Tool Loading**
```bash
# Run MCP client test
.venv\Scripts\python.exe -m pytest tests/unit/test_mcp_server/ -v -k "test_tool"
# Should show: PASSED for each tool
```

### **Test 4: Trace Observability**
```bash
# Send a message in Chainlit that uses MCP
# Check server logs for:
# INFO mcp_tools_loaded tool_count=5 tool_names=[...]
# INFO mcp_client_created servers=['zekalab']
```

---

## 📋 Component Checklist

### **Chainlit UI (demo-ui/app.py)**
- [ ] `MCP_SERVICES` dict defined (lines 333-343)
- [ ] `check_mcp_health()` function (lines 345-370)
- [ ] `get_all_mcp_status()` function for background monitoring
- [ ] Status badges displayed in welcome message
- [ ] `_format_mcp_data_flow()` displays MCP traces
- [ ] Data consent flow for MCP attribution

### **LangGraph (src/ALİM/agent/graph.py)**
- [ ] ToolNode created with MCP tools
- [ ] `get_mcp_tools()` called in make_graph()
- [ ] Agent can invoke MCP tools
- [ ] MCPTrace recorded for each call

### **MCP Adapters (src/ALİM/mcp/adapters.py)**
- [ ] `get_mcp_client_config()` builds config from env
- [ ] `create_mcp_client()` returns MultiServerMCPClient
- [ ] `get_mcp_tools()` fetches tools from all servers
- [ ] Profile-based filtering (PROFILE_MCP_SERVERS)
- [ ] Health check function

### **MCP Server (src/ALİM/mcp_server/zekalab_fastmcp.py)**
- [ ] FastMCP app created
- [ ] 5 tools exposed (irrigation, fertilization, pest control, subsidy, harvest)
- [ ] 3 resources exposed (rules, crop profiles, subsidy data)
- [ ] `/health` endpoint responds
- [ ] Runs on port 7777

### **Configuration (langgraph.json + .env)**
- [ ] `ZEKALAB_MCP_ENABLED=true`
- [ ] `ZEKALAB_MCP_URL=http://localhost:7777`
- [ ] `ZEKALAB_PORT=7777` (MCP server)
- [ ] Env vars passed to LangGraph runtime

---

## 🎯 Key Takeaways

| Aspect | Chainlit UI | LangGraph | MCP Server |
|:-------|:-----------|:----------|:-----------|
| **Reads config from** | `.env` vars | `langgraph.json` env | `os.getenv()` |
| **Monitors health** | ✅ Yes | ❌ No (UI does) | ❌ No (serves) |
| **Loads tools** | ❌ No | ✅ Yes via adapters | ✅ Exposes via MCP |
| **Port** | 8501 | 2024 | 7777 |
| **Connection method** | HTTP GET /health | HTTP MCP protocol | HTTP FastMCP |
| **Shows user** | Status badges | Tool execution | (invisible) |

---

## 🔄 Data Flow Example

**Scenario:** User asks "How much should I irrigate?"

```
1. CHAINLIT UI (8501)
   User message sent → LangGraph at http://localhost:2024

2. LANGGRAPH (2024)
   a) Loads MCP tools via adapters.py:
      - Connects to http://localhost:7777/mcp
      - Gets: [evaluate_irrigation_rules, ...]

   b) LLM processes message & decides: "need irrigation tool"

   c) ToolNode executes: evaluate_irrigation_rules()
      - Calls MCP: http://localhost:7777/mcp
      - Method: POST with tool call params

   d) Receives result
      - Records: MCPTrace(server="zekalab", tool="irrigation", ...)

   e) Returns to Chainlit with:
      - response: "Irrigate 30mm tomorrow"
      - mcp_traces: [MCPTrace(...)]

3. ZEKALAB MCP (7777)
   - Received irrigation request via HTTP
   - Executed rules (soil + temp + rainfall)
   - Returned recommendation
   - (Chainlit can also GET /health separately)

4. CHAINLIT UI (8501)
   a) Receives response + mcp_traces

   b) Displays:
      ✓ Answer to user
      ✓ "📊 Data from ZekaLab (irrigation rules, 42ms)"
      ✓ In header: "🔌 ✅ ZekaLab (12ms) • ✅ LangGraph (8ms)"

5. BACKGROUND (Continuous)
   - Chainlit periodically calls check_mcp_health()
   - Updates status badges
   - Shows real-time connectivity
```

---

## 🛠️ How to Add a New MCP Server

To integrate a new MCP server (e.g., Postgres MCP):

### **1. Add to MCP_SERVICES in Chainlit**
```python
# demo-ui/app.py

MCP_SERVICES = {
    "zekalab": {...},
    "langgraph": {...},
    "postgres_mcp": {  # NEW
        "name": "Database Queries",
        "url": os.getenv("POSTGRES_MCP_URL", "http://localhost:7778"),
        "health_endpoint": "/health",
    },
}
```

### **2. Add to LangGraph config**
```json
# langgraph.json
"env": {
    "ZEKALAB_MCP_ENABLED": "...",
    "POSTGRES_MCP_ENABLED": "POSTGRES_MCP_ENABLED",  # NEW
    "POSTGRES_MCP_URL": "POSTGRES_MCP_URL"  # NEW
}
```

### **3. Add to adapters config**
```python
# src/ALİM/mcp/adapters.py

if settings.postgres_mcp_enabled:
    postgres_config = {
        "url": f"{settings.postgres_mcp_url}/mcp",
        "transport": "http",
    }
    config["postgres"] = postgres_config
```

### **4. Add to profile permissions**
```python
# src/ALİM/mcp/adapters.py

PROFILE_MCP_SERVERS["expert"] = ["zekalab", "openweather", "postgres"]
```

### **5. Update profile UI selector**
```python
# demo-ui/app.py
# Add option to chat profile selector
```

**Now:** Chainlit shows status, LangGraph loads tools, user can use DB queries!

---

## 📚 Related Documentation

- [MCP-ARCHITECTURE.md](MCP-ARCHITECTURE.md) - Overall system design
- [24-MCP-PHASE-5-DEMO-ENHANCEMENT.md](24-MCP-PHASE-5-DEMO-ENHANCEMENT.md) - UI integration details
- [23-MCP-PHASE-3-INTERNAL-SERVER.md](23-MCP-PHASE-3-INTERNAL-SERVER.md) - FastMCP server setup
- [MCP-BLUEPRINT.md](MCP-BLUEPRINT.md) - Developer guidelines

---

## 🎓 Summary

**The Chainlit MCP button and the MCP setup are NOT separate systems—they are parts of one integrated architecture:**

1. **Chainlit** = UI layer that monitors and displays MCP status
2. **LangGraph** = Orchestration layer that uses MCP tools
3. **MCP Servers** = Backend layer providing tools
4. **Adapters** = Bridge connecting LangGraph to MCP servers
5. **Configuration** = Shared `.env` variables connecting all parts

When you see the ✅ status badge in Chainlit, it's directly monitoring the same MCP server that LangGraph loads tools from. They're talking to the same 7777 endpoint, using the same configuration, and the UI displays what the agent actually used in its decision-making process.

**This is the "sovereign MCP stack"—fully integrated, fully observable, fully traceable.** 🌾✨
