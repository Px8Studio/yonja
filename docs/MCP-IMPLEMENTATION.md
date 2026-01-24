# MCP (Model Context Protocol) Implementation Guide

## Overview

The Yonca AI project now has full MCP support enabled in the Chainlit UI. This allows the chat interface to connect to external tools and data sources through the Model Context Protocol standard.

### Chainlit Native MCP UI vs. Backend-Managed Connectors
- **Chainlit native MCP UI**: ships with a "Connect an MCP" modal (stdin/stdio/SSE/HTTP) so end-users can add their own servers. Use this if you intentionally want user-provided MCP endpoints.
- **Backend-managed connectors (current approach)**: we preload servers via `yonca.mcp.adapters` and surface status/tools in chat. This keeps credentials and routing server-side and avoids user setup friction.
- **LangGraph MCP adapters**: we rely on `langchain_mcp_adapters` to populate tools; this stays compatible with Chainlit's UI because tools are pulled server-side and rendered in chat.

Recommendation: keep backend-managed connectors as default; optionally expose the native MCP UI toggle later for power users, guarded by feature flags and per-mode access (fast = off, thinking = off, agent = full connectors).

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Chainlit UI Layer                       │
│  - Chat interface (demo-ui/app.py)                         │
│  - MCP status display                                       │
│  - Command handlers (/mcp, /mcp-status)                    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              MCP Connector (services/mcp_connector.py)      │
│  - Profile-based tool filtering                            │
│  - Health monitoring                                        │
│  - Tool discovery                                           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│         MCP Adapters (yonca/mcp/adapters.py)               │
│  - LangChain MCP adapter integration                       │
│  - Multi-server client management                          │
│  - Tool loading and caching                                │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            MCP Client (yonca/mcp/client.py)                │
│  - HTTP client for MCP servers                             │
│  - Error handling and retries                              │
│  - Latency tracking                                         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    MCP Servers                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ZekaLab MCP (port 7777)                            │  │
│  │  - Internal rules engine                             │  │
│  │  - Irrigation evaluation                             │  │
│  │  - Fertilization rules                               │  │
│  │  - Pest control logic                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  OpenWeather MCP (future)                           │  │
│  │  - Weather forecasts                                 │  │
│  │  - Historical data                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Other MCP Servers (future)                         │  │
│  │  - EKTIS (land registry)                            │  │
│  │  - CBAR (financial data)                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### 1. Chainlit MCP Settings

File: `demo-ui/.chainlit/config.toml`

```toml
[features.mcp]
enabled = true  # ✅ Already enabled

[features.mcp.sse]
enabled = true  # Server-Sent Events transport

[features.mcp.streamable-http]
enabled = true  # HTTP streaming transport

[features.mcp.stdio]
enabled = true  # Standard I/O transport
allowed_executables = [ "npx", "uvx" ]  # For local MCP servers
```

### 2. MCP Server Configuration

File: `.env` (environment variables)

```bash
# ZekaLab Internal MCP Server
ZEKALAB_MCP_ENABLED=true
ZEKALAB_MCP_URL=http://localhost:7777
ZEKALAB_MCP_SECRET=<optional-auth-token>
ZEKALAB_TIMEOUT_MS=2000

# OpenWeather MCP Server (future)
OPENWEATHER_MCP_ENABLED=false
OPENWEATHER_MCP_URL=http://localhost:7778
OPENWEATHER_API_KEY=<your-api-key>
```

## Profile-Based Access Control (Agent Modes)

Only the `agent` mode can use MCP connectors. Fast and Thinking are tool-less.

| Profile   | Allowed Servers              | Use Case                                  |
|-----------|------------------------------|-------------------------------------------|
| `fast`    | _None_ (connectors disabled) | Quick text answers, zero external calls   |
| `thinking`| _None_ (connectors disabled) | Deep reasoning, still offline/tools-off   |
| `agent`   | ZekaLab + OpenWeather        | Full autonomy with rules + weather tools  |

Configuration: `yonca/mcp/adapters.py` → `PROFILE_MCP_SERVERS`

## Usage

### For Users (Chat UI)

**Check MCP Connection Status:**
```
Type in chat: /mcp
```

**Output Example:**
```markdown
## 🔌 MCP Connections

**Profile:** agent

### Servers
- 🟢 **zekalab**: online
- 🟢 **openweather**: online

### Available Tools (12)
- `evaluate_irrigation_rules`: Evaluates irrigation timing based on soil and weather...
- `get_fertilization_plan`: Generates fertilization schedule for specific crops...
- `get_weather_forecast`: Fetches 7-day weather forecast for location...
...and 9 more tools
```

### For Developers

**1. Initialize MCP in Chat Session:**

The MCP connector is automatically initialized in `@cl.on_chat_start`:

```python
from services.mcp_connector import get_mcp_status, format_mcp_status

# Get status for current profile
mcp_status = await get_mcp_status(profile="agent")

# Store in session
cl.user_session.set("mcp_status", mcp_status)
cl.user_session.set("mcp_enabled", True)

# Display to user
formatted = format_mcp_status(mcp_status)
await cl.Message(content=formatted).send()
```

**2. Invoke MCP Tool:**

```python
from services.mcp_connector import invoke_mcp_tool

result = await invoke_mcp_tool(
   server="zekalab",
   tool_name="evaluate_irrigation_rules",
   args={
      "soil_moisture": 35,
      "crop_type": "apple",
      "region": "Ganja"
   },
   profile="agent"
)

if result["success"]:
    print(result["result"])
else:
    print(f"Error: {result['error']}")
```

**3. Get Tools for LangGraph:**

```python
from services.mcp_connector import get_tools_for_session

# Get tools filtered by current user's profile
tools = await get_tools_for_session()

# Use with LangGraph ToolNode
from langgraph.prebuilt import ToolNode
tool_node = ToolNode(tools)
```

## Running MCP Servers

### ZekaLab MCP Server

**Start Server:**
```bash
# Using VS Code task
Run task: 🧠 ZekaLab MCP Start

# Or manually
python -m uvicorn yonca.mcp_server.main:app --port 7777 --reload
```

**Test Server:**
```bash
# Health check
curl http://localhost:7777/health

# List tools
curl http://localhost:7777/tools
```

**Run Tests:**
```bash
# Run task: 🧠 ZekaLab MCP Tests
# Or manually
pytest tests/unit/test_mcp_server/test_zekalab_mcp.py -v
```

### OpenWeather MCP Server (Future)

Not yet implemented. Will follow similar pattern.

## Testing

### Unit Tests

**MCP Connector:**
```bash
pytest tests/unit/test_mcp_connector.py -v
```

**MCP Handler:**
```bash
pytest tests/unit/test_mcp_handlers/test_zekalab_handler.py -v
```

### Integration Tests

**Start All Services:**
```bash
# Run task: 🚀 Start All
# This starts:
# - Docker (Postgres, Redis, Ollama)
# - ZekaLab MCP Server
# - FastAPI Backend
# - Chainlit UI
```

**Manual Test Flow:**
1. Open chat UI: http://localhost:8501
2. Login with Google OAuth (if enabled)
3. Type `/mcp` to check connections
4. Ask question that triggers MCP tool: "What's the irrigation schedule for my apple orchard?" (requires `agent` mode)
5. Check logs for MCP calls

**Expected Logs:**
```
mcp_initialized | profile=agent | servers=['zekalab', 'openweather'] | tool_count=12
mcp_tool_invoked | server=zekalab | tool=evaluate_irrigation_rules | profile=agent
```

## Troubleshooting

### MCP Server Not Starting

**Symptom:** `/mcp` shows 🔴 offline

**Solutions:**
1. Check if server is running:
   ```bash
   curl http://localhost:7777/health
   ```
2. Check environment variables:
   ```bash
   echo $ZEKALAB_MCP_ENABLED
   echo $ZEKALAB_MCP_URL
   ```
3. Check logs:
   ```bash
   # Find server process
   ps aux | grep "uvicorn.*mcp_server"
   ```

### MCP Tools Not Showing

**Symptom:** `/mcp` shows 0 tools

**Solutions:**
1. Check profile configuration in `yonca/mcp/adapters.py`
2. Verify server has tools registered:
   ```bash
   curl http://localhost:7777/tools
   ```
3. Check for errors in `mcp_tools_loaded` logs

### Permission Errors

**Symptom:** "Server 'openweather' not allowed for profile 'general'"

**Solution:** This is expected behavior. Only `agent` mode has connectors. Switch the chat profile to `agent`.

## Future Enhancements

### Planned Features

1. **MCP Discovery UI**
   - Visual picker for available tools
   - Tool documentation viewer
   - Interactive tool testing

2. **External MCP Servers**
   - OpenWeather API integration
   - EKTIS land registry
   - CBAR financial data

3. **Advanced Security**
   - API key management UI
   - Per-user server access control
   - Rate limiting per server

4. **Observability**
   - MCP call tracing in Langfuse
   - Performance metrics dashboard
   - Error rate monitoring

### Contributing

To add a new MCP server:

1. **Define server config** in `yonca/mcp/config.py`
2. **Add to adapters** in `yonca/mcp/adapters.py`
3. **Update profile access** in `PROFILE_MCP_SERVERS`
4. **Add environment variables** to `.env.example`
5. **Update documentation** in this file

## Related Documentation

- [Chainlit MCP Documentation](https://docs.chainlit.io/advanced-features/mcp)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [LangChain MCP Adapters](https://github.com/rectalogic/langchain-mcp-adapters)

---

**Status:** ✅ Implemented (January 23, 2026)
**Version:** 1.0.0
**Maintainer:** ZekaLab Team
