# 🧠 Phase 3: Internal ZekaLab MCP Server (Cotton Rules Engine)

**Duration:** Week 3 (12-14 hours)
**Status:** Ready (After Phase 1.1 ✅)
**Criticality:** 🔴 **HIGHEST** - Your competitive advantage

---

## 🎯 Phase 3 Objective

Transform ALEM from a "question answerer" to an **"expert consultant with proprietary logic"** by wrapping your Cotton Rules Engine in an enterprise-grade MCP server that can be:
- ✅ Versioned independently
- ✅ Hot-deployed without restarting agent
- ✅ Shared with partners via standard protocol
- ✅ Audited for compliance

---

## 🏗️ Architecture: ZekaLab MCP Server

```
┌─────────────────────────────────────────┐
│  LangGraph Agent (ALEM)                 │
│  ├─ context_loader                      │
│  ├─ weather_node ──► OpenWeather MCP    │
│  └─ agronomist_node ┐                   │
└────────────────────┼──────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  ZekaLab MCP Server        │
        │  (fastmcp)                 │
        ├────────────────────────────┤
        │ TOOLS (Services):          │
        │ ├─ evaluate_irrigation     │
        │ ├─ evaluate_fertilization  │
        │ ├─ evaluate_pest_control   │
        │ ├─ calculate_subsidy       │
        │ └─ predict_harvest_date    │
        │                            │
        │ RESOURCES (Data):          │
        │ ├─ rules_yaml              │
        │ ├─ crop_profiles           │
        │ ├─ subsidy_database        │
        │ └─ soil_types              │
        └────────────────────────────┘
         (Docker Container on :7777)
```

---

## 📋 Phase 3 Tasks

### Task 3.1: Setup FastMCP Project Structure (1.5 hours)

**What:** Create MCP server skeleton using fastmcp
**Files:**

```
src/yonca/mcp_server/
├── __init__.py
├── main.py                    # FastMCP app
├── dockerfile                 # Container image
├── requirements.txt           # MCP dependencies
├── tools/
│   ├── __init__.py
│   ├── irrigation.py          # Irrigation tool
│   ├── fertilization.py       # Fertilization tool
│   ├── pest_control.py        # Pest control tool
│   ├── subsidy.py             # Subsidy calculator
│   └── harvest_prediction.py  # Harvest predictor
└── resources/
    ├── __init__.py
    ├── rules.py               # YAML rules as resources
    └── crop_profiles.py       # Crop data
```

**Create:** `src/yonca/mcp_server/requirements.txt`

```
fastmcp==0.5.0
pydantic==2.0+
aiohttp==3.8+
structlog==24.1+
pyyaml==6.0+
```

**Create:** `src/yonca/mcp_server/main.py`

```python
"""ZekaLab Internal MCP Server.

Exposes ALEM's agricultural rules engine as standardized MCP tools.
Designed for:
- Hot-deployment (restart-free)
- Version management
- Audit trails
- Partner integration

Architecture:
    Tools: Callable operations (evaluate_irrigation_rules, etc.)
    Resources: Data retrieval (rules_yaml, crop_profiles, etc.)

Run:
    python src/yonca/mcp_server/main.py

Environment:
    PORT=7777 (default)
    LOG_LEVEL=INFO
    RULES_PATH=src/yonca/rules/
"""

from contextlib import asynccontextmanager
import os
import json
from typing import Any
import structlog
from fastmcp import FastMCP
from pydantic import BaseModel

# Import tools and resources
from yonca.mcp_server.tools import (
    evaluate_irrigation_rules,
    evaluate_fertilization_rules,
    evaluate_pest_control_rules,
    calculate_subsidy,
    predict_harvest_date,
)
from yonca.mcp_server.resources import (
    get_rules_as_resource,
    get_crop_profiles_as_resource,
    get_subsidy_database_as_resource,
)

logger = structlog.get_logger(__name__)

# ============================================================
# FastMCP Server Setup
# ============================================================

app = FastMCP(
    name="zekalab-internal-mcp",
    description="ZekaLab Internal MCP Server - Cotton & Wheat Rules Engine",
    version="1.0.0",
)


# ============================================================
# Tools (RPC-style operations)
# ============================================================


class IrrigationRequest(BaseModel):
    """Irrigation evaluation request."""
    farm_id: str
    crop_type: str
    soil_type: str
    current_soil_moisture_percent: float
    temperature_c: float
    rainfall_mm_last_7_days: float


class IrrigationResponse(BaseModel):
    """Irrigation evaluation response."""
    should_irrigate: bool
    recommended_water_mm: float
    timing: str
    confidence: float
    rule_id: str
    reasoning: str


@app.tool()
async def evaluate_irrigation_rules(request: IrrigationRequest) -> IrrigationResponse:
    """Evaluate irrigation rules for cotton/wheat.

    Args:
        request: Farm context and current conditions

    Returns:
        Irrigation recommendation with confidence score
    """
    logger.info(
        "irrigation_evaluation_start",
        farm_id=request.farm_id,
        crop=request.crop_type,
    )

    # Load and evaluate rules
    from yonca.rules.engine import RulesEngine

    engine = RulesEngine()
    context = {
        "farm.crop_type": request.crop_type,
        "farm.soil_type": request.soil_type,
        "weather.soil_moisture_percent": request.current_soil_moisture_percent,
        "weather.temperature_c": request.temperature_c,
        "weather.rainfall_mm_7d": request.rainfall_mm_last_7_days,
    }

    matches = engine.evaluate_all(context)
    irrigation_matches = [m for m in matches if m["category"] == "irrigation"]

    if not irrigation_matches:
        return IrrigationResponse(
            should_irrigate=False,
            recommended_water_mm=0,
            timing="No irrigation needed",
            confidence=0.5,
            rule_id="default",
            reasoning="No matching rules found for current conditions",
        )

    best_match = max(irrigation_matches, key=lambda x: x["confidence"])

    logger.info(
        "irrigation_evaluation_complete",
        farm_id=request.farm_id,
        rule_matched=best_match["rule_id"],
        confidence=best_match["confidence"],
    )

    return IrrigationResponse(
        should_irrigate=best_match.get("recommended_action") == "irrigate",
        recommended_water_mm=best_match.get("water_mm", 0),
        timing=best_match.get("timing", "Morning preferred"),
        confidence=best_match["confidence"],
        rule_id=best_match["rule_id"],
        reasoning=best_match.get("recommendation_az", "Check conditions"),
    )


@app.tool()
async def evaluate_fertilization_rules(
    farm_id: str,
    crop_type: str,
    soil_nitrogen_ppm: float,
    soil_phosphorus_ppm: float,
    soil_potassium_ppm: float,
    growth_stage: str,
) -> dict[str, Any]:
    """Evaluate fertilization rules.

    Args:
        farm_id: Unique farm identifier
        crop_type: Cotton, Wheat, etc.
        soil_nitrogen_ppm: Soil N level
        soil_phosphorus_ppm: Soil P level
        soil_potassium_ppm: Soil K level
        growth_stage: seedling, vegetative, flowering, fruiting, mature

    Returns:
        Fertilization recommendation
    """
    logger.info(
        "fertilization_evaluation",
        farm_id=farm_id,
        crop=crop_type,
        stage=growth_stage,
    )

    from yonca.rules.engine import RulesEngine

    engine = RulesEngine()
    context = {
        "farm.crop_type": crop_type,
        "soil.nitrogen_ppm": soil_nitrogen_ppm,
        "soil.phosphorus_ppm": soil_phosphorus_ppm,
        "soil.potassium_ppm": soil_potassium_ppm,
        "crop.growth_stage": growth_stage,
    }

    matches = engine.evaluate_all(context)
    fert_matches = [m for m in matches if m["category"] == "fertilization"]

    if not fert_matches:
        return {
            "fertilize": False,
            "reasoning": "Nutrient levels sufficient",
            "confidence": 0.7,
        }

    best = max(fert_matches, key=lambda x: x["confidence"])

    return {
        "fertilize": True,
        "nitrogen_kg_per_ha": best.get("nitrogen_kg_ha", 0),
        "phosphorus_kg_per_ha": best.get("phosphorus_kg_ha", 0),
        "potassium_kg_per_ha": best.get("potassium_kg_ha", 0),
        "timing": best.get("timing", "Immediate"),
        "method": best.get("application_method", "Broadcast"),
        "confidence": best["confidence"],
        "rule_id": best["rule_id"],
    }


@app.tool()
async def evaluate_pest_control_rules(
    farm_id: str,
    crop_type: str,
    pest_detected: str,
    severity: str,  # low, medium, high
    temperature_c: float,
    humidity_percent: float,
) -> dict[str, Any]:
    """Evaluate pest control rules.

    Args:
        farm_id: Farm ID
        crop_type: Cotton, Wheat, etc.
        pest_detected: Aphids, Spider Mites, Boll Weevil, etc.
        severity: low, medium, high
        temperature_c: Current temperature
        humidity_percent: Current humidity

    Returns:
        Pest control recommendation
    """
    logger.info(
        "pest_control_evaluation",
        farm_id=farm_id,
        pest=pest_detected,
        severity=severity,
    )

    from yonca.rules.engine import RulesEngine

    engine = RulesEngine()
    context = {
        "farm.crop_type": crop_type,
        "pest.name": pest_detected,
        "pest.severity": severity,
        "weather.temperature_c": temperature_c,
        "weather.humidity_percent": humidity_percent,
    }

    matches = engine.evaluate_all(context)
    pest_matches = [m for m in matches if m["category"] == "pest_control"]

    if not pest_matches:
        return {
            "action": "monitor",
            "reasoning": "No immediate action required",
        }

    best = max(pest_matches, key=lambda x: x["confidence"])

    return {
        "action": best.get("action", "monitor"),
        "pesticide_recommended": best.get("pesticide_name"),
        "dosage_per_ha": best.get("dosage_per_ha"),
        "safety_period_days": best.get("safety_period_days", 0),
        "organic_alternative": best.get("organic_alternative"),
        "confidence": best["confidence"],
        "rule_id": best["rule_id"],
    }


@app.tool()
async def calculate_subsidy(
    farm_id: str,
    crop_type: str,
    area_hectares: float,
    production_tons: float,
) -> dict[str, Any]:
    """Calculate available subsidies.

    Args:
        farm_id: Farm ID
        crop_type: Cotton, Wheat, etc.
        area_hectares: Farm area
        production_tons: Estimated production

    Returns:
        Subsidy calculation and recommended programs
    """
    logger.info(
        "subsidy_calculation",
        farm_id=farm_id,
        crop=crop_type,
        area_ha=area_hectares,
    )

    # Load subsidy database
    from yonca.mcp_server.resources import get_subsidy_database_as_resource

    subsidy_db = await get_subsidy_database_as_resource()

    # Find matching programs
    programs = []
    total_subsidy = 0.0

    for program in subsidy_db.get("programs", []):
        if program["eligible_crops"] and crop_type in program["eligible_crops"]:
            if program.get("min_area_ha", 0) <= area_hectares <= program.get(
                "max_area_ha", float("inf")
            ):
                payment = area_hectares * program["subsidy_per_ha"]
                programs.append(
                    {
                        "program_name": program["name"],
                        "payment_eur": payment,
                        "payment_aud": payment * program.get("aud_rate", 1.5),
                        "deadline": program.get("deadline"),
                    }
                )
                total_subsidy += payment

    logger.info(
        "subsidy_calculation_complete",
        farm_id=farm_id,
        total_subsidy=total_subsidy,
        programs_count=len(programs),
    )

    return {
        "eligible_programs": programs,
        "total_subsidy_eur": total_subsidy,
        "total_subsidy_aud": total_subsidy * 1.5,
        "application_deadline": max(
            [p.get("deadline", "2026-12-31") for p in programs]
        ),
    }


@app.tool()
async def predict_harvest_date(
    farm_id: str,
    crop_type: str,
    planting_date: str,
    current_growth_stage: str,
    accumulated_growing_degree_days: float,
) -> dict[str, Any]:
    """Predict harvest date based on growing conditions.

    Args:
        farm_id: Farm ID
        crop_type: Cotton, Wheat, etc.
        planting_date: ISO format (YYYY-MM-DD)
        current_growth_stage: seedling, vegetative, flowering, fruiting, mature
        accumulated_growing_degree_days: GDD accumulated

    Returns:
        Predicted harvest date and confidence
    """
    from datetime import datetime, timedelta

    logger.info(
        "harvest_prediction",
        farm_id=farm_id,
        crop=crop_type,
        gdd=accumulated_growing_degree_days,
    )

    # Get crop profile
    from yonca.mcp_server.resources import get_crop_profiles_as_resource

    profiles = await get_crop_profiles_as_resource()
    crop = profiles.get(crop_type)

    if not crop:
        return {"error": f"Unknown crop type: {crop_type}"}

    # Calculate days remaining
    gdd_required = crop.get("gdd_to_maturity", 2500)
    gdd_remaining = gdd_required - accumulated_growing_degree_days
    days_remaining = max(0, gdd_remaining / 25.0)  # Assume 25 GDD/day average

    plant_date = datetime.fromisoformat(planting_date)
    harvest_date = plant_date + timedelta(days=days_remaining)

    logger.info(
        "harvest_prediction_complete",
        farm_id=farm_id,
        predicted_date=harvest_date.isoformat(),
        days_remaining=days_remaining,
    )

    return {
        "predicted_harvest_date": harvest_date.isoformat(),
        "days_until_harvest": int(days_remaining),
        "confidence": 0.85 if accumulated_growing_degree_days > 1000 else 0.65,
        "growth_stage": current_growth_stage,
        "recommendation": "Begin harvest prep" if days_remaining < 30 else "Monitor GDD",
    }


# ============================================================
# Resources (Data retrieval)
# ============================================================


@app.resource()
async def rules_yaml() -> dict[str, Any]:
    """Get all agricultural rules in JSON format.

    Returns:
        Complete rules database as JSON
    """
    resource = await get_rules_as_resource()
    return resource


@app.resource()
async def crop_profiles() -> dict[str, Any]:
    """Get crop profile database.

    Returns:
        Crop characteristics (GDD, water needs, etc.)
    """
    resource = await get_crop_profiles_as_resource()
    return resource


@app.resource()
async def subsidy_database() -> dict[str, Any]:
    """Get subsidy programs database.

    Returns:
        Available subsidies and eligibility rules
    """
    resource = await get_subsidy_database_as_resource()
    return resource


# ============================================================
# Health & Status
# ============================================================


@app.tool()
async def health_check() -> dict[str, Any]:
    """Server health and status."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "name": "zekalab-internal-mcp",
        "rules_loaded": True,
        "uptime_seconds": 0,
    }


# ============================================================
# Startup/Shutdown
# ============================================================


@asynccontextmanager
async def lifespan(app):
    """Startup and shutdown events."""
    logger.info("zekalab_mcp_server_starting")
    yield
    logger.info("zekalab_mcp_server_shutdown")


# ============================================================
# Run
# ============================================================


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "7777"))

    logger.info("starting_mcp_server", port=port)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
```

---

### Task 3.2: Implement Tools (4 hours)

**What:** Create individual tool modules
**Create:** `src/yonca/mcp_server/tools/irrigation.py`, etc.

(Skeleton shown above in main.py - break into separate files)

---

### Task 3.3: Implement Resources (2 hours)

**Create:** `src/yonca/mcp_server/resources/rules.py`

```python
"""Agricultural rules as MCP resources."""

import yaml
from pathlib import Path
from typing import Any, Dict

async def get_rules_as_resource() -> Dict[str, Any]:
    """Load all YAML rules and return as JSON-serializable resource."""
    rules_dir = Path(__file__).parent.parent.parent / "rules" / "rules"

    all_rules = {}

    for rule_file in rules_dir.glob("*.yaml"):
        category = rule_file.stem
        with open(rule_file) as f:
            rules = yaml.safe_load(f)

        all_rules[category] = rules

    return {
        "rules": all_rules,
        "total_rules": sum(len(r) for r in all_rules.values()),
        "categories": list(all_rules.keys()),
    }


async def get_crop_profiles_as_resource() -> Dict[str, Any]:
    """Get crop profile database."""
    return {
        "cotton": {
            "gdd_to_maturity": 2500,
            "water_mm_needed": 600,
            "nitrogen_kg_ha": 120,
            "pest_risk": "high",
        },
        "wheat": {
            "gdd_to_maturity": 1800,
            "water_mm_needed": 400,
            "nitrogen_kg_ha": 100,
            "pest_risk": "medium",
        },
    }


async def get_subsidy_database_as_resource() -> Dict[str, Any]:
    """Get available subsidy programs."""
    return {
        "programs": [
            {
                "name": "Cotton Production Subsidy",
                "eligible_crops": ["cotton"],
                "min_area_ha": 1,
                "max_area_ha": 100,
                "subsidy_per_ha": 50,
                "deadline": "2026-12-31",
                "aud_rate": 1.5,
            }
        ]
    }
```

---

### Task 3.4: Docker Setup (1.5 hours)

**Create:** `src/yonca/mcp_server/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import requests; requests.get('http://localhost:7777/health')"

# Run MCP server
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7777"]
```

**Create:** `docker-compose.mcp.yml` (for local testing)

```yaml
version: "3.9"

services:
  zekalab-mcp:
    build:
      context: .
      dockerfile: src/yonca/mcp_server/Dockerfile
    ports:
      - "7777:7777"
    environment:
      - LOG_LEVEL=INFO
      - PORT=7777
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7777/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

---

### Task 3.5: Tests & Integration (2 hours)

**Create:** `tests/integration/test_zekalab_mcp_server.py`

```python
@pytest.mark.asyncio
async def test_mcp_server_responds():
    """Test MCP server is reachable."""
    # Requires server running on 7777
    from yonca.mcp.client import MCPClient, MCPToolCall

    client = MCPClient("zekalab")

    call = MCPToolCall(
        server="zekalab",
        tool="health_check",
        args={}
    )

    result = await client.call_tool(call)
    assert result.success
    assert result.data["status"] == "healthy"
```

---

## ✅ Phase 3 Deliverables

By end of Phase 3:

- ✅ ZekaLab MCP server running on localhost:7777
- ✅ 5 tools exposed (irrigation, fertilization, pest control, subsidy, harvest prediction)
- ✅ 3 resources exposed (rules, crops, subsidies)
- ✅ Docker container ready
- ✅ Chainlit/LangGraph can call it via MCP client
- ✅ All calls logged to Langfuse
- ✅ Version independent from main agent

---

<div align="center">

**Phase 3: Internal MCP Server**
🏗️ Ready to Build

[Next: Phase 4 →](23-MCP-PHASE-4-LANGGRAPH-REFACTOR.md)

</div>
