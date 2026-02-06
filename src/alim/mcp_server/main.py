# src/ALİM/mcp_server/main.py
"""ZekaLab Internal MCP Server - Main Application.

FastMCP-based server exposing agricultural rules as MCP tools.
Handles: Irrigation, Fertilization, Pest Control, Subsidies, Harvest Prediction.

Run:
    python -m uvicorn ALİM.mcp_server.main:app --port 7777
    OR
    python src/ALİM/mcp_server/main.py

Architecture:
    FastMCP (standard MCP server framework)
        ├── 5 Tools (RPC operations)
        ├── 3 Resources (Data retrieval)
        └── Error handling + structured logging
"""

import os
from datetime import datetime, timedelta
from enum import Enum

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Setup unified logging BEFORE getting logger
from alim.utils.unified_logging import setup_unified_logging

setup_unified_logging(service_name="MCP", level="INFO")

logger = structlog.get_logger(__name__)

# ============================================================
# Server Configuration
# ============================================================

PORT = int(os.getenv("ZEKALAB_PORT", 7777))
LOG_LEVEL = os.getenv("ZEKALAB_LOG_LEVEL", "INFO")
RULES_PATH = os.getenv("ZEKALAB_RULES_PATH", "src/ALİM/rules")

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

# ============================================================
# Data Models - Requests
# ============================================================


class CropType(str, Enum):
    """Supported crop types."""

    COTTON = "cotton"
    WHEAT = "wheat"
    VEGETABLES = "vegetables"


class SoilType(str, Enum):
    """Soil classification."""

    SANDY = "sandy"
    LOAMY = "loamy"
    CLAY = "clay"
    CALCAREOUS = "calcareous"


class IrrigationRequest(BaseModel):
    """Irrigation rule evaluation request."""

    farm_id: str = Field(..., description="Farm identifier")
    crop_type: CropType = Field(..., description="Crop being grown")
    soil_type: SoilType = Field(..., description="Soil type")
    current_soil_moisture_percent: float = Field(
        ..., ge=0, le=100, description="Current soil moisture %"
    )
    temperature_c: float = Field(..., description="Current temperature in Celsius")
    rainfall_mm_last_7_days: float = Field(
        default=0, ge=0, description="Rainfall in last 7 days (mm)"
    )
    growth_stage_days: int = Field(default=0, ge=0, description="Days since planting")


class FertilizationRequest(BaseModel):
    """Fertilization rule evaluation request."""

    farm_id: str
    crop_type: CropType
    soil_type: SoilType
    soil_nitrogen_ppm: float | None = None
    soil_phosphorus_ppm: float | None = None
    soil_potassium_ppm: float | None = None
    growth_stage_days: int = Field(default=0, ge=0)
    previous_fertilizer_days_ago: int | None = None


class PestControlRequest(BaseModel):
    """Pest control rule evaluation request."""

    farm_id: str
    crop_type: CropType
    temperature_c: float
    humidity_percent: float = Field(ge=0, le=100)
    observed_pests: list[str] = Field(default_factory=list, description="Pests/diseases observed")
    growth_stage_days: int = Field(default=0, ge=0)
    rainfall_mm_last_3_days: float = Field(default=0, ge=0)


class SubsidyRequest(BaseModel):
    """Subsidy calculation request."""

    farm_id: str
    crop_type: CropType
    hectares: float = Field(..., gt=0)
    soil_type: SoilType
    farmer_age: int | None = None
    is_young_farmer: bool = False


class HarvestRequest(BaseModel):
    """Harvest prediction request."""

    farm_id: str
    crop_type: CropType
    planting_date: str = Field(..., description="Date planted (YYYY-MM-DD)")
    current_gdd_accumulated: float = Field(default=0, description="Growing Degree Days accumulated")
    base_temperature_c: float = Field(default=10)


# ============================================================
# Data Models - Responses
# ============================================================


class Recommendation(BaseModel):
    """Generic recommendation output."""

    action: str
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")
    rule_id: str
    reasoning: str
    severity: str = Field(default="medium", description="low/medium/high/critical")


class IrrigationResponse(BaseModel):
    """Irrigation evaluation response."""

    should_irrigate: bool
    recommended_water_mm: float
    timing: str = Field(description="6am/noon/6pm/anytime")
    confidence: float = Field(ge=0, le=1)
    rule_id: str
    reasoning: str


class FertilizationResponse(BaseModel):
    """Fertilization evaluation response."""

    should_fertilize: bool
    nitrogen_kg_per_hectare: float
    phosphorus_kg_per_hectare: float
    potassium_kg_per_hectare: float
    timing: str
    confidence: float = Field(ge=0, le=1)
    rule_id: str
    reasoning: str


class PestControlResponse(BaseModel):
    """Pest control evaluation response."""

    pests_detected: list[str]
    recommended_action: str
    method: str = Field(description="biological/chemical/cultural/integrated")
    severity: str = Field(description="low/medium/high/critical")
    confidence: float = Field(ge=0, le=1)
    rule_id: str
    reasoning: str


class SubsidyResponse(BaseModel):
    """Subsidy calculation response."""

    eligible: bool
    subsidy_azn: float = Field(ge=0, description="Subsidy amount in AZN")
    subsidy_per_hectare_azn: float = Field(ge=0)
    conditions: list[str]
    rule_id: str
    next_review_date: str | None = None


class HarvestResponse(BaseModel):
    """Harvest prediction response."""

    predicted_harvest_date: str = Field(description="YYYY-MM-DD")
    days_to_harvest: int
    maturity_confidence: float = Field(ge=0, le=1)
    recommended_checks: list[str]
    rule_id: str


# ============================================================
# FastAPI App Setup
# ============================================================

app = FastAPI(
    title="ZekaLab Internal MCP Server",
    description="Agricultural rules engine as MCP services",
    version="1.0.0",
)


# ============================================================
# Tool 1: Evaluate Irrigation Rules
# ============================================================


@app.post(
    "/tools/evaluate_irrigation_rules",
    response_model=IrrigationResponse,
    tags=["tools"],
    summary="Evaluate irrigation rules",
)
async def evaluate_irrigation_rules(request: IrrigationRequest) -> IrrigationResponse:
    """Evaluate when to irrigate based on farm conditions.

    **Rules:** Based on cotton/wheat cultivation guidelines
    - Soil moisture threshold
    - Temperature considerations
    - Growth stage
    - Rainfall integration

    **Returns:** Recommendation with confidence score
    """
    logger.info(
        "irrigation_evaluation",
        farm_id=request.farm_id,
        crop=request.crop_type,
        soil_moisture=request.current_soil_moisture_percent,
    )

    try:
        # ========== IRRIGATION RULES LOGIC ==========
        should_irrigate = False
        recommended_water_mm = 0.0
        timing = "anytime"
        reasoning = ""

        # Base threshold varies by crop and soil type
        moisture_threshold = 60  # Default for loamy soil
        if request.soil_type == SoilType.SANDY:
            moisture_threshold = 50  # Sandy needs more frequent irrigation
        elif request.soil_type == SoilType.CLAY:
            moisture_threshold = 70  # Clay retains water better

        # Check if irrigation is needed
        if request.current_soil_moisture_percent < moisture_threshold:
            should_irrigate = True
            confidence = 0.85

            # Calculate water amount based on deficit
            water_deficit = moisture_threshold - request.current_soil_moisture_percent
            recommended_water_mm = water_deficit * 2  # Simplified calculation

            # Timing based on temperature
            if request.temperature_c > 30:
                timing = "6am"  # Early morning for high temp
                rule_id = "RULE_IRR_001_HIGH_TEMP"
            elif request.temperature_c < 10:
                timing = "noon"  # Midday for low temp
                rule_id = "RULE_IRR_002_LOW_TEMP"
            else:
                timing = "6am"  # Default to morning
                rule_id = "RULE_IRR_003_NORMAL"

            # Adjust for recent rainfall
            if request.rainfall_mm_last_7_days > 30:
                should_irrigate = False
                confidence = 0.95
                reasoning = f"Recent rainfall ({request.rainfall_mm_last_7_days}mm) sufficient"
                recommended_water_mm = 0

            if should_irrigate:
                reasoning = f"Soil moisture {request.current_soil_moisture_percent}% below threshold {moisture_threshold}%. Recommend {recommended_water_mm:.0f}mm at {timing}."
        else:
            rule_id = "RULE_IRR_004_SUFFICIENT"
            confidence = 0.90
            reasoning = f"Soil moisture {request.current_soil_moisture_percent}% adequate. No irrigation needed."

        return IrrigationResponse(
            should_irrigate=should_irrigate,
            recommended_water_mm=recommended_water_mm,
            timing=timing,
            confidence=confidence,
            rule_id=rule_id,
            reasoning=reasoning,
        )

    except Exception as e:
        logger.error("irrigation_evaluation_error", error=str(e), farm_id=request.farm_id)
        raise HTTPException(status_code=500, detail=f"Irrigation evaluation failed: {str(e)}")


# ============================================================
# Tool 2: Evaluate Fertilization Rules
# ============================================================


@app.post(
    "/tools/evaluate_fertilization_rules",
    response_model=FertilizationResponse,
    tags=["tools"],
    summary="Evaluate fertilization rules",
)
async def evaluate_fertilization_rules(request: FertilizationRequest) -> FertilizationResponse:
    """Evaluate fertilization needs based on soil and crop.

    **Rules:** Based on soil analysis + crop requirements
    - NPK ratios
    - Growth stage
    - Crop type specific needs

    **Returns:** Fertilizer recommendations in kg/hectare
    """
    logger.info(
        "fertilization_evaluation",
        farm_id=request.farm_id,
        crop=request.crop_type,
    )

    try:
        # ========== FERTILIZATION RULES LOGIC ==========

        # Default NPK values for cotton (kg/ha)
        if request.crop_type == CropType.COTTON:
            base_nitrogen = 150
            base_phosphorus = 80
            base_potassium = 80
            rule_id = "RULE_FERT_001_COTTON"
        elif request.crop_type == CropType.WHEAT:
            base_nitrogen = 120
            base_phosphorus = 60
            base_potassium = 60
            rule_id = "RULE_FERT_002_WHEAT"
        else:
            base_nitrogen = 100
            base_phosphorus = 50
            base_potassium = 50
            rule_id = "RULE_FERT_003_VEGETABLES"

        # Adjust for soil nutrient levels
        nitrogen_recommendation = base_nitrogen
        phosphorus_recommendation = base_phosphorus
        potassium_recommendation = base_potassium

        if request.soil_nitrogen_ppm and request.soil_nitrogen_ppm > 30:
            nitrogen_recommendation *= 0.7  # Reduce if soil has good nitrogen

        if request.soil_phosphorus_ppm and request.soil_phosphorus_ppm > 20:
            phosphorus_recommendation *= 0.8

        if request.soil_potassium_ppm and request.soil_potassium_ppm > 200:
            potassium_recommendation *= 0.8

        # Adjust for growth stage
        should_fertilize = True
        timing = "Now"

        if request.growth_stage_days < 10:
            timing = "Post-planting (starter)"
            nitrogen_recommendation *= 1.1
        elif request.growth_stage_days > 100:
            timing = "Late season (post-flowering)"
            nitrogen_recommendation *= 0.5

        reasoning = f"Recommended NPK: N={nitrogen_recommendation:.0f}, P={phosphorus_recommendation:.0f}, K={potassium_recommendation:.0f} kg/ha. {timing}."

        return FertilizationResponse(
            should_fertilize=should_fertilize,
            nitrogen_kg_per_hectare=nitrogen_recommendation,
            phosphorus_kg_per_hectare=phosphorus_recommendation,
            potassium_kg_per_hectare=potassium_recommendation,
            timing=timing,
            confidence=0.85,
            rule_id=rule_id,
            reasoning=reasoning,
        )

    except Exception as e:
        logger.error("fertilization_evaluation_error", error=str(e), farm_id=request.farm_id)
        raise HTTPException(status_code=500, detail=f"Fertilization evaluation failed: {str(e)}")


# ============================================================
# Tool 3: Evaluate Pest Control Rules
# ============================================================


@app.post(
    "/tools/evaluate_pest_control_rules",
    response_model=PestControlResponse,
    tags=["tools"],
    summary="Evaluate pest control measures",
)
async def evaluate_pest_control_rules(request: PestControlRequest) -> PestControlResponse:
    """Evaluate pest/disease risk and recommend control measures.

    **Rules:** Based on weather conditions + observed pests
    - Temperature + humidity conditions
    - Common cotton pests
    - Preventive vs curative measures

    **Returns:** Pest control action plan
    """
    logger.info(
        "pest_control_evaluation",
        farm_id=request.farm_id,
        crop=request.crop_type,
        observed_pests=request.observed_pests,
    )

    try:
        # ========== PEST CONTROL RULES LOGIC ==========

        detected_pests = list(set(request.observed_pests))  # Remove duplicates
        recommended_action = "Monitor closely"
        method = "cultural"
        severity = "low"
        confidence = 0.7
        rule_id = "RULE_PEST_001_BASELINE"

        # Environmental risk assessment
        high_risk_conditions = (
            request.temperature_c > 25
            and request.humidity_percent > 70
            and request.rainfall_mm_last_3_days > 20
        )

        if high_risk_conditions:
            severity = "high"
            confidence = 0.85
            recommended_action = "Preventive treatment recommended"
            method = "biological"
            rule_id = "RULE_PEST_002_HIGH_RISK"

        # Specific pest handling
        if "cotton_bollworm" in detected_pests:
            severity = "critical"
            confidence = 0.95
            recommended_action = "Immediate treatment required"
            method = "integrated"
            rule_id = "RULE_PEST_003_BOLLWORM"

        elif "spider_mites" in detected_pests:
            recommended_action = "Monitor and treat if population >50 per leaf"
            method = "chemical"
            rule_id = "RULE_PEST_004_SPIDER_MITES"

        elif "leaf_curl_virus" in detected_pests:
            severity = "high"
            recommended_action = "Remove affected plants, control whiteflies"
            method = "cultural"
            rule_id = "RULE_PEST_005_VIRUS"

        reasoning = f"Pests detected: {', '.join(detected_pests) if detected_pests else 'None'}. Conditions: {request.temperature_c}°C, {request.humidity_percent}% RH. {recommended_action}"

        return PestControlResponse(
            pests_detected=detected_pests,
            recommended_action=recommended_action,
            method=method,
            severity=severity,
            confidence=confidence,
            rule_id=rule_id,
            reasoning=reasoning,
        )

    except Exception as e:
        logger.error("pest_control_evaluation_error", error=str(e), farm_id=request.farm_id)
        raise HTTPException(status_code=500, detail=f"Pest control evaluation failed: {str(e)}")


# ============================================================
# Tool 4: Calculate Subsidy
# ============================================================


@app.post(
    "/tools/calculate_subsidy",
    response_model=SubsidyResponse,
    tags=["tools"],
    summary="Calculate government subsidy eligibility",
)
async def calculate_subsidy(request: SubsidyRequest) -> SubsidyResponse:
    """Calculate government subsidy based on farm parameters.

    **Rules:** Based on government subsidy programs
    - Crop type support
    - Farm size
    - Young farmer incentives
    - Soil degradation support

    **Returns:** Eligible subsidy amount and conditions
    """
    logger.info(
        "subsidy_calculation",
        farm_id=request.farm_id,
        crop=request.crop_type,
        hectares=request.hectares,
    )

    try:
        # ========== SUBSIDY RULES LOGIC ==========

        eligible = True
        conditions = []
        rule_id = "RULE_SUBSIDY_001_BASE"

        # Base subsidy rates (AZN per hectare) - varies by crop
        subsidy_rates = {
            CropType.COTTON: 500,
            CropType.WHEAT: 300,
            CropType.VEGETABLES: 400,
        }

        rate_per_hectare = subsidy_rates.get(request.crop_type, 300)

        # Calculate base subsidy
        subsidy_azn = rate_per_hectare * request.hectares

        # Young farmer bonus (+25%)
        if request.is_young_farmer or (request.farmer_age and request.farmer_age < 40):
            subsidy_azn *= 1.25
            conditions.append("Young farmer bonus applied (+25%)")
            rule_id = "RULE_SUBSIDY_002_YOUNG_FARMER"

        # Calcareous soil support (+15%)
        if request.soil_type == SoilType.CALCAREOUS:
            subsidy_azn *= 1.15
            conditions.append("Calcareous soil support applied (+15%)")
            rule_id = "RULE_SUBSIDY_003_SOIL_SUPPORT"

        # Size limitations
        if request.hectares > 50:
            subsidy_azn *= 0.9  # 10% reduction for large farms
            conditions.append("Large farm reduction (-10%)")

        # Conditions
        conditions.extend(
            [
                "Must maintain production records",
                "Eco-friendly practices encouraged",
                "Must report production outcomes",
            ]
        )

        # Next review in 12 months
        next_review = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

        return SubsidyResponse(
            eligible=eligible,
            subsidy_azn=subsidy_azn,
            subsidy_per_hectare_azn=rate_per_hectare,
            conditions=conditions,
            rule_id=rule_id,
            next_review_date=next_review,
        )

    except Exception as e:
        logger.error("subsidy_calculation_error", error=str(e), farm_id=request.farm_id)
        raise HTTPException(status_code=500, detail=f"Subsidy calculation failed: {str(e)}")


# ============================================================
# Tool 5: Predict Harvest Date
# ============================================================


@app.post(
    "/tools/predict_harvest_date",
    response_model=HarvestResponse,
    tags=["tools"],
    summary="Predict crop harvest date",
)
async def predict_harvest_date(request: HarvestRequest) -> HarvestResponse:
    """Predict optimal harvest date based on GDD and crop type.

    **Rules:** Based on Growing Degree Days (GDD)
    - Cotton: 2400-2800 GDD to maturity
    - Wheat: 1800-2200 GDD to maturity
    - Base temperature: 10°C (configurable)

    **Returns:** Predicted harvest date with confidence
    """
    logger.info(
        "harvest_prediction",
        farm_id=request.farm_id,
        crop=request.crop_type,
        gdd=request.current_gdd_accumulated,
    )

    try:
        # ========== HARVEST PREDICTION RULES ==========

        # GDD requirements by crop
        gdd_requirements = {
            CropType.COTTON: 2600,  # Mid-range
            CropType.WHEAT: 2000,
            CropType.VEGETABLES: 1500,
        }

        target_gdd = gdd_requirements.get(request.crop_type, 2000)
        gdd_remaining = max(0, target_gdd - request.current_gdd_accumulated)

        # Average daily GDD accumulation (base temp 10°C)
        avg_daily_gdd = 15  # Conservative estimate

        days_to_harvest = int(gdd_remaining / avg_daily_gdd) if avg_daily_gdd > 0 else 60

        # Calculate predicted harvest date
        planting_date = datetime.strptime(request.planting_date, "%Y-%m-%d")
        predicted_harvest_date = planting_date + timedelta(days=days_to_harvest)

        maturity_confidence = min(
            0.95, 0.60 + (request.current_gdd_accumulated / target_gdd) * 0.35
        )

        recommended_checks = [
            "Monitor boll development",
            "Check for boll lock (cotton) or grain moisture (wheat)",
            "Plan harvesting logistics",
        ]

        rule_id = f"RULE_HARVEST_001_{request.crop_type.value.upper()}"

        f"GDD accumulated: {request.current_gdd_accumulated:.0f}/{target_gdd} ({(request.current_gdd_accumulated/target_gdd*100):.1f}% complete). Estimated {days_to_harvest} days to maturity."

        return HarvestResponse(
            predicted_harvest_date=predicted_harvest_date.strftime("%Y-%m-%d"),
            days_to_harvest=days_to_harvest,
            maturity_confidence=maturity_confidence,
            recommended_checks=recommended_checks,
            rule_id=rule_id,
        )

    except Exception as e:
        logger.error("harvest_prediction_error", error=str(e), farm_id=request.farm_id)
        raise HTTPException(status_code=500, detail=f"Harvest prediction failed: {str(e)}")


# ============================================================
# Resources (Data endpoints)
# ============================================================


@app.get("/resources/rules", tags=["resources"], summary="Get all rules as YAML")
async def get_rules_resource():
    """Return all agricultural rules as structured data.

    Returns: List of all rules with conditions and actions
    """
    logger.info("rules_resource_requested")

    rules = {
        "version": "1.0.0",
        "last_updated": datetime.now().isoformat(),
        "rules": {
            "irrigation": {
                "RULE_IRR_001": "Water cotton at 6am when soil <60% moisture",
                "RULE_IRR_002": "Water wheat at noon in cold weather",
            },
            "fertilization": {
                "RULE_FERT_001": "Cotton: 150N, 80P, 80K kg/ha base rate",
                "RULE_FERT_002": "Wheat: 120N, 60P, 60K kg/ha base rate",
            },
            "pest_control": {
                "RULE_PEST_001": "Monitor daily during high-risk weather",
                "RULE_PEST_002": "Cotton bollworm: immediate treatment required",
            },
        },
    }

    return rules


@app.get("/resources/crop_profiles", tags=["resources"], summary="Get crop profiles")
async def get_crop_profiles():
    """Return crop profiles with characteristics.

    Returns: Crop data including GDD, water needs, nutrients
    """
    logger.info("crop_profiles_resource_requested")

    profiles = {
        "cotton": {
            "gdd_requirement": 2600,
            "gdd_base_temp_c": 10,
            "water_requirement_mm": 400,
            "nitrogen_kg_ha": 150,
            "days_to_maturity": 150,
        },
        "wheat": {
            "gdd_requirement": 2000,
            "gdd_base_temp_c": 10,
            "water_requirement_mm": 300,
            "nitrogen_kg_ha": 120,
            "days_to_maturity": 120,
        },
        "vegetables": {
            "gdd_requirement": 1500,
            "gdd_base_temp_c": 10,
            "water_requirement_mm": 350,
            "nitrogen_kg_ha": 100,
            "days_to_maturity": 90,
        },
    }

    return profiles


@app.get("/resources/subsidy_database", tags=["resources"], summary="Get subsidy info")
async def get_subsidy_database():
    """Return government subsidy program information.

    Returns: Subsidy rates by crop, conditions, dates
    """
    logger.info("subsidy_database_resource_requested")

    database = {
        "version": "2026-01",
        "programs": {
            "cotton": {
                "rate_azn_per_hectare": 500,
                "eligibility": "All registered farms",
                "young_farmer_bonus": 0.25,
            },
            "wheat": {
                "rate_azn_per_hectare": 300,
                "eligibility": "Licensed grain producers",
                "young_farmer_bonus": 0.25,
            },
            "vegetables": {
                "rate_azn_per_hectare": 400,
                "eligibility": "All registered farms",
                "young_farmer_bonus": 0.25,
            },
        },
        "application_period": "January 1 - December 31",
        "contact": "subsidy-info@zekalab.gov.az",
    }

    return database


# ============================================================
# Health Check
# ============================================================


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "zekalab-internal-mcp",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/", tags=["system"], summary="MCP Server Info")
async def root():
    """Root endpoint - MCP server information and available endpoints."""
    return {
        "name": "🧠 ZekaLab Internal MCP Server",
        "version": "1.0.0",
        "status": "operational",
        "service": "zekalab-internal-mcp",
        "port": PORT,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "tools": "/tools",
            "resources": {
                "rules": "/resources/rules",
                "crop_profiles": "/resources/crop_profiles",
                "subsidy_database": "/resources/subsidy_database",
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/mcp", tags=["mcp"])
async def mcp_endpoint():
    """MCP protocol endpoint (SSE/streamable-http).

    Chainlit native MCP modal expects Server-Sent Events (SSE) streaming.
    Returns tools list and capabilities in proper MCP format.
    """

    async def sse_generator():
        """Generate SSE stream for MCP protocol (JSON-RPC 2.0 over HTTP)."""
        import json

        # MCP Protocol: Initialize with empty result object (server capabilities)
        init_message = {"jsonrpc": "2.0", "result": {}, "id": 1}
        yield f"data: {json.dumps(init_message)}\n\n"

        # Send tools available as a notification (after init)

        # Send as proper MCP notification: tools/list_changed
        tools_message = {
            "jsonrpc": "2.0",
            "method": "notifications/tools/list_changed",
            "params": {},
        }
        yield f"data: {json.dumps(tools_message)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/tools", tags=["mcp"])
async def list_tools():
    """List all available MCP tools (JSON endpoint for reference)."""
    return {
        "tools": [
            {
                "name": "evaluate_irrigation_rules",
                "description": "Evaluate when to irrigate based on farm conditions",
            },
            {
                "name": "evaluate_fertilization_rules",
                "description": "Evaluate fertilization needs based on soil and crop",
            },
            {
                "name": "evaluate_pest_control_rules",
                "description": "Evaluate pest control recommendations",
            },
            {
                "name": "calculate_subsidy_eligibility",
                "description": "Calculate subsidy eligibility and amount",
            },
            {
                "name": "predict_harvest_date",
                "description": "Predict harvest date based on growing conditions",
            },
        ]
    }


# ============================================================
# Startup
# ============================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(
        "zekalab_mcp_startup",
        port=PORT,
        log_level=LOG_LEVEL,
        rules_path=RULES_PATH,
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level=LOG_LEVEL.lower(),
    )
