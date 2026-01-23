# 🌤️ Phase 2: Public MCP Servers Integration (Weather)

**Duration:** Week 2 (6-8 hours)
**Status:** Ready to Start (After Phase 1.1 ✅)
**Blocking:** Nothing (Phase 3 can start in parallel)

---

## 🎯 Phase 2 Objective

Replace synthetic weather data with **real OpenWeather MCP integration**, making ALEM responsive to actual farm conditions while maintaining full observability and user consent.

---

## 📋 Phase 2 Tasks Breakdown

### Task 2.1: OpenWeather MCP Client Integration (2 hours)

**What:** Create a handler that calls OpenWeather MCP server
**Where:** `src/yonca/mcp/handlers/weather_handler.py`
**Code:**

```python
# src/yonca/mcp/handlers/weather_handler.py
"""Weather MCP handler for OpenWeather integration."""

from typing import Any, Optional
from datetime import datetime
import structlog

from yonca.agent.state import WeatherContext
from yonca.mcp.client import MCPClient, MCPToolCall, MCPCallResult
from yonca.mcp.config import get_server_config

logger = structlog.get_logger(__name__)


class WeatherMCPHandler:
    """Handles calls to Weather MCP servers."""

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        crop_type: str = "cotton",
        days: int = 7,
    ) -> Optional[WeatherContext]:
        """Fetch weather forecast from MCP server.

        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            crop_type: Crop type for agronomically relevant data
            days: Days of forecast

        Returns:
            WeatherContext or None if call fails
        """
        client = await self._get_client()

        if not client or not client.enabled:
            logger.warning("weather_mcp_disabled")
            return None

        # Build tool call
        call = MCPToolCall(
            server="openweather",
            tool="get_forecast",
            args={
                "latitude": latitude,
                "longitude": longitude,
                "crop_type": crop_type,
                "days": days,
            },
        )

        result = await client.call_tool(call)

        if not result.success:
            logger.error(
                "weather_forecast_failed",
                error=result.error,
                latency_ms=result.latency_ms,
            )
            return None

        # Parse response into WeatherContext
        try:
            data = result.data
            weather = WeatherContext(
                temperature_c=float(data.get("temperature_c", 25.0)),
                humidity_percent=float(data.get("humidity_percent", 50.0)),
                precipitation_mm=float(data.get("precipitation_mm", 0.0)),
                wind_speed_kmh=float(data.get("wind_speed_kmh", 10.0)),
                forecast_summary=str(data.get("forecast_summary", "No data")),
                last_updated=datetime.utcnow(),
            )

            logger.info(
                "weather_forecast_success",
                temp_c=weather.temperature_c,
                latency_ms=result.latency_ms,
                server="openweather",
            )

            return weather

        except (KeyError, ValueError, TypeError) as e:
            logger.error("weather_parsing_error", error=str(e))
            return None

    async def get_alerts(
        self,
        latitude: float,
        longitude: float,
        crop_type: str,
    ) -> list[dict[str, Any]]:
        """Get weather alerts (frost, drought, pest season).

        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            crop_type: Crop type for crop-specific alerts

        Returns:
            List of alerts with severity levels
        """
        client = await self._get_client()

        if not client or not client.enabled:
            return []

        call = MCPToolCall(
            server="openweather",
            tool="get_alerts",
            args={
                "latitude": latitude,
                "longitude": longitude,
                "crop_type": crop_type,
            },
        )

        result = await client.call_tool(call)

        if not result.success:
            logger.warning("weather_alerts_failed", error=result.error)
            return []

        try:
            alerts = result.data.get("alerts", [])
            logger.info("weather_alerts_fetched", count=len(alerts))
            return alerts
        except (KeyError, TypeError):
            return []

    async def _get_client(self) -> Optional[MCPClient]:
        """Get or create Weather MCP client."""
        try:
            from yonca.mcp.client import get_mcp_client

            client = await get_mcp_client("openweather")
            return client
        except Exception as e:
            logger.error("weather_client_error", error=str(e))
            return None
```

**Tests to Add:** `tests/unit/test_weather_handler.py`

```python
@pytest.mark.asyncio
async def test_get_forecast_success():
    """Test successful weather forecast retrieval."""
    handler = WeatherMCPHandler()

    # Mock the client
    with patch("yonca.mcp.handlers.weather_handler.get_mcp_client") as mock_get:
        mock_client = AsyncMock()
        mock_response = MCPCallResult(
            success=True,
            data={
                "temperature_c": 28.5,
                "humidity_percent": 65,
                "precipitation_mm": 2.0,
                "wind_speed_kmh": 15,
                "forecast_summary": "Partly cloudy, ideal for irrigation",
            },
            server="openweather",
            tool_name="get_forecast",
        )
        mock_client.call_tool.return_value = mock_response
        mock_get.return_value = mock_client

        weather = await handler.get_forecast(40.4, 49.9, "cotton")

        assert weather is not None
        assert weather.temperature_c == 28.5
        assert "irrigation" in weather.forecast_summary
```

---

### Task 2.2: Refactor context_loader_node (1 hour)

**What:** Update context_loader to use WeatherMCPHandler instead of synthetic data
**Where:** `src/yonca/agent/nodes/context_loader.py` (modify lines 106-125)

**Current Code:**
```python
# Load weather context (synthetic for now)
if "weather" in requires_context:
    # TODO: Integrate with real weather API
    farm_context = updates.get("farm_context") or state.get("farm_context")

    if farm_context:
        weather = await _get_synthetic_weather(farm_context.region)
        updates["weather"] = weather
```

**New Code:**
```python
# Load weather context (from OpenWeather MCP)
if "weather" in requires_context:
    from yonca.mcp.handlers.weather_handler import WeatherMCPHandler

    farm_context = updates.get("farm_context") or state.get("farm_context")

    if farm_context and farm_context.location:
        handler = WeatherMCPHandler()
        weather = await handler.get_forecast(
            latitude=farm_context.location.get("latitude", 40.4),
            longitude=farm_context.location.get("longitude", 49.9),
            crop_type=farm_context.active_crops[0]["crop"] if farm_context.active_crops else "cotton",
            days=7,
        )

        # Fallback to synthetic if MCP fails
        if weather is None:
            weather = await _get_synthetic_weather(farm_context.region)

        updates["weather"] = weather

        # Fetch weather alerts
        alerts = await handler.get_alerts(
            latitude=farm_context.location.get("latitude", 40.4),
            longitude=farm_context.location.get("longitude", 49.9),
            crop_type=farm_context.active_crops[0]["crop"] if farm_context.active_crops else "cotton",
        )

        if alerts:
            updates["alerts"] = alerts
```

---

### Task 2.3: Update AgentState for MCP Metadata (1 hour)

**What:** Extend AgentState to track MCP call sources
**Where:** `src/yonca/agent/state.py` (add to AgentState class)

```python
# Add to AgentState
@dataclass
class AgentState:
    # ... existing fields ...

    # MCP Integration (Phase 2+)
    mcp_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="MCP tool calls made during this request"
    )
    mcp_sources: dict[str, str] = Field(
        default_factory=dict,
        description="Data source attribution (e.g., 'weather': 'openweather-mcp')"
    )
    data_consent_given: bool = Field(
        default=False,
        description="User has given consent for external API access"
    )
```

---

### Task 2.4: Chainlit MCP Indicator UI (2 hours)

**What:** Show "🔌 Connected to OpenWeather" badge in Chainlit
**Where:** `demo-ui/app.py` (new function + integration)

**Code:**

```python
# demo-ui/app.py

async def show_mcp_status():
    """Display MCP server connection status."""
    from yonca.mcp.config import validate_mcp_config

    status = validate_mcp_config()

    status_text = "**🔌 Data Sources:**\n"

    if status.get("openweather") == "✅ enabled":
        status_text += "- 🌤️ Real-time weather from OpenWeather\n"
    else:
        status_text += "- 🌤️ Weather (Synthetic - no API configured)\n"

    if status.get("zekalab") == "✅ enabled":
        status_text += "- 🧠 Agriculture rules from ZekaLab\n"
    else:
        status_text += "- 🧠 Agriculture rules (Local - development)\n"

    if status.get("ektis") == "✅ enabled":
        status_text += "- 🚜 Farm data from EKTİS\n"

    if status.get("cbar") == "✅ enabled":
        status_text += "- 💰 Financial data from CBAR Banking\n"

    await cl.Message(content=status_text, author="System Status").send()


@cl.on_chat_start
async def start():
    """Initialize chat session."""
    # ... existing code ...

    # Show MCP status
    await show_mcp_status()


# In message handler, add source attribution
async def on_message(message: cl.Message):
    # ... existing code ...

    # After response generated, show data sources
    if hasattr(state, 'mcp_sources') and state.mcp_sources:
        sources_text = "**📊 Data Sources Used:**\n"
        for key, source in state.mcp_sources.items():
            sources_text += f"- {key}: {source}\n"

        await cl.Message(content=sources_text, author="Attribution").send()
```

---

### Task 2.5: Consent Flow for API Access (1.5 hours)

**What:** Ask user permission before accessing external APIs
**Where:** `demo-ui/app.py` (add consent dialog)

```python
@cl.on_chat_start
async def start():
    """Initialize chat session with consent flow."""
    # ... existing code ...

    # Check if consent needed
    from yonca.mcp.config import mcp_settings

    if mcp_settings.openweather_mcp_enabled or mcp_settings.cbar_mcp_enabled:
        # Show consent dialog
        actions = [
            cl.Action(
                name="consent_accept",
                label="✅ I accept using external data services",
            ),
            cl.Action(
                name="consent_decline",
                label="❌ Use only local data",
            ),
        ]

        msg = cl.Message(
            content="""
**🔐 Data Privacy Notice**

ALEM can access external services to provide better recommendations:
- 🌤️ **OpenWeather API** - Real-time hyperlocal forecasts
- 💰 **CBAR Banking** - Your account balance (with consent)
- 🚜 **EKTİS** - Your farm profile

Do you authorize this access?
            """,
            actions=actions,
        )
        await msg.send()


@cl.action_callback("consent_accept")
async def handle_consent_accept(action: cl.Action):
    """User accepts data access."""
    cl.user_session.set("data_consent_given", True)
    await cl.Message(
        content="✅ Thanks! You'll now get real-time weather updates.",
        author="System",
    ).send()


@cl.action_callback("consent_decline")
async def handle_consent_decline(action: cl.Action):
    """User declines data access."""
    cl.user_session.set("data_consent_given", False)
    await cl.Message(
        content="✅ No problem. Using local data only.",
        author="System",
    ).send()
```

---

## 📊 Phase 2 Success Metrics

By end of Phase 2, you should have:

- ✅ `src/yonca/mcp/handlers/weather_handler.py` (fully functional)
- ✅ `context_loader_node` calling WeatherMCPHandler instead of synthetic
- ✅ AgentState extended with `mcp_calls`, `mcp_sources`, `data_consent_given`
- ✅ Chainlit UI shows "🔌 Connected to OpenWeather" badge
- ✅ Consent flow working (accept/decline buttons)
- ✅ Data source attribution displayed after each response
- ✅ `pytest tests/unit/test_weather_handler.py -v` passes
- ✅ End-to-end test: "Pomidorları nə vaxt suvarmalıyam?" returns real weather

---

## 🧪 Phase 2 Integration Test

**Run this to verify Phase 2 completeness:**

```bash
#!/bin/bash
# tests/integration/test_phase_2_weather.sh

echo "Testing Phase 2: Weather MCP Integration"
echo "=========================================="

# 1. Check files exist
echo "[1] Checking files..."
test -f "src/yonca/mcp/handlers/weather_handler.py" || exit 1
echo "✅ weather_handler.py exists"

# 2. Run unit tests
echo "[2] Running unit tests..."
pytest tests/unit/test_weather_handler.py -v || exit 1
echo "✅ All tests pass"

# 3. Check config
echo "[3] Checking MCP config..."
python -c "from yonca.mcp.config import mcp_settings; print(f'OpenWeather enabled: {mcp_settings.openweather_mcp_enabled}')" || exit 1
echo "✅ Config validation passed"

# 4. Verify state extensions
echo "[4] Checking AgentState extensions..."
python -c "from yonca.agent.state import AgentState; assert hasattr(AgentState, 'mcp_calls')" || exit 1
echo "✅ AgentState has mcp_calls"

echo ""
echo "✅ Phase 2 Ready for Deployment!"
```

---

## 🚀 Next: Phase 3 - Internal ZekaLab MCP Server

Once Phase 2 ✅, you'll:
1. Build the ZekaLab MCP server (exposes Cotton Rules Engine)
2. Deploy it as a Docker container
3. Have ALEM call it for all agronomy recommendations

---

<div align="center">

**Phase 2: Weather Integration**
✅ Ready to Implement

[Next: Phase 3 →](22-MCP-PHASE-3-INTERNAL-SERVER.md)

</div>
