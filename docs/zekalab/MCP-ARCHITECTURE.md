# 🔌 MCP Architecture — Sovereign AI Stack

> **Version:** 2.0 | **Updated:** January 23, 2026
> **Purpose:** Single source of truth for MCP integration in ALEM

---

## 🎯 The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MCP ECOSYSTEM (2026 Sovereign Stack)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   🔄 LangGraph is BIDIRECTIONAL with MCP:                                   │
│      • As CLIENT → Calls external MCP tools (Weather, Postgres, Finance)    │
│      • As SERVER → Exposes ALEM as an MCP tool to other systems             │
│                                                                             │
│   This means:                                                               │
│   - Claude Desktop / GPT Agents can plug in ALEM's URL as a tool            │
│   - Master AI systems (DigiRella, Ministry) get ALEM "out of the box"       │
│   - No API integration needed — just MCP URL handshake                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Diagram

```
                                  ┌─────────────────────────────────┐
                                  │   EXTERNAL CONSUMERS            │
                                  │   (Claude Desktop, GPT, etc.)   │
                                  └───────────────┬─────────────────┘
                                                  │ MCP Protocol
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         LANGGRAPH SERVER (:2024)                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │ ✨ AUTO-EXPOSED AS MCP SERVER (Zero Code)                                    │ │
│  │    Your ALEM Agent becomes a callable MCP Tool for external systems          │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────────┐  │
│  │ SUPERVISOR NODE    │───▶│ CONTEXT LOADER     │───▶│ AGRONOMIST NODE        │  │
│  │ • Intent routing   │    │ • Load farm data   │    │ • Generate advice      │  │
│  │ • Language detect  │    │ • Call Weather MCP │    │ • Call ZekaLab MCP     │  │
│  └────────────────────┘    │ • Load scenarios   │    │ • Format response      │  │
│                            └─────────┬──────────┘    └───────────┬────────────┘  │
│                                      │                            │              │
│                        ┌─────────────┴─────────────┐   ┌──────────┴───────────┐  │
│                        │   MCP CLIENT CALLS        │   │  MCP CLIENT CALLS    │  │
│                        └─────────────┬─────────────┘   └──────────┬───────────┘  │
└───────────────────────────────────────┼────────────────────────────┼─────────────┘
                                        │                            │
        ┌───────────────────────────────┼────────────────────────────┼─────────────┐
        │                               ▼                            ▼             │
        │ ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐   │
        │ │ 🌤️ OpenWeather MCP  │  │ 🗄️ Postgres MCP     │  │ 🧠 ZekaLab MCP   │   │
        │ │ (External)          │  │ (Out-of-Box)        │  │ (Custom/FastMCP) │   │
        │ │ • get_forecast      │  │ • query_database    │  │ :7777            │   │
        │ │ • get_alerts        │  │ • get_schema        │  │ • irrigation     │   │
        │ │ • current_weather   │  │ • list_tables       │  │ • fertilization  │   │
        │ └─────────────────────┘  └─────────────────────┘  │ • pest_control   │   │
        │                                                    │ • subsidy        │   │
        │         M C P   S E R V E R S   L A Y E R         │ • harvest_date   │   │
        └───────────────────────────────────────────────────┴──────────────────────┘
```

---

## 📊 Component Roles

| Component | Role | Status | Code Location |
|:----------|:-----|:------:|:--------------|
| **LangGraph Server** | Graph Host + Auto MCP Server | ✅ Infra | `langgraph dev` |
| **ALEM (LangGraph)** | Brain — Orchestrates all nodes | ✅ Custom | `src/yonca/agent/graph.py` |
| **FastMCP (ZekaLab)** | Tool Factory — Custom agro rules | ✅ Custom | `src/yonca/mcp_server/main.py` |
| **Postgres MCP** | Data Bridge — Opens DB to AI | 🔮 Config Only | `@modelcontextprotocol/server-postgres` |
| **OpenWeather MCP** | External Data — Live forecasts | ✅ Handler | `src/yonca/mcp/handlers/weather_handler.py` |
| **Chainlit** | Window — Visualizes the graph | ✅ Custom | `demo-ui/app.py` |

---

## ✅ What's Implemented

### Phase 2: Weather MCP Integration ✅
| Component | Lines | Tests | Status |
|:----------|:-----:|:-----:|:------:|
| `WeatherMCPHandler` | 330 | 6/6 ✅ | Production |
| Context loader integration | — | — | ✅ |
| Graceful fallback | — | — | ✅ |

### Phase 3: ZekaLab Internal MCP ✅
| Component | Lines | Tests | Status |
|:----------|:-----:|:-----:|:------:|
| `mcp_server/main.py` | 793 | 24/24 ✅ | Production |
| `ZekaLabMCPHandler` | 570 | — | Production |
| Docker + deployment | — | — | ✅ |

**5 Tools Available:**
- `evaluate_irrigation_rules` → Should irrigate? How much? When?
- `evaluate_fertilization_rules` → NPK recommendations
- `evaluate_pest_control_rules` → Pest detection + action plans
- `calculate_subsidy` → Government subsidy calculations
- `predict_harvest_date` → GDD-based harvest prediction

### Phase 4: LangGraph Orchestration ✅
| Component | Lines | Tests | Status |
|:----------|:-----:|:-----:|:------:|
| Parallel MCP in context_loader | 460 | ✅ | Production |
| ZekaLab in agronomist node | 423 | 20/20 ✅ | Production |
| MCPTrace persistence | — | — | ✅ |
| Graceful degradation | — | — | ✅ |

**Key Features Implemented:**
- ✅ `asyncio.gather()` for parallel Weather + ZekaLab MCP calls
- ✅ 5-second global timeout with graceful fallback to synthetic data
- ✅ Intent-based ZekaLab tool routing (irrigation→evaluate_irrigation, etc.)
- ✅ MCPTrace recorded for every call (success/failure + duration_ms)
- ✅ `<MCP_QAYDALAR>` section injected into LLM prompt with rule summaries

---

## 🔮 What's Next

### Phase 5: Demo Enhancement ✅
| Feature | Status | Code Location |
|:--------|:------:|:--------------|
| MCP status badge in welcome | ✅ | `demo-ui/app.py:send_dashboard_welcome()` |
| Data flow visualization | ✅ | `demo-ui/app.py:_format_mcp_data_flow()` |
| Consent flow for external MCP | ✅ | `demo-ui/app.py:_show_data_consent_prompt()` |

**Key Features Implemented:**
- ✅ `get_all_mcp_status()` parallel health check for all MCP services
- ✅ MCP status line in welcome: "🔌 ✓ ZekaLab (12ms) • ✓ LangGraph (8ms)"
- ✅ `_format_mcp_data_flow()` shows which MCP servers contributed to each response
- ✅ Privacy-first consent prompt before calling external APIs (weather, etc.)
- ✅ `data_consent_given` flag passed to LangGraph agent state

### Phase 6: Postgres MCP (Planned)
- [ ] Deploy `@modelcontextprotocol/server-postgres` container
- [ ] Create "Data Navigator" node in LangGraph
- [ ] Bind Postgres MCP tools to node (no SQL writing)

---

## 🧩 Relationship Map

```
┌────────────────────────────────────────────────────────────────────┐
│                     HOW COMPONENTS RELATE                          │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   CHAINLIT ──────────▶ LANGGRAPH ──────────▶ MCP SERVERS           │
│   (Window)             (Brain)               (Tools/Data)          │
│                                                                    │
│   Shows UI ◀───────── Orchestrates ────────▶ Weather (real data)   │
│   Streams tokens        nodes                ZekaLab (rules)       │
│   Handles OAuth         Manages state        Postgres (DB access)  │
│                         Calls MCP tools                            │
│                                                                    │
│   ────────────────────────────────────────────────────────────     │
│                                                                    │
│   FASTMCP ────────────▶ ZekaLab MCP Server                         │
│   (Builder)             (Your custom tools)                        │
│                                                                    │
│   Creates MCP tools ──▶ evaluate_irrigation, calculate_subsidy...  │
│   with decorators       Runs on :7777                              │
│                                                                    │
│   ────────────────────────────────────────────────────────────     │
│                                                                    │
│   LANGGRAPH SERVER ──▶ Hosts ALEM + Exposes as MCP Tool            │
│   (Host/Adapter)        External systems can "use" your agent      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Commands

```powershell
# Start ZekaLab MCP Server
.venv\Scripts\python.exe -m uvicorn yonca.mcp_server.main:app --port 7777

# Test MCP Server
.venv\Scripts\python.exe -m pytest tests/unit/test_mcp_server/ -v

# Health Check
curl http://localhost:7777/health
```

---

## 📁 File Locations

```
src/yonca/
├── mcp/
│   ├── client.py              # MCP client (calls servers)
│   ├── config.py              # MCP config management
│   └── handlers/
│       ├── weather_handler.py # OpenWeather MCP handler
│       └── zekalab_handler.py # ZekaLab MCP handler
│
├── mcp_server/
│   ├── main.py                # ZekaLab MCP server (FastMCP)
│   ├── Dockerfile             # Container config
│   └── requirements.txt       # Server dependencies
│
└── agent/
    ├── graph.py               # LangGraph definition
    ├── state.py               # AgentState + MCPTrace
    └── nodes/
        ├── context_loader.py  # Calls Weather MCP
        └── agronomist.py      # Will call ZekaLab MCP (Phase 4)
```

---

## 🔐 Environment Variables

```env
# MCP General
MCP_ENABLED=true

# Weather MCP
WEATHER_MCP_ENABLED=true
WEATHER_MCP_URL=https://openweather.mcp.example.com
WEATHER_API_KEY=your_key

# ZekaLab MCP
ZEKALAB_MCP_ENABLED=true
ZEKALAB_MCP_URL=http://localhost:7777
ZEKALAB_TIMEOUT_MS=2000

# Postgres MCP (Phase 6)
POSTGRES_MCP_URL=postgresql://yonca:password@localhost:5433/yonca
```

---

## 📚 Deprecation Notice

The following docs are **superseded** by this file:
- `22-MCP-PHASE-2-WEATHER.md` → Implementation complete, code snippets removed
- `23-MCP-PHASE-3-INTERNAL-SERVER.md` → Implementation complete, code snippets removed
- `PHASE-2-COMPLETION-SUMMARY.md` → Merged into status table above
- `PHASE-3-COMPLETION-SUMMARY.md` → Merged into status table above
- `PHASE-4-HANDOFF.md` → Merged into "What's Next" section
- `QUICK-REFERENCE.md` → Merged into Quick Commands section

**Keep for reference:**
- `MCP-BLUEPRINT.md` → Developer prompt template (useful for new sessions)
