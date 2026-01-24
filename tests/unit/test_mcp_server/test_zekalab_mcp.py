"""Unit tests for ZekaLab MCP Server endpoints.

Tests all 5 tools:
- evaluate_irrigation_rules
- evaluate_fertilization_rules
- evaluate_pest_control_rules
- calculate_subsidy
- predict_harvest_date

Plus 3 resources and health check.
"""

from datetime import datetime

import pytest
from alim.mcp_server.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ============================================================
# Health Check Tests
# ============================================================


def test_health_check(client):
    """Test server health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "zekalab-internal-mcp"
    assert data["version"] == "1.0.0"


# ============================================================
# Tool 1: Irrigation Rules Tests
# ============================================================


def test_irrigation_low_moisture(client):
    """Test irrigation rule when soil moisture is low."""
    payload = {
        "farm_id": "farm_001",
        "crop_type": "cotton",
        "soil_type": "loamy",
        "current_soil_moisture_percent": 45,
        "temperature_c": 28,
        "rainfall_mm_last_7_days": 5,
        "growth_stage_days": 60,
    }

    response = client.post("/tools/evaluate_irrigation_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["should_irrigate"] is True
    assert data["recommended_water_mm"] > 0
    assert data["confidence"] > 0.8
    assert "RULE_IRR" in data["rule_id"]


def test_irrigation_high_moisture(client):
    """Test irrigation rule when soil moisture is sufficient."""
    payload = {
        "farm_id": "farm_002",
        "crop_type": "wheat",
        "soil_type": "clay",
        "current_soil_moisture_percent": 75,
        "temperature_c": 20,
        "rainfall_mm_last_7_days": 15,
        "growth_stage_days": 45,
    }

    response = client.post("/tools/evaluate_irrigation_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["should_irrigate"] is False
    assert data["recommended_water_mm"] == 0
    assert data["confidence"] > 0.8


def test_irrigation_recent_rainfall(client):
    """Test irrigation rule with recent heavy rainfall."""
    payload = {
        "farm_id": "farm_003",
        "crop_type": "cotton",
        "soil_type": "sandy",
        "current_soil_moisture_percent": 40,
        "temperature_c": 25,
        "rainfall_mm_last_7_days": 50,  # Heavy rainfall
        "growth_stage_days": 75,
    }

    response = client.post("/tools/evaluate_irrigation_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Should not irrigate due to recent rainfall despite low moisture
    assert data["should_irrigate"] is False
    assert "rainfall" in data["reasoning"].lower()


# ============================================================
# Tool 2: Fertilization Rules Tests
# ============================================================


def test_fertilization_cotton(client):
    """Test fertilization rule for cotton."""
    payload = {
        "farm_id": "farm_004",
        "crop_type": "cotton",
        "soil_type": "loamy",
        "soil_nitrogen_ppm": 15,
        "soil_phosphorus_ppm": 12,
        "soil_potassium_ppm": 150,
        "growth_stage_days": 30,
    }

    response = client.post("/tools/evaluate_fertilization_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["should_fertilize"] is True
    assert data["nitrogen_kg_per_hectare"] > 100
    assert data["confidence"] > 0.8
    assert "RULE_FERT" in data["rule_id"]


def test_fertilization_wheat_rich_soil(client):
    """Test fertilization for wheat in nutrient-rich soil."""
    payload = {
        "farm_id": "farm_005",
        "crop_type": "wheat",
        "soil_type": "loamy",
        "soil_nitrogen_ppm": 40,  # High nitrogen
        "soil_phosphorus_ppm": 35,  # High phosphorus
        "soil_potassium_ppm": 250,  # High potassium
        "growth_stage_days": 20,
    }

    response = client.post("/tools/evaluate_fertilization_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["should_fertilize"] is True
    # Recommendation should be reduced due to high soil nutrients
    assert data["nitrogen_kg_per_hectare"] < 120


def test_fertilization_late_season(client):
    """Test fertilization in late season (flowering)."""
    payload = {
        "farm_id": "farm_006",
        "crop_type": "cotton",
        "soil_type": "sandy",
        "growth_stage_days": 110,  # Late season
    }

    response = client.post("/tools/evaluate_fertilization_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "late season" in data["timing"].lower() or "post-flower" in data["timing"].lower()


# ============================================================
# Tool 3: Pest Control Rules Tests
# ============================================================


def test_pest_control_no_pests(client):
    """Test pest control with no observed pests."""
    payload = {
        "farm_id": "farm_007",
        "crop_type": "cotton",
        "temperature_c": 22,
        "humidity_percent": 45,
        "observed_pests": [],
        "growth_stage_days": 50,
        "rainfall_mm_last_3_days": 5,
    }

    response = client.post("/tools/evaluate_pest_control_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["pests_detected"]) == 0
    assert data["severity"] == "low"


def test_pest_control_high_risk_weather(client):
    """Test pest control in high-risk weather conditions."""
    payload = {
        "farm_id": "farm_008",
        "crop_type": "cotton",
        "temperature_c": 28,  # High temp
        "humidity_percent": 75,  # High humidity
        "observed_pests": [],
        "growth_stage_days": 60,
        "rainfall_mm_last_3_days": 30,  # Recent rain
    }

    response = client.post("/tools/evaluate_pest_control_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["severity"] == "high"
    assert "preventive" in data["recommended_action"].lower()


def test_pest_control_bollworm_detected(client):
    """Test pest control when cotton bollworm is detected."""
    payload = {
        "farm_id": "farm_009",
        "crop_type": "cotton",
        "temperature_c": 25,
        "humidity_percent": 60,
        "observed_pests": ["cotton_bollworm"],
        "growth_stage_days": 75,
        "rainfall_mm_last_3_days": 10,
    }

    response = client.post("/tools/evaluate_pest_control_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "cotton_bollworm" in data["pests_detected"]
    assert data["severity"] == "critical"
    assert "immediate" in data["recommended_action"].lower()
    assert data["confidence"] > 0.9


def test_pest_control_spider_mites(client):
    """Test pest control for spider mites."""
    payload = {
        "farm_id": "farm_010",
        "crop_type": "cotton",
        "temperature_c": 30,
        "humidity_percent": 50,
        "observed_pests": ["spider_mites"],
        "growth_stage_days": 80,
    }

    response = client.post("/tools/evaluate_pest_control_rules", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "spider_mites" in data["pests_detected"]
    assert data["method"] == "chemical"


# ============================================================
# Tool 4: Subsidy Calculation Tests
# ============================================================


def test_subsidy_basic_cotton(client):
    """Test basic subsidy calculation for cotton."""
    payload = {
        "farm_id": "farm_011",
        "crop_type": "cotton",
        "hectares": 10,
        "soil_type": "loamy",
        "is_young_farmer": False,
    }

    response = client.post("/tools/calculate_subsidy", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["eligible"] is True
    # 10 ha × 500 AZN/ha = 5000 AZN
    assert data["subsidy_azn"] == pytest.approx(5000, rel=0.1)
    assert data["subsidy_per_hectare_azn"] == 500


def test_subsidy_young_farmer_bonus(client):
    """Test subsidy with young farmer bonus."""
    payload = {
        "farm_id": "farm_012",
        "crop_type": "wheat",
        "hectares": 5,
        "soil_type": "loamy",
        "farmer_age": 35,
        "is_young_farmer": True,
    }

    response = client.post("/tools/calculate_subsidy", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 5 ha × 300 AZN/ha × 1.25 (young farmer) = 1875 AZN
    assert data["subsidy_azn"] == pytest.approx(1875, rel=0.1)
    assert "young farmer" in str(data["conditions"]).lower()


def test_subsidy_calcareous_soil(client):
    """Test subsidy with calcareous soil bonus."""
    payload = {
        "farm_id": "farm_013",
        "crop_type": "vegetables",
        "hectares": 8,
        "soil_type": "calcareous",
    }

    response = client.post("/tools/calculate_subsidy", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 8 ha × 400 AZN/ha × 1.15 (calcareous) = 3680 AZN
    assert data["subsidy_azn"] == pytest.approx(3680, rel=0.1)
    assert any("calcareous" in c.lower() for c in data["conditions"])


def test_subsidy_large_farm_reduction(client):
    """Test subsidy reduction for large farms."""
    payload = {
        "farm_id": "farm_014",
        "crop_type": "cotton",
        "hectares": 100,
        "soil_type": "loamy",
    }

    response = client.post("/tools/calculate_subsidy", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 100 ha × 500 AZN/ha × 0.9 (large farm) = 45000 AZN
    assert data["subsidy_azn"] == pytest.approx(45000, rel=0.1)
    assert any("large farm" in c.lower() for c in data["conditions"])


# ============================================================
# Tool 5: Harvest Prediction Tests
# ============================================================


def test_harvest_prediction_cotton(client):
    """Test harvest date prediction for cotton."""
    planting_date = "2026-04-01"
    payload = {
        "farm_id": "farm_015",
        "crop_type": "cotton",
        "planting_date": planting_date,
        "current_gdd_accumulated": 1300,
        "base_temperature_c": 10,
    }

    response = client.post("/tools/predict_harvest_date", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["days_to_harvest"] > 0
    assert data["maturity_confidence"] > 0.6
    assert "RULE_HARVEST" in data["rule_id"]
    # Predicted date should be in the future
    predicted = datetime.strptime(data["predicted_harvest_date"], "%Y-%m-%d")
    today = datetime.now()
    assert predicted > today


def test_harvest_prediction_wheat(client):
    """Test harvest date prediction for wheat."""
    planting_date = "2026-10-15"
    payload = {
        "farm_id": "farm_016",
        "crop_type": "wheat",
        "planting_date": planting_date,
        "current_gdd_accumulated": 800,
    }

    response = client.post("/tools/predict_harvest_date", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["days_to_harvest"] > 0
    # Wheat matures faster than cotton
    assert "WHEAT" in data["rule_id"]


def test_harvest_prediction_mature_crop(client):
    """Test harvest prediction when crop is nearly mature."""
    planting_date = "2025-04-01"
    payload = {
        "farm_id": "farm_017",
        "crop_type": "cotton",
        "planting_date": planting_date,
        "current_gdd_accumulated": 2500,  # Nearly at 2600 target
    }

    response = client.post("/tools/predict_harvest_date", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Should be close to harvest
    assert data["days_to_harvest"] < 20
    assert data["maturity_confidence"] > 0.9


# ============================================================
# Resources Tests
# ============================================================


def test_get_rules_resource(client):
    """Test rules resource endpoint."""
    response = client.get("/resources/rules")
    assert response.status_code == 200
    data = response.json()

    assert "version" in data
    assert "rules" in data
    assert "irrigation" in data["rules"]
    assert "fertilization" in data["rules"]
    assert "pest_control" in data["rules"]


def test_get_crop_profiles_resource(client):
    """Test crop profiles resource endpoint."""
    response = client.get("/resources/crop_profiles")
    assert response.status_code == 200
    data = response.json()

    assert "cotton" in data
    assert "wheat" in data
    assert "vegetables" in data

    # Check cotton profile structure
    cotton = data["cotton"]
    assert "gdd_requirement" in cotton
    assert "water_requirement_mm" in cotton
    assert "nitrogen_kg_ha" in cotton


def test_get_subsidy_database_resource(client):
    """Test subsidy database resource endpoint."""
    response = client.get("/resources/subsidy_database")
    assert response.status_code == 200
    data = response.json()

    assert "version" in data
    assert "programs" in data
    assert "cotton" in data["programs"]
    assert "wheat" in data["programs"]

    # Check program structure
    cotton_prog = data["programs"]["cotton"]
    assert "rate_azn_per_hectare" in cotton_prog
    assert cotton_prog["rate_azn_per_hectare"] == 500


# ============================================================
# Error Handling Tests
# ============================================================


def test_irrigation_invalid_crop_type(client):
    """Test irrigation with invalid crop type."""
    payload = {
        "farm_id": "farm_018",
        "crop_type": "invalid_crop",
        "soil_type": "loamy",
        "current_soil_moisture_percent": 50,
        "temperature_c": 25,
    }

    response = client.post("/tools/evaluate_irrigation_rules", json=payload)
    assert response.status_code == 422  # Validation error


def test_subsidy_invalid_hectares(client):
    """Test subsidy with negative hectares."""
    payload = {
        "farm_id": "farm_019",
        "crop_type": "cotton",
        "hectares": -5,  # Invalid
        "soil_type": "loamy",
    }

    response = client.post("/tools/calculate_subsidy", json=payload)
    assert response.status_code == 422  # Validation error


def test_harvest_invalid_date_format(client):
    """Test harvest prediction with invalid date format."""
    payload = {
        "farm_id": "farm_020",
        "crop_type": "cotton",
        "planting_date": "invalid-date",
        "current_gdd_accumulated": 1000,
    }

    response = client.post("/tools/predict_harvest_date", json=payload)
    assert response.status_code == 500  # Server error (date parsing fails)
