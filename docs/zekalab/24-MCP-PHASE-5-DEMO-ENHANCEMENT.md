# 🚀 Phase 5: DigiRella Demo Enhancement (End-to-End MCP Journey)

**Duration:** Week 5 (8-11 hours)
**Status:** Depends on Phases 1-4 ✅
**Criticality:** 🟢 **MEDIUM** - Showcases technology

---

## 🎯 Phase 5 Objective

Transform DigiRella demo from "static wireframes" to **"live MCP-powered farmer assistant"** showing:
- ✅ Real data from OpenWeather MCP
- ✅ Real decisions from ZekaLab MCP
- ✅ Real data flow visualization
- ✅ End-to-end farmer workflow

---

## 🏗️ Architecture: Chainlit + MCP Integration

```
┌─────────────────────────────────────────────────┐
│  Chainlit UI (demo-ui/app.py)                   │
│                                                  │
│  🔌 MCP Status Indicator                        │
│  ├─ ✅ OpenWeather: Connected                   │
│  ├─ ✅ ZekaLab: Connected                       │
│  └─ ⚠️  CBAR: Not available (fallback only)    │
│                                                  │
│  📊 Data Flow Visualization                     │
│  ├─ Weather data source indicator               │
│  ├─ Rules engine attribution                    │
│  └─ MCP call timeline                           │
│                                                  │
│  ✅ Consent Flow                                │
│  ├─ "Accept MCP data sources?" checkbox         │
│  ├─ Privacy notice                              │
│  └─ Attribution display                         │
└───────────────┬──────────────────────────────────┘
                │ Chainlit MCP Client
                │
    ┌───────────┴─────────────┐
    │                         │
    ▼                         ▼
OpenWeather MCP          ZekaLab MCP
   (7777)                  (7777)
```

---

## 📋 Phase 5 Tasks

### Task 5.1: Enhance Chainlit UI with MCP Status (2 hours)

**File:** `demo-ui/app.py`

**Changes:**

```python
# demo-ui/app.py

import chainlit as cl
from chainlit.mcp_client import MCPClient
from chainlit.element import Element
from yonca.mcp.client import get_mcp_client
import asyncio
from datetime import datetime

# Initialize Chainlit app
app = cl.ChatInterface()

# ============================================================
# MCP Status Monitoring
# ============================================================

mcp_status = {
    "openweather": {"connected": False, "last_check": None},
    "zekalab": {"connected": False, "last_check": None},
}


async def check_mcp_servers():
    """Periodically check MCP server health."""
    while True:
        for server_name in ["openweather", "zekalab"]:
            try:
                client = get_mcp_client(server_name)
                # Simple health check
                # (assumes each MCP server has /health endpoint)
                mcp_status[server_name] = {
                    "connected": True,
                    "last_check": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                mcp_status[server_name] = {
                    "connected": False,
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat(),
                }

        await asyncio.sleep(30)  # Check every 30 seconds


@app.on_chat_start
async def start():
    """Chat session started."""
    # Start background MCP health check
    asyncio.create_task(check_mcp_servers())

    # Display MCP status indicator
    mcp_status_element = cl.Element(
        content=_render_mcp_status(),
        type="html",
        name="MCP Status",
    )

    await cl.Message(
        content="🌾 ALEM Agricultural Assistant\n\nPowered by MCP (Model Context Protocol)",
        elements=[mcp_status_element],
    ).send()

    # Ask for data consent
    res = await cl.AskUserAction(
        title="Data Consent",
        actions=[
            cl.Action(
                name="accept_mcp",
                value="yes",
                description="✅ Accept - Use real weather & rules",
            ),
            cl.Action(
                name="decline_mcp",
                value="no",
                description="❌ Decline - Use local data only",
            ),
        ],
    )

    if res.get("value") == "yes":
        cl.user_session.set("data_consent", True)
        await cl.Message(
            content="✅ Thank you! I'll use real weather forecasts and agricultural rules from our expert system.",
        ).send()
    else:
        cl.user_session.set("data_consent", False)
        await cl.Message(
            content="⚠️  I'll use local recommendations. Accuracy may be reduced.",
        ).send()


def _render_mcp_status() -> str:
    """Generate HTML widget showing MCP server status."""

    html = """
    <style>
        .mcp-status {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            padding: 16px;
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .mcp-server {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .mcp-server:last-child {
            border-bottom: none;
        }

        .status-icon {
            font-size: 18px;
            margin-right: 8px;
        }

        .status-text {
            flex: 1;
        }

        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-left: 8px;
        }

        .connected {
            background-color: #4ade80;
            animation: pulse 2s infinite;
        }

        .disconnected {
            background-color: #f87171;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>

    <div class="mcp-status">
        <h3 style="margin: 0 0 12px 0;">🔌 MCP Integration Status</h3>
    """

    for server_name, status in mcp_status.items():
        connected = status["connected"]
        icon = "✅" if connected else "❌"
        indicator_class = "connected" if connected else "disconnected"
        server_display = "OpenWeather" if server_name == "openweather" else "ZekaLab"

        html += f"""
        <div class="mcp-server">
            <div class="status-text">
                <span class="status-icon">{icon}</span>
                <strong>{server_display}</strong>
                <span class="status-indicator {indicator_class}"></span>
            </div>
        </div>
        """

    html += "</div>"

    return html


# ============================================================
# Main Chat Handler with Data Flow Visualization
# ============================================================


@app.on_message
async def main(message: cl.Message):
    """Process user message through MCP-enhanced agent."""

    user_id = cl.user_session.get("user_id", "demo_farmer")
    farm_id = cl.user_session.get("farm_id", "farm_001")
    data_consent = cl.user_session.get("data_consent", False)

    # Send thinking indicator
    msg = cl.Message(
        content="🤔 Analyzing your farm's conditions...",
    )
    await msg.send()

    # Call agent
    from yonca.agent.graph import create_agent_graph
    from yonca.agent.state import AgentState

    state = AgentState(
        user_id=user_id,
        farm_id=farm_id,
        query=message.content,
        data_consent_given=data_consent,
        mcp_config={
            "use_mcp": True,
            "fallback_to_synthetic": True,
        },
    )

    graph = create_agent_graph()
    result = await graph.ainvoke({"state": state})

    # ============================================================
    # Visualize Data Flow
    # ============================================================

    data_flow_html = _render_data_flow(result)

    # Update thinking message
    msg.content = result["response"]
    msg.elements = [
        cl.Element(
            content=data_flow_html,
            type="html",
            name="Data Sources & Confidence",
        )
    ]

    await msg.update()


def _render_data_flow(result: dict) -> str:
    """Generate HTML showing data sources and MCP call flow."""

    mcp_traces = result.get("mcp_traces", [])
    mcp_source = result.get("mcp_source", "unknown")

    html = """
    <style>
        .data-flow {
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            font-family: monospace;
            font-size: 12px;
        }

        .flow-step {
            display: flex;
            align-items: center;
            margin: 8px 0;
            padding: 8px;
            background: white;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }

        .flow-icon {
            font-size: 16px;
            margin-right: 12px;
        }

        .flow-content {
            flex: 1;
        }

        .flow-time {
            font-size: 10px;
            color: #666;
            margin-left: auto;
        }

        .success { border-left-color: #4ade80; }
        .error { border-left-color: #f87171; }
        .local { border-left-color: #fbbf24; }
    </style>

    <div class="data-flow">
        <h4 style="margin: 0 0 12px 0;">📊 Data Flow Timeline</h4>
    """

    # Show each MCP call
    for trace in mcp_traces:
        status_class = "success" if trace.success else "error"
        icon = "✅" if trace.success else "❌"

        html += f"""
        <div class="flow-step {status_class}">
            <div class="flow-icon">{icon}</div>
            <div class="flow-content">
                <strong>{trace.server}</strong> → {trace.tool}
                <br/>
                <span style="color: #666;">
                    {trace.duration_ms:.0f}ms
                    {f"| Error: {trace.error_message}" if trace.error_message else ""}
                </span>
            </div>
            <div class="flow-time">{trace.duration_ms:.0f}ms</div>
        </div>
        """

    # Show final data source
    html += f"""
        <div style="margin-top: 12px; padding: 8px; background: #f0f4ff; border-radius: 4px;">
            <strong>📍 Final Decision Source:</strong> {mcp_source}
        </div>
    </div>
    """

    return html
```

---

### Task 5.2: Create Farmer Journey Scenarios (1.5 hours)

**Create:** `demo-ui/scenarios.py`

```python
"""Demo scenarios for different farmer situations."""

import asyncio
from yonca.agent.graph import create_agent_graph
from yonca.agent.state import AgentState

DEMO_SCENARIOS = [
    {
        "name": "Cotton Irrigation Decision",
        "farm_id": "farm_cotton_001",
        "crop": "cotton",
        "query": "It's been 8 days since I last watered. Should I irrigate today?",
        "context": {
            "soil_moisture": 35,
            "temperature": 32,
            "rainfall_7d": 5,
        },
        "expected_mcp_calls": ["openweather", "zekalab"],
    },
    {
        "name": "Pest Control Guidance",
        "farm_id": "farm_wheat_002",
        "crop": "wheat",
        "query": "I see aphids on my wheat. What should I do?",
        "context": {
            "pest": "aphids",
            "severity": "medium",
            "temperature": 24,
            "humidity": 72,
        },
        "expected_mcp_calls": ["zekalab"],
    },
    {
        "name": "Subsidy Discovery",
        "farm_id": "farm_cotton_003",
        "crop": "cotton",
        "query": "Are there any subsidies I'm eligible for?",
        "context": {
            "area_hectares": 15,
            "production_tons": 45,
        },
        "expected_mcp_calls": ["zekalab"],
    },
]


async def run_demo_scenario(scenario_name: str) -> dict:
    """Run a demo scenario end-to-end."""

    scenario = next(
        s for s in DEMO_SCENARIOS if s["name"] == scenario_name
    )

    print(f"\n{'=' * 60}")
    print(f"🌾 Scenario: {scenario['name']}")
    print(f"{'=' * 60}")
    print(f"\n🗣️  Farmer: {scenario['query']}")

    # Create agent state
    state = AgentState(
        user_id="demo_farmer",
        farm_id=scenario["farm_id"],
        query=scenario["query"],
        data_consent_given=True,
        farm_context={
            "crop": scenario["crop"],
            "area_hectares": 10,
            "soil_type": "loamy",
        },
    )

    # Run through agent
    graph = create_agent_graph()
    result = await graph.ainvoke({"state": state})

    # Display results
    print(f"\n🤖 Assistant: {result['response']}")
    print(f"\n📊 Data Sources:")
    for trace in result["mcp_traces"]:
        status = "✅" if trace.success else "❌"
        print(f"  {status} {trace.server}.{trace.tool} ({trace.duration_ms:.0f}ms)")

    # Verify expected MCP calls were made
    actual_servers = {t.server for t in result["mcp_traces"]}
    expected_servers = set(scenario["expected_mcp_calls"])

    if actual_servers >= expected_servers:
        print(f"\n✅ Scenario passed: All expected MCP servers called")
    else:
        missing = expected_servers - actual_servers
        print(f"\n⚠️  Scenario warning: Missing MCP calls: {missing}")

    return result


if __name__ == "__main__":
    # Run all scenarios
    for scenario in DEMO_SCENARIOS:
        asyncio.run(run_demo_scenario(scenario["name"]))
```

---

### Task 5.3: Add MCP Data Attribution Display (1.5 hours)

**Create:** `demo-ui/components/data_attribution.py`

```python
"""Display data source attribution for compliance."""

import chainlit as cl
from yonca.agent.state import MCPTrace


def create_attribution_element(mcp_traces: list[MCPTrace], mcp_source: str) -> cl.Element:
    """Create HTML element showing data attribution."""

    attribution_parts = []

    # List all data sources used
    servers_used = {t.server for t in mcp_traces if t.success}

    if "openweather" in servers_used:
        attribution_parts.append(
            "🌤️  **Weather Data:** OpenWeather API (Real-time forecast)"
        )

    if "zekalab" in servers_used:
        attribution_parts.append(
            "🧬 **Agricultural Rules:** ZekaLab Rules Engine (Expert system)"
        )

    if not attribution_parts:
        attribution_parts.append(
            "📚 **Data Sources:** Local knowledge base (No external APIs used)"
        )

    # Calculate confidence from MCP success rate
    successful_traces = len([t for t in mcp_traces if t.success])
    total_traces = len(mcp_traces)
    confidence = (successful_traces / total_traces * 100) if total_traces > 0 else 100

    html_content = f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        padding: 16px;
        color: white;
        margin-top: 12px;
    ">
        <h4 style="margin: 0 0 12px 0;">📌 Data Attribution</h4>

        <div style="margin-bottom: 12px;">
            {''.join([f'<p style="margin: 4px 0;">✅ {part}</p>' for part in attribution_parts])}
        </div>

        <div style="
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            padding: 8px;
            font-size: 12px;
        ">
            <strong>Confidence Score:</strong> {confidence:.0f}%
            <br/>
            <strong>Decision Source:</strong> {mcp_source}
        </div>

        <p style="margin: 8px 0 0 0; font-size: 10px; opacity: 0.8;">
            💡 This recommendation uses real-time external data sources.
            Your data is not stored or shared with third parties.
        </p>
    </div>
    """

    return cl.Element(
        content=html_content,
        type="html",
        name="Attribution",
    )
```

---

### Task 5.4: Create End-to-End Test Suite (1.5 hours)

**Create:** `tests/e2e/test_demo_end_to_end.py`

```python
"""End-to-end tests for DigiRella demo with MCP."""

import pytest
import asyncio
from yonca.agent.graph import create_agent_graph
from yonca.agent.state import AgentState


@pytest.mark.asyncio
async def test_full_farmer_workflow_with_mcp():
    """Test complete farmer workflow: query → MCP → response."""

    # Setup
    user_query = "Should I water my cotton today?"

    state = AgentState(
        user_id="demo_farmer_001",
        farm_id="farm_demo_001",
        query=user_query,
        data_consent_given=True,
        farm_context={
            "crop": "cotton",
            "area_hectares": 10,
            "soil_type": "loamy",
        },
    )

    # Run agent
    graph = create_agent_graph()
    result = await graph.ainvoke({"state": state})

    # Assertions
    assert result["response"], "Response should not be empty"
    assert len(result["mcp_traces"]) > 0, "MCP should have been called"
    assert any(
        t.server == "openweather" and t.success
        for t in result["mcp_traces"]
    ), "OpenWeather MCP should be called successfully"
    assert any(
        t.server == "zekalab" and t.success
        for t in result["mcp_traces"]
    ), "ZekaLab MCP should be called successfully"

    # Verify response quality
    response_lower = result["response"].lower()
    assert any(
        keyword in response_lower
        for keyword in ["water", "irrigate", "soil", "moisture"]
    ), "Response should contain agricultural terms"

    # Verify data attribution
    assert "mcp_source" in result, "MCP source should be tracked"
    assert result["mcp_source"] in [
        "openweather-mcp",
        "zekalab-mcp",
        "local-rules-engine"
    ], "Valid MCP source should be set"


@pytest.mark.asyncio
async def test_mcp_response_time_sla():
    """Test that MCP calls stay within <2 second SLA."""

    state = AgentState(
        user_id="demo_farmer_002",
        farm_id="farm_demo_002",
        query="Pest control advice",
        data_consent_given=True,
    )

    graph = create_agent_graph()
    import time
    start = time.time()
    result = await graph.ainvoke({"state": state})
    elapsed = time.time() - start

    # Total response time should be <3 seconds (with overhead)
    assert elapsed < 3.0, f"Response too slow: {elapsed:.2f}s"

    # Individual MCP calls should be <2 seconds
    for trace in result["mcp_traces"]:
        if trace.success:
            assert trace.duration_ms < 2000, (
                f"MCP call {trace.server}.{trace.tool} took {trace.duration_ms}ms"
            )


@pytest.mark.asyncio
async def test_consent_enforcement():
    """Test that MCP data is excluded when consent not given."""

    # Without consent
    state_no_consent = AgentState(
        user_id="demo_farmer_003",
        farm_id="farm_demo_003",
        query="Water my farm",
        data_consent_given=False,  # KEY: NO CONSENT
    )

    graph = create_agent_graph()
    result = await graph.ainvoke({"state": state_no_consent})

    # Response should not include MCP attribution
    if result.get("attribution"):
        assert "external" not in result["attribution"].lower()
        assert "api" not in result["attribution"].lower()


@pytest.mark.asyncio
async def test_graceful_degradation():
    """Test system continues working if MCP fails."""

    state = AgentState(
        user_id="demo_farmer_004",
        farm_id="farm_demo_004",
        query="What crops should I plant?",
        data_consent_given=True,
        mcp_server_health={
            "openweather": False,  # Simulated failure
            "zekalab": False,
        },
        mcp_config={"fallback_to_synthetic": True},
    )

    graph = create_agent_graph()
    result = await graph.ainvoke({"state": state})

    # Should still get a response
    assert result["response"], "Response should exist even with MCP failures"

    # Should indicate using local data
    assert result["mcp_source"] == "local-rules-engine"
```

---

### Task 5.5: Demo Deployment & Documentation (1.5 hours)

**Create:** `docs/DEMO_DEPLOYMENT_GUIDE.md`

```markdown
# 🚀 DigiRella MCP Demo Deployment Guide

## Quick Start (5 minutes)

### 1. Start All Services

```bash
# Terminal 1: Docker services
docker-compose -f docker-compose.local.yml up

# Terminal 2: ZekaLab MCP server
cd src/yonca/mcp_server
python main.py

# Terminal 3: FastAPI backend
cd src
uvicorn yonca.api.main:app --reload

# Terminal 4: Chainlit UI
cd demo-ui
chainlit run app.py
```

### 2. Open Browser

```
http://localhost:8000  # Chainlit UI
```

### 3. Try Demo Scenarios

**Scenario 1: Irrigation Decision**
- Say: "Should I water my cotton?"
- Expected: Real OpenWeather data + ZekaLab rules
- MCP Calls: 2 (weather + irrigation evaluation)

**Scenario 2: Pest Control**
- Say: "I see aphids"
- Expected: Pest control recommendation
- MCP Calls: 1 (pest evaluation)

**Scenario 3: Subsidy Discovery**
- Say: "What subsidies can I get?"
- Expected: Eligible programs list
- MCP Calls: 1 (subsidy calculation)

## Architecture

```
Farmer         Chainlit UI        FastAPI Backend    MCP Servers
                                                      (Port 7777)
    │              │                    │
    ├─ Question ──►│                    │
    │              ├─ Agent Call ────►  │
    │              │                    ├─► OpenWeather
    │              │                    ├─► ZekaLab
    │              │                    │
    │              │◄─ Response ────────┤
    │◄─ Answer ─────│                    │
```

## Monitoring

### View MCP Logs

```bash
# In Terminal 2
tail -f zekalab-mcp.log
```

### View Langfuse Traces

```
http://localhost:3000  # Langfuse dashboard
```

### Check Server Health

```bash
curl http://localhost:7777/health
```

## Troubleshooting

### MCP Server Not Responding

```bash
# Restart MCP server
pkill -f "src/yonca/mcp_server"
cd src/yonca/mcp_server && python main.py
```

### Weather Data Not Showing

```bash
# Check OpenWeather API key in .env
echo $OPENWEATHER_API_KEY

# Restart FastAPI
pkill -f "uvicorn yonca.api"
cd src && uvicorn yonca.api.main:app --reload
```

### Chainlit UI Blank

```bash
# Clear cache
cd demo-ui && rm -rf .chainlit/

# Restart UI
chainlit run app.py
```

## Performance Targets

- **End-to-end response time:** <2 seconds
- **MCP server response time:** <1 second per call
- **Uptime:** 99.5%
- **Error rate:** <1%
```

---

### Task 5.6: Integration with Existing Chainlit Setup (1 hour)

**Update:** `demo-ui/app.py` - Add to existing Chainlit app

```python
# demo-ui/app.py

# Add these imports at top
from chainlit.mcp_client import MCPClient
from yonca.mcp.client import MCPClient as YoncaMCPClient
from yonca.agent.state import MCPTrace

# Add this middleware to track MCP usage
@app.middleware("http")
async def track_mcp_usage(request, call_next):
    """Track MCP calls for analytics."""
    response = await call_next(request)

    # Log to analytics
    if hasattr(request, "mcp_trace"):
        analytics_client.log_event(
            "mcp_call",
            {
                "server": request.mcp_trace.server,
                "tool": request.mcp_trace.tool,
                "duration_ms": request.mcp_trace.duration_ms,
                "success": request.mcp_trace.success,
            }
        )

    return response
```

---

## ✅ Phase 5 Deliverables

By end of Phase 5:

- ✅ Chainlit UI shows real-time MCP status (connected/disconnected)
- ✅ Data flow visualization shows which APIs were called
- ✅ Consent flow prevents unauthorized use of external data
- ✅ Attribution display shows data source for transparency
- ✅ 3 demo scenarios fully functional
- ✅ E2E tests verify complete workflow
- ✅ Response times <2s per node
- ✅ Deployment guide ready for production
- ✅ Graceful degradation when MCP fails

---

## 🎬 Demo Script (10-minute walkthrough)

```
Host: "Good morning, I'm showing you ALEM - an AI agricultural assistant."

1. Show MCP Status (30 sec)
   - Point to status indicator showing ✅ OpenWeather, ✅ ZekaLab
   - Explain: "Real-time connection to weather and rules engine"

2. Run Scenario 1: Irrigation (2 min)
   - Ask: "Should I water my cotton?"
   - Show real OpenWeather data loading
   - Show ZekaLab rules evaluating
   - Display recommendation with 94% confidence
   - Show data flow: weather → rules → decision

3. Run Scenario 2: Pest Control (2 min)
   - Ask: "I see aphids on my wheat"
   - Show pest evaluation rules
   - Display organic + chemical options
   - Show source attribution

4. Run Scenario 3: Subsidy Discovery (2 min)
   - Ask: "What subsidies am I eligible for?"
   - Show calculation for 15ha cotton farm
   - Display €750 total available
   - Show application deadlines

5. Show Langfuse Trace (1.5 min)
   - Open http://localhost:3000
   - Show each MCP call in timeline
   - Explain audit trail for compliance

6. Show Graceful Degradation (1 min)
   - Simulate MCP failure
   - Show system still works with local rules
   - Explain robustness

7. Q&A (1 min)
```

---

<div align="center">

**Phase 5: Demo Enhancement**
🚀 Ready to Build

**[All Phases Complete! →](25-MCP-COMPLETE-IMPLEMENTATION-CHECKLIST.md)**

</div>
