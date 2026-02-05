# 🔌 MCP Architecture — ALEM Sovereign AI Stack

> **Version:** 3.1 | **Updated:** February 2026
> **Status:** ✅ Production Ready (uses `langchain-mcp-adapters`)

---

## 🎯 Overview

ALEM integrates external tools via **Model Context Protocol (MCP)** using the official `langchain-mcp-adapters` library. LangGraph Server's `ToolNode` automatically binds and invokes MCP tools.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    ALEM ARCHITECTURE WITH MCP                                │
│                                                                               │
│   ┌─────────────┐     HTTP      ┌─────────────────────────────────────────┐  │
│   │  Chainlit   │──────────────▶│        LangGraph Server :2024           │  │
│   │  UI :8501   │◀──────────────│  ┌─────────────────────────────────┐    │  │
│   │             │   SSE Stream  │  │         StateGraph              │    │  │
│   │ • Chat UI   │               │  │  ┌───────────┐  ┌───────────┐   │    │  │
│   │ • Files     │               │  │  │supervisor │─▶│agronomist │   │    │  │
│   │ • Consent   │               │  │  └───────────┘  └─────┬─────┘   │    │  │
│   └─────────────┘               │  │                       │         │    │  │
│                                  │  │              ┌───────▼───────┐ │    │  │
│                                  │  │              │   ToolNode    │ │    │  │
│                                  │  │              │ (auto-invoke) │ │    │  │
│                                  │  │              └───────┬───────┘ │    │  │
│                                  │  └──────────────────────┼─────────┘    │  │
│                                  └─────────────────────────┼──────────────┘  │
│                                                            │                 │
│                    ┌───────────────────────────────────────┼────────────┐    │
│                    │              MCP SERVERS LAYER (mcp profile)       │    │
│                    │  ┌────────────────────┐    ┌──────────▼─────────┐  │    │
│                    │  │  Python Viz MCP    │    │  ZekaLab FastMCP   │  │    │
│                    │  │  :7778             │    │  :7777             │  │    │
│                    │  │  • generate_chart  │    │  • irrigation_rules│  │    │
│                    │  │  • create_graph    │    │  • fertilizer_rules│  │    │
│                    │  │  • data_viz        │    │  • pest_control    │  │    │
│                    │  └────────────────────┘    │  • subsidy_calc    │  │    │
│                    │                            │  • harvest_predict │  │    │
│                    │                            └────────────────────┘  │    │
│                    └────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Roles

| Component | Port | Profile | Responsibility |
|:----------|:----:|:--------|:---------------|
| **Chainlit** | 8501 | `app` | Chat UI, file uploads, MCP health display |
| **FastAPI** | 8000 | `app` | REST API gateway |
| **LangGraph Server** | 2024 | `core` | Graph execution, state persistence |
| **ToolNode** | — | — | Auto-binds & invokes MCP tools from LLM calls |
| **ZekaLab FastMCP** | 7777 | `mcp` | Agricultural rules engine (5 tools) |
| **Python Viz MCP** | 7778 | `mcp` | Chart/visualization generation |
| **MCP Adapters** | — | — | `langchain-mcp-adapters` for tool loading |

---

## 📁 Key Files

```
src/alim/
├── mcp/
│   └── adapters.py              # MCP client config (langchain-mcp-adapters)
├── mcp_server/
│   ├── zekalab_fastmcp.py       # Agricultural rules (5 tools)
│   └── Dockerfile               # ZekaLab MCP container
└── agent/
    ├── graph.py                 # StateGraph + make_graph() entrypoint
    └── state.py                 # AgentState + MCPTrace + file_paths

Dockerfile.mcp.viz               # Python Viz MCP container
deploy/langgraph/langgraph.json  # Graph config + MCP env vars
```

---

## 🔧 MCP Tools

### ZekaLab MCP (:7777) — Agricultural Rules

| Tool | Purpose | Key Args |
|:-----|:--------|:---------|
| `evaluate_irrigation_rules` | Should water? How much? | soil_moisture, temp, rainfall |
| `evaluate_fertilization_rules` | NPK recommendations | crop, soil_data, growth_stage |
| `evaluate_pest_control_rules` | Pest action plans | weather, pests_observed |
| `calculate_subsidy` | Government subsidy calc | crop, hectares, farmer_age |
| `predict_harvest_date` | GDD harvest prediction | planting_date, gdd_target |

### Python Viz MCP (:7778) — Chart Generation

| Tool | Purpose | Key Args |
|:-----|:--------|:---------|
| `generate_chart` | Create matplotlib charts | data, chart_type, title |
| `create_graph` | Generate network graphs | nodes, edges, layout |
| `data_viz` | General data visualization | dataset, viz_type |

---

## ⚙️ Configuration

### Docker Compose (mcp profile)
```bash
# Start MCP servers
docker compose --profile mcp up -d

# Health checks
curl http://localhost:7777/health  # ZekaLab
curl http://localhost:7778/health  # Python Viz
```

### Environment Variables
```bash
ZEKALAB_MCP_ENABLED=true
ZEKALAB_MCP_URL=http://localhost:7777

PYTHON_VIZ_MCP_ENABLED=true
PYTHON_VIZ_MCP_URL=http://localhost:7778
```

---

## 🚀 Quick Start

```powershell
# 1. Start ZekaLab MCP Server (VS Code task or manual)
.venv\Scripts\python.exe -m uvicorn ALİM.mcp_server.zekalab_fastmcp:mcp --port 7777

# 2. Start LangGraph Server
langgraph dev

# 3. Start Chainlit UI
chainlit run demo-ui/app.py

# 4. Verify MCP health
curl http://localhost:7777/health
```

---

## 🧪 Testing

```powershell
# ZekaLab MCP server tests
pytest tests/unit/test_mcp_server/test_zekalab_mcp.py -v
```

---

## 📊 MCP Trace (Observability)

Every MCP call is recorded in `AgentState.mcp_traces`:
```python
MCPTrace(
    server="zekalab",
    tool="evaluate_irrigation_rules",
    duration_ms=42.5,
    success=True
)
```

---

## 🔮 Roadmap

| Feature | Status |
|:--------|:------:|
| ZekaLab FastMCP Server | ✅ |
| langchain-mcp-adapters integration | ✅ |
| ToolNode auto-binding | ✅ |
| Chainlit file upload flow | ✅ |
| Postgres MCP (NL-to-SQL) | 🔮 |
| Docling MCP (documents) | 🔮 |
| ALEM exposed as MCP Server | 🔮 |
