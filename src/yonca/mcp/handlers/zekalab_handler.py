# src/yonca/mcp/handlers/zekalab_handler.py
"""ZekaLab Internal MCP Server Handler.

Provides domain-specific abstraction over ZekaLab MCP server calls.
Handles irrigation, fertilization, pest control, subsidy, and harvest prediction.

Phase 4: Orchestration layer for internal rules engine.
"""

import asyncio
import os
import time
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from yonca.agent.state import MCPTrace

logger = structlog.get_logger(__name__)


class ZekaLabMCPHandler:
    """Handler for calling ZekaLab internal MCP server.

    Wraps HTTP calls to the MCP server with error handling, logging, and tracing.
    All calls are recorded as MCPTrace for audit trail.

    Configuration via environment variables:
        ZEKALAB_MCP_ENABLED: bool (default: True)
        ZEKALAB_MCP_URL: str (default: http://localhost:7777)
        ZEKALAB_MCP_SECRET: str (optional, for future auth)
        ZEKALAB_TIMEOUT_MS: int (default: 2000)
    """

    def __init__(self):
        """Initialize handler with environment config."""
        self.enabled = os.getenv("ZEKALAB_MCP_ENABLED", "true").lower() == "true"
        self.mcp_url = os.getenv("ZEKALAB_MCP_URL", "http://localhost:7777")
        self.secret = os.getenv("ZEKALAB_MCP_SECRET", None)
        self.timeout_ms = int(os.getenv("ZEKALAB_TIMEOUT_MS", 2000))
        self.timeout_s = self.timeout_ms / 1000.0
        self.client: httpx.AsyncClient | None = None

        logger.info(
            "zekalab_handler_init",
            enabled=self.enabled,
            url=self.mcp_url,
            timeout_ms=self.timeout_ms,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_s),
                limits=httpx.Limits(max_connections=10),
            )
        return self.client

    async def _call_tool(
        self,
        tool_name: str,
        input_args: dict[str, Any],
    ) -> tuple[dict[str, Any], MCPTrace]:
        """Call a ZekaLab MCP tool and return result + trace.

        Args:
            tool_name: Name of the tool to call (e.g., "evaluate_irrigation_rules")
            input_args: Tool arguments

        Returns:
            Tuple of (result_dict, MCPTrace) for audit trail

        Raises:
            TimeoutError: If call exceeds timeout
            Exception: Any other HTTP/network error
        """
        start_time = time.time()
        success = False
        error_message = None
        output = {}

        try:
            if not self.enabled:
                logger.warning(
                    "zekalab_mcp_disabled",
                    tool=tool_name,
                )
                raise RuntimeError("ZekaLab MCP is disabled")

            client = await self._get_client()
            url = f"{self.mcp_url}/tools/{tool_name}"

            logger.debug(
                "zekalab_mcp_call_start",
                tool=tool_name,
                url=url,
                args=input_args,
            )

            response = await client.post(
                url,
                json=input_args,
                timeout=self.timeout_s,
            )
            response.raise_for_status()

            output = response.json()
            success = True

            logger.debug(
                "zekalab_mcp_call_success",
                tool=tool_name,
                output_keys=list(output.keys()),
            )

        except asyncio.TimeoutError as e:
            error_message = f"Timeout after {self.timeout_ms}ms: {str(e)}"
            logger.error("zekalab_mcp_timeout", tool=tool_name, error=error_message)
            raise TimeoutError(error_message) from e

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error("zekalab_mcp_http_error", tool=tool_name, error=error_message)
            raise Exception(f"ZekaLab MCP error: {error_message}") from e

        except Exception as e:
            error_message = str(e)
            logger.error("zekalab_mcp_error", tool=tool_name, error=error_message)
            raise

        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Create trace record
            trace = MCPTrace(
                server="zekalab",
                tool=tool_name,
                input_args=input_args,
                output=output,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                timestamp=datetime.now(UTC),
            )

            logger.info(
                "zekalab_mcp_trace",
                tool=tool_name,
                success=success,
                duration_ms=f"{duration_ms:.1f}",
                error=error_message,
            )

            return output, trace

    # ====================================================================
    # Tool 1: Irrigation Rules
    # ====================================================================

    async def evaluate_irrigation_rules(
        self,
        farm_id: str,
        crop_type: str,
        soil_type: str,
        current_soil_moisture_percent: float,
        temperature_c: float,
        rainfall_mm_last_7_days: float = 0,
        growth_stage_days: int = 0,
    ) -> tuple[dict[str, Any], MCPTrace]:
        """Evaluate irrigation rules.

        Args:
            farm_id: Farm identifier
            crop_type: "cotton", "wheat", or "vegetables"
            soil_type: "sandy", "loamy", "clay", or "calcareous"
            current_soil_moisture_percent: 0-100
            temperature_c: Current temperature
            rainfall_mm_last_7_days: Recent rainfall
            growth_stage_days: Days since planting

        Returns:
            (result_dict, trace) where result contains:
                - should_irrigate: bool
                - recommended_water_mm: float
                - timing: str (6am/noon/6pm/anytime)
                - confidence: float (0-1)
                - rule_id: str
                - reasoning: str
        """
        input_args = {
            "farm_id": farm_id,
            "crop_type": crop_type,
            "soil_type": soil_type,
            "current_soil_moisture_percent": current_soil_moisture_percent,
            "temperature_c": temperature_c,
            "rainfall_mm_last_7_days": rainfall_mm_last_7_days,
            "growth_stage_days": growth_stage_days,
        }

        logger.info(
            "evaluate_irrigation",
            farm_id=farm_id,
            crop=crop_type,
            soil_moisture=current_soil_moisture_percent,
        )

        return await self._call_tool("evaluate_irrigation_rules", input_args)

    # ====================================================================
    # Tool 2: Fertilization Rules
    # ====================================================================

    async def evaluate_fertilization_rules(
        self,
        farm_id: str,
        crop_type: str,
        soil_type: str,
        soil_nitrogen_ppm: float | None = None,
        soil_phosphorus_ppm: float | None = None,
        soil_potassium_ppm: float | None = None,
        growth_stage_days: int = 0,
        previous_fertilizer_days_ago: int | None = None,
    ) -> tuple[dict[str, Any], MCPTrace]:
        """Evaluate fertilization rules.

        Args:
            farm_id: Farm identifier
            crop_type: "cotton", "wheat", or "vegetables"
            soil_type: Soil classification
            soil_nitrogen_ppm: Soil nitrogen level (optional)
            soil_phosphorus_ppm: Soil phosphorus level (optional)
            soil_potassium_ppm: Soil potassium level (optional)
            growth_stage_days: Days since planting
            previous_fertilizer_days_ago: When last fertilized (optional)

        Returns:
            (result_dict, trace) where result contains:
                - should_fertilize: bool
                - nitrogen_kg_per_hectare: float
                - phosphorus_kg_per_hectare: float
                - potassium_kg_per_hectare: float
                - timing: str
                - confidence: float
                - rule_id: str
                - reasoning: str
        """
        input_args = {
            "farm_id": farm_id,
            "crop_type": crop_type,
            "soil_type": soil_type,
            "soil_nitrogen_ppm": soil_nitrogen_ppm,
            "soil_phosphorus_ppm": soil_phosphorus_ppm,
            "soil_potassium_ppm": soil_potassium_ppm,
            "growth_stage_days": growth_stage_days,
            "previous_fertilizer_days_ago": previous_fertilizer_days_ago,
        }

        logger.info(
            "evaluate_fertilization",
            farm_id=farm_id,
            crop=crop_type,
            stage=growth_stage_days,
        )

        return await self._call_tool("evaluate_fertilization_rules", input_args)

    # ====================================================================
    # Tool 3: Pest Control Rules
    # ====================================================================

    async def evaluate_pest_control_rules(
        self,
        farm_id: str,
        crop_type: str,
        temperature_c: float,
        humidity_percent: float,
        observed_pests: list[str] | None = None,
        growth_stage_days: int = 0,
        rainfall_mm_last_3_days: float = 0,
    ) -> tuple[dict[str, Any], MCPTrace]:
        """Evaluate pest control rules.

        Args:
            farm_id: Farm identifier
            crop_type: "cotton", "wheat", or "vegetables"
            temperature_c: Current temperature
            humidity_percent: Current humidity (0-100)
            observed_pests: List of observed pests (optional)
            growth_stage_days: Days since planting
            rainfall_mm_last_3_days: Recent rainfall

        Returns:
            (result_dict, trace) where result contains:
                - pests_detected: list[str]
                - recommended_action: str
                - method: str (biological/chemical/cultural/integrated)
                - severity: str (low/medium/high/critical)
                - confidence: float
                - rule_id: str
                - reasoning: str
        """
        if observed_pests is None:
            observed_pests = []

        input_args = {
            "farm_id": farm_id,
            "crop_type": crop_type,
            "temperature_c": temperature_c,
            "humidity_percent": humidity_percent,
            "observed_pests": observed_pests,
            "growth_stage_days": growth_stage_days,
            "rainfall_mm_last_3_days": rainfall_mm_last_3_days,
        }

        logger.info(
            "evaluate_pest_control",
            farm_id=farm_id,
            crop=crop_type,
            pests=len(observed_pests),
        )

        return await self._call_tool("evaluate_pest_control_rules", input_args)

    # ====================================================================
    # Tool 4: Subsidy Calculator
    # ====================================================================

    async def calculate_subsidy(
        self,
        farm_id: str,
        crop_type: str,
        hectares: float,
        soil_type: str,
        farmer_age: int | None = None,
        is_young_farmer: bool = False,
    ) -> tuple[dict[str, Any], MCPTrace]:
        """Calculate government subsidy eligibility.

        Args:
            farm_id: Farm identifier
            crop_type: "cotton", "wheat", or "vegetables"
            hectares: Farm size in hectares
            soil_type: Soil classification
            farmer_age: Farmer age (optional)
            is_young_farmer: Young farmer flag

        Returns:
            (result_dict, trace) where result contains:
                - eligible: bool
                - subsidy_azn: float
                - subsidy_per_hectare_azn: float
                - conditions: list[str]
                - rule_id: str
                - next_review_date: str (YYYY-MM-DD)
        """
        input_args = {
            "farm_id": farm_id,
            "crop_type": crop_type,
            "hectares": hectares,
            "soil_type": soil_type,
            "farmer_age": farmer_age,
            "is_young_farmer": is_young_farmer,
        }

        logger.info(
            "calculate_subsidy",
            farm_id=farm_id,
            crop=crop_type,
            hectares=hectares,
        )

        return await self._call_tool("calculate_subsidy", input_args)

    # ====================================================================
    # Tool 5: Harvest Prediction
    # ====================================================================

    async def predict_harvest_date(
        self,
        farm_id: str,
        crop_type: str,
        planting_date: str,
        current_gdd_accumulated: float = 0,
        base_temperature_c: float = 10,
    ) -> tuple[dict[str, Any], MCPTrace]:
        """Predict crop harvest date.

        Args:
            farm_id: Farm identifier
            crop_type: "cotton", "wheat", or "vegetables"
            planting_date: Date planted (YYYY-MM-DD format)
            current_gdd_accumulated: Growing Degree Days accumulated
            base_temperature_c: Base temperature for GDD (default 10°C)

        Returns:
            (result_dict, trace) where result contains:
                - predicted_harvest_date: str (YYYY-MM-DD)
                - days_to_harvest: int
                - maturity_confidence: float (0-1)
                - recommended_checks: list[str]
                - rule_id: str
        """
        input_args = {
            "farm_id": farm_id,
            "crop_type": crop_type,
            "planting_date": planting_date,
            "current_gdd_accumulated": current_gdd_accumulated,
            "base_temperature_c": base_temperature_c,
        }

        logger.info(
            "predict_harvest_date",
            farm_id=farm_id,
            crop=crop_type,
            gdd=current_gdd_accumulated,
        )

        return await self._call_tool("predict_harvest_date", input_args)

    # ====================================================================
    # Resource Access
    # ====================================================================

    async def get_rules_resource(self) -> tuple[dict[str, Any], MCPTrace]:
        """Fetch all agricultural rules as resource data.

        Returns:
            (rules_dict, trace) containing all rules by category
        """
        logger.info("fetch_rules_resource")

        start_time = time.time()
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.mcp_url}/resources/rules",
                timeout=self.timeout_s,
            )
            response.raise_for_status()
            output = response.json()
            success = True
            error_message = None

        except Exception as e:
            output = {}
            success = False
            error_message = str(e)
            logger.error("rules_resource_error", error=error_message)

        finally:
            duration_ms = (time.time() - start_time) * 1000
            trace = MCPTrace(
                server="zekalab",
                tool="get_rules",
                input_args={},
                output={"rules_count": len(output.get("rules", {}))},
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                timestamp=datetime.now(UTC),
            )

        return output, trace

    async def get_crop_profiles_resource(self) -> tuple[dict[str, Any], MCPTrace]:
        """Fetch crop profiles as resource data.

        Returns:
            (profiles_dict, trace) containing crop characteristics
        """
        logger.info("fetch_crop_profiles_resource")

        start_time = time.time()
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.mcp_url}/resources/crop_profiles",
                timeout=self.timeout_s,
            )
            response.raise_for_status()
            output = response.json()
            success = True
            error_message = None

        except Exception as e:
            output = {}
            success = False
            error_message = str(e)
            logger.error("crop_profiles_error", error=error_message)

        finally:
            duration_ms = (time.time() - start_time) * 1000
            trace = MCPTrace(
                server="zekalab",
                tool="get_crop_profiles",
                input_args={},
                output={"crops_count": len(output)},
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                timestamp=datetime.now(UTC),
            )

        return output, trace

    async def get_subsidy_database_resource(self) -> tuple[dict[str, Any], MCPTrace]:
        """Fetch subsidy database as resource data.

        Returns:
            (subsidy_db, trace) containing government subsidy information
        """
        logger.info("fetch_subsidy_database_resource")

        start_time = time.time()
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.mcp_url}/resources/subsidy_database",
                timeout=self.timeout_s,
            )
            response.raise_for_status()
            output = response.json()
            success = True
            error_message = None

        except Exception as e:
            output = {}
            success = False
            error_message = str(e)
            logger.error("subsidy_database_error", error=error_message)

        finally:
            duration_ms = (time.time() - start_time) * 1000
            trace = MCPTrace(
                server="zekalab",
                tool="get_subsidy_database",
                input_args={},
                output={"programs_count": len(output.get("programs", {}))},
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                timestamp=datetime.now(UTC),
            )

        return output, trace

    async def close(self):
        """Close HTTP client connection."""
        if self.client:
            await self.client.aclose()
            self.client = None


# ========================================================================
# Singleton instance
# ========================================================================

_zekalab_handler: ZekaLabMCPHandler | None = None


async def get_zekalab_handler() -> ZekaLabMCPHandler:
    """Get or create ZekaLab MCP handler singleton."""
    global _zekalab_handler
    if _zekalab_handler is None:
        _zekalab_handler = ZekaLabMCPHandler()
    return _zekalab_handler
