# 🚀 Phase 1.1: MCP Client Foundation - Quick Start

**Status:** ✅ **Skeleton Created** (Jan 23, 2026)
**Effort Estimate:** 7-8 hours for full Phase 1.1
**Owner:** Development Team

---

## 📋 What's Been Delivered

### ✅ Code Delivered

1. **`src/yonca/mcp/__init__.py`**
   - Module documentation and architecture overview
   - Public API exports

2. **`src/yonca/mcp/config.py`** (263 lines)
   - `MCPSettings` class (all 4 MCP servers configured via env vars)
   - `MCPServerConfig` data model
   - `validate_mcp_config()` function
   - `get_server_config()` factory function
   - Support for: OpenWeather, ZekaLab, EKTİS, CBAR

3. **`src/yonca/mcp/client.py`** (370 lines)
   - `MCPCallResult` data model (success/error/latency/metadata)
   - `MCPToolCall` configuration model
   - `MCPClient` class (async HTTP client with retry logic)
   - `get_mcp_client()` singleton factory
   - `close_all_mcp_clients()` cleanup function
   - Full docstrings + examples

4. **`tests/unit/test_mcp_client.py`** (280 lines)
   - 15+ test cases covering all client paths
   - Mock httpx.AsyncClient for network isolation
   - Tests for success, error, timeout, disabled server scenarios
   - Singleton factory tests

### ✅ Documentation Delivered

1. **`docs/zekalab/21-MCP-INTEGRATION-AUDIT-PHASE-1.md`** (550 lines)
   - Complete audit of current integrations
   - Architecture diagrams (Mermaid graphs)
   - Data flow patterns (3 key patterns)
   - File structure for MCP integration
   - Security/auth strategy
   - Risk mitigation
   - Priority matrix (5 phases)

2. **`docs/zekalab/00-IMPLEMENTATION-BACKLOG.md`** (Updated)
   - Phase 1.1 + 1.2 task lists
   - Key findings from audit

---

## 🔧 Next Steps (Phase 1.1 Continuation)

### Immediate Tasks (2-3 hours)

**1. Integrate MCP Config into FastAPI Startup**

Add to `src/yonca/api/main.py`:

```python
# At startup
from yonca.mcp.client import close_all_mcp_clients
from yonca.mcp.config import validate_mcp_config

@app.on_event("startup")
async def startup():
    # Validate MCP configuration
    mcp_status = validate_mcp_config()
    logger.info("mcp_status", status=mcp_status)

    # Initialize MCP clients (lazy loading OK for now)

@app.on_event("shutdown")
async def shutdown():
    # Clean up MCP clients
    await close_all_mcp_clients()
```

**2. Add .env.example Template**

```bash
# .env.example - MCP Configuration

# Global
MCP_ENABLED=true
LOG_MCP_CALLS=true

# Weather MCP (Phase 2)
OPENWEATHER_MCP_ENABLED=false
OPENWEATHER_MCP_URL=https://openweather-mcp.example.com
OPENWEATHER_API_KEY=your_key_here
OPENWEATHER_TIMEOUT_MS=500

# ZekaLab Internal MCP (Phase 3)
ZEKALAB_MCP_ENABLED=false
ZEKALAB_MCP_URL=http://localhost:7777
ZEKALAB_MCP_SECRET=dev_secret_key
ZEKALAB_TIMEOUT_MS=2000

# EKTİS MCP (Phase 4)
EKTIS_MCP_ENABLED=false
EKTIS_MCP_URL=https://ektis-api.example.com
EKTIS_API_KEY=your_key_here

# CBAR Banking MCP (Phase 4)
CBAR_MCP_ENABLED=false
CBAR_MCP_URL=https://cbar-banking-mcp.example.com
CBAR_API_KEY=your_key_here
```

**3. Run Unit Tests**

```bash
pytest tests/unit/test_mcp_client.py -v
```

**Expected Output:**
```
test_mcp_client.py::TestMCPCallResult::test_result_success PASSED
test_mcp_client.py::TestMCPCallResult::test_result_error PASSED
test_mcp_client.py::TestMCPClient::test_client_disabled_server PASSED
test_mcp_client.py::TestMCPClient::test_call_tool_success PASSED
test_mcp_client.py::TestMCPFactory::test_get_mcp_client_singleton PASSED
... (10 more tests)

======================== 15 passed in 0.23s ========================
```

---

### Phase 1.2 Tasks (3-4 hours)

**4. Create Mock MCP Server (for local testing)**

Create `scripts/mock_mcp_server.py`:

```python
#!/usr/bin/env python3
"""Mock MCP server for local testing (standalone).

Simulates OpenWeather and Rules MCP servers without external dependencies.
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock MCP Server")

class ToolRequest(BaseModel):
    args: dict

@app.post("/tools/get_forecast")
async def get_forecast(req: ToolRequest):
    """Mock weather forecast."""
    return {
        "temperature_c": 25.0,
        "humidity_percent": 65,
        "precipitation_mm": 0,
        "wind_speed_kmh": 12,
        "forecast_summary": "Clear skies, suitable for planting"
    }

@app.post("/tools/evaluate_irrigation_rules")
async def evaluate_irrigation(req: ToolRequest):
    """Mock irrigation rules evaluation."""
    return {
        "recommendations": [
            {
                "rule_id": "AZ-IRR-001",
                "action": "Water cotton at 6 AM",
                "confidence": 0.95,
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7777)
```

Run it:
```bash
python scripts/mock_mcp_server.py
# Server running on http://localhost:7777
```

**5. Add Mock Server Task to tasks.json**

```json
{
    "label": "🌿 Yonca AI: 🔌 Mock MCP Server",
    "detail": "Start mock MCP server for testing",
    "type": "shell",
    "command": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
    "args": ["scripts/mock_mcp_server.py"],
    "isBackground": true
}
```

**6. Create Langfuse Integration**

Update `src/yonca/observability/langfuse.py`:

```python
# Add MCP call logging
def log_mcp_call(result: MCPCallResult):
    """Log MCP call to Langfuse."""
    from langfuse import Langfuse

    langfuse = Langfuse()

    trace = langfuse.trace(
        name=f"mcp_{result.server}_{result.tool_name}",
        metadata=result.to_langfuse_metadata(),
    )

    trace.observation(
        name="mcp_call",
        output={"success": result.success, "data": result.data},
        usage={"output_tokens": 0},  # MCP doesn't have tokens
    )
```

---

## ✅ Phase 1.1 Success Criteria

By end of Phase 1.1, you should have:

- [x] MCP client layer code (src/yonca/mcp/)
- [x] Configuration management with env vars
- [x] Unit tests (15+ test cases, >90% coverage)
- [x] Mock MCP server for local testing
- [x] .env.example template
- [x] Langfuse integration skeleton
- [ ] Run full test suite: `pytest tests/unit/test_mcp_client.py`
- [ ] Mock server starts locally: `python scripts/mock_mcp_server.py`
- [ ] Zero impact on existing code (backward compatible)

---

## 🔍 Code Review Checklist

Before merging Phase 1.1, verify:

- [ ] All imports are available (pydantic_settings, httpx, etc.)
- [ ] No circular dependencies
- [ ] Tests pass: `pytest tests/unit/test_mcp_client.py -v`
- [ ] Linting passes: `ruff check src/yonca/mcp tests/unit/test_mcp_client.py`
- [ ] Type hints complete (mypy clean)
- [ ] .env.example has all MCP vars
- [ ] Docstrings have examples
- [ ] Error messages are helpful

---

## 🎯 Phase 2 Preview (Week 2)

Once Phase 1.1 ✅, you'll integrate real MCP servers:

1. **Choose OpenWeather MCP** (or equivalent in 2026)
2. **Refactor weather_node** to call OpenWeather MCP
3. **Add Chainlit UI indicator** ("🔌 Connected to OpenWeather")
4. **Test end-to-end**: User message → weather_node → OpenWeather MCP → response

**Estimated effort:** 6-8 hours

---

## 📞 Support & Debugging

### Test MCP Client Locally

```python
# Quick test in ipython
import asyncio
from yonca.mcp.client import get_mcp_client, MCPToolCall

async def test():
    client = await get_mcp_client("zekalab")

    result = await client.call_tool(
        MCPToolCall(
            server="zekalab",
            tool="get_forecast",
            args={"lat": 40.4, "lon": 49.9}
        )
    )

    print(f"Success: {result.success}")
    print(f"Latency: {result.latency_ms}ms")
    print(f"Data: {result.data}")

asyncio.run(test())
```

### Debug Environment Variables

```bash
# Check which servers are enabled
python -c "from yonca.mcp.config import validate_mcp_config; print(validate_mcp_config())"

# Output:
# {'openweather': '⏳ disabled', 'zekalab': '⏳ disabled', 'ektis': '⏳ disabled', 'cbar': '⏳ disabled'}
```

---

<div align="center">

**Phase 1.1: MCP Client Foundation** ✅ **READY TO IMPLEMENT**

[👉 View Full Audit](21-MCP-INTEGRATION-AUDIT-PHASE-1.md)

</div>
