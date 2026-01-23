"""Tests for WeatherMCPHandler - Phase 2 Implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from yonca.mcp.handlers.weather_handler import WeatherMCPHandler


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = AsyncMock()
    return client


@pytest.fixture
def weather_handler(mock_mcp_client):
    """Create a weather handler with mocked MCP client."""
    with patch("yonca.mcp.handlers.weather_handler.get_mcp_client") as mock_get_client:
        mock_get_client.return_value = mock_mcp_client
        handler = WeatherMCPHandler()
        handler.mcp_client = mock_mcp_client
        return handler


@pytest.mark.asyncio
async def test_get_forecast_success(weather_handler, mock_mcp_client):
    """Test successful weather forecast retrieval."""

    # Mock successful MCP response
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.data = {
        "current": {
            "temperature": 28.5,
            "humidity": 65,
            "wind_speed": 12,
            "rainfall_mm": 0,
        },
        "forecast": [
            {
                "date": "2026-01-24",
                "temperature_high": 30,
                "temperature_low": 22,
            }
        ],
        "gdd_today": 18.5,
        "gdd_accumulated_month": 245,
        "alerts": [],
    }

    mock_mcp_client.call_tool.return_value = mock_result

    # Call handler
    forecast = await weather_handler.get_forecast("farm_123", lat=40.4, lon=49.9)

    # Assertions
    assert forecast is not None
    assert forecast["current"]["temperature"] == 28.5
    assert forecast["data_source"] == "openweather-mcp"
    assert "fetched_at" in forecast


@pytest.mark.asyncio
async def test_get_forecast_mcp_failure(weather_handler, mock_mcp_client):
    """Test weather forecast when MCP fails."""

    # Mock failed MCP response
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.error_message = "API timeout"

    mock_mcp_client.call_tool.return_value = mock_result

    # Should raise exception
    with pytest.raises(Exception, match="MCP call failed"):
        await weather_handler.get_forecast("farm_123", lat=40.4, lon=49.9)


@pytest.mark.asyncio
async def test_get_alerts_success(weather_handler, mock_mcp_client):
    """Test successful weather alerts retrieval."""

    # Mock successful response
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.data = {
        "alerts": [
            {
                "type": "storm",
                "severity": "high",
                "description": "Severe thunderstorm warning",
                "starts_at": "2026-01-23T14:00:00Z",
                "ends_at": "2026-01-23T18:00:00Z",
            }
        ]
    }

    mock_mcp_client.call_tool.return_value = mock_result

    # Call handler
    alerts = await weather_handler.get_alerts("farm_123", lat=40.4, lon=49.9)

    # Assertions
    assert len(alerts["alerts"]) == 1
    assert alerts["alerts"][0]["type"] == "storm"


@pytest.mark.asyncio
async def test_get_alerts_mcp_failure_returns_empty(weather_handler, mock_mcp_client):
    """Test weather alerts gracefully returns empty on MCP failure."""

    # Mock failed response
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.error_message = "API error"

    mock_mcp_client.call_tool.return_value = mock_result

    # Call handler - should not raise, just return empty alerts
    alerts = await weather_handler.get_alerts("farm_123", lat=40.4, lon=49.9)

    # Assertions
    assert alerts["alerts"] == []


@pytest.mark.asyncio
async def test_get_current_conditions(weather_handler, mock_mcp_client):
    """Test getting current weather conditions."""

    # Mock forecast response
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.data = {
        "current": {
            "temperature": 28.5,
            "humidity": 65,
            "wind_speed": 12,
            "rainfall_mm": 0,
            "pressure": 1013,
            "dew_point": 18.5,
        }
    }

    mock_mcp_client.call_tool.return_value = mock_result

    # Call handler
    conditions = await weather_handler.get_current_conditions("farm_123")

    # Assertions
    assert conditions.temperature_c == 28.5
    assert conditions.humidity_percent == 65
    assert conditions.wind_speed_kmh == 12


@pytest.mark.asyncio
async def test_calculate_gdd(weather_handler, mock_mcp_client):
    """Test GDD calculation."""

    # Mock forecast response with GDD data
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.data = {
        "current": {"temperature": 25},
        "gdd_today": 15.5,
        "gdd_accumulated_month": 230,
        "gdd_accumulated_season": 1200,
    }

    mock_mcp_client.call_tool.return_value = mock_result

    # Mock the get_forecast to avoid database calls
    with patch.object(weather_handler, "get_forecast", return_value=mock_result.data):
        # Call handler
        gdd = await weather_handler.calculate_gdd("farm_123")

        # Assertions
        assert gdd["gdd_today"] == 15.5
        assert gdd["gdd_accumulated_month"] == 230
        assert gdd["gdd_accumulated_season"] == 1200
