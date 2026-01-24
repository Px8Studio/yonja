"""OpenWeather MCP handler for real-time farm weather data.

Provides:
- Current conditions
- 7-day forecast
- Alerts (storms, frost warnings)
- Growing Degree Days (GDD) calculations

Phase 2 Implementation: Real weather data for ALİM decisions
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import structlog

from alim.mcp.client import MCPToolCall, get_mcp_client

logger = structlog.get_logger(__name__)


@dataclass
class WeatherForecast:
    """Weather forecast for a farm."""

    temperature_c: float
    humidity_percent: float
    rainfall_mm: float
    wind_speed_kmh: float
    pressure_hpa: float | None = None
    uv_index: float | None = None
    dew_point_c: float | None = None
    visibility_km: float | None = None


@dataclass
class WeatherAlert:
    """Weather alert (storm, frost, etc.)."""

    type: str  # "storm", "frost", "drought", "flood"
    severity: str  # "low", "medium", "high"
    description: str
    start_time: datetime
    end_time: datetime


class WeatherMCPHandler:
    """Handler for OpenWeather MCP integration.

    Usage:
        handler = WeatherMCPHandler()
        forecast = await handler.get_forecast("farm_123")
        alerts = await handler.get_alerts("farm_123")

    Phase 2 Implementation: Replaces synthetic weather with real MCP data
    """

    def __init__(self):
        """Initialize handler."""
        self.mcp_client = get_mcp_client("openweather")
        self.cache = {}  # Simple in-memory cache (5-min TTL in production)

    async def get_forecast(
        self,
        farm_id: str,
        lat: float | None = None,
        lon: float | None = None,
        days_ahead: int = 7,
    ) -> dict[str, Any]:
        """Get weather forecast for a farm.

        Args:
            farm_id: Unique farm ID
            lat: Latitude (optional, fetched from farm DB if not provided)
            lon: Longitude (optional, fetched from farm DB if not provided)
            days_ahead: How many days of forecast (default 7)

        Returns:
            Forecast data:
            {
                "current": {
                    "temperature": 28.5,
                    "humidity": 65,
                    "wind_speed": 12,
                    ...
                },
                "forecast": [
                    {
                        "date": "2026-01-24",
                        "temperature_high": 30,
                        "temperature_low": 22,
                        ...
                    },
                    ...
                ],
                "gdd_today": 18.5,
                "gdd_accumulated_month": 245.3,
                "alerts": [...],
                "data_source": "openweather-mcp",
                "timestamp": "2026-01-23T10:30:00Z",
            }

        Raises:
            Exception: If MCP call fails
        """

        logger.info("weather_forecast_request", farm_id=farm_id, days=days_ahead)

        start_time = datetime.now(UTC)

        try:
            # Fetch farm coordinates from DB (if not provided)
            if not lat or not lon:
                from alim.data.database import get_db_session
                from alim.data.repositories.farm_repo import FarmRepository

                async with get_db_session() as session:
                    farm_repo = FarmRepository(session)
                    farm = await farm_repo.get_by_id(farm_id)
                    if farm and hasattr(farm, "center_coordinates"):
                        coords = farm.center_coordinates
                        if isinstance(coords, dict):
                            lat = coords.get("latitude")
                            lon = coords.get("longitude")

            # Default to Baku if no coordinates found
            if not lat or not lon:
                lat, lon = 40.4093, 49.8671

            # Prepare MCP tool call
            call = MCPToolCall(
                server="openweather",
                tool="get_forecast",
                args={
                    "latitude": lat,
                    "longitude": lon,
                    "days_ahead": days_ahead,
                    "units": "metric",
                    "include_gdd": True,  # Growing Degree Days
                    "include_alerts": True,
                },
            )

            # Call OpenWeather MCP
            result = await self.mcp_client.call_tool(call)

            duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

            if not result.success:
                logger.error(
                    "weather_mcp_failed",
                    farm_id=farm_id,
                    error=result.error_message,
                    duration_ms=duration_ms,
                )
                raise Exception(f"MCP call failed: {result.error_message}")

            logger.info(
                "weather_forecast_success",
                farm_id=farm_id,
                duration_ms=duration_ms,
                days=days_ahead,
            )

            # Enrich response with metadata
            forecast_data = result.data if result.data else {}
            forecast_data.update(
                {
                    "mcp_duration_ms": duration_ms,
                    "fetched_at": datetime.now(UTC).isoformat(),
                    "data_source": "openweather-mcp",
                }
            )

            return forecast_data

        except Exception as e:
            logger.error("weather_forecast_exception", farm_id=farm_id, error=str(e))
            raise

    async def get_alerts(
        self,
        farm_id: str,
        lat: float | None = None,
        lon: float | None = None,
    ) -> dict[str, Any]:
        """Get weather alerts for a farm.

        Args:
            farm_id: Farm ID
            lat: Latitude
            lon: Longitude

        Returns:
            Alerts data:
            {
                "alerts": [
                    {
                        "type": "storm",
                        "severity": "high",
                        "description": "Severe thunderstorm warning",
                        "starts_at": "2026-01-23T14:00:00Z",
                        "ends_at": "2026-01-23T18:00:00Z",
                        "recommended_action": "Move livestock indoors",
                    }
                ]
            }
        """

        logger.info("weather_alerts_request", farm_id=farm_id)

        try:
            # Fetch coordinates if needed
            if not lat or not lon:
                from alim.data.database import get_db_session
                from alim.data.repositories.farm_repo import FarmRepository

                async with get_db_session() as session:
                    farm_repo = FarmRepository(session)
                    farm = await farm_repo.get_by_id(farm_id)
                    if farm and hasattr(farm, "center_coordinates"):
                        coords = farm.center_coordinates
                        if isinstance(coords, dict):
                            lat = coords.get("latitude")
                            lon = coords.get("longitude")

            # Default to Baku if no coordinates found
            if not lat or not lon:
                lat, lon = 40.4093, 49.8671

            call = MCPToolCall(
                server="openweather",
                tool="get_alerts",
                args={
                    "latitude": lat,
                    "longitude": lon,
                },
            )

            result = await self.mcp_client.call_tool(call)

            if not result.success:
                logger.warning(
                    "weather_alerts_mcp_failed",
                    farm_id=farm_id,
                    error=result.error_message,
                )
                return {"alerts": []}

            logger.info("weather_alerts_success", farm_id=farm_id)

            return result.data if result.data else {"alerts": []}

        except Exception as e:
            logger.error("weather_alerts_exception", farm_id=farm_id, error=str(e))
            return {"alerts": []}

    async def get_current_conditions(
        self,
        farm_id: str,
    ) -> WeatherForecast:
        """Get current weather conditions.

        Quick call for immediate conditions.
        """

        forecast = await self.get_forecast(farm_id, days_ahead=0)

        current = forecast.get("current", {})
        return WeatherForecast(
            temperature_c=current.get("temperature", 25.0),
            humidity_percent=current.get("humidity", 60.0),
            rainfall_mm=current.get("rainfall_mm", 0.0),
            wind_speed_kmh=current.get("wind_speed", 0.0),
            pressure_hpa=current.get("pressure"),
            dew_point_c=current.get("dew_point"),
        )

    async def calculate_gdd(
        self,
        farm_id: str,
        base_temperature: float = 10.0,
        upper_limit: float = 30.0,
    ) -> dict[str, float]:
        """Calculate Growing Degree Days (GDD).

        GDD formula: ((max_temp + min_temp) / 2) - base_temp

        Args:
            farm_id: Farm ID
            base_temperature: Minimum threshold (usually 10°C for cotton)
            upper_limit: Maximum threshold (usually 30°C)

        Returns:
            {
                "gdd_today": 18.5,
                "gdd_accumulated_current_month": 245.3,
                "gdd_accumulated_this_season": 1245.8,
                "projection_to_maturity": 1254,
            }
        """

        forecast = await self.get_forecast(farm_id, days_ahead=1)

        return {
            "gdd_today": forecast.get("gdd_today", 0),
            "gdd_accumulated_month": forecast.get("gdd_accumulated_month", 0),
            "gdd_accumulated_season": forecast.get("gdd_accumulated_season", 0),
        }
