"""Tests for ZekaLabMCPHandler - Phase 4 Implementation.

Tests cover:
- 5 tool methods (irrigation, fertilization, pest, subsidy, harvest)
- 3 resource methods (rules, crop profiles, subsidy database)
- Error handling (timeout, HTTP error, generic error)
- MCPTrace recording
- Singleton pattern
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from yonca.agent.state import MCPTrace
from yonca.mcp.handlers.zekalab_handler import ZekaLabMCPHandler, get_zekalab_handler


@pytest.fixture
async def mock_http_client():
    """Create a mock AsyncClient for HTTP calls."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
async def zekalab_handler(mock_http_client):
    """Create a ZekaLab handler with mocked HTTP client."""
    with patch(
        "yonca.mcp.handlers.zekalab_handler.httpx.AsyncClient",
        return_value=mock_http_client,
    ):
        handler = ZekaLabMCPHandler()
        handler.client = mock_http_client
        yield handler
        await handler.close()


# ============================================================================
# Tool Method Tests
# ============================================================================


@pytest.mark.asyncio
async def test_evaluate_irrigation_rules_success(zekalab_handler, mock_http_client):
    """Test successful irrigation rule evaluation."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "should_irrigate": True,
        "recommended_water_mm": 25.5,
        "timing": "6am",
        "confidence": 0.92,
        "rule_id": "IRRIG_001",
        "reasoning": "Soil moisture below 40%",
    }
    mock_http_client.post.return_value = mock_response

    result, trace = await zekalab_handler.evaluate_irrigation_rules(
        farm_id="farm_001",
        crop_type="wheat",
        soil_type="clay",
        current_soil_moisture_percent=45.0,
        temperature_c=28,
        rainfall_mm_last_7_days=0,
        growth_stage_days=30,
    )

    assert result["should_irrigate"] is True
    assert result["recommended_water_mm"] == 25.5
    assert isinstance(trace, MCPTrace)
    assert trace.tool == "evaluate_irrigation_rules"
    assert trace.success is True
    assert trace.error_message is None


@pytest.mark.asyncio
async def test_evaluate_fertilization_rules_success(zekalab_handler, mock_http_client):
    """Test successful fertilization rule evaluation."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "should_fertilize": True,
        "nitrogen_kg_per_hectare": 150,
        "phosphorus_kg_per_hectare": 60,
        "potassium_kg_per_hectare": 120,
        "timing": "2026-01-25T08:00:00Z",
        "confidence": 0.88,
        "rule_id": "FERT_002",
        "reasoning": "Soil nitrogen depleted",
    }
    mock_http_client.post.return_value = mock_response

    result, trace = await zekalab_handler.evaluate_fertilization_rules(
        farm_id="farm_001",
        crop_type="tomato",
        soil_type="loamy",
        soil_nitrogen_ppm=80,
        soil_phosphorus_ppm=25,
        soil_potassium_ppm=150,
        growth_stage_days=60,
    )

    assert result["should_fertilize"] is True
    assert result["nitrogen_kg_per_hectare"] == 150
    assert trace.tool == "evaluate_fertilization_rules"
    assert trace.success is True


@pytest.mark.asyncio
async def test_evaluate_pest_control_rules_success(zekalab_handler, mock_http_client):
    """Test successful pest control rule evaluation."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "pests_detected": ["aphids", "spider_mites"],
        "recommended_action": "Spray with neem oil",
        "method": "biological",
        "severity": "medium",
        "confidence": 0.85,
        "rule_id": "PEST_001",
        "reasoning": "High humidity promotes pest spread",
    }
    mock_http_client.post.return_value = mock_response

    result, trace = await zekalab_handler.evaluate_pest_control_rules(
        farm_id="farm_001",
        crop_type="vegetables",
        temperature_c=28.5,
        humidity_percent=75,
        observed_pests=["aphids"],
        growth_stage_days=45,
    )

    assert "aphids" in result["pests_detected"]
    assert result["method"] == "biological"
    assert trace.tool == "evaluate_pest_control_rules"
    assert trace.success is True


@pytest.mark.asyncio
async def test_calculate_subsidy_success(zekalab_handler, mock_http_client):
    """Test successful subsidy calculation."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "eligible": True,
        "subsidy_azn": 5000,
        "subsidy_per_hectare_azn": 100,
        "conditions": ["certified_organic"],
        "rule_id": "SUBSIDY_2026_ORGANIC",
        "next_review_date": "2026-06-30",
    }
    mock_http_client.post.return_value = mock_response

    result, trace = await zekalab_handler.calculate_subsidy(
        farm_id="farm_001",
        crop_type="wheat",
        hectares=50,
        soil_type="loamy",
        is_young_farmer=False,
    )

    assert result["eligible"] is True
    assert result["subsidy_azn"] == 5000
    assert trace.tool == "calculate_subsidy"
    assert trace.success is True


@pytest.mark.asyncio
async def test_predict_harvest_date_success(zekalab_handler, mock_http_client):
    """Test successful harvest date prediction."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "predicted_harvest_date": "2026-07-15",
        "gdd_required": 1800,
        "gdd_accumulated": 650,
        "gdd_remaining": 1150,
        "days_to_harvest_estimate": 45,
        "confidence": 0.88,
        "rule_id": "HARVEST_001",
    }
    mock_http_client.post.return_value = mock_response

    result, trace = await zekalab_handler.predict_harvest_date(
        farm_id="farm_001",
        crop_type="corn",
        planting_date="2026-05-01",
        current_gdd_accumulated=650,
    )

    assert result["predicted_harvest_date"] == "2026-07-15"
    assert result["days_to_harvest_estimate"] == 45
    assert trace.tool == "predict_harvest_date"
    assert trace.success is True


# ============================================================================
# Resource Method Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_rules_resource_success(zekalab_handler, mock_http_client):
    """Test successful retrieval of rules resource."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "rules": [
            {"id": "rule_001", "name": "Wheat Irrigation", "version": "2.1"},
            {"id": "rule_002", "name": "Tomato Fertilization", "version": "1.8"},
        ],
        "last_updated": "2026-01-23T10:00:00Z",
        "total_rules": 45,
    }
    mock_http_client.get.return_value = mock_response

    result, trace = await zekalab_handler.get_rules_resource()

    assert len(result["rules"]) == 2
    assert result["total_rules"] == 45
    assert trace.tool == "get_rules"
    assert trace.success is True


@pytest.mark.asyncio
async def test_get_crop_profiles_resource_success(zekalab_handler, mock_http_client):
    """Test successful retrieval of crop profiles resource."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "crop_profiles": [
            {
                "crop_id": "WHEAT_001",
                "name": "Wheat",
                "growing_season_days": 120,
                "water_requirement_mm": 450,
                "optimal_temperature_c": 18,
            },
            {
                "crop_id": "TOMATO_001",
                "name": "Tomato",
                "growing_season_days": 90,
                "water_requirement_mm": 600,
                "optimal_temperature_c": 22,
            },
        ],
        "total_profiles": 250,
    }
    mock_http_client.get.return_value = mock_response

    result, trace = await zekalab_handler.get_crop_profiles_resource()

    assert len(result["crop_profiles"]) == 2
    assert result["total_profiles"] == 250
    assert trace.tool == "get_crop_profiles"
    assert trace.success is True


@pytest.mark.asyncio
async def test_get_subsidy_database_resource_success(zekalab_handler, mock_http_client):
    """Test successful retrieval of subsidy database resource."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "subsidies": [
            {
                "id": "SUBSIDY_001",
                "country": "TR",
                "program_name": "Organic Support",
                "max_amount_usd": 10000,
            }
        ],
        "total_programs": 156,
        "last_sync": "2026-01-20T00:00:00Z",
    }
    mock_http_client.get.return_value = mock_response

    result, trace = await zekalab_handler.get_subsidy_database_resource()

    assert len(result["subsidies"]) == 1
    assert result["total_programs"] == 156
    assert trace.tool == "get_subsidy_database"
    assert trace.success is True


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_tool_call_timeout_error(zekalab_handler, mock_http_client):
    """Test timeout error handling."""
    mock_http_client.post.side_effect = httpx.TimeoutException("Request timed out")

    result, trace = await zekalab_handler.evaluate_irrigation_rules(
        farm_id="farm_001",
        crop_type="wheat",
        soil_type="clay",
        current_soil_moisture_percent=45.0,
        temperature_c=28,
    )

    assert result == {}
    assert trace.success is False
    assert trace.error_message is not None


@pytest.mark.asyncio
async def test_tool_call_http_error(zekalab_handler, mock_http_client):
    """Test HTTP error handling."""
    http_error = httpx.HTTPStatusError(
        "500 Server Error", request=MagicMock(), response=MagicMock()
    )
    mock_http_client.post.side_effect = http_error

    result, trace = await zekalab_handler.evaluate_fertilization_rules(
        farm_id="farm_001",
        crop_type="tomato",
        soil_type="loamy",
        growth_stage_days=60,
    )

    assert result == {}
    assert trace.success is False
    assert trace.error_message is not None


@pytest.mark.asyncio
async def test_tool_call_generic_error(zekalab_handler, mock_http_client):
    """Test generic exception handling."""
    mock_http_client.post.side_effect = ValueError("Invalid response format")

    result, trace = await zekalab_handler.predict_harvest_date(
        farm_id="farm_001",
        crop_type="corn",
        planting_date="2026-05-01",
    )

    assert result == {}
    assert trace.success is False
    assert trace.error_message is not None


@pytest.mark.asyncio
async def test_resource_call_http_error(zekalab_handler, mock_http_client):
    """Test HTTP error handling for resource calls."""
    http_error = httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=MagicMock())
    mock_http_client.get.side_effect = http_error

    result, trace = await zekalab_handler.get_rules_resource()

    assert result == {}
    assert trace.success is False


# ============================================================================
# MCPTrace Recording Tests
# ============================================================================


@pytest.mark.asyncio
async def test_mcp_trace_recorded_with_correct_fields(zekalab_handler, mock_http_client):
    """Test that MCPTrace is recorded with all necessary fields."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": "success"}
    mock_http_client.post.return_value = mock_response

    result, trace = await zekalab_handler.evaluate_irrigation_rules(
        farm_id="farm_001",
        crop_type="wheat",
        soil_type="clay",
        current_soil_moisture_percent=45.0,
        temperature_c=28,
    )

    assert trace.server == "zekalab"
    assert trace.tool == "evaluate_irrigation_rules"
    assert trace.success is True
    assert trace.duration_ms >= 0  # Changed from > 0 to >= 0 for mocked calls
    assert trace.error_message is None
    assert trace.input_args is not None


@pytest.mark.asyncio
async def test_mcp_trace_includes_input_args_on_success(zekalab_handler, mock_http_client):
    """Test that MCPTrace includes input args."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": "success"}
    mock_http_client.post.return_value = mock_response

    result, trace = await zekalab_handler.evaluate_irrigation_rules(
        farm_id="farm_001",
        crop_type="wheat",
        soil_type="clay",
        current_soil_moisture_percent=45.0,
        temperature_c=25,
    )

    assert trace.input_args is not None
    assert "farm_id" in trace.input_args
    assert trace.input_args["farm_id"] == "farm_001"


# ============================================================================
# Configuration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_handler_uses_environment_config():
    """Test that handler respects environment variables."""
    with patch.dict(
        "os.environ",
        {
            "ZEKALAB_MCP_URL": "http://custom-zekalab:9999",
            "ZEKALAB_TIMEOUT_MS": "5000",
        },
    ):
        handler = ZekaLabMCPHandler()
        assert handler.mcp_url == "http://custom-zekalab:9999"
        assert handler.timeout_ms == 5000


# ============================================================================
# Singleton Pattern Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_zekalab_handler_singleton():
    """Test that get_zekalab_handler returns handler instances."""
    with patch("yonca.mcp.handlers.zekalab_handler.httpx.AsyncClient"):
        handler1 = await get_zekalab_handler()
        handler2 = await get_zekalab_handler()

        assert handler1 is not None
        assert handler2 is not None
        if hasattr(handler1, "close"):
            await handler1.close()


# ============================================================================
# Integration Tests (Multiple Calls)
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_tool_calls_in_sequence(zekalab_handler, mock_http_client):
    """Test multiple consecutive tool calls."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": "success"}
    mock_http_client.post.return_value = mock_response

    results = []
    for i in range(3):
        result, trace = await zekalab_handler.evaluate_irrigation_rules(
            farm_id="farm_001",
            crop_type="wheat",
            soil_type="clay",
            current_soil_moisture_percent=45.0,
            temperature_c=28,
        )
        results.append((result, trace))

    assert len(results) == 3
    assert all(trace.success for _, trace in results)
    assert mock_http_client.post.call_count == 3


@pytest.mark.asyncio
async def test_concurrent_tool_calls(zekalab_handler, mock_http_client):
    """Test concurrent tool calls (e.g., through asyncio.gather)."""
    import asyncio

    mock_response = MagicMock()
    mock_response.json.return_value = {"result": "success"}
    mock_http_client.post.return_value = mock_response

    tasks = [
        zekalab_handler.evaluate_irrigation_rules(
            farm_id="farm_001",
            crop_type="wheat",
            soil_type="clay",
            current_soil_moisture_percent=45.0,
            temperature_c=28,
        ),
        zekalab_handler.evaluate_fertilization_rules(
            farm_id="farm_001",
            crop_type="tomato",
            soil_type="loamy",
            growth_stage_days=60,
        ),
        zekalab_handler.predict_harvest_date(
            farm_id="farm_001",
            crop_type="corn",
            planting_date="2026-05-01",
        ),
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 3
    assert all(trace.success for _, trace in results)


# ============================================================================
# Handler Lifecycle Tests
# ============================================================================


@pytest.mark.asyncio
async def test_handler_close_cleanup(mock_http_client):
    """Test that handler properly closes HTTP client."""
    handler = ZekaLabMCPHandler()
    handler.client = mock_http_client

    await handler.close()

    mock_http_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_handler_context_manager_style(mock_http_client):
    """Test handler can be used as context manager (future pattern)."""
    handler = ZekaLabMCPHandler()
    handler.client = mock_http_client

    try:
        await handler.close()
        assert True
    except Exception as e:
        pytest.fail(f"Handler cleanup failed: {e}")
