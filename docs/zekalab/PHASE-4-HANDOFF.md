# 🚀 Phase 4 Handoff Document - Ready to Build!

**Created After:** Phase 3 Completion
**Date:** January 23, 2026
**Status:** ✅ All prerequisites complete, ready to build
**Estimated Duration:** 10-13 hours

---

## 📋 What's Ready for Phase 4

### ✅ Phase 2 Complete
- WeatherMCPHandler fully implemented (330 lines)
- Weather integration tested (6 tests passing)
- context_loader calls weather MCP with fallback
- All MCPTrace infrastructure in place

### ✅ Phase 3 Complete
- ZekaLab MCP server running on port 7777
- 5 tools fully tested (24 tests passing)
- 3 resources accessible
- Dockerfile and deployment guide ready
- Live tested and verified working

### ✅ Infrastructure Ready
- MCPTrace model in AgentState
- MCP config system operational
- .env file supports all MCP settings
- AgentState extensions complete

---

## 🎯 Phase 4 Objective

**Wire the internal MCP server into the agent graph via orchestration**

```
CURRENT STATE (Phase 3):
  LangGraph Agent
    ├─ context_loader (calls weather MCP) ✅
    └─ agronomist_node (hardcoded rules)

PHASE 4 TARGET:
  LangGraph Agent
    ├─ context_loader (weather + subsidy + harvest) ← UPDATED
    └─ agronomist_node (calls zekalab MCP for rules) ← NEW
              ├─ determine intent → which rule to call
              ├─ call zekalab MCP tool
              ├─ record MCP trace
              └─ format response with rule citations
```

---

## 📝 Phase 4 Tasks Breakdown

### Task 4.1: Create ZekaLabMCPHandler (2 hours)
**Parallel to:** WeatherMCPHandler
**Location:** `src/yonca/mcp/handlers/zekalab_handler.py`

**Create class with methods:**
```python
class ZekaLabMCPHandler:
    """Handler for calling ZekaLab internal MCP server (port 7777)."""

    async def evaluate_irrigation_rules(
        farm_id: str,
        crop_type: str,
        soil_moisture: float,
        temperature: float,
        rainfall_7d: float,
    ) -> IrrigationRecommendation

    async def evaluate_fertilization_rules(
        farm_id: str,
        crop_type: str,
        soil_data: SoilAnalysis,
        growth_stage_days: int,
    ) -> FertilizationRecommendation

    async def evaluate_pest_control_rules(
        farm_id: str,
        crop_type: str,
        temperature: float,
        humidity: float,
        observed_pests: list[str],
    ) -> PestControlRecommendation

    async def calculate_subsidy(
        farm_id: str,
        hectares: float,
        farmer_age: Optional[int],
    ) -> SubsidyRecommendation

    async def predict_harvest_date(
        farm_id: str,
        planting_date: str,
        gdd_accumulated: float,
    ) -> HarvestPrediction
```

**Features to implement:**
- ✅ HTTP calls to localhost:7777 (configurable in .env)
- ✅ Error handling + timeout/retry logic
- ✅ MCPTrace recording
- ✅ Structlog logging
- ✅ Fallback for development (if server down)

**Tests needed:**
- Unit tests mocking HTTP responses
- Integration tests with running server (optional)

---

### Task 4.2: Refactor agronomist_node (3 hours)
**Location:** `src/yonca/agent/nodes/agronomist.py`

**Current Flow:**
```python
def agronomist_node(state: AgentState):
    user_message = state["messages"][-1].content
    farm_context = state.get("farm_context")
    weather = state.get("weather")

    # Build prompt with hardcoded rules
    prompt = build_intent_prompt(state["routing"].intent)

    # Call LLM to generate response
    response = llm.invoke(prompt)

    return {"messages": [response]}
```

**New Flow (Phase 4):**
```python
async def agronomist_node(state: AgentState):
    intent = state["routing"].intent
    farm_context = state.get("farm_context")
    weather = state.get("weather")
    mcp_traces = state.get("mcp_traces", [])

    # Step 1: Determine which MCP tool to call based on intent
    if intent == UserIntent.IRRIGATION:
        rec = await zekalab_handler.evaluate_irrigation_rules(
            farm_id=farm_context.farm_id,
            crop_type=farm_context.crop_type,
            soil_moisture=farm_context.soil_moisture,
            temperature=weather.temperature,
            rainfall_7d=weather.rainfall_7d,
        )
        mcp_traces.append(MCPTrace(...))  # Record call

    elif intent == UserIntent.FERTILIZATION:
        rec = await zekalab_handler.evaluate_fertilization_rules(...)
        mcp_traces.append(MCPTrace(...))

    elif intent == UserIntent.PEST_CONTROL:
        rec = await zekalab_handler.evaluate_pest_control_rules(...)
        mcp_traces.append(MCPTrace(...))

    # Step 2: Format response with rule citations
    response = format_mcp_response(
        recommendation=rec,
        intent=intent,
        farm_context=farm_context,
        rule_id=rec.rule_id,
        confidence=rec.confidence,
    )

    # Step 3: Return with MCP trace
    return {
        "messages": [response_message],
        "mcp_traces": mcp_traces,
    }
```

**Key Changes:**
- ✅ Make node async (use `async def`)
- ✅ Inject ZekaLabMCPHandler
- ✅ Intent-based tool selection
- ✅ MCP trace recording
- ✅ Response formatting with rule citations

**Tests needed:**
- Unit tests with mocked ZekaLab handler
- Integration tests with real handler

---

### Task 4.3: Multi-MCP Orchestration (3 hours)
**Location:** `src/yonca/agent/nodes/context_loader.py` + new orchestration logic

**Current:**
```python
async def context_loader_node(state: AgentState):
    # Load user context
    user = await load_user(state["user_id"])

    # Load farm context
    farm = await load_farm(state["farm_id"])

    # Load weather (Phase 2)
    weather = await weather_handler.get_forecast(...)

    return {
        "user_context": user,
        "farm_context": farm,
        "weather": weather,
    }
```

**New (Phase 4):**
```python
async def context_loader_node(state: AgentState):
    # Load user + farm contexts (unchanged)
    user = await load_user(state["user_id"])
    farm = await load_farm(state["farm_id"])

    # PARALLEL MCP CALLS (new):
    # Call both MCP servers simultaneously
    tasks = [
        weather_handler.get_forecast(
            farm_id=farm.id,
            lat=farm.latitude,
            lon=farm.longitude,
        ),
        zekalab_handler.calculate_subsidy(
            farm_id=farm.id,
            hectares=farm.hectares,
            farmer_age=user.age,
        ),
        zekalab_handler.predict_harvest_date(
            farm_id=farm.id,
            planting_date=farm.planting_date.isoformat(),
            gdd_accumulated=farm.gdd_accumulated,
        ),
    ]

    # Wait for all to complete (or timeout)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    weather, subsidy, harvest = results

    # Handle failures gracefully
    if isinstance(weather, Exception):
        weather = await get_synthetic_weather(farm.region)

    # Record all MCP traces
    mcp_traces = state.get("mcp_traces", [])
    mcp_traces.extend([
        weather_trace,
        subsidy_trace,
        harvest_trace,
    ])

    return {
        "user_context": user,
        "farm_context": farm,
        "weather": weather,
        "subsidy_info": subsidy,
        "harvest_info": harvest,
        "mcp_traces": mcp_traces,
    }
```

**Key Features:**
- ✅ Parallel execution with `asyncio.gather()`
- ✅ Exception handling (one failure doesn't break all)
- ✅ MCP trace collection
- ✅ State enrichment with subsidy + harvest info

---

### Task 4.4: Langfuse Integration (2 hours)
**Location:** `src/yonca/observability/langfuse.py` + node updates

**Create MCP tracing utilities:**
```python
async def trace_mcp_call(
    langfuse_trace,
    mcp_server: str,
    tool_name: str,
    input_args: dict,
    output: dict,
    duration_ms: float,
    success: bool,
    error_message: Optional[str] = None,
):
    """Log MCP call to Langfuse for audit trail."""

    langfuse_trace.span(
        name=f"mcp_{mcp_server}_{tool_name}",
        input={"args": input_args},
        output={"result": output},
        metadata={
            "mcp_server": mcp_server,
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "error": error_message,
        },
    )
```

**Integration points:**
1. In ZekaLabMCPHandler:
   ```python
   async def evaluate_irrigation_rules(...):
       start = time.time()
       try:
           result = await http_call(...)
           duration_ms = (time.time() - start) * 1000
           await trace_mcp_call(
               mcp_server="zekalab",
               tool_name="evaluate_irrigation_rules",
               input_args={...},
               output=result,
               duration_ms=duration_ms,
               success=True,
           )
           return result
       except Exception as e:
           await trace_mcp_call(..., success=False, error_message=str(e))
           raise
   ```

2. In agronomist_node:
   ```python
   # MCP trace automatically recorded by handler
   # Just ensure it's added to state
   ```

3. Dashboard visualization:
   - Show MCP call timeline
   - Tool names + arguments
   - Success/failure rates
   - Performance metrics

---

### Task 4.5: Performance Tuning (1 hour)
**Target:** <2 seconds per request

**Measurement points:**
- ✅ Measure context_loader end-to-end
- ✅ Measure agronomist_node end-to-end
- ✅ Measure MCP call durations
- ✅ Profile hot paths

**Optimization strategies:**
- ✅ Parallel MCP calls (already done in 4.3)
- ✅ Response caching (optional)
- ✅ Connection pooling (aiohttp session reuse)
- ✅ Timeout tuning

**Performance targets:**
- Context loader: <500ms
- Agronomist node: <500ms
- MCP calls: <200ms each
- Total response: <2s ✅

---

## 🔍 Code Template: What to Build

### ZekaLabMCPHandler Template
```python
# src/yonca/mcp/handlers/zekalab_handler.py
"""Handler for ZekaLab internal MCP server."""

import asyncio
import structlog
from typing import Optional
from httpx import AsyncClient

from yonca.agent.state import MCPTrace

class ZekaLabMCPHandler:
    def __init__(self):
        self.mcp_url = os.getenv("ZEKALAB_MCP_URL", "http://localhost:7777")
        self.timeout_s = int(os.getenv("ZEKALAB_TIMEOUT_MS", 2000)) / 1000
        self.client = None

    async def get_client(self) -> AsyncClient:
        if not self.client:
            self.client = AsyncClient(timeout=self.timeout_s)
        return self.client

    async def evaluate_irrigation_rules(self, **kwargs) -> dict:
        client = await self.get_client()
        response = await client.post(
            f"{self.mcp_url}/tools/evaluate_irrigation_rules",
            json=kwargs,
        )
        response.raise_for_status()
        return response.json()
```

---

## ✅ Pre-Phase 4 Checklist

- [x] Phase 2 complete (weather MCP)
- [x] Phase 3 complete (zekalab MCP)
- [x] MCPTrace model in place
- [x] AgentState extended
- [x] MCP config system ready
- [x] ZekaLab server running and tested
- [x] Deployment guide written
- [x] Documentation complete
- [x] All Phase 2-3 tests passing

**Ready to start Phase 4?** YES! ✅

---

## 📚 Reference Files

**Key files to modify in Phase 4:**
- `src/yonca/mcp/handlers/zekalab_handler.py` ← CREATE NEW
- `src/yonca/agent/nodes/agronomist.py` ← REFACTOR
- `src/yonca/agent/nodes/context_loader.py` ← UPDATE
- `src/yonca/observability/langfuse.py` ← UPDATE
- `tests/unit/test_mcp_handlers/` ← ADD TESTS
- `tests/integration/` ← ADD INTEGRATION TESTS

**Key files already complete:**
- `src/yonca/agent/state.py` (MCPTrace model)
- `src/yonca/mcp/config.py` (MCP configuration)
- `src/yonca/mcp_server/main.py` (ZekaLab MCP server)
- `src/yonca/mcp/handlers/weather_handler.py` (Weather MCP handler)

---

## 🎯 Success Criteria for Phase 4

- [ ] ZekaLabMCPHandler fully implemented
- [ ] agronomist_node refactored to use MCP
- [ ] Parallel MCP calls in context_loader
- [ ] All MCP calls traced in Langfuse
- [ ] Performance <2s per request
- [ ] 15+ new tests passing
- [ ] No breaking changes
- [ ] Documentation updated
- [ ] Live tested with real MCP server

---

## 🚀 Ready to Build!

**All prerequisites complete. Phase 4 can start immediately.**

**Estimated timeline:**
- Start: Next session
- Duration: 10-13 hours
- End: Full multi-MCP orchestration complete
- Final: Phase 5 demo enhancement

---

**Next: Phase 4.1 - Create ZekaLabMCPHandler** 🎯
