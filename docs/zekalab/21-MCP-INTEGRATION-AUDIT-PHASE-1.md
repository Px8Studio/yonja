# 🔍 MCP Integration Audit - Phase 1: Foundation & Assessment

**Status:** 📋 Completed
**Date:** January 23, 2026
**Owner:** Development Team
**Duration:** Phase 1 (Week 1)

---

## 🎯 Executive Summary

ALEM has a **mature, production-ready LangGraph orchestrator** with clear separation of concerns. The codebase is **ideal for MCP integration** because:

✅ **Modular node architecture** - Each node handles one concern (weather, agronomist, validator)
✅ **Explicit state management** - `AgentState` clearly defines all data flows
✅ **Synthetic-to-real switchability** - Currently synthetic; MCP makes real data easy to plug in
✅ **Deterministic rules engine** - Candidates for private MCP server (Cotton Rules, Subsidy Logic)
✅ **Observability ready** - Langfuse tracing + logging infrastructure in place

**Key Finding:** You're not starting from scratch; you're **professionalizing existing integrations**.

---

## 📊 Current Architecture Overview

### LangGraph Orchestrator Flow

```
START
  │
  ▼
┌─────────────────────┐
│  SUPERVISOR NODE    │  ← Routes user intent
│ (Intent detection)  │
└─────────────────────┘
  │
  └─► "end" (off-topic) ─────────► END
  └─► "context_loader" ──────────┐
      │                           │
      ├─► "agronomist" ────────┐  │
      │   (rule-based advice)  │  │
      │                        │  │
      ├─► "weather" ──────────┤  │
      │   (weather analysis)   │  │
      │                        │  │
      ├─► "nl_to_sql" ────────┤  │
      │   (data queries)       │  │
      │                        │  │
      ├─► "vision_to_action"──┤  │
      │   (image analysis)     │  │
      │                        │  │
      └─► "validator" ◄───────┘  │
          (confidence scoring)    │
          │                       │
          └──────────────────────► END
```

### State Machine (AgentState)

```python
@dataclass
class AgentState:
    # Input
    user_id: str
    current_input: str                    # User message

    # Routing & Intent
    routing: RoutingDecision | None       # Supervisor's decision
    intent: UserIntent | None             # Classified intent

    # Context (Loaded by context_loader node)
    user_context: UserContext | None      # User profile
    farm_context: FarmContext | None      # Farm data
    weather: WeatherContext | None        # Weather data ← SYNTHETIC (TODO)

    # Execution
    current_response: str | None          # Generated response
    nodes_visited: list[str]              # Path through graph
    messages: list[dict[str, Any]]        # Conversation history
```

---

## 🔗 Integration Point Analysis

### 1. **Weather Node** (weather.py)

| Aspect | Current State | MCP Candidate |
|--------|:-------------:|:-------------:|
| **Data Source** | Synthetic (random generator) | ✅ **OpenWeather MCP** |
| **Function** | Analyzes weather + farm context | Yes (Weather + Agro context) |
| **Frequency** | Per-request | Real-time forecasts |
| **User Visibility** | Shows in response | Show data source in UI |
| **Latency Requirement** | <2s | <500ms (cache) |

**Current Code:**
```python
# src/yonca/agent/nodes/context_loader.py (lines 106-125)
if "weather" in requires_context:
    # TODO: Integrate with real weather API
    farm_context = updates.get("farm_context") or state.get("farm_context")

    if farm_context:
        weather = await _get_synthetic_weather(farm_context.region)
        updates["weather"] = weather
    else:
        # Default weather if no farm context
        updates["weather"] = WeatherContext(...)
```

**MCP Transformation:**
- Replace `_get_synthetic_weather()` with call to **Weather MCP Server**
- Pass `(latitude, longitude, crop_type)` as context
- Receive `WeatherContext` in standardized format
- Add MCP metadata: `{"source": "openweather-mcp", "freshness_seconds": 300}`

---

### 2. **Rules Engine** (rules/engine.py)

| Aspect | Current State | MCP Candidate |
|--------|:-------------:|:-------------:|
| **Data Source** | Local YAML files (irrigation.yaml, fertilization.yaml) | ✅ **ZekaLab Private MCP** |
| **Function** | Context-aware rule evaluation | Expose as MCP tools |
| **Rules Count** | 20+ (AZ- prefixed) | Scalable |
| **User Visibility** | Trust scores + rule citations | Explicit tool calls in trace |
| **Business Logic** | Cotton, Wheat, Vegetables | Proprietary → MCP server |

**Current Rules:**
```
├── irrigation.yaml
├── fertilization.yaml
├── pest_control.yaml
└── harvest.yaml
```

Each rule has:
- Conditions (field → operator → value)
- Priority (low/medium/high/critical)
- Confidence score
- Localized recommendations (AZ + EN)

**MCP Transformation:**
- Create `fastmcp` server at `/src/yonca/mcp/internal_server.py`
- Expose each rule category as MCP **tools**
  - `evaluate_irrigation_rules(farm_data, weather_data) → Recommendation[]`
  - `evaluate_fertilization_rules(soil_data, crop_type) → Recommendation[]`
  - `evaluate_pest_control_rules(weather_data, crop_stage) → Recommendation[]`
- Keep YAML as **resources** (fetched by agent for explainability)
- Add subsidy database as **resource** (read-only)

---

### 3. **Data Repositories** (data/repositories/)

| Aspect | Current State | MCP Candidate |
|--------|:-------------:|:-------------:|
| **Data Source** | PostgreSQL (synthetic) | ✅ **EKTİS MCP** (later) |
| **Function** | Farm, User, Parcel queries | Hot-swap for real farms |
| **Cache Layer** | Redis (in-process) | Preserved with MCP |
| **Read/Write** | Read-mostly | Read-only (for now) |

**Current:**
```python
# Cached repositories
CachedUserRepository(base_repo)
CachedFarmRepository(base_repo)
```

**MCP Fit:** These are **later-phase integrations** (Phase 3-4):
- EKTİS MCP (Government farm database)
- CBAR Banking MCP (Fermer Kartı)
- These replace the repository layer, not the node layer

---

### 4. **Vision/Image Analysis** (vision_to_action.py)

| Aspect | Current State | MCP Candidate |
|--------|:-------------:|:-------------:|
| **Data Source** | Ollama vision model (local) | ✅ **Vision MCP** (future) |
| **Function** | Pest/disease detection from photos | Tool-based analysis |
| **Latency** | 5-10s (local model) | Can offload to MCP |

**MCP Fit:** Lower priority (Phase 4), but doable.

---

### 5. **LLM Provider Layer** (llm/factory.py)

| Aspect | Current State | MCP Candidate |
|--------|:-------------:|:-------------:|
| **Abstraction** | Provider factory (Ollama, Groq, etc.) | ✅ Agnostic to MCP calls |
| **Impact** | LLM output parsed into state | MCP tools = structured outputs |

**MCP Fit:** **No change needed**. LLM layer is already decoupled from data sources.

---

## 📈 Data Flow Patterns

### Pattern 1: Synthetic → Real (Weather Example)

```
CURRENT STATE:
  context_loader_node
    ├─ Check if "weather" in requires_context
    ├─ Call _get_synthetic_weather(region)
    └─ Store in state.weather

MCP STATE:
  context_loader_node (REFACTORED)
    ├─ Check if "weather" in requires_context
    ├─ Create MCP client
    ├─ Call weather_mcp.get_forecast(lat, lon, crop_type)
    ├─ Receive standardized WeatherContext + MCP metadata
    └─ Store in state.weather + state.mcp_context
```

**Key Insight:** The `WeatherContext` data model **doesn't change**. We just swap the source.

---

### Pattern 2: Rules as MCP Tools

```
CURRENT STATE:
  agronomist_node
    ├─ Load rules from engine.py
    ├─ Call rule.evaluate(context)
    └─ Return matched recommendations

MCP STATE:
  agronomist_node (REFACTORED)
    ├─ Create MCP client
    ├─ Call zekalab_mcp.evaluate_irrigation_rules(farm_context, weather)
    ├─ Receive Recommendation[] with rule citations
    └─ Format response + log to Langfuse
```

**Benefit:** Rules are now **version-controlled in MCP server**, not baked into the agent binary.

---

### Pattern 3: Data Query (NL-to-SQL)

```
CURRENT STATE:
  nl_to_sql_node
    ├─ Generate SQL from user query
    └─ Execute via sql_executor_node

MCP STATE:
  nl_to_sql_node (MINIMAL CHANGE)
    ├─ Generate SQL from user query
    ├─ Execute via sql_executor_node (unchanged)
    ├─ (Later) Replace repository layer with EKTİS MCP
    └─ All history/logging preserved
```

**Impact:** Zero changes needed for Phase 1. EKTİS integration is Phase 3.

---

## 🗂️ File Structure for MCP Integration

### New Files Needed

```
src/yonca/
├── mcp/                              ← NEW: MCP client layer
│   ├── client.py                     # MCP client factory
│   ├── handlers/
│   │   ├── weather_handler.py        # Call weather MCP
│   │   ├── rules_handler.py          # Call internal MCP
│   │   └── __init__.py
│   └── __init__.py
│
├── mcp_server/                       ← NEW: Internal MCP server (fastmcp)
│   ├── __init__.py
│   ├── main.py                       # FastMCP app
│   ├── resources/
│   │   ├── rules.py                  # Expose YAML rules
│   │   ├── subsidies.py              # Subsidy database
│   │   └── __init__.py
│   └── tools/
│       ├── irrigation.py             # Irrigation evaluation
│       ├── fertilization.py          # Fertilization evaluation
│       ├── pest_control.py           # Pest control evaluation
│       └── __init__.py
│
└── agent/
    └── nodes/
        ├── weather.py                # ✏️ REFACTORED: Use weather MCP
        ├── agronomist.py             # ✏️ REFACTORED: Use rules MCP
        └── context_loader.py         # ✏️ REFACTORED: Orchestrate MCP calls
```

---

## 🔐 Authentication & Security

### MCP Client Configuration

**For Public MCP Servers:**
```
OPENWEATHER_MCP_URL=https://openweather-mcp.example.com
OPENWEATHER_API_KEY=...              # In .env
OPENWEATHER_TIMEOUT=500ms
```

**For ZekaLab Private MCP Server:**
```
ZEKALAB_MCP_URL=http://localhost:7777
ZEKALAB_MCP_SECRET=...               # Shared secret
ZEKALAB_MCP_TIMEOUT=1000ms           # Longer timeout for local
```

**For Future Integration (EKTİS):**
```
EKTIS_MCP_URL=https://ektis-api.example.com
EKTIS_JWT_SECRET=...
EKTIS_CLIENT_ID=...
```

---

## 📋 Dependency Analysis

### Packages to Add (pyproject.toml)

```toml
[dependencies]
# MCP Client
mcp = "^0.8.0"              # Official MCP SDK
httpx = "^0.24.0"           # Already in use (async HTTP)

# MCP Server (for internal server)
fastmcp = "^0.5.0"          # Build internal server
pydantic = "^2.0"           # Already in use
```

### No Breaking Changes

- ✅ Existing dependencies preserved
- ✅ LangGraph/Chainlit unchanged
- ✅ Database layer untouched (Phase 1)
- ✅ State model can be extended (backward compatible)

---

## 🎯 MCP Integration Candidates (Priority Order)

### Phase 1: Foundation (Week 1) - **START HERE**

| # | Component | Type | Effort | Priority | Why First |
|---|-----------|------|:------:|:--------:|-----------|
| 1.1 | **MCP Client Layer** | Code | 2-3h | 🔴 | Foundation for all MCP calls |
| 1.2 | **MCP Config + Env** | Config | 1h | 🔴 | Standardize credentials |
| 1.3 | **Test Framework** | Tests | 2h | 🔴 | Mock MCP for unit tests |
| 1.4 | **Langfuse MCP Logging** | Observability | 2h | 🟠 | Trace MCP calls |

**Estimated Time:** 7-8 hours
**Blocker:** None (foundation only)

---

### Phase 2: Public MCP Servers (Week 2)

| # | Component | Type | Effort | Priority | Why Second |
|---|-----------|------|:------:|:--------:|-----------|
| 2.1 | **Weather MCP Integration** | Integration | 4-5h | 🔴 | Highest ROI; ready to demo |
| 2.2 | **Chainlit UI Indicators** | UI | 2-3h | 🟠 | User feedback |

**Estimated Time:** 6-8 hours
**Blocker:** 1.1, 1.2, 1.3

---

### Phase 3: Internal MCP Server (Week 3)

| # | Component | Type | Effort | Priority | Why Third |
|---|-----------|------|:------:|:--------:|-----------|
| 3.1 | **FastMCP Server Setup** | Code | 3-4h | 🔴 | Deploy rules as MCP |
| 3.2 | **Rules as MCP Tools** | Refactor | 5-6h | 🔴 | Core logic exposure |
| 3.3 | **Subsidy DB as MCP Resource** | Code | 2h | 🟠 | Data governance |
| 3.4 | **Security + Auth** | Security | 2h | 🟠 | Enterprise ready |

**Estimated Time:** 12-14 hours
**Blocker:** 1.1, 1.2, 1.3

---

### Phase 4: LangGraph Refactor (Week 4)

| # | Component | Type | Effort | Priority | Why Fourth |
|---|-----------|------|:------:|:--------:|-----------|
| 4.1 | **Agronomist Node Refactor** | Refactor | 3-4h | 🔴 | Use rules MCP |
| 4.2 | **Weather Node Refactor** | Refactor | 2-3h | 🔴 | Use weather MCP |
| 4.3 | **Multi-MCP Orchestration** | Tests | 2-3h | 🟠 | Complex workflows |
| 4.4 | **Performance Tuning** | Optimization | 2-3h | 🟠 | <2s response time |

**Estimated Time:** 10-13 hours
**Blocker:** 2.1, 3.1

---

### Phase 5: Demo & Documentation (Week 5)

| # | Component | Type | Effort | Priority | Why Fifth |
|---|-----------|------|:------:|:--------:|-----------|
| 5.1 | **Chainlit MCP Status Display** | UI | 2-3h | 🟠 | Visibility |
| 5.2 | **Data Source Attribution** | UI | 1-2h | 🟠 | Trust building |
| 5.3 | **End-to-End Demo** | Testing | 2-3h | 🟠 | Show stakeholders |
| 5.4 | **Documentation** | Docs | 2-3h | 🟠 | Handoff |

**Estimated Time:** 8-11 hours
**Blocker:** 4.1, 4.2

---

## 📊 Success Metrics (Phase 1)

By end of Week 1, you should have:

- ✅ MCP client layer (`src/yonca/mcp/`) integrated into codebase
- ✅ Configuration management for MCP servers (dev + prod)
- ✅ Unit tests with mocked MCP calls (100% coverage)
- ✅ Langfuse integration tracking MCP latency + success rates
- ✅ Zero impact on existing LangGraph nodes (backward compatible)
- ✅ Documentation of MCP data flow in existing architecture

---

## 🚀 Phase 1 Deliverables

### Code Deliverables
1. `src/yonca/mcp/client.py` - MCP client factory
2. `src/yonca/mcp/config.py` - Configuration management
3. `tests/unit/test_mcp_client.py` - Unit tests
4. Updated `src/yonca/config.py` - MCP settings

### Documentation Deliverables
1. `docs/zekalab/22-MCP-CLIENT-ARCHITECTURE.md` - Technical design
2. `docs/zekalab/23-MCP-TESTING-STRATEGY.md` - Testing approach
3. `.env.example` - MCP configuration template

### Proof-of-Concept
1. Mock weather MCP integration (tests)
2. Mock rules MCP integration (tests)
3. Langfuse trace showing MCP call metadata

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|:------:|-----------|
| MCP spec changes (unstable in 2026?) | 🔴 High | Pin version, test compatibility |
| Latency (MCP calls add overhead) | 🟠 Medium | Cache aggressively, set <500ms timeouts |
| Auth/credential management | 🟠 Medium | Use HashiCorp Vault / Doppler (later) |
| Vendor lock-in (weather API) | 🟡 Low | MCP abstraction = easy swap |

---

## 📝 Next Steps

1. **Code Review Phase 1 Plan** with team
2. **Start Phase 1.1**: MCP client layer (3h estimated)
3. **Create mock MCP server** for local testing
4. **Set up CI/CD** for MCP integration tests
5. **Weekly sync** to validate assumptions

---

## 📚 Reference Materials

- [MCP Official Spec](https://modelcontextprotocol.io/)
- [FastMCP Docs](https://docs.glama.ai/fastmcp/)
- [Your Existing Integration Roadmap](19-YONCA-AI-INTEGRATION-UNIVERSE.md)
- [Rules Engine Current State](../../src/yonca/rules/engine.py)

---

<div align="center">

**Phase 1: Foundation & Assessment**
✅ **AUDIT COMPLETE**

**Ready for Phase 1.1: MCP Client Layer**

</div>
