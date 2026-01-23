# 🔄 Phase 4: LangGraph Orchestrator Refactor (Multi-MCP Workflows)

**Duration:** Week 4 (10-13 hours)
**Status:** Depends on Phase 1.1 ✅ + Phase 3 ✅
**Criticality:** 🟡 **HIGH** - Multiplies agent intelligence

---

## 🎯 Phase 4 Objective

Refactor LangGraph to orchestrate **multiple MCP servers in parallel** while maintaining:
- ✅ Backwards compatibility (synthetic fallback)
- ✅ Response time SLA (<2 seconds per node)
- ✅ Full audit trail (all MCP calls logged to Langfuse)
- ✅ Graceful degradation (one MCP fails ≠ whole agent fails)

---

## 🏗️ Architecture: Multi-MCP Orchestration

```
┌──────────────────────────────────────────────────┐
│  User Query: "My cotton needs irrigation?"        │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Supervisor Node       │ Route to agronomist
    └────────────┬───────────┘
                 │
                 ▼
    ┌──────────────────────────────────────────┐
    │  Context Loader Node                     │
    │  Fetch: User | Farm | Weather            │
    │                                          │
    │  │ Phase 2: Call OpenWeather MCP        │
    │  │ Phase 3: Call ZekaLab MCP (health)   │
    │  └─► Parallel execution                 │
    └────────┬──────────────────────────────────┘
             │
             ├─ user_context: {name, language}
             ├─ farm_context: {crop, area, soil}
             ├─ weather: {temp, rainfall, humidity}
             │   ↑ MCP: OpenWeather
             ├─ server_health: {zekalab, availability}
             │   ↑ MCP: ZekaLab (ping)
             └─ system_capability: MCP connected or fallback?

                 ▼
    ┌──────────────────────────────────────────┐
    │  Agronomist Node                         │
    │  Decision: "Does cotton need water?"      │
    │                                          │
    │  • Call ZekaLab MCP:                     │
    │    evaluate_irrigation_rules(...)        │
    │    ↓ Returns: {should_irrigate, confidence}
    │                                          │
    │  • Falls back to local engine if fails   │
    │  • Logs to Langfuse: MCP call trace      │
    └────────┬──────────────────────────────────┘
             │ {decision, mcp_data_source}
             │
             ▼
    ┌──────────────────────────────────────────┐
    │  Validator Node                          │
    │  Verify: Farmer has consent to use MCP?  │
    │                                          │
    │  Check: AgentState.data_consent_given    │
    │  - If Yes: include MCP attribution       │
    │  - If No: strip MCP sources (fallback)   │
    └────────┬──────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │  Response to Farmer                      │
    │  "Water your cotton: 25mm today"          │
    │  "Data: OpenWeather API + ZekaLab Rules" │
    │  "Confidence: 94%"                       │
    └──────────────────────────────────────────┘
```

---

## 📋 Phase 4 Tasks

### Task 4.1: Extend AgentState (1 hour)

**Current State:** See `src/yonca/agent/state.py`

**Changes to Make:**

```python
# src/yonca/agent/state.py

from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime

class MCPTrace(BaseModel):
    """Single MCP call record."""
    server: str  # "openweather", "zekalab", etc.
    tool: str    # "get_forecast", "evaluate_irrigation_rules"
    input_args: Dict  # What we sent
    output: Dict  # What we got
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """Extended to include MCP orchestration metadata."""

    # === EXISTING FIELDS ===
    user_id: str
    farm_id: str
    query: str
    conversation_history: List[Dict]  # Existing

    # === NEW FIELDS: MCP ORCHESTRATION ===

    # Track all MCP calls during this conversation turn
    mcp_traces: List[MCPTrace] = Field(default_factory=list)

    # Did user consent to using external APIs?
    data_consent_given: bool = False

    # Which servers are currently healthy?
    mcp_server_health: Dict[str, bool] = Field(
        default_factory=lambda: {
            "openweather": True,
            "zekalab": True,
        }
    )

    # Session-level MCP configuration
    mcp_config: Dict = Field(
        default_factory=lambda: {
            "use_mcp": True,
            "fallback_to_synthetic": True,
            "max_mcp_calls_per_turn": 10,
            "mcp_timeout_seconds": 5,
            "log_to_langfuse": True,
        }
    )

    # Existing fields
    response: Optional[str] = None
    error: Optional[str] = None
```

---

### Task 4.2: Refactor Context Loader Node (2 hours)

**File:** `src/yonca/agent/nodes/context_loader.py`

**Changes:**

```python
# src/yonca/agent/nodes/context_loader.py

import asyncio
from datetime import datetime
from structlog import get_logger
from yonca.agent.state import AgentState, MCPTrace
from yonca.mcp.client import MCPClient, MCPToolCall, get_mcp_client
from yonca.rules.engine import RulesEngine

logger = get_logger(__name__)


async def context_loader_node(state: AgentState) -> dict:
    """Load context from all sources: user, farm, weather (MCP).

    NEW BEHAVIOR:
    - Phase 2: Call OpenWeather MCP in parallel
    - Phase 3: Check ZekaLab server health
    - Fallback: Use synthetic data if MCP fails
    - Log: All MCP calls to mcp_traces

    Returns:
        Updated AgentState with context loaded
    """

    logger.info("context_loader_start", user_id=state.user_id, farm_id=state.farm_id)

    # Get user and farm context (existing)
    user_context = {
        "id": state.user_id,
        "language": "az",  # TODO: detect from user profile
        "timezone": "Asia/Baku",
    }

    farm_context = {
        "id": state.farm_id,
        "crop": "cotton",  # TODO: fetch from DB
        "area_hectares": 10,
        "soil_type": "loamy",
    }

    # ============================================================
    # NEW: Parallel MCP calls with fallback
    # ============================================================

    # Initialize MCP traces list
    mcp_traces = []

    # Try to fetch weather and server health in parallel
    weather_data = None
    server_health = {}

    if state.mcp_config.get("use_mcp", True):
        try:
            # Parallel calls: weather + server checks
            weather_coro = _get_weather_via_mcp(
                state.farm_id,
                farm_context,
                mcp_traces
            )
            health_coro = _check_mcp_server_health(
                mcp_traces
            )

            weather_data, server_health = await asyncio.gather(
                weather_coro,
                health_coro,
                return_exceptions=True,
            )

            # Handle exceptions
            if isinstance(weather_data, Exception):
                logger.warning(
                    "weather_mcp_failed",
                    error=str(weather_data)
                )
                weather_data = None

            if isinstance(server_health, Exception):
                logger.warning(
                    "server_health_check_failed",
                    error=str(server_health)
                )
                server_health = {}

        except Exception as e:
            logger.error("mcp_parallel_call_failed", error=str(e))
            weather_data = None
            server_health = {}

    # Fallback to synthetic if MCP failed
    if not weather_data and state.mcp_config.get("fallback_to_synthetic", True):
        logger.info("using_synthetic_weather_fallback")
        weather_data = _get_synthetic_weather(farm_context)

    # ============================================================
    # Return updated state
    # ============================================================

    return {
        "user_context": user_context,
        "farm_context": farm_context,
        "weather": weather_data or {},
        "mcp_traces": mcp_traces,
        "mcp_server_health": server_health,
    }


async def _get_weather_via_mcp(
    farm_id: str,
    farm_context: dict,
    mcp_traces: list,
) -> dict:
    """Call OpenWeather MCP for real forecast data."""

    start_time = datetime.utcnow()

    try:
        # Get MCP client (singleton)
        client = get_mcp_client("openweather")

        # Prepare tool call
        call = MCPToolCall(
            server="openweather",
            tool="get_forecast",
            args={
                "farm_id": farm_id,
                "days_ahead": 7,
                "include_alerts": True,
            }
        )

        logger.info("openweather_mcp_call_start", farm_id=farm_id)

        # Execute MCP call
        result = await client.call_tool(call)

        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Record trace
        mcp_traces.append(
            MCPTrace(
                server="openweather",
                tool="get_forecast",
                input_args=call.args,
                output=result.data if result.success else {},
                duration_ms=duration_ms,
                success=result.success,
                error_message=result.error_message,
            )
        )

        if not result.success:
            logger.warning(
                "openweather_mcp_failed",
                error=result.error_message,
                duration_ms=duration_ms,
            )
            return None

        logger.info(
            "openweather_mcp_success",
            duration_ms=duration_ms,
            farm_id=farm_id,
        )

        return result.data

    except Exception as e:
        logger.error("openweather_mcp_exception", error=str(e))
        return None


async def _check_mcp_server_health(mcp_traces: list) -> dict:
    """Ping all MCP servers to check health."""

    servers = ["openweather", "zekalab"]
    health_status = {}

    for server_name in servers:
        start_time = datetime.utcnow()

        try:
            client = get_mcp_client(server_name)

            # Call health_check tool (available on all servers)
            call = MCPToolCall(
                server=server_name,
                tool="health_check",
                args={},
            )

            result = await asyncio.wait_for(
                client.call_tool(call),
                timeout=2,  # 2 second timeout per server
            )

            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            mcp_traces.append(
                MCPTrace(
                    server=server_name,
                    tool="health_check",
                    input_args={},
                    output=result.data if result.success else {},
                    duration_ms=duration_ms,
                    success=result.success,
                )
            )

            health_status[server_name] = result.success

            logger.info(
                f"{server_name}_health_check",
                success=result.success,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            logger.warning(f"{server_name}_health_check_timeout")
            health_status[server_name] = False

        except Exception as e:
            logger.warning(f"{server_name}_health_check_failed", error=str(e))
            health_status[server_name] = False

    return health_status


def _get_synthetic_weather(farm_context: dict) -> dict:
    """Fallback to synthetic weather (existing function)."""
    # TODO: import from existing code
    return {
        "temperature_c": 28.5,
        "humidity_percent": 65,
        "rainfall_mm_7d": 15,
        "wind_speed_kmh": 12,
        "source": "synthetic",
    }
```

---

### Task 4.3: Refactor Agronomist Node (2 hours)

**File:** `src/yonca/agent/nodes/agronomist.py`

**Changes:**

```python
# src/yonca/agent/nodes/agronomist.py

import asyncio
from datetime import datetime
from structlog import get_logger
from yonca.agent.state import AgentState, MCPTrace
from yonca.mcp.client import MCPClient, MCPToolCall, get_mcp_client
from yonca.rules.engine import RulesEngine

logger = get_logger(__name__)


async def agronomist_node(state: AgentState) -> dict:
    """Make agricultural decisions using ZekaLab MCP rules.

    NEW BEHAVIOR:
    - Phase 3: Call ZekaLab MCP for irrigation, fertilization, pest control
    - Log: All MCP calls to mcp_traces
    - Fallback: Use local RulesEngine if MCP fails

    Returns:
        Agronomic recommendation with MCP attribution
    """

    logger.info("agronomist_start", farm_id=state.farm_id)

    farm_context = state.farm_context
    weather = state.weather

    # Prepare decision context
    decision_context = {
        "farm_id": state.farm_id,
        "crop_type": farm_context.get("crop", "cotton"),
        "soil_type": farm_context.get("soil_type", "loamy"),
        "temperature_c": weather.get("temperature_c", 28),
        "humidity_percent": weather.get("humidity_percent", 65),
        "rainfall_mm_7d": weather.get("rainfall_mm_7d", 15),
    }

    # ============================================================
    # NEW: Call ZekaLab MCP with fallback
    # ============================================================

    mcp_traces = list(state.mcp_traces)  # Copy existing traces

    recommendation = None
    mcp_source = None

    if state.mcp_config.get("use_mcp") and state.mcp_server_health.get("zekalab"):
        try:
            # Call ZekaLab evaluate_irrigation_rules
            recommendation, trace = await _call_zekalab_mcp(
                decision_context
            )

            mcp_traces.append(trace)
            mcp_source = "zekalab-mcp"

            logger.info("zekalab_mcp_success", trace=trace)

        except Exception as e:
            logger.warning("zekalab_mcp_failed", error=str(e))
            recommendation = None

    # Fallback to local RulesEngine
    if not recommendation:
        logger.info("using_local_rules_engine_fallback")

        engine = RulesEngine()
        rules_matches = engine.evaluate_all(decision_context)

        if rules_matches:
            best_match = max(rules_matches, key=lambda x: x.get("confidence", 0))
            recommendation = {
                "action": best_match.get("recommended_action"),
                "confidence": best_match.get("confidence"),
                "reasoning": best_match.get("recommendation_az"),
            }
            mcp_source = "local-rules-engine"

    # ============================================================
    # Return recommendation with attribution
    # ============================================================

    return {
        "recommendation": recommendation or {},
        "mcp_source": mcp_source,
        "mcp_traces": mcp_traces,
    }


async def _call_zekalab_mcp(decision_context: dict) -> tuple:
    """Call ZekaLab MCP evaluate_irrigation_rules tool."""

    start_time = datetime.utcnow()

    try:
        client = get_mcp_client("zekalab")

        call = MCPToolCall(
            server="zekalab",
            tool="evaluate_irrigation_rules",
            args={
                "farm_id": decision_context["farm_id"],
                "crop_type": decision_context["crop_type"],
                "soil_type": decision_context["soil_type"],
                "current_soil_moisture_percent": 45,  # TODO: from sensors
                "temperature_c": decision_context["temperature_c"],
                "rainfall_mm_last_7_days": decision_context["rainfall_mm_7d"],
            }
        )

        result = await asyncio.wait_for(
            client.call_tool(call),
            timeout=3,
        )

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace = MCPTrace(
            server="zekalab",
            tool="evaluate_irrigation_rules",
            input_args=call.args,
            output=result.data if result.success else {},
            duration_ms=duration_ms,
            success=result.success,
            error_message=result.error_message,
        )

        if not result.success:
            raise Exception(f"MCP call failed: {result.error_message}")

        return result.data, trace

    except asyncio.TimeoutError:
        raise Exception("ZekaLab MCP timeout")
    except Exception as e:
        raise Exception(f"ZekaLab MCP error: {str(e)}")
```

---

### Task 4.4: Update Validator Node (1.5 hours)

**File:** `src/yonca/agent/nodes/validator.py`

**Changes:**

```python
# src/yonca/agent/nodes/validator.py

async def validator_node(state: AgentState) -> dict:
    """Validate recommendation and enforce consent policy.

    NEW: Check if farmer consented to MCP data before including it.
    """

    recommendation = state.recommendation
    mcp_source = state.mcp_source
    data_consent_given = state.data_consent_given

    # If recommendation came from MCP but user didn't consent, strip attribution
    if mcp_source and mcp_source.startswith("mcp") and not data_consent_given:
        logger.warning("stripping_mcp_source_no_consent", source=mcp_source)
        # Return recommendation without MCP attribution
        return {
            "validated_recommendation": recommendation,
            "attribution": "Local recommendation (consult agronomist)",
            "user_action_needed": "REQUEST_DATA_CONSENT",
        }

    # If user consented, include full attribution
    if data_consent_given and mcp_source:
        return {
            "validated_recommendation": recommendation,
            "attribution": f"Data source: {mcp_source}. Weather: OpenWeather API. Rules: ZekaLab Agriculture Engine.",
            "data_sources": [
                "OpenWeather API",
                "ZekaLab Rules Engine",
            ],
        }

    # Local recommendations
    return {
        "validated_recommendation": recommendation,
        "attribution": "Local recommendation",
    }
```

---

### Task 4.5: Integration Tests (2 hours)

**Create:** `tests/integration/test_multi_mcp_workflow.py`

```python
"""Test multi-MCP orchestration in LangGraph."""

import pytest
from yonca.agent.graph import create_agent_graph
from yonca.agent.state import AgentState, MCPTrace
from datetime import datetime


@pytest.mark.asyncio
async def test_context_loader_calls_weather_mcp():
    """Test context_loader node calls OpenWeather MCP."""

    # Mock MCP client responses
    state = AgentState(
        user_id="farmer_123",
        farm_id="farm_456",
        query="Does my cotton need water?",
        data_consent_given=True,
        mcp_config={"use_mcp": True, "fallback_to_synthetic": True},
    )

    graph = create_agent_graph()

    # Run context_loader node
    result = await graph.invoke({
        "state": state,
        "node": "context_loader",
    })

    # Verify MCP was called
    assert len(result["mcp_traces"]) > 0
    weather_traces = [t for t in result["mcp_traces"] if t.server == "openweather"]
    assert len(weather_traces) > 0
    assert weather_traces[0].success


@pytest.mark.asyncio
async def test_agronomist_calls_zekalab_mcp():
    """Test agronomist node calls ZekaLab MCP for rules."""

    state = AgentState(
        user_id="farmer_123",
        farm_id="farm_456",
        query="What should I do?",
        data_consent_given=True,
        mcp_server_health={"zekalab": True},
        mcp_config={"use_mcp": True},
    )

    graph = create_agent_graph()

    # Run agronomist node
    result = await graph.invoke({
        "state": state,
        "node": "agronomist",
    })

    # Verify MCP was called
    zekalab_traces = [
        t for t in result["mcp_traces"]
        if t.server == "zekalab"
    ]
    assert len(zekalab_traces) > 0


@pytest.mark.asyncio
async def test_fallback_when_mcp_fails():
    """Test system uses local rules when MCP fails."""

    state = AgentState(
        user_id="farmer_123",
        farm_id="farm_456",
        query="What should I do?",
        mcp_config={
            "use_mcp": True,
            "fallback_to_synthetic": True,
        },
        mcp_server_health={"zekalab": False},  # MCP unavailable
    )

    graph = create_agent_graph()
    result = await graph.invoke({"state": state})

    # Should still get recommendation from local engine
    assert result["recommendation"]
    assert result["mcp_source"] == "local-rules-engine"


@pytest.mark.asyncio
async def test_consent_required_for_mcp_attribution():
    """Test MCP attribution stripped if consent not given."""

    state = AgentState(
        user_id="farmer_123",
        farm_id="farm_456",
        query="What should I do?",
        data_consent_given=False,  # NO CONSENT
        mcp_config={"use_mcp": True},
    )

    graph = create_agent_graph()
    result = await graph.invoke({"state": state})

    # Should not include MCP attribution
    assert "User action needed: REQUEST_DATA_CONSENT" in result
```

---

### Task 4.6: Langfuse Integration (1.5 hours)

**Update:** `src/yonca/agent/graph.py`

```python
# Add to each node:

from langfuse.decorators import observe

@observe(name="context_loader_node")
async def context_loader_node(state: AgentState) -> dict:
    """Context loader with Langfuse tracing."""
    # Existing code...

    # Log MCP traces to Langfuse
    for trace in mcp_traces:
        trace_data = trace.dict()
        langfuse.trace(
            input=trace_data["input_args"],
            output=trace_data["output"],
            metadata={
                "mcp_server": trace_data["server"],
                "mcp_tool": trace_data["tool"],
                "duration_ms": trace_data["duration_ms"],
                "success": trace_data["success"],
            },
        )

    return {...}
```

---

## ✅ Phase 4 Deliverables

By end of Phase 4:

- ✅ AgentState extended with MCP orchestration metadata
- ✅ Context loader calls OpenWeather + ZekaLab in parallel
- ✅ Agronomist node uses ZekaLab MCP with fallback
- ✅ Validator enforces consent requirements
- ✅ All MCP calls logged to Langfuse with traces
- ✅ Response time <2s per node (measured)
- ✅ Graceful degradation when MCP fails
- ✅ Full integration tests pass
- ✅ No breaking changes to existing agent

---

<div align="center">

**Phase 4: LangGraph Refactor**
🔄 Ready to Build

[Next: Phase 5 →](24-MCP-PHASE-5-DEMO-ENHANCEMENT.md)

</div>
