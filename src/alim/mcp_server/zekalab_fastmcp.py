# src/ALİM/mcp_server/zekalab_fastmcp.py
"""ZekaLab MCP Server - FastMCP Implementation.

Protocol-compliant MCP server exposing agricultural rules as tools.
This is the new implementation using the official `mcp.server.fastmcp` framework.

Handles: Irrigation, Fertilization, Pest Control, Subsidies, Harvest Prediction.

Run:
    python src/ALİM/mcp_server/zekalab_fastmcp.py

Architecture:
    FastMCP (official MCP server framework)
        ├── 5 Tools (RPC operations)
        ├── 3 Resources (Data retrieval)
        └── Standard MCP protocol endpoints
"""

import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import structlog
from mcp.server.fastmcp import FastMCP

logger = structlog.get_logger(__name__)

# ============================================================
# Server Configuration
# ============================================================

PORT = int(os.getenv("ZEKALAB_PORT", 7777))
LOG_LEVEL = os.getenv("ZEKALAB_LOG_LEVEL", "INFO")

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

# ============================================================
# FastMCP Server Instance
# ============================================================

mcp = FastMCP(
    "ZekaLab",
    instructions="""ZekaLab is an agricultural rules engine for Azerbaijan farmers.

Available tools:
- evaluate_irrigation_rules: Determine when and how much to irrigate
- evaluate_fertilization_rules: Get NPK recommendations
- evaluate_pest_control_rules: Identify pests and recommend treatments
- calculate_subsidy: Calculate government subsidy eligibility
- predict_harvest_date: Predict optimal harvest timing based on GDD

All tools work with cotton, wheat, and vegetable crops.""",
)


# ============================================================
# Enums for Type Safety
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


# ============================================================
# Tool 1: Evaluate Irrigation Rules
# ============================================================


@mcp.tool()
async def evaluate_irrigation_rules(
    farm_id: str,
    crop_type: str,
    soil_type: str,
    current_soil_moisture_percent: float,
    temperature_c: float,
    rainfall_mm_last_7_days: float = 0.0,
    growth_stage_days: int = 0,
) -> dict[str, Any]:
    """Evaluate irrigation rules for a farm.

    Determines whether irrigation is needed and provides recommendations
    based on soil moisture, temperature, rainfall, and crop type.

    Args:
        farm_id: Unique farm identifier
        crop_type: Type of crop (cotton, wheat, vegetables)
        soil_type: Soil classification (sandy, loamy, clay, calcareous)
        current_soil_moisture_percent: Current soil moisture 0-100%
        temperature_c: Current temperature in Celsius
        rainfall_mm_last_7_days: Rainfall in last 7 days (mm)
        growth_stage_days: Days since planting

    Returns:
        Irrigation recommendation with timing and water amount
    """
    logger.info(
        "irrigation_evaluation",
        farm_id=farm_id,
        crop=crop_type,
        soil_moisture=current_soil_moisture_percent,
    )

    # Validate inputs
    crop_type.lower()
    soil = soil_type.lower()

    # Base threshold varies by soil type
    moisture_threshold = 60  # Default for loamy soil
    if soil == "sandy":
        moisture_threshold = 50
    elif soil == "clay":
        moisture_threshold = 70

    should_irrigate = False
    recommended_water_mm = 0.0
    timing = "anytime"
    reasoning = ""
    rule_id = ""

    # Check if irrigation is needed
    if current_soil_moisture_percent < moisture_threshold:
        should_irrigate = True
        confidence = 0.85

        # Calculate water amount based on deficit
        water_deficit = moisture_threshold - current_soil_moisture_percent
        recommended_water_mm = water_deficit * 2

        # Timing based on temperature
        if temperature_c > 30:
            timing = "6am"
            rule_id = "RULE_IRR_001_HIGH_TEMP"
        elif temperature_c < 10:
            timing = "noon"
            rule_id = "RULE_IRR_002_LOW_TEMP"
        else:
            timing = "6am"
            rule_id = "RULE_IRR_003_NORMAL"

        # Adjust for recent rainfall
        if rainfall_mm_last_7_days > 30:
            should_irrigate = False
            confidence = 0.95
            reasoning = f"Recent rainfall ({rainfall_mm_last_7_days}mm) sufficient"
            recommended_water_mm = 0

        if should_irrigate:
            reasoning = f"Soil moisture {current_soil_moisture_percent}% below threshold {moisture_threshold}%. Recommend {recommended_water_mm:.0f}mm at {timing}."
    else:
        rule_id = "RULE_IRR_004_SUFFICIENT"
        confidence = 0.90
        reasoning = (
            f"Soil moisture {current_soil_moisture_percent}% adequate. No irrigation needed."
        )

    return {
        "should_irrigate": should_irrigate,
        "recommended_water_mm": recommended_water_mm,
        "timing": timing,
        "confidence": confidence,
        "rule_id": rule_id,
        "reasoning": reasoning,
    }


# ============================================================
# Tool 2: Evaluate Fertilization Rules
# ============================================================


@mcp.tool()
async def evaluate_fertilization_rules(
    farm_id: str,
    crop_type: str,
    soil_type: str,
    soil_nitrogen_ppm: float | None = None,
    soil_phosphorus_ppm: float | None = None,
    soil_potassium_ppm: float | None = None,
    growth_stage_days: int = 0,
    previous_fertilizer_days_ago: int | None = None,
) -> dict[str, Any]:
    """Evaluate fertilization needs for a farm.

    Provides NPK recommendations based on soil analysis, crop requirements,
    and growth stage.

    Args:
        farm_id: Unique farm identifier
        crop_type: Type of crop (cotton, wheat, vegetables)
        soil_type: Soil classification
        soil_nitrogen_ppm: Current soil nitrogen (ppm)
        soil_phosphorus_ppm: Current soil phosphorus (ppm)
        soil_potassium_ppm: Current soil potassium (ppm)
        growth_stage_days: Days since planting
        previous_fertilizer_days_ago: Days since last fertilizer application

    Returns:
        NPK recommendations in kg/hectare with timing
    """
    logger.info(
        "fertilization_evaluation",
        farm_id=farm_id,
        crop=crop_type,
    )

    crop = crop_type.lower()

    # Default NPK values (kg/ha)
    if crop == "cotton":
        base_nitrogen = 150
        base_phosphorus = 80
        base_potassium = 80
        rule_id = "RULE_FERT_001_COTTON"
    elif crop == "wheat":
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

    if soil_nitrogen_ppm and soil_nitrogen_ppm > 30:
        nitrogen_recommendation *= 0.7

    if soil_phosphorus_ppm and soil_phosphorus_ppm > 20:
        phosphorus_recommendation *= 0.8

    if soil_potassium_ppm and soil_potassium_ppm > 200:
        potassium_recommendation *= 0.8

    # Adjust for growth stage
    should_fertilize = True
    timing = "Now"

    if growth_stage_days < 10:
        timing = "Post-planting (starter)"
        nitrogen_recommendation *= 1.1
    elif growth_stage_days > 100:
        timing = "Late season (post-flowering)"
        nitrogen_recommendation *= 0.5

    reasoning = f"Recommended NPK: N={nitrogen_recommendation:.0f}, P={phosphorus_recommendation:.0f}, K={potassium_recommendation:.0f} kg/ha. {timing}."

    return {
        "should_fertilize": should_fertilize,
        "nitrogen_kg_per_hectare": nitrogen_recommendation,
        "phosphorus_kg_per_hectare": phosphorus_recommendation,
        "potassium_kg_per_hectare": potassium_recommendation,
        "timing": timing,
        "confidence": 0.85,
        "rule_id": rule_id,
        "reasoning": reasoning,
    }


# ============================================================
# Tool 3: Evaluate Pest Control Rules
# ============================================================


@mcp.tool()
async def evaluate_pest_control_rules(
    farm_id: str,
    crop_type: str,
    temperature_c: float,
    humidity_percent: float,
    observed_pests: list[str] | None = None,
    growth_stage_days: int = 0,
    rainfall_mm_last_3_days: float = 0.0,
) -> dict[str, Any]:
    """Evaluate pest/disease risk and recommend control measures.

    Analyzes environmental conditions and observed pests to recommend
    appropriate control measures (biological, chemical, or cultural).

    Args:
        farm_id: Unique farm identifier
        crop_type: Type of crop
        temperature_c: Current temperature in Celsius
        humidity_percent: Current relative humidity 0-100%
        observed_pests: List of observed pest/disease names
        growth_stage_days: Days since planting
        rainfall_mm_last_3_days: Rainfall in last 3 days (mm)

    Returns:
        Pest assessment with recommended actions
    """
    logger.info(
        "pest_control_evaluation",
        farm_id=farm_id,
        crop=crop_type,
        observed_pests=observed_pests,
    )

    detected_pests = list(set(observed_pests or []))
    recommended_action = "Monitor closely"
    method = "cultural"
    severity = "low"
    rule_id = "RULE_PEST_001_BASELINE"
    confidence = 0.7

    # Environmental risk assessment
    high_risk_conditions = (
        temperature_c > 25 and humidity_percent > 70 and rainfall_mm_last_3_days > 20
    )

    if high_risk_conditions:
        severity = "high"
        confidence = 0.85
        recommended_action = "Preventive treatment recommended"
        method = "biological"
        if (
            "cotton_bollworm" not in detected_pests
            and "spider_mites" not in detected_pests
            and "leaf_curl_virus" not in detected_pests
        ):
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

    reasoning = f"Pests detected: {', '.join(detected_pests) if detected_pests else 'None'}. Conditions: {temperature_c}°C, {humidity_percent}% RH. {recommended_action}"

    return {
        "pests_detected": detected_pests,
        "recommended_action": recommended_action,
        "method": method,
        "severity": severity,
        "confidence": confidence,
        "rule_id": rule_id,
        "reasoning": reasoning,
    }


# ============================================================
# Tool 4: Calculate Subsidy
# ============================================================


@mcp.tool()
async def calculate_subsidy(
    farm_id: str,
    crop_type: str,
    hectares: float,
    soil_type: str,
    farmer_age: int | None = None,
    is_young_farmer: bool = False,
) -> dict[str, Any]:
    """Calculate government subsidy eligibility.

    Calculates available subsidies based on crop type, farm size,
    and farmer eligibility criteria.

    Args:
        farm_id: Unique farm identifier
        crop_type: Type of crop (cotton, wheat, vegetables)
        hectares: Farm size in hectares
        soil_type: Soil classification
        farmer_age: Farmer's age in years
        is_young_farmer: Whether farmer qualifies as young farmer

    Returns:
        Subsidy amount and eligibility conditions
    """
    logger.info(
        "subsidy_calculation",
        farm_id=farm_id,
        crop=crop_type,
        hectares=hectares,
    )

    crop = crop_type.lower()
    soil = soil_type.lower()

    eligible = True
    conditions = []

    # Base subsidy rates (AZN per hectare)
    subsidy_rates = {
        "cotton": 500,
        "wheat": 300,
        "vegetables": 400,
    }

    rate_per_hectare = subsidy_rates.get(crop, 300)
    subsidy_azn = rate_per_hectare * hectares

    # Track which bonuses are applied
    young_farmer_bonus = False
    calcareous_bonus = False

    # Young farmer bonus (+25%)
    if is_young_farmer or (farmer_age and farmer_age < 40):
        subsidy_azn *= 1.25
        young_farmer_bonus = True
        conditions.append("Young farmer bonus applied (+25%)")

    # Calcareous soil support (+15%)
    if soil == "calcareous":
        subsidy_azn *= 1.15
        calcareous_bonus = True
        conditions.append("Calcareous soil support applied (+15%)")

    # Determine rule_id based on applied bonuses
    if calcareous_bonus:
        rule_id = "RULE_SUBSIDY_003_SOIL_SUPPORT"
    elif young_farmer_bonus:
        rule_id = "RULE_SUBSIDY_002_YOUNG_FARMER"
    else:
        rule_id = "RULE_SUBSIDY_001_BASE"

    # Size limitations
    if hectares > 50:
        subsidy_azn *= 0.9
        conditions.append("Large farm reduction (-10%)")

    # Standard conditions
    conditions.extend(
        [
            "Must maintain production records",
            "Eco-friendly practices encouraged",
            "Must report production outcomes",
        ]
    )

    next_review = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

    return {
        "eligible": eligible,
        "subsidy_azn": subsidy_azn,
        "subsidy_per_hectare_azn": rate_per_hectare,
        "conditions": conditions,
        "rule_id": rule_id,
        "next_review_date": next_review,
    }


# ============================================================
# Tool 5: Predict Harvest Date
# ============================================================


@mcp.tool()
async def predict_harvest_date(
    farm_id: str,
    crop_type: str,
    planting_date: str,
    current_gdd_accumulated: float = 0.0,
    base_temperature_c: float = 10.0,
) -> dict[str, Any]:
    """Predict optimal harvest date based on Growing Degree Days.

    Uses GDD accumulation to predict crop maturity and optimal
    harvest timing.

    Args:
        farm_id: Unique farm identifier
        crop_type: Type of crop
        planting_date: Date planted (YYYY-MM-DD format)
        current_gdd_accumulated: Growing Degree Days accumulated so far
        base_temperature_c: Base temperature for GDD calculation

    Returns:
        Predicted harvest date with confidence
    """
    logger.info(
        "harvest_prediction",
        farm_id=farm_id,
        crop=crop_type,
        gdd=current_gdd_accumulated,
    )

    crop = crop_type.lower()

    # GDD requirements by crop
    gdd_requirements = {
        "cotton": 2600,
        "wheat": 2000,
        "vegetables": 1500,
    }

    target_gdd = gdd_requirements.get(crop, 2000)
    gdd_remaining = max(0, target_gdd - current_gdd_accumulated)

    # Average daily GDD accumulation
    avg_daily_gdd = 15

    days_to_harvest = int(gdd_remaining / avg_daily_gdd) if avg_daily_gdd > 0 else 60

    # Calculate predicted harvest date
    planting = datetime.strptime(planting_date, "%Y-%m-%d")
    predicted_harvest = planting + timedelta(days=days_to_harvest)

    maturity_confidence = min(0.95, 0.60 + (current_gdd_accumulated / target_gdd) * 0.35)

    recommended_checks = [
        "Monitor boll development",
        "Check for boll lock (cotton) or grain moisture (wheat)",
        "Plan harvesting logistics",
    ]

    rule_id = f"RULE_HARVEST_001_{crop.upper()}"

    return {
        "predicted_harvest_date": predicted_harvest.strftime("%Y-%m-%d"),
        "days_to_harvest": days_to_harvest,
        "maturity_confidence": maturity_confidence,
        "recommended_checks": recommended_checks,
        "rule_id": rule_id,
        "reasoning": f"GDD accumulated: {current_gdd_accumulated:.0f}/{target_gdd} ({(current_gdd_accumulated/target_gdd*100):.1f}% complete). Estimated {days_to_harvest} days to maturity.",
    }


# ============================================================
# Resources
# ============================================================


@mcp.resource("zekalab://rules")
async def get_rules_resource() -> str:
    """Get all agricultural rules as structured data."""
    import json

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

    return json.dumps(rules, indent=2)


@mcp.resource("zekalab://crop_profiles")
async def get_crop_profiles() -> str:
    """Get crop profiles with characteristics."""
    import json

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

    return json.dumps(profiles, indent=2)


@mcp.resource("zekalab://subsidy_database")
async def get_subsidy_database() -> str:
    """Get government subsidy program information."""
    import json

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

    return json.dumps(database, indent=2)


# ============================================================
# Startup
# ============================================================

if __name__ == "__main__":
    logger.info(
        "zekalab_fastmcp_startup",
        port=PORT,
        log_level=LOG_LEVEL,
        transport="http",
    )

    # Run with HTTP transport for LangChain MCP Adapters compatibility
    mcp.run(transport="http", host="0.0.0.0", port=PORT)
