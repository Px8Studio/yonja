# 🔌 MCP Architecture — ALEM Sovereign AI Stack

> **Version:** 3.0 | **Updated:** January 2026
> **Status:** ✅ Production Ready (uses `langchain-mcp-adapters`)

---

## 🎯 Overview

ALEM integrates external tools via **Model Context Protocol (MCP)** using the official `langchain-mcp-adapters` library. LangGraph's `ToolNode` automatically binds and invokes MCP tools.

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
│                    │              MCP SERVERS LAYER        │            │    │
│                    │  ┌────────────────┐    ┌──────────────▼─────────┐  │    │
│                    │  │ OpenWeather    │    │    ZekaLab FastMCP     │  │    │
│                    │  │ (optional)     │    │    :7777               │  │    │
│                    │  │ • forecast     │    │    • irrigation_rules  │  │    │
│                    │  │ • alerts       │    │    • fertilizer_rules  │  │    │
│                    │  └────────────────┘    │    • pest_control      │  │    │
│                    │                        │    • subsidy_calc      │  │    │
│                    │                        │    • harvest_predict   │  │    │
│                    │                        └────────────────────────┘  │    │
│                    └────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Roles

| Component | Port | Responsibility |
|:----------|:----:|:---------------|
| **Chainlit** | 8501 | Chat UI, file uploads, MCP health display |
| **LangGraph Server** | 2024 | Graph execution, state persistence |
| **ToolNode** | — | Auto-binds & invokes MCP tools from LLM calls |
| **ZekaLab FastMCP** | 7777 | Custom agronomy rules engine |
| **MCP Adapters** | — | `langchain-mcp-adapters` for tool loading |

---

## 📁 Key Files

```
src/yonca/
├── mcp/
│   └── adapters.py              # MCP client config (langchain-mcp-adapters)
├── mcp_server/
│   └── zekalab_fastmcp.py       # FastMCP server (5 tools, 3 resources)
└── agent/
    ├── graph.py                 # StateGraph + make_graph() entrypoint
    └── state.py                 # AgentState + MCPTrace + file_paths

langgraph.json                   # Graph config + MCP env vars
```

---

## 🔧 ZekaLab MCP Tools

| Tool | Purpose | Key Args |
|:-----|:--------|:---------|
| `evaluate_irrigation_rules` | Should water? How much? | soil_moisture, temp, rainfall |
| `evaluate_fertilization_rules` | NPK recommendations | crop, soil_data, growth_stage |
| `evaluate_pest_control_rules` | Pest action plans | weather, pests_observed |
| `calculate_subsidy` | Government subsidy calc | crop, hectares, farmer_age |
| `predict_harvest_date` | GDD harvest prediction | planting_date, gdd_target |

---

## ⚙️ Configuration

### langgraph.json
```json
{
  "graphs": {
    "yonca_agent": "./src/yonca/agent/graph.py:make_graph"
  },
  "env": ".env"
}
```

### Environment Variables
```bash
ZEKALAB_MCP_ENABLED=true
ZEKALAB_MCP_URL=http://localhost:7777
ZEKALAB_MCP_SECRET=optional-auth-token
```

---

## 🚀 Quick Start

```powershell
# 1. Start ZekaLab MCP Server (VS Code task or manual)
.venv\Scripts\python.exe -m uvicorn yonca.mcp_server.zekalab_fastmcp:mcp --port 7777

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
